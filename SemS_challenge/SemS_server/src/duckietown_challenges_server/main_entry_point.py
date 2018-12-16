# coding=utf-8
import json
import os
from threading import Thread

from pyramid.config import Configurator
from pyramid.renderers import JSON

from . import cslogger, __version__
from .database import db_connection
from .my_logging import dbinfo


def main(global_config, **settings):
    from duckietown_challenges.col_logging import setup_logging
    setup_logging()
    cslogger.info("Started with configuration:\n%s" % json.dumps(settings, indent=4))

    parameters = [
        'mysql_db',
        'mysql_host',
        'mysql_uid',
        'mysql_pwd',
        's3_prefix',
        's3',
        'aws_access_key_id',
        'aws_secret_access_key',
        'bucket_name',
        'insecure',
        'wordpress_rest',
        'wordpress_token']

    allow_missing = ['wordpress_rest', 'wordpress_token']
    for _ in allow_missing:
        assert _ in parameters
    from .constants import ChallengeServerConstants

    for setting in parameters:
        k = 'duckietown_challenges_server.%s' % setting
        if k in settings:
            val = settings[k]
            setattr(ChallengeServerConstants, setting, val)
        else:
            env = 'DCS_%s' % setting.upper()
            if env in os.environ:
                val = os.environ[env]
                setattr(ChallengeServerConstants, setting, val)
            else:
                msg = 'Could not find either configuration %s or env variable %s' % (setting, env)
                if setting in allow_missing:
                    cslogger.error(msg)
                else:
                    raise Exception(msg)

    ChallengeServerConstants.s3 = bool(int(ChallengeServerConstants.s3))
    ChallengeServerConstants.insecure = bool(int(ChallengeServerConstants.insecure))

    cslogger.info('Using S3: %r' % ChallengeServerConstants.s3)
    cslogger.info('Insecure: %r' % ChallengeServerConstants.insecure)

    with db_connection(request=None) as cursor:
        from duckietown_challenges import __version__ as dcs_version
        dbinfo(cursor, "Duckietown Challenges Server starting; DCS: %s; DC: %s." % (__version__, dcs_version))

        # challenges = read_challenges(cursor)

        # dbinfo(cursor, 'Loaded %d challenges.' % len(challenges))

    from duckietown_challenges_server.db_users import get_users_thread
    t = Thread(target=get_users_thread)
    t.start()

    config = Configurator(settings=settings)
    config.add_renderer('json-indent', JSON(indent=4))

    config.include("cornice")
    # config.add_settings(handle_exceptions=False)

    config.add_route('home', '/')
    config.add_route('dashboard', '/humans/dashboard')
    config.add_route('docs', '/humans/docs')
    config.add_route('api-docs', '/humans/api-docs')

    config.add_route('humans_jobs', '/humans/jobs')
    config.add_route('humans_jobs_one', '/humans/jobs/{job_id}')
    config.add_route('humans_users', '/humans/users')
    config.add_route('humans_users_one', '/humans/users/{user_id}')
    config.add_route('humans_submissions', '/humans/submissions')
    config.add_route('humans_submissions_one', '/humans/submissions/{submission_id}')

    config.add_route('humans_jobs_art', '/humans/jobs/{job_id}/artefacts')
    config.add_route('humans_jobs_art_view', '/humans/jobs/{job_id}/artefacts/view/{first}*rest')
    config.add_route('humans_challenges', '/humans/challenges')
    config.add_route('humans_challenges_one', '/humans/challenges/{cname}')
    config.add_route('humans_leaderboards_one', '/humans/challenges/{cname}/leaderboard')
    config.add_route('humans_leaderboards_image', '/humans/challenges/{cname}/leaderboard/image.png')
    config.add_route('humans_leaderboards_secret', '/humans/challenges/{cname}/secret')
    config.add_route('humans_evaluators', '/humans/evaluators')
    config.add_route('humans_queue', '/humans/queue')
    config.add_route('humans_logs', '/humans/logs')
    config.add_route('humans_evaluators_one', '/humans/evaluators/{evaluator_id}')

    config.scan("duckietown_challenges_server.humans_api_docs")
    config.scan("duckietown_challenges_server.humans_challenges")
    config.scan("duckietown_challenges_server.humans_evaluators")
    config.scan("duckietown_challenges_server.humans_home")
    config.scan("duckietown_challenges_server.humans_users")
    config.scan("duckietown_challenges_server.humans_jobs")
    config.scan("duckietown_challenges_server.humans_leaderboards")
    config.scan("duckietown_challenges_server.humans_submissions")
    config.scan("duckietown_challenges_server.humans_queue")
    config.scan("duckietown_challenges_server.humans_logs")

    config.scan("duckietown_challenges_server.rest")
    config.scan("duckietown_challenges_server.rest_pub_challenges")
    config.scan("duckietown_challenges_server.rest_evaluator_jobs")
    config.scan("duckietown_challenges_server.rest_job_submission")
    config.scan("duckietown_challenges_server.rest_info")
    config.scan("duckietown_challenges_server.rest_leaderboards_data")
    config.scan("duckietown_challenges_server.rest_organizer_challenges")
    # config.scan("duckietown_challenges_server.rest_subs_by_challenge")
    config.scan("duckietown_challenges_server.rest_user_submissions")
    config.scan("duckietown_challenges_server.rest_user_submission")

    return config.make_wsgi_app()
