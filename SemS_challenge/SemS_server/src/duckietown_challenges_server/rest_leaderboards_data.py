# coding=utf-8
import json
import time
from collections import defaultdict, OrderedDict

from duckietown_challenges.challenge import Score

from .database import db_connection
from .db_challenges import read_challenges, Challenge
from .db_submissions import read_submissions2
from .db_users import read_users
from .rest import s_leaderboards_data
from .rest_subs_by_challenge import NoSuchChallenge

WHY_NOT_RANKED = 'why-not-ranked'
NOT_COMPETING = [3, 6, 341, 365, 443, 449, 455, 482,
                 506, 534, 844, 847, 309, 393]


@s_leaderboards_data.get()
def get_submissions_by_challenge(request):
    cid = request.matchdict['cid']
    cid = int(cid)
    try:
        with db_connection(request) as cursor:
            challenges = read_challenges(cursor)
            uptodatejobs = {}
            leaderboard = get_leaderboard3(cursor, challenges[cid], challenges, uptodatejobs)
            for entry in leaderboard:
                del entry['submission']
                del entry['user']
        return {'ok': True, 'leaderboard': leaderboard}
    except NoSuchChallenge as e:
        return {'ok': False, 'msg': str(e)}


from . import cslogger
import numpy as np


def discretize(value, D):
    k = np.ceil(value / D) * D
    return float(k)


class JobStatsCache(object):
    """
    Note that the stats of a success job never change.
    Very safe to cache
    """
    job2result = {}

    @staticmethod
    def read_stats_for_job(cursor, job_id):
        if job_id not in JobStatsCache.job2result:
            cmd = '''
                      select name, value from aido_evaluation_jobs_stats where job_id = %s
                        '''
            cursor.execute(cmd, (job_id,))

            res = {}
            for score_name, value_json in cursor.fetchall():
                res[score_name] = json.loads(value_json)

            JobStatsCache.job2result[job_id] = res
        return JobStatsCache.job2result[job_id]


def get_leaderboard3(cursor, challenge, uptodatejobs, challenges, max_entries=15, only_ranked=True):
    assert isinstance(challenge, Challenge)
    # repeat_user = False
    scorename2desc = OrderedDict()
    for _ in challenge.scoring.scores:
        scorename2desc[_.name] = _

    cslogger.debug('get_leaderboard3 for ch %s has %s' % (challenge.challenge_id, len(uptodatejobs)))

    submissions = read_submissions2(cursor, challenge_id=challenge.challenge_id, uptodatejobs=uptodatejobs,
                                    exclude_aborted_and_retired=True, challenges=challenges)

    cslogger.debug('get_leaderboard3 for ch %s has now %s' % (challenge.challenge_id, len(uptodatejobs)))

    submissions2scores = defaultdict(dict)

    t0 = time.time()
    for submission_id, submission in submissions.items():
        # if submission.user_retired or submission.admin_aborted:
        #     continue
        if not submission.submission_status.complete:
            continue
        if submission.submission_status.result != 'success':  # XXX
            continue

        job_ids = submission.submission_status.step2job.values()
        for job_id in job_ids:

            res = JobStatsCache.read_stats_for_job(cursor, job_id)
            for score_name, value in res.items():
                if score_name in scorename2desc:
                    desc = scorename2desc[score_name]

                    if desc.discretization is not None:
                        value = discretize(value, desc.discretization)

                    submissions2scores[submission_id][score_name] = value
    cursor.debug('Read scores in %d ms' % (1000 * (time.time() - t0)))
    # cslogger.info(submissions2scores)
    users = read_users(cursor)

    entries = []

    for submission_id, scores in submissions2scores.items():
        # submission = read_submission(cursor, submission_id, challenges=challenges, uptodatejobs=uptodatejobs)
        # submissionid2submission[submission_id] = submission
        submission = submissions[submission_id]
        user = users[submission.user_id]
        user_url = 'https://www.duckietown.org/site/pm_profile?uid=%s' % submission.user_id
        entry = {
            'submission_id': submission_id,
            'user_name': user.display_name,
            'user_url': user_url,
            'scores': scores,
            'date_submitted': submission.date_submitted.isoformat(),
            'submission': submission,
            'user': user
        }
        entries.append(entry)

    def forder(x):
        t = []
        s = submissions2scores[x['submission_id']]
        for name, score_desc in scorename2desc.items():
            assert isinstance(score_desc, Score)
            value = s.get(name, 0.0)
            if score_desc.order == Score.LOWER_IS_BETTER:
                value = -value
            elif score_desc.order == Score.HIGHER_IS_BETTER:
                value = value
            else:
                assert False, score_desc.order

            t.append(value)
        return tuple(t)

    entries.sort(key=forder, reverse=True)

    top_users = []
    entries2 = []

    rank = 1
    for entry in entries:
        user_id = entry['user'].user_id
        is_an_admin = user_id in NOT_COMPETING
        another_from_same_user = user_id in top_users
        top_users.append(user_id)

        if is_an_admin:
            entry[WHY_NOT_RANKED] = 'not competing'
        elif another_from_same_user:
            entry[WHY_NOT_RANKED] = 'not best'

        else:
            entry['rank'] = rank
            rank += 1

        if only_ranked and not 'rank' in entry:
            continue

        entry['score_vector'] = list(forder(entry))
        entries2.append(entry)

        if len(entries2) >= max_entries:
            break

    if not only_ranked:
        for i, entry in enumerate(entries):
            bonus = max(0, 25 - i)
            submission_id = entry['submission_id']
            if bonus > 0:
                actual = 50 + bonus
                cmd = """ update aido_submissions set admin_priority = GREATEST(admin_priority, %s) where submission_id = %s"""
                cursor.execute(cmd, (actual, submission_id))

    return entries2
