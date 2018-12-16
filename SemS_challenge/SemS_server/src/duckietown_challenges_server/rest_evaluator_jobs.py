# coding=utf-8
import json

from pyramid.httpexceptions import HTTPBadRequest

from duckietown_challenges import ChallengesConstants as CS
from duckietown_challenges.challenge import EvaluationParameters
from duckietown_challenges.utils import indent
from duckietown_challenges_server.db_challenges import EvaluationStep, read_challenge
from duckietown_challenges_server.locks import timeout_lock
from . import cslogger
from .auth import valid_dt1_token
from .constants import ChallengeServerConstants
from .database import db_connection
from .db_jobs import read_job
from .db_submissions import get_jobs_opportunities, JobOpportunity, read_submission
from .misc import result_success, result_failure, memoized_db_operation
from .my_logging import dbinfo, dberror
from .rest import s_take_submission
from .rest_user_submissions import reset_submission


def update_old_jobs(cursor):
    # mark as timeout the jobs that are evaluating

    cmd = """ 
      SELECT 
      aido_evaluation_jobs.job_id, 
      aido_evaluation_jobs.submission_id ,
      TIMESTAMPDIFF(MINUTE, date_started, UTC_TIMESTAMP() )
      from aido_evaluation_jobs, aido_submissions
      where 
      aido_evaluation_jobs.status = %s and 
      TIMESTAMPDIFF(MINUTE,date_started, UTC_TIMESTAMP()) > %s   and 
      aido_submissions.submission_id = aido_evaluation_jobs.submission_id
"""
    cursor.execute(cmd, (CS.STATUS_JOB_EVALUATION, CS.JOB_TIMEOUT_MINUTES))

    update = set()
    if cursor.rowcount > 0:
        for job_id, submission_id, minutes in list(cursor.fetchall()):
            msg = 'I can see how the job %s is timeout because passed %s' % (job_id, minutes)
            cslogger.info(msg)
            update.add(submission_id)
            cmd = "update aido_evaluation_jobs set status = %s, date_completed = UTC_TIMESTAMP() where job_id = %s"
            cursor.execute(cmd, (CS.STATUS_JOB_TIMEOUT, job_id))

    # if a submission is in evaluating but there are no jobs in evaluating,
    # then mark it as submitted
    for submission_id in update:
        cmd = "select job_id from aido_evaluation_jobs where submission_id = %s and status = %s"
        cursor.execute(cmd, (submission_id, CS.STATUS_JOB_EVALUATION))
        if cursor.rowcount == 0:
            msg = 'Now marking submission %s as todo' % submission_id
            cslogger.info(msg)
            cmd = "update aido_submissions set  status = %s where submission_id  = %s"
            cursor.execute(cmd, (CS.STATUS_SUBMITTED, submission_id))
            # cmd = "update aido_submissions set last_status_change = %s and status = %s where submission_id  = %s"
            # cursor.execute(cmd, (now, CS.STATUS_SUBMITTED, submission_id))


def update_evaluators_log(cursor, request, machine_id, process_id, evaluator_version):
    uid = request.validated['uid']
    addr = request.remote_addr
    cmd = '''
        select 
            evaluator_id 
        from 
            aido_evaluators 
        where 
            uid = %s and ip4 = %s and machine_id = %s and process_id = %s and evaluator_version=%s
    '''
    cursor.execute(cmd, (uid, addr, machine_id, process_id, evaluator_version))
    if cursor.rowcount == 0:
        cslogger.info('New evaluator uid = %s addr = %s' % (uid, addr))
        cmd = '''
            insert into 
                aido_evaluators(uid, ip4, machine_id, process_id, evaluator_version, first_heard, last_heard, npings) 
            values (%s, %s, %s, %s, %s, UTC_TIMESTAMP(), UTC_TIMESTAMP(), %s)
        '''
        cursor.execute(cmd, (uid, addr, machine_id, process_id, evaluator_version, 0))
        return True, cursor.lastrowid
    else:
        evaluator_id, = cursor.fetchone()
        cmd = 'update aido_evaluators set last_heard = UTC_TIMESTAMP(), npings  = npings + 1 where evaluator_id = %s'
        cursor.execute(cmd, (evaluator_id,))
        return False, evaluator_id


