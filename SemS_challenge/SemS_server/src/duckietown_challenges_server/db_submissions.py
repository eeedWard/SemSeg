# coding=utf-8
import json
import time
from collections import OrderedDict, namedtuple

from . import cslogger
from .db_challenges import read_challenges, read_challenge
from .locks import timeout_lock
from .misc import timedb


class SubmissionStatus(object):
    def __init__(self, complete, result, next_steps, step2status, step2job):
        self.complete = complete
        self.result = result
        self.next_steps = next_steps
        self.step2job = step2job
        self.step2status = step2status

    def as_dict(self):
        return dict(complete=self.complete, result=self.result, next_steps=self.next_steps,
                    step2status=self.step2status, step2job=self.step2job)


class Submission(object):

    def __init__(self, submission_id, user_id, date_submitted, status,
                 last_status_change, challenge_id, parameters, user_label, user_payload,
                 submission_status, user_retired, admin_aborted, user_priority,
                 admin_priority):
        assert isinstance(submission_status, SubmissionStatus), submission_status
        assert isinstance(parameters, dict), parameters
        self.submission_id = submission_id
        self.user_id = user_id
        self.date_submitted = date_submitted
        self.status = status
        self.last_status_change = last_status_change
        self.challenge_id = challenge_id
        self.parameters = parameters

        user_image = self.parameters.pop('hash', None)

        self.user_label = user_label
        self.user_image = user_image
        self.user_payload = user_payload
        self.submission_status = submission_status
        self.user_retired = user_retired
        self.admin_aborted = admin_aborted
        self.user_priority = user_priority
        self.admin_priority = admin_priority

    def redact(self):
        self.user_image = None
        self.user_payload = None

    def as_dict(self):
        return dict(submission_id=self.submission_id,
                    user_id=self.user_id,
                    date_submitted=self.date_submitted.isoformat(),
                    status=self.status,
                    last_status_change=self.last_status_change.isoformat(),
                    challenge_id=self.challenge_id,
                    parameters=self.parameters,
                    user_label=self.user_label,
                    user_image=self.user_image,
                    user_payload=self.user_payload,
                    user_retired=self.user_retired,
                    admin_aborted=self.admin_aborted,
                    user_priority=self.user_priority,
                    admin_priority=self.admin_priority,
                    )


def _interpret_one(cursor, _, challenges, uptodatejobs):
    submission_id, user_id, date_submitted, status, last_status_change, challenge_id, parameters_json, user_label_json, user_payload_json, user_retired, admin_aborted, user_priority, admin_priority = _

    parameters = json.loads(parameters_json)
    user_payload = json.loads(user_payload_json)
    user_label = json.loads(user_label_json)

    submission_status = SubmissionStatus(complete=None, result=None, next_steps=None, step2status=None, step2job=None)
    j = Submission(submission_id, user_id, date_submitted, status,
                   last_status_change, challenge_id, parameters, user_label, user_payload,
                   submission_status, user_retired, admin_aborted, user_priority,
                   admin_priority)

    j.submission_status = get_status_submission(cursor, j, challenges=challenges, uptodatejobs=uptodatejobs)
    # cslogger.debug('_interpret_one %s has %s' % (j.submission_id, len(uptodatejobs)))
    return j


SubmissionJobs = namedtuple('SubmissionJobs', 'stepname2jobid stepname2status')


def get_uptodate_jobs(cursor, uptodatejobs, submission_ids=None):
    t0 = time.time()
    before = len(uptodatejobs)

    cmd_ = """
       select submission_id, job_id, step_name, status from 
           aido_evaluation_jobs, aido_challenges_evaluation_steps 
       where  
           aido_challenges_evaluation_steps.step_id = aido_evaluation_jobs.step_id and 
           aido_challenges_evaluation_steps.evaluation_parameters = aido_evaluation_jobs.evaluation_parameters 

   """

    if submission_ids is not None:
        cslogger.debug('submission_ids: %s' % submission_ids)
        for _ in submission_ids:
            cmd = cmd_ + (' AND submission_id = %s' % _) + ' ORDER BY job_id ASC'
            cursor.execute(cmd)
            # cslogger.debug('for %s: rows %d' % (_, cursor.rowcount))
            get_uptodate_jobs_process(uptodatejobs, cursor)
            if _ not in uptodatejobs:
                # cslogger.debug('%s: %s is new' % (submission_id, job_id))
                uptodatejobs[_] = SubmissionJobs({}, {'START': 'success'})

    else:

        cmd0 = """select submission_id from aido_evaluation_jobs"""
        cursor.execute(cmd0)
        for _, in cursor.fetchall():
            uptodatejobs[_] = SubmissionJobs({}, {'START': 'success'})

        cmd = cmd_ + ' ORDER BY job_id ASC'
        cursor.execute(cmd)
        get_uptodate_jobs_process(uptodatejobs, cursor)

    delta = time.time() - t0
    cursor.debug('uptodatejobs: %.1fs n %s->%s' % (delta, before, len(uptodatejobs)))


