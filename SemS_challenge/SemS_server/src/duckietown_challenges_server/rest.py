# coding=utf-8
from cornice import Service


def my_error_handler(request):
    first_error = request.errors[0]
    body = {'description': first_error['description']}

    response = HTTPBadRequest()
    response.body = json.dumps(body).encode("utf-8")
    response.content_type = 'application/json'
    return response


r = dict(renderer="json-indent", error_handler=my_error_handler)

s_challenge_define = Service(name='challenge_define',
                             path='/challenge-define', **r)

s_take_submission = Service(name='take_submission',
                            path='/take-submission',
                            **r)

s_info = Service(name='info',
                 path='/info',
                 cors_origins=('*',), **r)

s_submissions = Service(name='submissions', path='/submissions', **r)
s_reset_submission = Service(name='reset-submission', path='/reset-submission', **r)
s_reset_job = Service(name='reset-job', path='/reset-job', **r)

s_submissions_list = Service(name='submissions-list', path='/submissions-list', **r)

s_submission = Service(name='submission', path='/submission/{sid}', **r)

s_sub_by_challenges = Service(name='sub_by_challenges', path='/subs-by-challenge/{cid}', **r)

s_sub_by_challenges2 = Service(name='sub_by_challenges2', path='/challenges', **r)

s_jobs_by_submissions = Service(name='jobs_by_submissions', path='/jobs-by-submission/{sid}', **r)

s_leaderboards_data = Service(name='leaderboards_data', path='/leaderboards-data/{cid}', **r)

s_challenges = Service(name='challenges', path='/challenges', description='List challenges',
                       cors_origins=('*',),
                       **r)

s_challenges_def = Service(name='challenges_def', path='/challenges/{cid}/description',
                           description='Describes challenges',
                           cors_origins=('*',),
                           **r)

# noinspection PyUnresolvedReferences
from .rest_pub_challenges import *
# noinspection PyUnresolvedReferences
from .rest_info import *
# noinspection PyUnresolvedReferences
from .rest_job_submission import *
# noinspection PyUnresolvedReferences
from .rest_leaderboards_data import *
# noinspection PyUnresolvedReferences
from .rest_organizer_challenges import *
# noinspection PyUnresolvedReferences
from .rest_subs_by_challenge import *
# noinspection PyUnresolvedReferences
from .rest_user_submissions import *
# noinspection PyUnresolvedReferences
from .rest_user_submission import *
# noinspection PyUnresolvedReferences
from .rest_evaluator_jobs import *