@memoized_db_operation
def get_featurename2featureid(cursor):
    cmd = """
             select feature_name, evaluation_feature_id from aido_evaluation_features
             
         """
    cursor.execute(cmd)
    res = {}
    for feature_name, feature_id in cursor.fetchall():
        res[feature_name] = feature_id
    return res


def update_evaluators_features(cursor, evaluator_id, features):
    cmd = """
        delete from aido_evaluators_features 
            where evaluator_id = %s
    """
    cursor.execute(cmd, (evaluator_id,))

    featurename2featureid = get_featurename2featureid(cursor)

    for fname, amount in features.items():

        if fname not in featurename2featureid:
            msg = 'Invalid feature %r' % fname
            cslogger.error(msg)
            continue
        evaluation_feature_id = featurename2featureid[fname]
        cmd = """
            insert into aido_evaluators_features(evaluator_id, evaluation_feature_id, amount) VALUES (%s,%s,%s)
        """
        cursor.execute(cmd, (evaluator_id, evaluation_feature_id, int(amount)))

        # print '%s %s evaluation_feature_id %s ' % (fname, amount, evaluation_feature_id)


def compatible(features, step):
    assert isinstance(step, EvaluationStep)

    problems = []
    for feature_name, min_amount in step.features_required.items():
        if feature_name not in features:
            msg = 'Evaluator does not declare feature "%s" (required >= %s)' % (feature_name, min_amount)
            problems.append(msg)
        else:
            has = features[feature_name]
            if has < min_amount:
                msg = 'Evaluator needs for feature "%s" at least %s but it has only %s' % (
                    feature_name, min_amount, has)
                problems.append(msg)
            # else:
            #     msg = 'OK, evaluator has %s >= %s for %r' % (has, min_amount, feature_name)
            #     cslogger.info(msg)

    if problems:
        return False, "\n".join(problems)
    else:
        return True, ""


def get_most_likely_job(cursor, user_id, features, challenges, uptodatejobs, preferred_submission_id=None):
    """

        returns found, JobOpportunity, msg_if_not_found

    """

    job_opportunites = get_jobs_opportunities(cursor, challenges=challenges, uptodatejobs=uptodatejobs)
    if not job_opportunites:
        return False, None, "No jobs available in general."

    # first, find out which jobs this evaluator *could* do
    explanations = []
    submission_id2inc_explanation = {}

    available = []
    for jo in job_opportunites:
        assert isinstance(jo, JobOpportunity)

        if not jo.challenge_id in challenges:
            challenges[jo.challenge_id] = read_challenge(cursor, jo.challenge_id)

        # print('steps: %s' % list(challenges[jo.challenge_id].steps))
        step = challenges[jo.challenge_id].steps[jo.step_id]
        ok, explanation = compatible(features, step)

        if not ok:
            msg = 'Evaluator is not qualified for submission %s (step %s in challenge %s)' % (
                jo.submission_id, jo.step_name, jo.challenge_name)
            msg += '\n' + indent(explanation, '  > ')
            explanations.append(msg)
            # cslogger.debug(msg)

            submission_id2inc_explanation[jo.submission_id] = msg
        else:
            # cslogger.debug('OK, compatible with step %s: %s' % (jo.step_id, explanation))
            available.append(jo)

    if not available:
        return False, None, "Not qualified for any of %s jobs:\n%s" % (len(job_opportunites),
                                                                       indent("\n".join(explanations), "  > "))

    if preferred_submission_id is not None:
        preferred = [_ for _ in available if _.submission_id == preferred_submission_id]
        if preferred:
            return True, preferred[0], "Giving preferred submission"
        else:
            if preferred_submission_id in submission_id2inc_explanation:
                msg = submission_id2inc_explanation[preferred_submission_id]
                return False, None, msg

    # if there is one sent by them, use that one
    own = [_ for _ in available if _.user_id == user_id]
    if own:
        # sort by user priority
        own_sorted = sorted(own, key=jo_sort)
        return True, own_sorted[0], "Giving one of own submissions"

    available_sorted = sorted(available, key=jo_sort)
    return True, available_sorted[0], "Giving a community submissions"