def get_uptodate_jobs_process(uptodatejobs, cursor):
    for submission_id, job_id, step_name, step_status in cursor.fetchall():
        # cslogger.debug('%s: %s' % (submission_id, job_id))
        if submission_id not in uptodatejobs:
            # cslogger.debug('%s: %s is new' % (submission_id, job_id))
            uptodatejobs[submission_id] = SubmissionJobs({}, {'START': 'success'})

        uptodatejobs[submission_id].stepname2status[str(step_name)] = step_status
        uptodatejobs[submission_id].stepname2jobid[str(step_name)] = job_id


def get_status_submission(cursor, submission, challenges, uptodatejobs):
    challenge_id = submission.challenge_id
    submission_id = submission.submission_id

    if not challenge_id in challenges:
        challenges[challenge_id] = read_challenge(cursor, challenge_id)
    if submission_id not in uptodatejobs:
        cursor.debug('submission %d triggering full uptodatejobs search' % submission_id)
        get_uptodate_jobs(cursor, uptodatejobs)
        # no jobs yet
        if submission_id not in uptodatejobs:
            uptodatejobs[submission_id] = SubmissionJobs({}, {'START': 'success'})  # XXX

    challenge = challenges[challenge_id]

    stepname2jobid = uptodatejobs[submission_id].stepname2jobid
    stepname2status = uptodatejobs[submission_id].stepname2status
    complete, result, next_steps = challenge.transitions.get_next_steps(stepname2status,
                                                                        step2age=stepname2jobid)

    next_steps = list(map(str, next_steps))  # TODO
    return SubmissionStatus(complete, result, next_steps, step2status=stepname2status, step2job=stepname2jobid)


def read_submissions2(cursor, challenges, uptodatejobs, submission_ids=None, user_id=None, challenge_id=None, start=0,
                      limit=10000, order_by_priority=False,
                      exclude_aborted_and_retired=False):
    # cursor.debug('read_submissions2 for ch %s has %s' % (challenge_id, len(uptodatejobs)))

    if submission_ids:
        get_uptodate_jobs(cursor, uptodatejobs, submission_ids=submission_ids)

        res = OrderedDict()
        for submission_id in submission_ids:
            res[submission_id] = read_submission(cursor, submission_id, challenges=challenges,
                                                 uptodatejobs=uptodatejobs)
        return res
    else:
        res = OrderedDict()
        where = 'WHERE TRUE'
        if challenge_id:
            where += ' AND (challenge_id = %s) ' % challenge_id
        if user_id:
            where += ' AND (user_id = %s) ' % user_id

        if exclude_aborted_and_retired:
            where += ' AND (user_retired = FALSE) AND (admin_aborted = FALSE)'

        order = 'submission_id DESC'
        if order_by_priority:
            order = 'admin_priority DESC'

        cmd = """
        SELECT
            submission_id,
            user_id,
            date_submitted,
            status,
            last_status_change,
            challenge_id,
            parameters,
            user_label,
            user_metadata,
            user_retired,
            admin_aborted,
            user_priority,
            admin_priority
        FROM aido_submissions
        %s
        ORDER BY %s
        LIMIT %s, %s
        
        """ % (where, order, start, limit)
        cursor.execute(cmd)

        for _ in cursor.fetchall():
            j = _interpret_one(cursor, _, challenges=challenges, uptodatejobs=uptodatejobs)
            res[j.submission_id] = j
        return res


def read_submission(cursor, submission_id, challenges, uptodatejobs):
    cmd = """
       SELECT
           submission_id,
           user_id,
           date_submitted,
           status,
           last_status_change, 
           challenge_id,
           parameters,
           user_label,
           user_metadata,
           user_retired,
           admin_aborted,
           user_priority,
           admin_priority
       FROM aido_submissions
       WHERE submission_id = %s
       ORDER BY last_status_change DESC"""
    cursor.execute(cmd, (submission_id,))
    if cursor.rowcount == 0:
        msg = 'Could not find submission %s' % submission_id
        raise KeyError(msg)
    _ = cursor.fetchone()
    j = _interpret_one(cursor, _, challenges=challenges, uptodatejobs=uptodatejobs)
    return j


