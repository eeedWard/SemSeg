# coding=utf-8
from .auth import valid_dt1_token
from .my_logging import dbdebug

from .database import db_connection
from .db_challenges import read_challenges
from .misc import result_success, result_failure
from .rest import s_challenges, s_challenges_def


@s_challenges.get()
def get_challenges(request):
    with db_connection(request) as cursor:
        from .db_challenges import read_challenges
        challenges = read_challenges(cursor)
        res = {}
        for k, v in challenges.items():
            res[k] = v.as_dict()
        return result_success(res)


@s_challenges_def.get(validators=valid_dt1_token)
def get_challenge_definition(request):
    with db_connection(request) as cursor:
        cname = request.matchdict['cid']

        challenges = read_challenges(cursor)

        found = []
        for challenge_id, challenge in challenges.items():
            found.append(challenge.queue_name)
            if challenge.queue_name == cname:
                break

        else:
            msg = u'Could not find challenge %s among %s.' % (cname, u", ".join(found))
            return result_failure(msg)

        dbdebug(cursor, "User {submitter} is locally evaluating challenge {challenge}",
                submitter_id=request.validated['uid'],
                challenge_id=challenge_id,
                category='private')

        asd = challenge.as_dict_for_challenge_description()
        from duckietown_challenges.challenge import ChallengeDescription
        cd = ChallengeDescription.from_yaml(asd)
        json_dict = cd.as_dict()

        # really make sure we can deserialize
        cd2 = ChallengeDescription.from_yaml(json_dict)

        res = {'challenge': cd.as_dict()}

        return result_success(res)
