# coding=utf-8
import json
import subprocess

import yaml
from pyramid.httpexceptions import HTTPBadRequest

from duckietown_challenges import ChallengesConstants, InvalidConfiguration
from duckietown_challenges.challenge import ChallengeDescription, InvalidChallengeDescription, ChallengeStep, \
    EvaluationParameters, NotEquivalent, SUBMISSION_CONTAINER_TAG
from duckietown_challenges.utils import indent
from . import cslogger
from .auth import valid_dt1_token, is_superadmin
from .database import db_connection
from .misc import result_success, result_failure
from .my_logging import dbinfo
from .rest import s_challenge_define


class InvalidConfigForChallenge(Exception):
    pass


check_tag = False


def validate_config(challenge_description):
    assert isinstance(challenge_description, ChallengeDescription)
    nappears = 0

    if len(challenge_description.steps) == 0:
        msg = 'No steps.'
        raise InvalidConfigForChallenge(msg)

    for step_name, step in challenge_description.steps.items():
        for service_name, service in step.evaluation_parameters.services.items():
            if service.image == '_':
                msg = 'Invalid image name "%s" for service "%s" :\n\n%s' % (service.image, service_name,
                                                                            indent(service, '  '))
                raise InvalidConfigForChallenge(msg)

            if service.image == SUBMISSION_CONTAINER_TAG:
                nappears += 1

            if ':' in service.image:
                repository, tag = service.image.split(':')

                if check_tag:
                    try:
                        check_tag_exists(repository, tag)
                    except CouldNotCheck as e:
                        cslogger.warning('Could not check: %s' % e)
                    except DoesNotExist as e:
                        msg = 'Could not find tag %s for %s:\n\n%s' % (tag, repository, indent(e, '  '))
                        raise InvalidConfigForChallenge(msg)
                    else:
                        cslogger.info('ok, I verified that %s has tag %s' % (repository, tag))

    if nappears == 0:
        msg = 'The code %s does not appear anywhere.' % SUBMISSION_CONTAINER_TAG
        raise InvalidConfigForChallenge(msg)


class CouldNotCheck(Exception):
    pass


class DoesNotExist(Exception):
    pass


def check_tag_exists(repository, tag, timeout=2):
    # repository += "XXX"
    url = "https://index.docker.io/v1/repositories/%s/tags/%s" % (repository, tag)

    cslogger.info('making call to %s' % url)
    try:
        cmd = ['curl', '-m', str(timeout), "--silent", "--show-error", "--fail", url]
        try:
            output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            if e.returncode == 22:
                msg = 'CURL does not find %s ' % url
                raise DoesNotExist(msg)
            else:
                msg = str(e)
                raise CouldNotCheck(msg)

        # cslogger.info('curl says %r' % output)
        # if 'not found' in output:
        #     msg = 'CURL got "%s" when looking at\n %s ' % (output, url )
        #     raise DoesNotExist(msg)
        # try:
        #     urllib2.urlopen(url, timeout=timeout)
        # except urllib2.HTTPError as e:
        #     # we expect 404
        #     if e.code == 404:
        #         msg = 'URL gives 404: %s' % url
        #         raise DoesNotExist(msg)
        #     else:
        #         msg = 'error while checking %s has tag %s: %s' % (repository, tag, e)
        #         raise CouldNotCheck(msg)

        #
        # r = requests.get(url, timeout=timeout)
        # if r.status_code == 404:
        #     msg = 'URL gives 404: %s' % url
        #     raise DoesNotExist(msg)
    #
    # except requests.exceptions.ConnectionError as e:
    #     msg = 'error while checking %s has tag %s: %s' % (repository, tag, e)
    #     raise CouldNotCheck(msg)
    # except requests.exceptions.Timeout as e:
    #     msg = 'timeout while checking %s has tag %s: %s' % (repository, tag, e)
    #     raise CouldNotCheck(msg)
    except DoesNotExist:
        raise
    except BaseException as e:
        msg = 'unexpected error while checking %s has tag %s: %s' % (repository, tag, e)
        raise CouldNotCheck(msg)