def jo_sort(_):
    admin_priority = -_.admin_priority
    recent = -_.submission_id
    return admin_priority, recent


class TakeSubmission(object):
    lock = timeout_lock.lock()


@s_take_submission.get(validators=valid_dt1_token)
def take_submission(request):
    with timeout_lock(owner='%s' % id(request), lock=TakeSubmission.lock, timeout=5,
                      raise_on_timeout=True):
        return take_submission_(request)


def take_submission_(request):
    with db_connection(request) as cursor:
        uptodatejobs = {}
        challenges = {}
        update_old_jobs(cursor)

        user_id = request.validated['uid']

        text = request.text
        data = json.loads(text)

        try:
            preferred_submission_id = data['submission_id']
            machine_id = data['machine_id']
            process_id = data['process_id']
            evaluator_version = data['evaluator_version']
            features = data['features']
            reset = data.get('reset', False)

            # if 'nutonomy' in machine_id:
            #     msg = 'Excluding you in particular'
            #     raise HTTPBadRequest(msg)

        except KeyError as e:
            msg = 'Invalid request body: %s' % e
            cslogger.error(msg)
            raise HTTPBadRequest(msg)

        new_one, evaluator_id = update_evaluators_log(cursor, request, machine_id, process_id, evaluator_version)

        if new_one:
            dbinfo(cursor, 'New evaluator {evaluator}  available owned by {evaluator_owner}.',
                   evaluator_id=evaluator_id,
                   evaluator_owner_id=user_id)

        MIN_SPACE_MB = 1000
        space_available_mb = features.get('disk_available_mb', 0)
        if space_available_mb < MIN_SPACE_MB:
            msg = 'The evaluator has only %d MB of space; %d MB are required.' % (space_available_mb, MIN_SPACE_MB)
            return result_failure(msg)

        MIN_FREE_PROCESSOR_PERCENT = 50

        free_processor = features.get('processor_free_percent', 0)
        if free_processor < MIN_FREE_PROCESSOR_PERCENT:
            msg = 'The evaluator has only %d %% free processor %d %% is required.' % (free_processor, MIN_FREE_PROCESSOR_PERCENT)
            return result_failure(msg)

        update_evaluators_features(cursor, evaluator_id, features)

        if preferred_submission_id is not None and reset:
            # if the submission already exists and the user matches it,
            # then reset the submission
            cmd = '''
                select user_id from aido_submissions where submission_id = %s
            '''
            cursor.execute(cmd, (preferred_submission_id,))
            if cursor.rowcount == 0:
                # no, it does not exist
                cslogger.info('submission does not exist')
                # TODO: raise Error
            else:
                author, = cursor.fetchone()
                if author == user_id:
                    cslogger.info('resetting submission')
                    reset_submission(cursor, user_id, preferred_submission_id)
                else:
                    cslogger.info('will not reset submission')

        found, jo, found_msg = get_most_likely_job(cursor, user_id, features,
                                                   challenges=challenges,
                                                   uptodatejobs=uptodatejobs,
                                                   preferred_submission_id=preferred_submission_id)

        # cslogger.debug('found %s %s %s' % (found, found_msg, jo))
        if not found:
            msg = 'Could not find any new submission to evaluate:\n\n%s' % found_msg
            res = dict(msg=msg, submission_id=None)
            return result_success(res)

        challenges = {}
        submission = read_submission(cursor, jo.submission_id, challenges, uptodatejobs)

        assert isinstance(jo, JobOpportunity)

        cmd = """
            select evaluation_parameters from aido_challenges_evaluation_steps where step_id = %s
        """
        cursor.execute(cmd, (jo.step_id,))
        evaluation_parameters_json, = cursor.fetchone()
        evaluation_parameters2 = EvaluationParameters.from_yaml(json.loads(evaluation_parameters_json))
        # cmd = """
        #     select parameters from aido_submissions where submission_id = %s
        # """
        # cursor.execute(cmd, (jo.submission_id,))
        # submission_parameters, = cursor.fetchone()

        # submission_parameters = submission.parameters

        parameters = {'hash': submission.user_image}

        cursor.connection.commit()
        # now make sure that we didn't assign it yet
        cmd = """
        SELECT * FROM aido_evaluation_jobs
        WHERE status = %s and step_id = %s and submission_id = %s 
        """
        args = (CS.STATUS_EVALUATION, jo.step_id, evaluation_parameters_json)
        cursor.execute(cmd, args)
        if cursor.rowcount > 0:
            msg = 'Preventing double allocation.'
            cslogger.info(msg)
            msg = 'Could not find any new submission to evaluate:\n\n%s' % found_msg
            res = dict(msg=msg, submission_id=None)
            return result_success(res)

        cmd = """
        INSERT INTO aido_evaluation_jobs(step_id, submission_id, evaluator_id, date_started, 
        date_completed, status, stats, evaluation_parameters) 
        VALUES (%s, %s, %s, UTC_TIMESTAMP(), %s, %s, %s, %s) 
        """
        cursor.connection.commit()

        date_completed = None
        status = CS.STATUS_EVALUATION
        stats = None
        cursor.execute(cmd, (
            jo.step_id, jo.submission_id, evaluator_id,
            date_completed, status, stats,
            evaluation_parameters_json))
        job_id = cursor.lastrowid

        if ChallengeServerConstants.s3:
            aws_config = dict(aws_access_key_id=ChallengeServerConstants.aws_access_key_id,
                              aws_secret_access_key=ChallengeServerConstants.aws_secret_access_key,
                              bucket_name=ChallengeServerConstants.bucket_name, )

            s3_prefix = ChallengeServerConstants.s3_prefix
            aws_config['path'] = 'v3/%s/jobs/%s/%s' % (s3_prefix, job_id, jo.step_name)
            aws_config['path_by_value'] = 'v3/%s/by-value' % s3_prefix
        else:
            aws_config = None

        steps2artefacts = create_step2artefact(jo, cursor)

        res = dict(step_id=jo.step_id,
                   step_name=jo.step_name,
                   submission_id=jo.submission_id,
                   parameters=parameters,
                   job_id=job_id,
                   challenge_id=jo.challenge_id,
                   challenge_name=jo.challenge_name,
                   challenge_parameters=evaluation_parameters2.as_dict(),
                   protocol=jo.protocol,
                   aws_config=aws_config,
                   steps2artefacts=steps2artefacts,
                   )

        dbinfo(cursor,
               "Evaluator {evaluator} owned by {evaluator_owner} is assigned job {job} for submission {submission} for challenge {challenge} (step {step}) created by {submitter}.",
               evaluator_id=evaluator_id,
               evaluator_owner_id=user_id,
               submission_id=jo.submission_id,
               step_id=jo.step_id,
               challenge_id=jo.challenge_id,
               submitter_id=jo.user_id,
               job_id=job_id)

        return result_success(res)


