# coding=utf-8
import json

from .database import db_connection
from .misc import result_success, result_failure
from .rest import s_jobs_by_submissions
from .rest_subs_by_challenge import NoSuchChallenge


@s_jobs_by_submissions.get()
def get_submissions_by_challenge(request):
    sid = request.matchdict['sid']
    sid = int(sid)
    with db_connection(request) as cursor:
        try:
            jobs = get_evaluation_jobs_by_submission_db(cursor, sid)
            return result_success(jobs)
        except NoSuchChallenge as e:
            return result_failure(e)


def get_evaluation_jobs_by_submission_db(cursor, sid):
    cmd = "select submission_id from aido_submissions"
    cursor.execute(cmd)
    ids = [int(_) for _, in cursor.fetchall()]
    if sid not in ids:
        msg = 'Could not find submission_id %s; available: %s' % (sid, ids)
        raise NoSuchChallenge(msg)

    cmd = """ select job_id, evaluator_id, date_started, status, date_completed, stats 
          from aido_evaluation_jobs where submission_id = %s """

    cursor.execute(cmd, (sid,))
    jobs = []
    for _ in cursor.fetchall():
        job_id, evaluator_id, date_started, status, date_completed, stats = _
        job = {
            'job_id': job_id,
            'evaluator_id': evaluator_id,
            'date_started': date_started.isoformat(),
            'date_completed': date_completed.isoformat(),

            'status': status,
            'stats': json.loads(stats) if stats else None,
        }

        jobs.append(job)
    return jobs
