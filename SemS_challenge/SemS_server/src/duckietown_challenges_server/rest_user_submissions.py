# coding=utf-8
import json
import sys
from collections import OrderedDict

import colander
from cornice.validators import colander_querystring_validator

from duckietown_challenges import ChallengesConstants as CS
from duckietown_challenges_server.db_challenges import get_challenge_by_name
from . import cslogger
from .auth import valid_dt1_token, is_superadmin
from .database import db_connection
from .misc import result_success, result_failure
from .my_logging import dbinfo, dberror
from .request_validation import challenge_ids_list_validator
from .rest import s_submissions, s_submissions_list, s_reset_submission, s_reset_job

s_submissions_sort_by_map = {
    'date': 'last_status_change',
    'challenge': 'challenge_id',
    'challenge_id': 'challenge_id',
    'submission': 'submission_id',
    'submission_id': 'submission_id',
    'status': 'status'
}


# QueryString scheme
class S_Submissions_GET_Schema(colander.MappingSchema):
    challenge_id = colander.SchemaNode(
            colander.String(),
            validator=colander.Function(challenge_ids_list_validator),
            missing=None
    )
    status = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf(CS.ALLOWED_SUB_STATUS),
            missing=None
    )
    keywords = colander.SchemaNode(
            colander.String(),
            missing=None
    )
    sort_by = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf(s_submissions_sort_by_map.keys()),
            missing=False
    )
    sort_order = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf(['asc', 'desc', 'ASC', 'DESC']),
            missing='ASC'
    )
    page = colander.SchemaNode(
            colander.Int(),
            validator=colander.Range(1, sys.maxint),
            missing=1
    )
    results = colander.SchemaNode(
            colander.Int(),
            validator=colander.Range(1, sys.maxint),
            missing=sys.maxint
    )


@s_submissions.get(schema=S_Submissions_GET_Schema(), validators=[colander_querystring_validator, valid_dt1_token])
def submissions(request):
    with db_connection(request) as cursor:
        user_id = request.validated['uid']
        # base query
        query = """
            SELECT SQL_CALC_FOUND_ROWS S.submission_id, S.challenge_id, S.status, S.last_status_change, S.date_submitted, S.parameters,
            aido_challenges.queue_name, S.user_label, S.user_metadata
            FROM aido_submissions as S, aido_challenges
            WHERE S.user_id = %s AND {where1} AND {where2} AND {where3}
            AND S.challenge_id = aido_challenges.challenge_id
            ORDER BY {order_by}
            LIMIT {limit}
        """
        args = [user_id]
        query_parts = {
            'where1': '1',
            'where2': '1',
            'where3': '1',
            'order_by': 'S.last_status_change DESC'
        }
        # filter by challenge_id
        if request.validated['challenge_id']:
            ids = [id_.strip() for id_ in request.validated['challenge_id'].split(',')]
            query_parts['where1'] = 'S.challenge_id IN (%s)' % ','.join(["'%s'" % s for s in ids])
        # filter by status
        if request.validated['status']:
            query_parts['where2'] = "S.status = %s"
            args.append(request.validated['status'])
        # filter by keywords
        if request.validated['keywords']:
            query_parts['where3'] = "JSON_EXTRACT(S.parameters, '$.user_label') LIKE %s"
            args.append('%' + request.validated['keywords'] + '%')
        # sorting
        if request.validated['sort_by']:
            sort_by_field = s_submissions_sort_by_map[request.validated['sort_by']]
            sort_by_order = request.validated['sort_order']
            query_parts['order_by'] = "S.%s %s" % (sort_by_field, sort_by_order)
        # pagination
        start = (request.validated['page'] - 1) * request.validated['results']
        count = request.validated['results']
        query_parts['limit'] = "%s, %s" % (start, count)

        # build and execute query
        query = query.format(**query_parts)
        cursor.execute(query, args)

        results = OrderedDict()
        for submission_id, challenge_id, status, last_status_change, date_submitted, parameters, challenge_name, user_label, user_metadata in cursor.fetchall():
            user_label = json.loads(user_label)
            results[submission_id] = dict(submission_id=submission_id,
                                          status=status,
                                          date_submitted=date_submitted.isoformat(),
                                          last_status_change=last_status_change.isoformat(),
                                          parameters=parameters,
                                          challenge_id=challenge_id,
                                          challenge_name=challenge_name,
                                          user_label=user_label,
                                          user_metadata=user_metadata
                                          )

        query = "SELECT FOUND_ROWS()"
        cursor.execute(query)
        total, = cursor.fetchone()

        return result_success(results, total)