# evaluation_jobs = Service(name='evaluation_jobs', path='/evaluation-jobs', renderer='json-indent')

JobOpportunity = namedtuple('JobOpportunity',
                            'protocol challenge_name challenge_id submission_id step_name step_id user_priority admin_priority user_id step2job_id')


class JobOpportunityCache(object):
    lock = timeout_lock.lock()
    job_opportunities = None
    last_timestamp = None
    last_computed = 0


def get_db_timestamp(cursor):
    cmd = "SELECT GREATEST(MAX(date_completed), MAX(date_started)) FROM `aido_evaluation_jobs`"
    cursor.execute(cmd)
    jobs_timestamp, = cursor.fetchone()

    cmd = "SELECT GREATEST(MAX(date_submitted), MAX(last_status_change)) FROM aido_submissions"
    cursor.execute(cmd)
    subs_timestamp, = cursor.fetchone()
    if jobs_timestamp == None:
        jobs_timestamp = subs_timestamp
    if subs_timestamp == None:
        subs_timestamp = jobs_timestamp


    return max(jobs_timestamp, subs_timestamp)


def get_jobs_opportunities(cursor, challenges=None, uptodatejobs=None, max_opportunities=10):
    C = JobOpportunityCache

    def should_update():
        table_timestamp = get_db_timestamp(cursor)
        delta_computed = time.time() - C.last_computed

        s = (C.job_opportunities is None) or (C.last_timestamp != table_timestamp) or (delta_computed > LIMIT)
        if s:
            msg = 'I need to update job opportunities.\nCache timestamp: %s\n DB timestamp %s\ndelta computed: %s' % (
                C.last_timestamp, table_timestamp, delta_computed)
            cursor.info(msg)
        return s

    LIMIT = 300

    if should_update():

        with timeout_lock(owner='%s' % id(cursor), lock=C.lock, timeout=30,
                          raise_on_timeout=True):

            if should_update():
                table_timestamp = get_db_timestamp(cursor)
                fresh = get_jobs_opportunities_fresh(cursor, challenges=challenges, uptodatejobs=uptodatejobs,
                                                     max_opportunities=max_opportunities)
                C.job_opportunities = fresh
                C.last_timestamp = table_timestamp
                C.last_computed = time.time()
                msg = 'Updated job_opportunities.'
                cursor.debug(msg)
            else:
                msg = 'Somebody updated for me.'
                cursor.debug(msg)
    else:
        msg = 'No need to update job opportunities.'
        cursor.debug(msg)
    return C.job_opportunities


# noinspection PyArgumentList
@timedb
def get_jobs_opportunities_fresh(cursor, challenges=None, uptodatejobs=None, max_opportunities=10):
    # find open submissions

    t0 = time.time()
    jos = []
    limit = 200
    uptodatejobs = uptodatejobs or {}
    challenges = challenges or read_challenges(cursor)
    for i in range(200):
        start = i * limit

        submissions = read_submissions2(cursor, challenges=challenges,
                                        uptodatejobs=uptodatejobs, exclude_aborted_and_retired=True,
                                        order_by_priority=True,
                                        limit=limit, start=start)
        for id_submission, submission in submissions.items():

            if submission.submission_status.complete:
                continue

            for step_name in submission.submission_status.next_steps:
                challenge = challenges[submission.challenge_id]
                step_id = challenge.step_id_from_name(step_name)
                jo = JobOpportunity(protocol=challenge.protocol,
                                    challenge_name=challenge.queue_name,
                                    challenge_id=challenge.challenge_id,
                                    submission_id=submission.submission_id,
                                    step_name=step_name,
                                    step_id=step_id,
                                    user_priority=submission.user_priority,
                                    admin_priority=submission.admin_priority,
                                    user_id=submission.user_id,
                                    step2job_id=submission.submission_status.step2job)

                jos.append(jo)

            if len(jos) > max_opportunities:
                break
        if len(jos) > max_opportunities:
            break

    delta = time.time() - t0

    cslogger.debug('%.1fs seconds for job opportunities' % delta)
    return jos
