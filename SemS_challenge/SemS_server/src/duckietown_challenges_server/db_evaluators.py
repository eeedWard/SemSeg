# coding=utf-8
from collections import OrderedDict

from duckietown_challenges import ChallengesConstants
from duckietown_challenges_server.misc import memoized_db_operation

from . import cslogger


class EvaluationFeature(object):

    def __init__(self, evaluation_feature_id, feature_name, short, long_md, parent_evaluation_feature_id):
        self.evaluation_feature_id = evaluation_feature_id
        self.feature_name = feature_name
        self.short = short
        self.long_md = long_md
        self.parent_evaluation_feature_id = parent_evaluation_feature_id

        self.children = []


@memoized_db_operation
def read_evaluation_features(cursor):
    cmd = '''
        select 
            evaluation_feature_id, feature_name, short, long_md, parent_evaluation_feature_id 
        from aido_evaluation_features 
        ORDER BY evaluation_feature_id ASC'''
    cursor.execute(cmd)

    evaluation_features = OrderedDict()
    for _ in cursor.fetchall():
        ei = EvaluationFeature(*_)
        evaluation_features[ei.evaluation_feature_id] = ei

    for x in evaluation_features.values():
        if x.parent_evaluation_feature_id is not None:
            evaluation_features[x.parent_evaluation_feature_id].children.append(x)

    return evaluation_features


#
# def now_tz():
#     # from dateutil.tz import tzlocal
#     # Get the current date/time with the timezone.
#     # now = datetime.datetime.now(tzlocal())
#     # return now
#
#     return datetime.datetime.now()


class EvaluatorInfo(object):
    ACTIVE_THRESHOLD_S = 60 * 5

    EVALUATOR_STATUS_ACTIVE = 'active'
    EVALUATOR_STATUS_INACTIVE = 'inactive'

    def __init__(self, evaluator_id, process_id, evaluator_version, machine_id, uid, user_display_name, first_heard,
                 last_heard, npings, last_heard_secs):
        self.evaluator_id = evaluator_id
        self.machine_id = machine_id
        self.process_id = process_id
        self.evaluator_version = evaluator_version
        self.uid = uid
        self.user_display_name = user_display_name
        self.first_heard = first_heard
        self.last_heard = last_heard
        self.npings = npings
        self.status2njobs = None

        self.last_heard_secs = last_heard_secs

        if self.last_heard_secs < EvaluatorInfo.ACTIVE_THRESHOLD_S:
            status = EvaluatorInfo.EVALUATOR_STATUS_ACTIVE
        else:
            status = EvaluatorInfo.EVALUATOR_STATUS_INACTIVE

        self.status = status

        self.features = {}


def read_evaluator(cursor, evaluator_id):
    cmd = '''
        select evaluator_id, process_id, evaluator_version, machine_id, uid, wp_users.display_name, first_heard,
         last_heard, npings, TIMESTAMPDIFF(SECOND, last_heard, UTC_TIMESTAMP()) from aido_evaluators, wp_users where wp_users.ID = aido_evaluators.uid
         and evaluator_id = %s
          ORDER BY last_heard DESC
         '''
    cursor.execute(cmd, (evaluator_id,))
    if cursor.rowcount == 0:
        msg = 'Could not find evaluator %s' % evaluator_id
        raise KeyError(msg)

    _ = cursor.fetchone()
    return interpret_one_evaluator(cursor, _)


def interpret_one_evaluator(cursor, _):
    ei = EvaluatorInfo(*_)
    status2njobs = {}
    for k in ChallengesConstants.ALLOWED_JOB_STATUS:
        status2njobs[k] = 0

    cmd = 'select status from aido_evaluation_jobs where evaluator_id = %s'
    cursor.execute(cmd, (ei.evaluator_id,))
    for status, in cursor.fetchall():
        if status in status2njobs:
            status2njobs[status] += 1
    # for k in ChallengesConstants.ALLOWED_JOB_STATUS:
    #
    #
    #     status2njobs[k] = cursor.rowcount
    ei.status2njobs = dict(**status2njobs)

    cmd = """ select evaluation_feature_id, amount 
                    from aido_evaluators_features where evaluator_id = %s
                   """
    cursor.execute(cmd, (ei.evaluator_id,))

    for evaluation_feature_id, amount in cursor.fetchall():
        ei.features[evaluation_feature_id] = amount
    return ei


def read_evaluators(cursor, evaluator_ids=None, user_id=None,
                    limit=10000, start=0):
    if evaluator_ids:
        evaluators = OrderedDict()
        for _ in evaluator_ids:
            e = read_evaluator(cursor, _)
            evaluators[e.evaluator_id] = e
        return evaluators
    else:
        where = ''
        if user_id:
            where += ' AND (uid = %s) ' % user_id

        cmd = '''
         select 
            evaluator_id, process_id, evaluator_version, 
            machine_id, uid, wp_users.display_name, first_heard,
         last_heard, npings, TIMESTAMPDIFF(SECOND, last_heard, UTC_TIMESTAMP()) 
         from aido_evaluators, wp_users 
         where 
            wp_users.ID = aido_evaluators.uid
            %s
         
          ORDER BY last_heard DESC
          LIMIT %s, %s
         ''' % (where, start, limit)

        cursor.execute(cmd)

        evaluators = OrderedDict()
        for _ in cursor.fetchall():
            e = interpret_one_evaluator(cursor, _)
            evaluators[e.evaluator_id] = e
        cslogger.info('read %d evaluators (limit = %s)' % (len(evaluators), limit))
        return evaluators
