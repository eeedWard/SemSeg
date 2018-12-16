# coding=utf-8
import json
from collections import OrderedDict


class EvaluationJob(object):

    def __init__(self, challenge_id, job_id, step_id, submission_id, evaluator_id, date_started, date_completed, status,
                 stats, challenge_name, artifacts, scores, uptodate):
        self.challenge_id = challenge_id
        self.challenge_name = challenge_name
        self.job_id = job_id
        self.step_id = step_id
        self.submission_id = submission_id
        self.evaluator_id = evaluator_id
        self.date_started = date_started
        self.date_completed = date_completed
        self.status = status
        self.stats = stats
        self.artefacts = artifacts
        self.scores = scores
        self.uptodate = uptodate

    def as_dict(self):
        _artefacts = dict([(k, v.as_dict()) for k, v in self.artefacts.items()])
        return dict(challenge_id=self.challenge_id,
                    challenge_name=self.challenge_name,
                    job_id=self.job_id,
                    step_id=self.step_id,
                    submission_id=self.submission_id,
                    evaluator_id=self.evaluator_id,
                    date_started=self.date_started.isoformat(),
                    date_complated=self.date_completed.isoformat() if self.date_completed else None,
                    status=self.status,
                    stats=self.stats,
                    uptodate=self.uptodate,
                    artefacts=_artefacts,
                    scores=self.scores)


class S3Object(object):
    def __init__(self, bucket_name, object_key, url):
        self.bucket_name = bucket_name
        self.object_key = object_key
        self.url = url

    def as_dict(self):
        return dict(bucket_name=self.bucket_name, object_key=self.object_key, url=self.url)

    @staticmethod
    def from_yaml(data):
        d0 = dict(**data)

        bucket_name = d0.pop('bucket_name')
        object_key = d0.pop('object_key')
        url = d0.pop('url')

        if d0:
            msg = 'Extra fields: %s' % list(d0)
            raise ValueError(msg)

        return S3Object(bucket_name, object_key, url)


class Artefact(object):
    def __init__(self, artifact_id, rpath, mime_type, size, sha256hex,
                 storage):
        self.artifact_id = artifact_id
        self.rpath = rpath
        self.mime_type = mime_type
        self.size = size
        self.sha256hex = sha256hex
        self.storage = storage

    def as_dict(self):
        storage = dict((k, v.as_dict()) for k, v in self.storage.items())
        return dict(artifact_id=self.artifact_id,
                    rpath=self.rpath,
                    mime_type=self.mime_type,
                    sha256hex=self.sha256hex,
                    size=self.size,
                    storage=storage)

    @staticmethod
    def from_yaml(data):
        d0 = dict(**data)

        artifact_id = None
        rpath = d0.pop('rpath')
        mime_type = d0.pop('mime_type')
        size = d0.pop('size')
        sha256hex = d0.pop('sha256hex')

        if d0:
            msg = 'Extra fields: %s' % list(d0)
            raise ValueError(msg)

        storage_ = d0.pop('storage')
        storage = {}
        if 's3' in storage_:
            storage['s3'] = S3Object.from_yaml(storage_['s3'])

        return Artefact(artifact_id, rpath, mime_type, size, sha256hex, storage)


def read_job(cursor, job_id, no_artifacts=False):
    cmd = """select 
                aido_challenges.queue_name, 
                aido_submissions.challenge_id, 
                job_id, 
                aido_evaluation_jobs.step_id, 
                aido_evaluation_jobs.submission_id, 
                evaluator_id, date_started, date_completed, 
                aido_evaluation_jobs.status, 
                stats,
                aido_challenges_evaluation_steps.evaluation_parameters = aido_evaluation_jobs.evaluation_parameters
          from 
                aido_evaluation_jobs, aido_submissions, aido_challenges, aido_challenges_evaluation_steps
          
          WHERE  aido_evaluation_jobs.submission_id = aido_submissions.submission_id
          and aido_challenges.challenge_id = aido_submissions.challenge_id
          and aido_challenges_evaluation_steps.step_id = aido_evaluation_jobs.step_id
          and job_id = %s 
          
          ORDER BY date_started DESC"""
    cursor.execute(cmd, (job_id,))
    if cursor.rowcount == 0:
        msg = 'Cannot find job %s' % job_id
        raise KeyError(msg)
    _ = cursor.fetchone()
    return interpret_one_job_(cursor, _, no_artifacts=no_artifacts)


