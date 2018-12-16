# coding=utf-8
from collections import OrderedDict

from duckietown_challenges import ChallengesConstants as CS
from duckietown_challenges_server.db_users import read_user

from . import cslogger
from .auth import valid_dt1_token
from .database import db_connection
from .misc import result_success, result_failure
from .rest import s_info


@s_info.get(validators=valid_dt1_token)
def get_info(request):
    uid = request.validated['uid']
    cslogger.debug('getting info for user %s' % uid)

    with db_connection(request) as cursor:

        try:
            user = read_user(cursor, uid)
        except KeyError:
            msg = "Could not find uid %r" % uid
            return result_failure(msg)

        data = OrderedDict()
        data['uid'] = uid
        data['user_login'] = user.user_login
        data['name'] = user.display_name
        data['profile'] = user.user_url
        # data['github_username'] = user.github_username

        # get user statistics (best submission per challenge)
        query = """
            SELECT S.challenge_id, S.submission_id, MAX(JSON_EXTRACT(J.stats, '$.scores.score1')) AS score1
            FROM aido_submissions AS S, aido_evaluation_jobs AS J
            WHERE S.submission_id = J.submission_id AND J.status = 'success' AND S.user_id = %s
            GROUP BY S.challenge_id, S.submission_id
            HAVING score1 IN (
                SELECT MAX(JSON_EXTRACT(J1.stats, '$.scores.score1')) AS score1
                FROM aido_submissions AS S1, aido_evaluation_jobs AS J1
                WHERE S1.submission_id = J1.submission_id AND J1.status = 'success' AND S1.user_id = %s
                GROUP BY S1.challenge_id
            )
        """
        cursor.execute(query, (uid, uid))
        all_scores = ['score1']
        best_submission_per_challenge_by_user = {
            score: {
                challenge_id: dict(
                        challenge_id=challenge_id,
                        submission_id=submission_id,
                        score=score1
                ) for challenge_id, submission_id, score1 in cursor.fetchall()
            } for score in all_scores
        }

        # get user statistics (number of submission per status)
        submissions_status = {status: 0 for status in CS.ALLOWED_SUB_STATUS}
        query = """
            SELECT S.status, COUNT(S.submission_id) AS count
            FROM aido_submissions AS S
            WHERE S.user_id = %s
            GROUP BY S.status
        """
        cursor.execute(query, (uid,))
        submissions_status.update({status: count for status, count in cursor.fetchall()})

        # append stats data
        data['stats'] = {
            'best_submission_per_challenge': best_submission_per_challenge_by_user,
            'submissions_status': submissions_status,
            'total_submissions': sum(submissions_status.values())
        }

        user_msg = None
        if user.display_name.lower().startswith('user'):
            user_msg = """             
You have been assigned a temporary username. Your user information will be
updated shortly from the Duckietown.org database.
"""

        return result_success(data, user_msg=user_msg, total=1)