def create_step2artefact(jo, cursor):
    steps2artefacts = {}
    for step_name, job_id in jo.step2job_id.items():
        job = read_job(cursor, job_id)
        art = {}
        for artefact in job.artefacts.values():
            res = artefact.as_dict()
            res.pop('artifact_id')
            art[artefact.rpath] = res
        steps2artefacts[step_name] = art
    return steps2artefacts


def store_uploads(cursor, job_id, uploaded):
    cslogger.debug('uploaded; %s' % uploaded)
    for up in uploaded:
        storage = up['storage']
        size = up['size']
        mime_type = up['mime_type']
        rpath = up['rpath']
        sha256hex = up['sha256hex']

        cmd = """
           insert into aido_evaluation_jobs_artefacts
           (job_id, rpath, size, mime_type,  sha256hex) 
           values (%s, %s, %s, %s, %s)
        """
        args = (job_id, rpath, size, mime_type, sha256hex)
        cursor.execute(cmd, args)

        if 's3' in storage:
            ups3 = storage.pop('s3')
            cslogger.debug(ups3)
            bucket_name = ups3['bucket_name']
            object_key = ups3['object_key']
            url = ups3['url']

            # TODO: add
            cmd = """
                    insert into aido_artefacts_s3objects
                    (sha256hex, bucket_name, object_key, url) 
                    values (%s, %s, %s, %s)
            """
            args = (sha256hex, bucket_name, object_key, url)
            cursor.execute(cmd, args)

        if storage:
            msg = 'I do not know how to deal with this storage: %s' % storage
            cslogger.warning(msg)


