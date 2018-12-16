# coding=utf-8
import json
from collections import OrderedDict

from bs4 import Tag

from duckietown_challenges.challenge import ChallengeTransitions, Scoring
from .utils_xml import stag


class Challenge(object):
    """ Note that steps is stepid2step """
    def __init__(self, challenge_id, queue_name, title, description, date_open, date_close, stepid2step, transitions,
                 scoring, tags, protocol, is_open, days_remaining):
        assert isinstance(transitions, ChallengeTransitions), transitions
        self.challenge_id = challenge_id
        self.queue_name = queue_name
        self.description = description
        self.date_open = date_open
        self.date_close = date_close
        self.title = title
        self.steps = stepid2step
        for k, v in stepid2step.items():
            assert isinstance(k, int), k.__repr__()
            assert isinstance(v, EvaluationStep), v.__repr__()
        self.transitions = transitions
        self.scoring = scoring
        self.tags = tags
        self.protocol = protocol
        self.is_open = is_open
        self.days_remaining = days_remaining

    def step_id_from_name(self, name):
        for step_id, step in self.steps.items():
            if step.step_name == name:
                return step_id
        raise KeyError(name)

    def as_dict(self):
        _steps = dict((k, v.as_dict()) for k, v in self.steps.items())
        return dict(challenge_id=self.challenge_id,
                    queue_name=self.queue_name,
                    description=self.description,
                    date_open=self.date_open.isoformat(),
                    date_close=self.date_close.isoformat(),
                    title=self.title,
                    steps=_steps, tags=self.tags,
                    transitions=self.transitions.as_list())

    # noinspection PyDictCreation
    def as_dict_for_challenge_description(self):
        data = {}
        data['challenge'] = self.queue_name
        data['description'] = self.description
        data['date-open'] = self.date_open.isoformat()
        data['date-close'] = self.date_close.isoformat()
        data['title'] = self.title
        data['steps'] = {}
        data['roles'] = {}
        data['scoring'] = self.scoring.as_dict()

        data['transitions'] = self.transitions.as_list()
        for step in self.steps.values():
            ds = step.as_dict()

            ds['title'] = None
            ds['description'] = ds.pop('step_description')
            ds['timeout'] = 1000  # XXXX
            ds.pop('step_name')
            ds.pop('step_id')
            data['steps'][step.step_name] = ds

        data['protocol'] = self.protocol
        return data


class EvaluationStep(object):

    def __init__(self, step_id, step_name, step_description, evaluation_parameters, features_required,
                 features_required_by_id):
        self.step_id = step_id
        self.step_name = step_name
        self.step_description = step_description
        self.evaluation_parameters = evaluation_parameters
        self.features_required = features_required
        self.features_required_by_id = features_required_by_id

    def as_dict(self):
        return dict(step_id=self.step_id,
                    step_name=self.step_name,
                    step_description=self.step_description,
                    evaluation_parameters=self.evaluation_parameters,
                    features_required=self.features_required)


def read_evaluation_steps(cursor, challenge_id):
    steps = {}
    cmd = "select step_id, step_name, step_description, evaluation_parameters from aido_challenges_evaluation_steps where challenge_id = %s"
    cursor.execute(cmd, (challenge_id,))

    for _ in list(cursor.fetchall()):
        step_id, step_name, step_description, evaluation_parameters = _

        cmd = """ select feature_name, aido_challenges_evaluation_steps_req_features.evaluation_feature_id, min_amount      from aido_challenges_evaluation_steps_req_features,
           aido_evaluation_features  
           where aido_challenges_evaluation_steps_req_features.evaluation_feature_id = aido_evaluation_features.evaluation_feature_id
           and step_id = %s
           order by evaluation_feature_id ASC
           
           """
        cursor.execute(cmd, (step_id,))
        features_required = OrderedDict()
        features_required_by_id = OrderedDict()
        for feature_name, evaluation_feature_id, min_amount in list(cursor.fetchall()):
            features_required[feature_name] = min_amount
            features_required_by_id[evaluation_feature_id] = min_amount

        evaluation_parameters = json.loads(evaluation_parameters)
        steps[step_id] = EvaluationStep(step_id, step_name, step_description, evaluation_parameters, features_required,
                                        features_required_by_id)

    return steps


def get_challenge_by_name(cursor, challenge_name):
    # XXX
    challenges = read_challenges(cursor)
    for challenge_id, challenge in challenges.items():
        if challenge.queue_name == challenge_name:
            return challenge
    raise KeyError(challenge_name)


def read_challenge(cursor, challenge_id):
    cmd = """
            select 
                challenge_id, queue_name, title, description, date_open, date_close, scoring, tags, protocol,
                (date_open <= UTC_TIMESTAMP()) AND (UTC_TIMESTAMP() <= date_close),
                TIMESTAMPDIFF(DAY, UTC_TIMESTAMP(), date_close),
                transitions
            from aido_challenges 
            where challenge_id = %s
    """

    cursor.execute(cmd, (challenge_id,))
    if cursor.rowcount == 0:
        msg = 'Could not find challenge %s' % challenge_id
        raise KeyError(msg)

    _ = cursor.fetchone()

    return interpret_one(cursor, _)


def interpret_one(cursor, _):
    challenge_id, queue_name, title, description, date_open, date_close, scoring, tags, protocol, \
    is_open, days_remaining, transitions_json = _
    stepid2step = read_evaluation_steps(cursor, challenge_id)

    tags = json.loads(tags)

    scoring = Scoring.from_yaml(json.loads(scoring))
    transitions_list = json.loads(transitions_json)


    ct = ChallengeTransitions(transitions_list, ChallengeTransitions.steps_from_transitions(transitions_list))

    c = Challenge(challenge_id, queue_name, title, description, date_open, date_close, stepid2step, ct,
                  scoring, tags=tags, protocol=protocol,
                  is_open=is_open,
                  days_remaining=days_remaining)
    return c


def read_challenges(cursor, challenge_ids=None):
    challenges = {}
    if challenge_ids:
        for challenge_id in challenge_ids:
            challenges[challenge_id] = read_challenge(cursor, challenge_id)
        return challenges
    else:
        cmd = """
            select 
                challenge_id, queue_name, title, description, date_open, date_close, scoring, tags, protocol,
                (date_open <= UTC_TIMESTAMP()) AND (UTC_TIMESTAMP() <= date_close),
                TIMESTAMPDIFF(DAY, UTC_TIMESTAMP(), date_close),
                transitions
            from aido_challenges 
        
            """
        cursor.execute(cmd)

        for _ in cursor.fetchall():
            c = interpret_one(cursor, _)
            challenges[c.challenge_id] = c
        return challenges


def challenge_html(challenge):
    t = Tag(name='span')
    href = ''
    a = stag('a', challenge.queue_name, href=href)
    t.append(a)
    return t
#
#
# def get_transition_for_challenge(cursor, challenge_id):
#     cmd = """
#         select transitions from aido_challenges where challenge_id = %s
#     """
#     cursor.execute(cmd, (challenge_id,))
#     transitions, = cursor.fetchone()
#     transitions = json.loads(transitions)
#
#     # read steps
#     cmd = """
#         select step_name from aido_challenges_evaluation_steps where challenge_id = %s
#     """
#     cursor.execute(cmd, (challenge_id,))
#     steps = []
#     for step_name, in cursor.fetchall():
#         steps.append(str(step_name))
#
#     ct = ChallengeTransitions(transitions, steps)
#     return ct