# https://index.docker.io/v1/repositories/andreacensi/aido1_lf1-v3-submission/tags/2018_10_10_17_13_29


@s_challenge_define.post(validators=valid_dt1_token)
def challenge_define(request):
    with db_connection(request) as cursor:

        text = request.text
        data = json.loads(text)
        user_id = request.validated['uid']

        if not is_superadmin(user_id):
            msg = 'You are not authorized.'
            return result_failure(msg)

        force_invalidate = data['force-invalidate']

        try:
            yaml_string = data['yaml']
        except KeyError as e:
            msg = 'Invalid request body: %s' % e
            cslogger.error(msg)
            raise HTTPBadRequest(msg)

        data = yaml.load(yaml_string)

        try:
            c = ChallengeDescription.from_yaml(data)
        except (InvalidChallengeDescription, InvalidConfiguration) as e:
            msg = 'Invalid challenge format: %s' % e
            return result_failure(msg)

        try:
            validate_config(c)
        except InvalidConfigForChallenge as e:
            msg = 'Invalid challenge format:\n\n%s' % e
            return result_failure(msg)

        cslogger.debug(yaml.dump(c.as_dict(), default_flow_style=False))

        date_open = c.date_open.strftime("%Y-%m-%d %H:%M:00")
        date_close = c.date_close.strftime("%Y-%m-%d %H:%M:00")

        print(date_open)
        print(date_close)

        transitions_json = json.dumps(c.ct.transitions)

        # search if we have a challenge already
        cmd = 'select challenge_id from aido_challenges where queue_name = %s'
        cursor.execute(cmd, (c.name,))
        if cursor.rowcount == 0:
            cslogger.info('No existing challenge %s' % c.name)

            cmd = """
                insert into 
                    aido_challenges(queue_name, title, description, protocol, 
                                    transitions, tags, scoring, date_open, date_close) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            args = (c.name, c.title, c.description, c.protocol, transitions_json, json.dumps(c.tags),
                    json.dumps(c.scoring.as_dict()), date_open, date_close)
            cursor.execute(cmd, args)

            created = True
            challenge_id = cursor.lastrowid
        else:
            cslogger.info('Found existing challenge %s' % c.name)
            challenge_id, = cursor.fetchone()

            cmd = """
                update aido_challenges set 
                    title = %s, description = %s, protocol = %s,
                    transitions = %s, tags = %s, scoring = %s,
                    date_open = %s, date_close = %s 
                where challenge_id = %s
            """
            args = (c.title, c.description, c.protocol,
                    transitions_json, json.dumps(c.tags), json.dumps(c.scoring.as_dict()),
                    date_open, date_close,
                    challenge_id)

            cursor.execute(cmd, args)
            # if cursor.rowcount != 1:
            #     msg = 'Error while updating challenge %s (rowcount = %s, %s).' % (challenge_id, cursor.rowcount, affected)
            #     return result_failure(msg)
            created = False

        for user, permissions in c.roles.items():

            if user.startswith('user:'):
                username = user.replace('user:', '')
            else:
                msg = 'Wrong form for %r, should start with "user:"' % user
                return result_failure(msg)

            cmd = """
                select ID from wp_users where user_login = %s or user_email = %s 
            """
            args = (username, username)
            cursor.execute(cmd, args)
            if cursor.rowcount == 0:
                msg = 'Could not find any user by looking for %r' % username
                return result_failure(msg)
            elif cursor.rowcount > 1:
                msg = 'Multiple users match for %r' % username
                return result_failure(msg)

            this_user_id, = cursor.fetchone()

            cmd = """
                delete from aido_challenges_role_assignments
                where challenge_id = %s and user_id = %s;             
            """
            args = (challenge_id, this_user_id)
            cursor.execute(cmd, args)

            p2 = dict(**permissions)
            power_change = bool(p2.pop('change', False))
            power_grant = bool(p2.pop('grant', False))
            power_moderate = bool(p2.pop('moderate', False))
            power_snoop = bool(p2.pop('snoop', False))
            if p2:
                msg = 'Unknown powers: %s' % p2
                return result_failure(msg)

            cmd = """
                insert into aido_challenges_role_assignments(user_id, 
                challenge_id, power_change, power_grant, power_moderate, power_snoop)
                values (%s, %s, %s, %s, %s, %s)
            """
            args = (this_user_id, challenge_id, power_change, power_grant, power_moderate, power_snoop)
            cursor.execute(cmd, args)

        steps_updated = {}

        for step_name, step in c.get_steps().items():
            assert isinstance(step, ChallengeStep)

            cmd = """
              select step_id, evaluation_parameters 
              from aido_challenges_evaluation_steps where challenge_id=%s and step_name = %s
            """
            args = (challenge_id, step_name)
            cursor.execute(cmd, args)
            if cursor.rowcount == 0:

                cmd = """
                    insert into aido_challenges_evaluation_steps(step_name, step_description, challenge_id,
                    evaluation_parameters) values (%s, %s, %s, %s)
                """
                args = (step_name, step.description, challenge_id, json.dumps(step.evaluation_parameters.as_dict()))
                cursor.execute(cmd, args)
                step_id = cursor.lastrowid

                steps_updated[step_name] = "New step."
            else:
                step_id, old_evaluation_parameters_json = cursor.fetchone()

                try:
                    old_evaluation_parameters = EvaluationParameters.from_yaml(json.loads(
                            old_evaluation_parameters_json))
                except:
                    old_evaluation_parameters = EvaluationParameters(version='3', services={})

                # cslogger.debug('old: %s' % old_evaluation_parameters)
                # cslogger.debug('new: %s' % step.evaluation_parameters)

                try:
                    old_evaluation_parameters.equivalent(step.evaluation_parameters)

                    if force_invalidate:
                        msg = 'Forcing NotEquivalent because of force_invalidate'
                        raise NotEquivalent(msg)

                except NotEquivalent as e:
                    msg = 'I need to update the challenge:\n\n%s' % indent(e, '  ')
                    cslogger.info(msg)

                    steps_updated[step_name] = msg

                    cmd = """
                        update  aido_challenges_evaluation_steps
                        set step_description = %s, evaluation_parameters = %s where step_id = %s
                    """
                    args = (step.description, json.dumps(step.evaluation_parameters.as_dict()), step_id)
                    cursor.execute(cmd, args)

                else:
                    pass
                    # msg = 'No need to update as the parameters are equivalent.'
                    # cslogger.info(msg)

            cmd = "delete from aido_challenges_evaluation_steps_req_features where step_id = %s"
            cursor.execute(cmd, (step_id,))

            for feature_name, value in step.features_required.items():
                min_amount = int(value)
                cmd = """select evaluation_feature_id from aido_evaluation_features where feature_name = %s"""
                cursor.execute(cmd, (feature_name,))
                if cursor.rowcount == 0:
                    msg = 'Cannot find feature %s' % feature_name
                    return result_failure(msg)

                evaluation_feature_id, = cursor.fetchone()
                cmd = """insert into
                 aido_challenges_evaluation_steps_req_features(step_id, evaluation_feature_id, min_amount) 
                 values(%s, %s, %s)"""
                args = (step_id, evaluation_feature_id, min_amount)
                cursor.execute(cmd, args)

        if created:
            dbinfo(cursor, "Challenge {challenge} created by {admin}",
                   admin_id=user_id, challenge_id=challenge_id)
        else:
            longer = 'Updated steps %s.' % ", ".join(steps_updated)
            dbinfo(cursor, "Challenge {challenge} updated by {admin}", longer=longer,
                   admin_id=user_id, challenge_id=challenge_id)

        cmd = """
            update aido_submissions
            set status = %s
            where challenge_id = %s
            and status != %s
            
        """
        # not sure about this
        cursor.execute(cmd, (ChallengesConstants.STATUS_SUBMITTED, challenge_id,

                             ChallengesConstants.STATUS_FAILED))

        return result_success({'challenge_id': challenge_id, 'steps_updated': steps_updated})


def check_good_evaluation_parameters(evaluation_parameters):
    assert isinstance(evaluation_parameters, EvaluationParameters)
