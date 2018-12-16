# coding=utf-8
from .database import db_connection
from .misc import result_success, result_failure
from .rest import s_sub_by_challenges


@s_sub_by_challenges.get()
def get_submissions_by_challenge(request):
    cid = request.matchdict['cid']
    cid = int(cid)
    with db_connection(request) as cursor:
        try:
            submissions = get_submissions_by_challenge_db(cursor, cid)
            return result_success(submissions)
        except NoSuchChallenge as e:
            return result_failure(str(e))


class NoSuchChallenge(Exception):
    pass


def get_submissions_by_challenge_db(cursor, cid):

    cmd = "select challenge_id from aido_challenges "
    cursor.execute(cmd)
    ids = [int(_) for _, in cursor.fetchall()]
    if cid not in ids:
        msg = 'Could not find challenge %s; available: %s' % (cid, ids)
        raise NoSuchChallenge(msg)

    cmd = "select submission_id,  user_id, date_submitted, status, last_status_change from aido_submissions where challenge_id = %s "
    cursor.execute(cmd, (cid,))
    submissions = []
    for _ in cursor.fetchall():
        submission_id, user_id, date_submitted, status, last_status_change = _
        submission = {'submission_id': submission_id,
                      'user_id': user_id,
                      'date_submitted': date_submitted.isoformat(),
                      'last_status_change': last_status_change.isoformat(),
                      'status': status
                      }

        submissions.append(submission)
    return submissions
