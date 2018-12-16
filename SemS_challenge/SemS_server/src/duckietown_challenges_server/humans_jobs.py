# coding=utf-8
from bs4 import BeautifulSoup, Tag
from duckietown_challenges.utils import friendly_size
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.response import Response
from pyramid.view import view_config

from .database import db_connection
from .db_challenges import read_challenges, read_challenge
from .db_evaluators import read_evaluators, read_evaluator
from .db_jobs import read_jobs, EvaluationJob, Artefact, read_job
from .db_submissions import read_submissions2, read_submission
from .humans_html import html_date, html_submission, html_evaluator, \
    html_job, html_step, html_challenge_code
from .humans_logs import get_page_navigation
from .utils_xml import stag, get_minimal_html, transpose_table


@view_config(route_name='humans_jobs')
def humans_jobs(request):
    html = get_minimal_html(title='Evaluation Jobs')
    html.body.attrs['class'] = 'page-jobs'
    body = html.body
    head = html.head

    head.append(stag('base', '', href='..'))

    body.append(stag('h1', "List of evaluation jobs"))

    section = Tag(name='section')
    body.append(section)

    page = int(request.params.get("page", 0))
    limit = int(request.params.get("limit", 25))
    start = limit * page

    with db_connection(request) as cursor:
        jobs = read_jobs(cursor, start=start, limit=limit)
        challenge_ids = set([_.challenge_id for _ in jobs.values()])
        evaluator_ids = set([_.evaluator_id for _ in jobs.values()])
        submission_ids = set([_.submission_id for _ in jobs.values()])
        challenges = read_challenges(cursor, challenge_ids=challenge_ids)
        evaluators = read_evaluators(cursor, evaluator_ids=evaluator_ids)
        uptodatejobs = {}
        submissions = read_submissions2(cursor, submission_ids=submission_ids, challenges=challenges,
                                        uptodatejobs=uptodatejobs)

    p1, p2 = get_page_navigation('humans/jobs', page, limit, num=len(jobs))

    section.append(p1)
    section.append(p2)
    table = format_jobs(jobs, challenges, submissions, evaluators)
    section.append(table)

    p = Tag(name='p')
    p.attrs['style'] = 'margin-top: 10em'
    p.append('This is the list of jobs already run. For the list of jobs in the queue see ')
    a = Tag(name='a')
    a.append('here')
    a.attrs['href'] = '/humans/queue'
    p.append(a)
    p.append('.')
    section.append(p)

    return Response(str(html))


@view_config(route_name='humans_jobs_one')
def humans_jobs_one(request):
    job_id = int(request.matchdict['job_id'])

    html = get_minimal_html(title='Job %s' % job_id)
    html.body.attrs['class'] = 'page-jobs'
    html.head.append(stag('base', '', href='../..'))
    body = html.body

    uptodatejobs = {}
    with db_connection(request) as cursor:
        try:
            job = read_job(cursor, job_id)
        except KeyError:
            msg = 'No job %s found' % job_id
            raise HTTPNotFound(msg)

        job0 = {job_id: job}
        evaluator = read_evaluator(cursor, job.evaluator_id)
        evaluators = {job.evaluator_id: evaluator}
        challenge = read_challenge(cursor, job.challenge_id)
        challenges = {job.challenge_id: challenge}
        submission = read_submission(cursor, job.submission_id, challenges=challenges, uptodatejobs=uptodatejobs)

    submissions = {job.submission_id: submission}
    body.append(stag('h1', 'Job %s' % job_id))
    d = Tag(name='section')
    table = format_jobs(job0, challenges, submissions, evaluators)
    table2 = transpose_table(table)
    d.append(table2)
    body.append(d)

    from .humans_submissions import get_highlights
    body.append(get_highlights(job0))

    return Response(str(html))