@s_take_submission.post(validators=valid_dt1_token)
def report_submission(request):
    with db_connection(request) as cursor:

        text = request.text
        data = json.loads(text)
        user_id = request.validated['uid']

        try:
            job_id = data['job_id']
            result = data['result']
            stats = data['stats']
            machine_id = data['machine_id']
            process_id = data['process_id']
            evaluator_version = data['evaluator_version']
            uploaded = data['uploaded']
            # print('uploaded: %s' % uploaded)

        except KeyError as e:
            msg = 'Invalid request body: %s' % e
            cslogger.error(msg)
            raise HTTPBadRequest(msg)

        new_one, evaluator_id = update_evaluators_log(cursor, request, machine_id, process_id, evaluator_version)
        if new_one:
            dbinfo(cursor,
                   'New evaluator {evaluator} available owned by {evaluator_owner}; but not supposed to happen!',
                   evaluator_id=evaluator_id, evaluator_owner_id=user_id)

        store_uploads(cursor, job_id, uploaded)

        cmd = """
            select
                aido_evaluation_jobs.submission_id,
                aido_evaluation_jobs.evaluator_id,
                aido_evaluation_jobs.step_id,
                aido_submissions.challenge_id,
                aido_submissions.user_id
            from 
                aido_evaluation_jobs, aido_submissions 
            where 
                aido_evaluation_jobs.job_id = %s
            and  
                aido_submissions.submission_id = aido_evaluation_jobs.submission_id
        """
        cursor.execute(cmd, (job_id,))

        if cursor.rowcount == 0:
            msg = 'Invalid job id = %s.' % job_id
            dberror(cursor, msg, evaluator_id=evaluator_id)
            return result_failure(msg)

        submission_id, assigned_evaluator_id, step_id, challenge_id, submitter_id = cursor.fetchone()

        context = dict(evaluator_owner_id=user_id,
                       submission_id=submission_id,
                       step_id=step_id,
                       challenge_id=challenge_id,
                       submitter_id=submitter_id,
                       evaluator_id=evaluator_id,
                       job_id=job_id)

        dbinfo(cursor,
               """Evaluator {evaluator} owned by {evaluator_owner} reports that job {job} has result <code>%s</code>\
                for step {step} of submission {submission} in challenge {challenge} by {submitter}.""" % result,
               **context)
        #
        # if False:
        #     if assigned_evaluator_id != evaluator_id:
        #         msg = 'Job %s was assigned to evaluator %s, not %s.' % (job_id, assigned_evaluator_id, evaluator_id)
        #         dberror(cursor, msg, **context)
        #         return result_failure(msg)

        if result not in CS.ALLOWED_JOB_STATUS:
            msg = 'Invalid status "%s" not in "%s"' % (result, CS.ALLOWED_JOB_STATUS)
            dberror(cursor, msg, **context)
            return result_failure(msg)

        assert result in CS.ALLOWED_SUB_STATUS, result

        cmd = "UPDATE aido_evaluation_jobs SET status=%s, stats=%s, date_completed=UTC_TIMESTAMP() WHERE job_id = %s "
        args = (result, json.dumps(stats), job_id)
        cursor.execute(cmd, args)

        if 'scores' in stats:
            for score_name, score_value in stats['scores'].items():
                cmd = """insert into aido_evaluation_jobs_stats (job_id, name, value)  values (%s, %s, %s)"""
                score_value_json = json.dumps(score_value)
                cursor.execute(cmd, (job_id, score_name, score_value_json))

        if cursor.rowcount == 0:
            msg = 'Cannot find job ID %s - race condition?' % job_id
            cslogger.error(msg)
            dberror(cursor, msg, **context)
            return result_failure(msg)
        else:
            cslogger.info('completed job %s' % job_id)
            return result_success("Job completed")