class SHACache(object):
    sha256_to_s3object = {}


def get_s3_object(cursor, sha256hex):
    if sha256hex in SHACache.sha256_to_s3object:
        return SHACache.sha256_to_s3object[sha256hex]
    cmd = """
            select sha256hex, bucket_name, object_key, url from aido_artefacts_s3objects
            where sha256hex = %s 
            LIMIT 1
    """
    cursor.execute(cmd, (sha256hex,))
    if cursor.rowcount == 0:
        raise KeyError(sha256hex)
    # cslogger.debug('found %s rows for %s queries' % (cursor.rowcount))

    sha256hex_, bucket_name, object_key, url = cursor.fetchone()

    # cslogger.debug('found %s - >%s ' % (sha256hex, url))
    SHACache.sha256_to_s3object[sha256hex_] = S3Object(bucket_name, object_key, url)
    return SHACache.sha256_to_s3object[sha256hex_]


def interpret_one_job_(cursor, _, no_artifacts=False):
    (challenge_name, challenge_id, job_id, step_id, submission_id, evaluator_id,
     date_started, date_completed, status, stats, uptodate) = _
    if stats:
        stats = json.loads(stats)

    artifacts = OrderedDict()

    if not no_artifacts:
        cmd = """
            select artefact_id, rpath, mime_type, size, sha256hex
            from aido_evaluation_jobs_artefacts
            where job_id = %s
            ORDER BY rpath ASC
        """
        cursor.execute(cmd, (job_id,))

        records = list(cursor.fetchall())

        for artifact_id, rpath, mime_type, size, sha256hex in records:
            storage = {}
            try:
                storage['s3'] = get_s3_object(cursor, sha256hex)
            except KeyError:
                pass

            a = Artefact(artifact_id, rpath, mime_type, size, sha256hex, storage=storage)
            artifacts[rpath] = a

    scores = OrderedDict()
    cmd = """
            select name, value
            from aido_evaluation_jobs_stats
            where job_id = %s
            ORDER BY name ASC
        """
    cursor.execute(cmd, (job_id,))
    for score_name, value_json in cursor.fetchall():
        scores[score_name] = json.loads(value_json)

    j = EvaluationJob(challenge_id, job_id, step_id, submission_id, evaluator_id, date_started, date_completed,
                      status, stats, challenge_name, artifacts, scores, uptodate)
    return j


from . import cslogger


def read_jobs(cursor, submission_id=None, evaluator_id=None, start=0, limit=10000, no_artifacts=False):
    submission_test = "true"
    if submission_id is not None:
        submission_test += " AND (aido_evaluation_jobs.submission_id = %s)" % submission_id

    if evaluator_id is not None:
        submission_test += ' AND (evaluator_id = %s)' % evaluator_id

    ejobs = OrderedDict()
    cmd = """
        select 
                aido_challenges.queue_name, 
                aido_submissions.challenge_id, 
                job_id, aido_evaluation_jobs.step_id, aido_evaluation_jobs.submission_id, 
                evaluator_id, date_started, date_completed, aido_evaluation_jobs.status, stats, 
              aido_challenges_evaluation_steps.evaluation_parameters = aido_evaluation_jobs.evaluation_parameters
          from 
                aido_evaluation_jobs, aido_submissions, aido_challenges, aido_challenges_evaluation_steps
      
          WHERE  aido_evaluation_jobs.submission_id = aido_submissions.submission_id
          and aido_challenges.challenge_id = aido_submissions.challenge_id
          and aido_challenges_evaluation_steps.step_id = aido_evaluation_jobs.step_id 
          and {submission_test}    
          ORDER BY aido_evaluation_jobs.job_id DESC 
          LIMIT {start}, {limit}
        
          
          """.format(limit=limit, start=start, submission_test=submission_test)

    cursor.execute(cmd)
    found = list(cursor.fetchall())
    cslogger.debug('Now reading %d jobs' % len(found))
    for _ in found:
        j = interpret_one_job_(cursor, _, no_artifacts=no_artifacts)
        ejobs[j.job_id] = j
    return ejobs

# evaluation_jobs = Service(name='evaluation_jobs', path='/evaluation-jobs', renderer='json-indent')