@view_config(route_name='humans_jobs_art_view')
def humans_jobs_art_view(request):
    job_id = int(request.matchdict['job_id'])
    first = request.matchdict['first']
    rest = request.matchdict['rest']
    rpath = "/".join((first,) + rest)

    with db_connection(request) as cursor:
        try:
            job = read_job(cursor, job_id)
        except KeyError:
            msg = 'No job %s found' % job_id
            raise HTTPNotFound(msg)

        html = get_minimal_html(title='Job %s' % job_id)

        if rpath in job.artefacts:
            artifact = job.artefacts[rpath]
            if 's3' in artifact.storage:
                url = artifact.storage['s3'].url

                if artifact.mime_type == 'text/html':
                    d = Tag(name='iframe')
                    d.attrs['src'] = url
                    d.attrs['style'] = 'display: block; clear: both; width: 100%; height: 100%'
                    d.append('iframe')
                    html.body.append(d)
                else:

                    raise HTTPFound(url)

        else:
            html.append('Could not find artifact %s' % rpath)
        return Response(str(html))



@view_config(route_name='humans_jobs_art')
def humans_jobs_art(request):
    job_id = int(request.matchdict['job_id'])

    html = get_minimal_html(title='Job %s' % job_id)
    html.body.attrs['class'] = 'page-jobs'
    html.head.append(stag('base', '', href='../../..'))
    body = html.body

    uptodatejobs = {}
    with db_connection(request) as cursor:
        try:
            job = read_job(cursor, job_id)
        except KeyError:
            msg = 'No job %s found' % job_id
            raise HTTPNotFound(msg)

        job0 = {job_id: job}
        evaluator = read_evaluator(cursor, job.evaluator_id)
        evaluators = {job.evaluator_id: evaluator}
        challenge = read_challenge(cursor, job.challenge_id)
        challenges = {job.challenge_id: challenge}
        submission = read_submission(cursor, job.submission_id, challenges=challenges, uptodatejobs=uptodatejobs)

    from .humans_submissions import get_highlights

    body.append(stag('h1', 'Artifacts for %s' % job_id))
    body.append(format_artifacts_table(job, job.artefacts, links='relative'))

    body.append(get_highlights(job0))

    return Response(str(html))

    # config.add_route('humans_jobs_art', '/humans/jobs/{job_id}/artefacts')
    # config.add_route('humans_jobs_art_view', '/humans/jobs/{job_id}/artefacts/{rpath}')


def format_jobs(jobs, challenges, submissions, evaluators):
    if not jobs:
        msg = 'No jobs to display.'
        return stag('p', msg)

    table = Tag(name='table')

    th = Tag(name='tr')
    th.append(stag('td', 'Job ID'))

    th.append(stag('td', 'submission'))
    th.append(stag('td', 'challenge'))

    th.append(stag('td', 'step'))
    th.append(stag('td', 'status'))
    th.append(stag('td', 'up to date'))

    th.append(stag('td', 'evaluator'))
    th.append(stag('td', 'date started'))
    th.append(stag('td', 'date completed'))
    th.append(stag('td', 'duration'))

    th.append(stag('td', 'message'))
    th.append(stag('td', 'artifacts'))
    th.append(stag('td', 'scores'))

    table.append(stag('thead', th))

    for id_job, job in jobs.items():
        assert isinstance(job, EvaluationJob)
        tr = Tag(name='tr')
        tr.attrs['class'] = [job.status, "is-uptodate" if job.uptodate else "not-uptodate"]
        tr.append(stag('td', html_job(job)))
        tr.append(stag('td', html_submission(submissions[job.submission_id])))
        challenge = challenges[job.challenge_id]
        tr.append(stag('td', html_challenge_code(challenge), _class='challenge'))
        # cslogger.info('job %s' % json.dumps(job.as_dict(), indent=4))
        # cslogger.info('challenge %s ' % json.dumps(challenge.as_dict(), indent=4))

        step = challenge.steps[job.step_id]
        tr.append(stag('td', html_step(step), _class='step'))
        tr.append(stag('td', job.status, _class='status'))
        tr.append(stag('td', "yes" if job.uptodate else "no", _class='uptodate'))

        if job.evaluator_id in evaluators:
            tr.append(stag('td', html_evaluator(evaluators[job.evaluator_id])))
        else:
            tr.append(stag('td', '-'))

        tr.append(stag('td', html_date(job.date_started)))
        tr.append(stag('td', html_date(job.date_completed)))

        if job.date_completed:
            difference = job.date_completed - job.date_started
            tr.append(stag('td', str(difference)))
        else:
            tr.append(stag('td', '-'))

        if job.stats and 'msg' in job.stats and job.stats['msg']:
            msg = job.stats['msg']
            tr.append(stag('td', html_log_details(msg)))
        else:
            tr.append(stag('td', ''))

        if job.date_completed:
            tr.append(stag('td', format_artifacts(job, job.artefacts)))
            tr.append(stag('td', format_scores(challenge, job.scores)))
        else:
            tr.append(stag('td', '-'))
            tr.append(stag('td', '-'))
        # tr.append(stag('td', str(job.stats)))

        table.append(tr)
    # language=html
    extra_head = """
       
    """
    table.append(BeautifulSoup(extra_head, 'lxml'))
    return table


