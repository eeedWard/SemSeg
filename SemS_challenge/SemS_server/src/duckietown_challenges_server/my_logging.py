# coding=utf-8
from bs4 import BeautifulSoup, Tag

from . import cslogger
from .db_challenges import read_challenges
from .db_evaluators import read_evaluators
from .db_jobs import read_job
from .db_submissions import read_submission
from .db_users import read_users
from .humans_html import date_tag, html_user, html_submission, html_job, html_challenge, \
    html_evaluator
from .utils_xml import stag


def dbinfo(cursor, *args, **kwargs):
    return dblog(cursor, *args, log_level='info', **kwargs)


def dbdebug(cursor, *args, **kwargs):
    return dblog(cursor, *args, log_level='debug', **kwargs)


def dberror(cursor, *args, **kwargs):
    return dblog(cursor, *args, log_level='error', **kwargs)


def dbwarning(cursor, *args, **kwargs):
    return dblog(cursor, *args, log_level='warning', **kwargs)


def dblog(cursor, short, longer=None, log_level='info', category=None,
          evaluator_id=None, evaluator_owner_id=None, challenge_id=None, step_id=None, job_id=None, submission_id=None,
          submitter_id=None, admin_id=None
          ):
    cslogger.info('dblog: %s%s' % (short, longer and ('\n' + longer) or ""))
    if category is None:
        log_category_id = 1
    else:
        log_category_id = {'private': 2}[category]

    content_short_html = short
    content_long_html = longer

    cmd = """
    insert into aido_log_entries(
        log_category_id, timestamp, content_short_html, content_long_html, log_level, 
        evaluator_id, admin_id, evaluator_owner_id, challenge_id, step_id, job_id,
        submission_id, submitter_id) values (%s, UTC_TIMESTAMP(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    args = (log_category_id, content_short_html, content_long_html, log_level,
            evaluator_id, admin_id, evaluator_owner_id, challenge_id, step_id, job_id,
            submission_id, submitter_id)
    cursor.execute(cmd, args)


def get_logs(cursor, category_id, start=0, limit=100000, evaluators=None, uptodatejobs=None):
    cmd = """ select  timestamp, log_category_id, content_short_html, content_long_html,
        log_level, evaluator_id, evaluator_owner_id, challenge_id, step_id, job_id, submission_id,
        submitter_id, admin_id from aido_log_entries 
        WHERE log_category_id = %s
        ORDER BY log_entry_id DESC 
        LIMIT %s, %s
    """
    cursor.execute(cmd, (category_id, start, limit))
    entries = list(cursor.fetchall())

    section = Tag(name='section')

    table = Tag(name='table')
    table.attrs['class'] = 'logs'

    users = read_users(cursor)
    challenges = read_challenges(cursor)
    evaluators = evaluators or {}
    uptodatejobs = uptodatejobs or {}

    # in the log entries you can use the following macros:
    #
    #    {admin_id}, {evaluator_id}, challenge_id, step_id, job_id, submission_id, admin_id
    #
    # plus the following which will evaluate to the hyperlinked name of the entity:
    #
    #  {admin}  - name of the admin
    #  {evaluator}
    #  {evaluator_owner}
    #  {submitter}
    #  {challenge}
    #  {step}
    #  {job}
    #  {submission}

    submissions = {}

    def load_submission(submission_id):
        if not submission_id in submissions:
            try:
                submission = read_submission(cursor, submission_id, challenges=challenges, uptodatejobs=uptodatejobs)
            except KeyError:
                raise
            submissions[submission_id] = submission
        return submissions[submission_id]

    jobs = {}

    def load_evaluator(evaluator_id):
        if evaluator_id not in evaluators:
            try:
                more = read_evaluators(cursor, evaluator_ids=[evaluator_id])
                assert evaluator_id in more
                evaluators.update(more)
            except KeyError:
                raise
            # evaluators[evaluator_id] = _
        assert evaluator_id in evaluators
        return evaluators[evaluator_id]

    def load_job(job_id):
        if not job_id in jobs:
            try:
                job = read_job(cursor, job_id, no_artifacts=True)
            except KeyError:
                raise
            jobs[job_id] = job
        return jobs[job_id]

    def substitute(a, tag, ff):
        if tag in a:
            sub = ff()
            return a.replace(tag, str(sub))
        else:
            return a

    for (timestamp, log_category_id, content_short_html, content_long_html,
         log_level, evaluator_id, evaluator_owner_id, challenge_id, step_id, job_id, submission_id,
         submitter_id, admin_id) in entries:

        # # XXX
        # if log_category_id != 1:
        #     continue

        tr = Tag(name='tr')
        tr.attrs['class'] = log_level
        td = Tag(name='td')
        td.attrs['class'] = 'log_level'
        td.append(log_level)
        tr.append(td)
        td = Tag(name='td')
        td.attrs['class'] = 'timestamp'
        td.append(date_tag(timestamp))
        tr.append(td)

        td = Tag(name='td')

        def replace_macros(s):
            if s is None:
                return ''

            def tag_person(person_id):
                if person_id is None:
                    return '(unspecified)'
                if person_id not in users:
                    return '(unknown id %s)' % person_id
                return html_user(users[person_id])

            def tag_admin():
                return tag_person(admin_id)

            def tag_submitter():
                return tag_person(submitter_id)

            def tag_evaluator_owner():
                return tag_person(evaluator_owner_id)

            def tag_submission():
                submission = load_submission(submission_id)
                return html_submission(submission)

            def tag_job():
                job = load_job(job_id)
                return html_job(job)

            def tag_challenge():
                if challenge_id not in challenges:
                    return '(unknown)'
                else:
                    return html_challenge(challenges[challenge_id])

            def tag_evaluator():
                evaluator = load_evaluator(evaluator_id)

                return html_evaluator(evaluator)

            def tag_step():
                # TODO
                cmd = "select step_name from aido_challenges_evaluation_steps where step_id = %s"
                cursor.execute(cmd, (step_id,))
                step_name, = cursor.fetchone()
                return stag('code', step_name)

            others = {
                'evaluator_id': evaluator_id,
                'evaluator_owner_id': evaluator_owner_id,
                'challenge_id': challenge_id,
                'step_id': step_id,
                'job_id': job_id,
                'submitter_id': submitter_id,
                'admin_id': admin_id,
            }
            for k, v in others.items():
                if v is None:
                    v = '(undefined)'
                s = s.replace('{%s}' % k, str(v))

            s = substitute(s, '{admin}', tag_admin)
            s = substitute(s, '{submitter}', tag_submitter)
            s = substitute(s, '{evaluator_owner}', tag_evaluator_owner)

            s = substitute(s, '{submission}', tag_submission)
            s = substitute(s, '{challenge}', tag_challenge)
            s = substitute(s, '{step}', tag_step)
            s = substitute(s, '{evaluator}', tag_evaluator)

            s = substitute(s, '{job}', tag_job)

            return s

        content_short_html2 = replace_macros(content_short_html)
        content_long_html2 = replace_macros(content_long_html)

        short = bs(content_short_html2)
        short.name = 'span'

        longer = bs(content_long_html2)
        longer.name = 'span'

        if content_long_html:
            td.append(short)

            details = Tag(name='details')

            summary = Tag(name='summary')
            summary.append('more details')
            details.append(summary)
            details.append(longer)
            td.append(details)
        else:
            td.append(short)
        tr.append(td)

        table.append(tr)

    section.append(table)
    return len(entries), section


def bs(fragment):
    """ Returns the contents wrapped in an element called "fragment".
        Expects fragment as a str in utf-8 """

    # check_isinstance(fragment, (str, unicode))

    if isinstance(fragment, unicode):
        fragment = fragment.encode('utf8')
    s = '<fragment>%s</fragment>' % fragment

    parsed = BeautifulSoup(s, 'lxml', from_encoding='utf-8')
    res = parsed.html.body.fragment
    assert res.name == 'fragment'
    return res