@s_submissions_list.get(schema=S_Submissions_GET_Schema(), validators=[colander_querystring_validator, valid_dt1_token])
def submissions_list(request):
    res = submissions(request)
    res['result'] = res['result'].values()
    return res


@s_submissions.post(validators=valid_dt1_token)
def add_submission(request):
    with db_connection(request) as cursor:
        user_id = request.validated['uid']

        text = request.text

        cslogger.debug('%s %r' % (user_id, text))

        data = json.loads(text)

        try:
            queue = data['queue']
            parameters = data['parameters']
            user_label = data['parameters'].pop('user_label')
            user_metadata = data['parameters'].pop('user_payload')
            protocols_submission = data['parameters'].pop('protocols')
        except KeyError as e:
            msg = 'Could not parse\n\n%s\n\n %s' % (text, e)
            return result_failure(msg)

        if not isinstance(user_label, str):
            user_label = str(user_label)

        try:
            challenge = get_challenge_by_name(cursor, queue)
        except KeyError:
            msg = 'Could not find challenge by name of "%s"' % queue
            cursor.execute('select queue_name from aido_challenges')
            available = [_ for (_,) in cursor.fetchall()]

            msg += '\n available: %s' % ", ".join(sorted(available))
            cslogger.error(msg)
            return result_failure(msg)

        # challenge_id, protocol_challenge = cursor.fetchone()
        if challenge.protocol not in protocols_submission:
            msg = ('The submission has protocol %s but the server accepts %s' %
                   (protocols_submission, challenge.protocol))
            return result_failure(msg)

        if not challenge.is_open:
            website = 'https://challenges.duckietown.org/'
            msg = '''

The challenge "%s" closed on %s.

Either the competition has finished, or there is a new version of this challenge 
to which you should submit. Please consult the website %s.
 
 
''' % (queue, challenge.date_close.strftime('%b %-d, %Y'), website)

            return result_failure(msg)

        cmd = """
    INSERT INTO aido_submissions(user_id, date_submitted, status, last_status_change, challenge_id, parameters,
    evaluation_parameters, user_label, user_metadata)
        VALUES(%s, UTC_TIMESTAMP(), %s, UTC_TIMESTAMP(), %s ,%s, %s, %s, %s)
    """
        status = CS.STATUS_SUBMITTED
        values = (user_id, status, challenge.challenge_id, json.dumps(parameters), 'null',
                  json.dumps(user_label),
                  json.dumps(user_metadata))

        cursor.execute(cmd, values)

        submission_id = cursor.lastrowid

        dbinfo(cursor, "User {submitter} has created submission {submission} for challenge {challenge}",

               submission_id=submission_id,

               challenge_id=challenge.challenge_id,
               submitter_id=user_id)

        user_msg = """

Thanks for your submission.

Please note that in this phase we might reset the DB from time to time.
        
        """
        return result_success(submission_id, user_msg=user_msg)


@s_submissions.delete(validators=valid_dt1_token)
def retire_submission(request):
    with db_connection(request) as cursor:
        user_id = request.validated['uid']

        text = request.text
        data = json.loads(text)

        submission_id = data['submission_id']
        cmd = 'SELECT status FROM aido_submissions WHERE user_id = %s and submission_id = %s'
        args = (user_id, submission_id)
        cursor.execute(cmd, args)
        if cursor.rowcount == 0:
            msg = 'Could not find submission %s' % submission_id
            return result_failure(msg)

        status, = cursor.fetchone()

        # TODO: only allow for particular status?

        cmd = "UPDATE aido_submissions SET user_retired = TRUE where submission_id = %s"
        args = (submission_id,)
        cursor.execute(cmd, args)

        dbinfo(cursor, "User {submitter} has retired submission {submission}.",
               submission_id=submission_id,
               submitter_id=user_id)

        return result_success(submission_id)