def format_scores(challenge, scores):
    if not scores:
        return stag('span', 'No scores')

    d = Tag(name='div')
    official = list(_.name for _ in challenge.scoring.scores)
    not_official = [_ for _ in scores if _ not in official]

    present = [x for x in scores if x in official]
    if present:
        table1 = make_table(official, scores)
        d.append(table1)
        d.append(Tag(name='br'))
    if not_official:
        table2 = make_table(not_official, scores)
        details = Tag(name='details')
        summary = Tag(name='summary')
        summary.append("other stats")
        details.append(summary)
        details.append(table2)
        d.append(details)
    return d


def make_table(which, scores):
    table = Tag(name='table')

    for score_name in which:
        if score_name in scores:
            score_value = scores[score_name]
        else:
            continue
            # score_value = None

        tr = Tag(name='tr')

        td = Tag(name='td')
        td.append(score_name)
        tr.append(td)
        td = Tag(name='td')
        value = json.dumps(score_value)
        if len(value) < 40:

            td.append(value)
        else:
            details = Tag(name='details')
            summary = Tag(name='summary')
            summary.append("details")
            details.append(summary)
            details.append(value)
            td.append(details)

        tr.append(td)

        table.append(tr)
    return table


import json


def format_artifacts(job, artifacts):
    S = Tag(name='span')
    if artifacts:
        details = Tag(name='details')
        summary = Tag(name='summary')
        details.append(summary)

        summary.append('%d artifacts ' % len(artifacts))

        table = format_artifacts_table(job, artifacts, links='s3')

        details.append(table)

        S.append(details)
    else:
        S.append('0 artifacts ')
    return S


def format_artifacts_table(job, artifacts, links):
    table = Tag(name='table')

    for artifact in artifacts.values():
        assert isinstance(artifact, Artefact)
        tr = Tag(name='tr')

        td = Tag(name='td')
        td.attrs['class'] = 'artefact-size'
        td.append(friendly_size(artifact.size))
        tr.append(td)
        td = Tag(name='td')
        td.attrs['class'] = 'artefact-rpath'
        a = Tag(name='a')

        if links == 's3':
            if 's3' in artifact.storage:
                s3object = artifact.storage['s3']
                a.attrs['href'] = s3object.url
                local_name = artifact.rpath.replace('/', '___')
                a.attrs['download'] = local_name
                a.append(artifact.rpath)
                td.append(a)
            else:
                td.append(artifact.rpath)
        elif links == 'relative':
            if 's3' in artifact.storage:
                url = 'humans/jobs/{job_id}/artefacts/view/{rpath}'.format(job_id=job.job_id, rpath=artifact.rpath)
                a.attrs['href'] = url
                a.append(artifact.rpath)
                td.append(a)
        else:
            raise ValueError(links)
        td.append(a)
        tr.append(td)

        table.append(tr)
    return table


def html_log_details(msg):
    t = Tag(name='details')
    s = Tag(name='summary')
    s.append(msg[:20] + ' [...]')
    t.append(s)
    pre = Tag(name='pre')
    code = Tag(name='code')
    # conv = Ansi2HTMLConverter()
    # html = bs(conv.convert(msg, full=False))
    code.append(msg)
    pre.append(code)
    t.append(pre)
    return t
