# coding=utf-8
from bs4 import Tag, BeautifulSoup
from pyramid.response import Response
from pyramid.view import view_config

from .database import db_connection
from .db_submissions import get_jobs_opportunities, JobOpportunity, read_submissions2
from .db_users import read_users
from .humans_html import html_submission, html_challenge, html_user
from .utils_xml import get_minimal_html, stag


@view_config(route_name='humans_queue')
def humans_submissions(request):
    html = get_minimal_html(title='Job queues')
    html.body.attrs['class'] = 'page-jobs'
    body = html.body
    head = html.head
    head.append(stag('base', '', href='..'))

    body.append(stag('h1', "Job queue"))

    body.append(stag('p', 'These are the jobs that will be executed next.'))
    section = Tag(name='section')
    body.append(section)

    from .db_challenges import read_challenges

    with db_connection(request) as cursor:
        challenges = read_challenges(cursor)
        uptodatejobs = {}
        job_opportunites = get_jobs_opportunities(cursor, challenges=challenges, uptodatejobs=uptodatejobs)
        submissions = read_submissions2(cursor, challenges=challenges, uptodatejobs=uptodatejobs)

        users = read_users(cursor)

        table = format_job_opportunities(job_opportunites, submissions, challenges, users)
        section.append(table)

    p = Tag(name='p')
    p.attrs['style'] = 'margin-top: 10em'
    p.append('This is the list of jobs to run. For completed jobs see ')
    a = Tag(name='a')
    a.append('here')
    a.attrs['href'] = 'humans/jobs'
    p.append(a)
    p.append('.')
    section.append(p)

    return Response(str(html))


def format_job_opportunities(job_opportunites, submissions, challenges, users):
    if not job_opportunites:
        msg = 'No job_opportunites to display'
        return stag('p', msg)

    table = Tag(name='table')

    th = Tag(name='tr')
    th.append(stag('td', 'Submission'))
    th.append(stag('td', 'Challenge'))
    th.append(stag('td', 'Step'))
    th.append(stag('td', 'Admin priority'))
    th.append(stag('td', 'User'))
    th.append(stag('td', 'User priority'))

    table.append(stag('thead', th))

    for jo in job_opportunites:
        assert isinstance(jo, JobOpportunity)
        # 'challenge_id submission_id step_name step_id user_priority admin_priority user_id')
        tr = Tag(name='tr')

        tr.append(stag('td', html_submission(submissions[jo.submission_id])))
        tr.append(stag('td', html_challenge(challenges[jo.challenge_id])))
        tr.append(stag('td', str(jo.step_name)))

        tr.append(stag('td', str(jo.admin_priority)))
        tr.append(stag('td', html_user(users[jo.user_id])))
        tr.append(stag('td', str(jo.user_priority)))



        table.append(tr)

    extra_head = """
    """
    table.append(BeautifulSoup(extra_head, 'lxml'))
    return table