@s_reset_job.post(validators=valid_dt1_token)
def reset_job_request(request):
    with db_connection(request) as cursor:
        user_id = request.validated['uid']

        text = request.text
        data = json.loads(text)

        job_id = data['job_id']

        return reset_job(cursor, user_id, job_id)


@s_reset_submission.post(validators=valid_dt1_token)
def reset_submission_req(request):
    with db_connection(request) as cursor:
        user_id = request.validated['uid']

        text = request.text
        data = json.loads(text)
        submission_id = data['submission_id']
        return reset_submission(cursor, user_id, submission_id)


def reset_job(cursor, user_id, job_id):
    cmd = '''
        SELECT 
            aido_evaluation_jobs.status,
            aido_evaluation_jobs.submission_id,
            aido_submissions.user_id 
        from 
            aido_evaluation_jobs,
            aido_submissions
        where
            aido_submissions.submission_id = aido_evaluation_jobs.submission_id
            and 
            job_id = %s 
    '''
    cursor.execute(cmd, (job_id,))
    if cursor.rowcount == 0:
        msg = 'Could not find job %s' % job_id
        dberror(cursor, 'User tried to reset invalid job #%s' % job_id)
        return result_failure(msg)

    status, submission_id, submitter_id = cursor.fetchone()

    if user_id != submitter_id and not is_superadmin(user_id):
        msg = 'Cannot reset job that is not yours.'
        dberror(cursor, 'User {admin} tried to reset job #%s of user %s' % (job_id, submitter_id),
                admin_id=user_id,
                submitter_id=submitter_id)
        return result_failure(msg)

    cmd = "UPDATE aido_submissions SET status = %s where submission_id = %s"
    args = (CS.STATUS_SUBMITTED, submission_id)
    cursor.execute(cmd, args)

    cmd = "UPDATE aido_evaluation_jobs SET status = %s where job_id = %s"
    args = (CS.STATUS_JOB_ABORTED, job_id)
    cursor.execute(cmd, args)

    dbinfo(cursor, "User {admin} has reset computation for job {job_id} to challenge {challenge}.",
           admin_id=user_id,
           submission_id=submission_id,
           job_id=job_id,
           submitter_id=submitter_id)

    return result_success(job_id)


def reset_submission(cursor, admin_id, submission_id):
    cmd = 'SELECT user_id, status, challenge_id FROM aido_submissions WHERE submission_id = %s'
    args = (submission_id,)
    cursor.execute(cmd, args)
    if cursor.rowcount == 0:
        msg = 'Could not find submission %s' % submission_id
        return result_failure(msg)

    owner_id, status, challenge_id = cursor.fetchone()

    if not is_superadmin(admin_id):
        if admin_id != owner_id:
            msg = 'You do not have permissions to reset submission %s' % submission_id
            return result_failure(msg)

    # TODO: only allow for particular status?

    # mark jobs that are in timeout, evaluating, as aborted

    # STATUS_JOB_TIMEOUT = 'timeout'
    # STATUS_JOB_EVALUATION = 'evaluating'
    # STATUS_JOB_FAILED = 'failed'  # submission failed
    # STATUS_JOB_ERROR = 'error'  # evaluation failed
    # STATUS_JOB_SUCCESS = 'success'
    # STATUS_JOB_ABORTED = 'aborted'

    cmd = "UPDATE aido_submissions SET status = %s where submission_id = %s"
    args = (CS.STATUS_SUBMITTED, submission_id)
    cursor.execute(cmd, args)

    cmd = "UPDATE aido_evaluation_jobs SET status = %s where submission_id = %s"
    args = (CS.STATUS_JOB_ABORTED, submission_id)
    cursor.execute(cmd, args)

    dbinfo(cursor, "User {admin} has reset computation for submission {submission} to challenge {challenge}.",
           submission_id=submission_id,
           challenge_id=challenge_id,
           admin_id=admin_id)

    return result_success(submission_id)
