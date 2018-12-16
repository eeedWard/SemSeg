# coding=utf-8
from .auth import valid_dt1_token
from .database import db_connection
from .db_submissions import read_submission, get_uptodate_jobs
from .misc import result_success, result_failure
from .rest import s_submission


@s_submission.get(validators=valid_dt1_token)
def get_submission(request):
    with db_connection(request) as cursor:
        user_id = request.validated['uid']
        submission_id = request.matchdict['sid']
        challenges = {}
        uptodatejobs = {}

        get_uptodate_jobs(cursor, uptodatejobs, submission_ids=[submission_id])

        try:

            submission = read_submission(cursor, submission_id, challenges=challenges, uptodatejobs=uptodatejobs)
        except KeyError:
            msg = 'Could not find submission %s' % submission_id
            return result_failure(msg)

        if submission.user_id != user_id:
            # remove details
            submission.redact()

        data = submission.as_dict()

        data['status-details'] = submission.submission_status.as_dict()

        return result_success(data, total=1)
