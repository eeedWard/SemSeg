# coding=utf-8
from collections import defaultdict

from bs4 import BeautifulSoup, Tag
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config

from .database import db_connection
from .db_jobs import read_jobs, EvaluationJob, Artefact
from .db_submissions import read_submissions2, Submission, read_submission, get_uptodate_jobs
from .db_users import read_users, read_user
from .humans_html import html_challenge, html_date, html_submission, html_user, html_job, html_job_id
from .humans_jobs import format_jobs
from .humans_logs import get_page_navigation
from .utils_xml import stag, get_minimal_html, transpose_table, catch_ui_render_problem


@view_config(route_name='humans_submissions')
def humans_submissions(request):
    html = get_minimal_html(title='Submissions')
    html.body.attrs['class'] = 'page-submissions'
    body = html.body
    head = html.head
    head.append(stag('base', '', href='..'))

    body.append(stag('h1', "List of submissions"))

    section = Tag(name='section')
    body.append(section)

    from .db_challenges import read_challenges

    page = int(request.params.get("page", 0))
    limit = int(request.params.get("limit", 25))
    start = limit * page

    with db_connection(request) as cursor:
        challenges = read_challenges(cursor)
        uptodatejobs = {}
        submissions = read_submissions2(cursor, start=start, limit=limit, challenges=challenges,
                                        uptodatejobs=uptodatejobs)
        users = read_users(cursor)

    p1, p2 = get_page_navigation('humans/submissions', page, limit, num=len(submissions))

    section.append(p1)
    section.append(p2)
    table = format_submissions(submissions, challenges, users)
    section.append(table)

    return Response(str(html))


@view_config(route_name='humans_submissions_one')
def humans_submissions_one(request):
    submission_id = int(request.matchdict['submission_id'])

    html = get_minimal_html(title='Submission %s' % submission_id)
    html.body.attrs['class'] = 'page-submissions'
    html.head.append(stag('base', '', href='../..'))
    body = html.body

    with db_connection(request) as cursor:
        challenges = {}
        uptodatejobs = {}

        get_uptodate_jobs(cursor, uptodatejobs, submission_ids=[submission_id])
        try:
            submission = read_submission(cursor, submission_id, challenges=challenges, uptodatejobs=uptodatejobs)
        except KeyError:
            msg = 'No submission with ID %s found' % submission_id
            raise HTTPNotFound(msg)

        # challenge = read_challenge(cursor, submission.challenge_id)
        # challenge = challenges[submission.challenge_id]
        user = read_user(cursor, submission.user_id)
        # evaluators = read_evaluator(cursor)

        body.append(stag('h1', 'Submission %s' % submission_id))
        d = Tag(name='section')
        submissions = {submission_id: submission}
        # challenges = {submission.challenge_id: challenge}
        users = {submission.user_id: user}
        table = format_submissions(submissions, challenges, users)
        cursor.debug('users: %s' % users)
        cursor.debug('submission: %s' % submission.as_dict())
        d.append(transpose_table(table))
        body.append(d)

        # body.append(stag('pre', stag('code', submission.parameters.__repr__())))

        his = read_jobs(cursor, submission_id=submission_id)

        status = submission.submission_status

        # body.append(stag('p', 'Complete? %s' % status.complete))

        if not status.complete:
            body.append(stag('p', 'Step to execute: %s' % status.next_steps))
        # else:
        #     body.append(stag('p', 'Result? %s' % status.result))

        body.append(get_highlights(his))
        body.append(stag('h2', 'Evaluation jobs for this submission'))
        body.append(format_jobs(his, challenges, submissions, evaluators={}))

    return Response(str(html))


import os


def get_highlights(his):
    s = Tag(name='div')

    for job_id, job in his.items():

        assert isinstance(job, EvaluationJob), job
        links = []

        videos = []

        urls_used_as_image_links = []

        def get_html_url_for_artifact(rpath):
            h = os.path.splitext(rpath)[0] + '.html'
            if h in job.artefacts:
                return get_url_for_artifact(job.artefacts[h])
            else:
                raise KeyError

        def get_url_for_artifact(artifact):
            if 's3' in artifact.storage:
                ob = artifact.storage['s3']
                if ob.url is None:
                    raise KeyError()
                else:
                    url = ob.url
                    if 'amazonaws' in url:
                        url = url.replace('http://', 'https://')
                    return url
            else:
                raise KeyError()

        for rpath in sorted(job.artefacts):
            artifact = job.artefacts[rpath]
            assert isinstance(artifact, Artefact)

            try:
                url = get_url_for_artifact(artifact)
            except KeyError:
                continue

            if artifact.mime_type == 'video/mp4':
                video = get_video_tag(artifact, url)
                videos.append(video)
            if artifact.mime_type in ['image/png', 'image/jpg', 'image/svg+xml']:
                image = get_image_tag(artifact, url)
                try:
                    html_url_for_artifact = get_html_url_for_artifact(rpath)
                except KeyError:
                    videos.append(image)
                else:
                    urls_used_as_image_links.append(html_url_for_artifact)
                    a = stag('a', image, href=html_url_for_artifact)
                    a.attrs['class'] = 'link-for-image'
                    a.attrs['style'] = 'outline: solid 2px blue; margin: 5px;'
                    videos.append(a)

        container2stream2url = defaultdict(dict)
        for rpath in sorted(job.artefacts):
            artifact = job.artefacts[rpath]
            assert isinstance(artifact, Artefact)
            try:
                url = get_url_for_artifact(artifact)
            except KeyError:
                continue

            if url in urls_used_as_image_links:
                continue

            if artifact.mime_type in ['application/pdf', 'text/html']:
                if rpath.startswith('logs'):
                    tokens = rpath.split('/')
                    assert tokens[0] == 'logs'
                    container = tokens[1]
                    stream = os.path.splitext(tokens[2])[0]
                    container2stream2url[container][stream] = url

                else:
                    a = Tag(name='a')
                    a.append(artifact.rpath)
                    a.attrs['href'] = url
                    p = stag('p', a)
                    links.append(p)

        logs = Tag(name='div')
        logs.attrs['class'] = 'logs'
        for container, streams in container2stream2url.items():
            det1 = Tag(name='details')
            sum1 = Tag(name='summary')
            sum1.append('logs for container ')
            sum1.append(stag('code', container))
            det1.append(sum1)
            for stream, url in streams.items():
                det2 = Tag(name='details')
                det2.attrs['style'] = 'margin-left: 3em;'
                sum2 = stag('summary', stream)
                det2.append(sum2)
                iframe = Tag(name='iframe')
                iframe.attrs['src'] = url
                iframe.attrs['style'] = 'width:100%; min-height: 50vh'
                det2.append(iframe)
                det1.append(det2)

            logs.append(det1)

        if videos or links or container2stream2url:
            s.append(stag('p', html_job(job)))

        s.append(logs)

        for l in links:
            s.append(l)

        if urls_used_as_image_links:
            s.append(stag('p', 'Click the images to see detailed statistics about the episode.'))
        for v in videos:
            s.append(v)

    return s


def get_image_tag(artefact, url):
    img = Tag(name='image')
    img.attrs['src'] = url
    img.attrs['width'] = 320
    return img


def get_video_tag(artefact, url):
    video = Tag(name='video')
    video.attrs['style'] = 'border: solid 1px black'
    video.attrs['width'] = 320
    # video.attrs['height'] = 320
    video.attrs['autoplay'] = 1
    video.attrs['controls'] = 1
    video.attrs['loop'] = 1
    source = Tag(name='source')
    source.attrs['type'] = artefact.mime_type
    source.attrs['src'] = url
    video.append(source)
    return video


@catch_ui_render_problem
def format_submissions(submissions, challenges, users):
    if not submissions:
        msg = 'No submissions to display'
        return stag('p', msg)
    table = Tag(name='table')

    th = Tag(name='tr')
    # th.append(stag('td', ''))
    th.append(stag('td', 'Submission'))
    th.append(stag('td', 'Status'))
    th.append(stag('td', 'Challenge'))
    th.append(stag('td', 'User'))
    th.append(stag('td', 'Date submitted'))

    th.append(stag('td', 'Complete'))
    th.append(stag('td', 'Result'))
    th.append(stag('td', 'Jobs'))
    # th.append(stag('td', 'TODO'))

    # th.append(stag('td', 'Image'))
    th.append(stag('td', 'User label'))
    # th.append(stag('td', 'User payload'))

    table.append(stag('thead', th))

    for id_sub, sub in submissions.items():
        assert isinstance(sub, Submission)
        tr = Tag(name='tr')
        # tr.attrs['class'] = sub.submission_status.result

        tr.append(stag('td', html_submission(sub)))
        tr.append(stag('td', sub.user_retired and "retired" or sub.admin_aborted and "aborted" or "normal"))

        tr.append(stag('td', html_challenge(challenges[sub.challenge_id])))
        tr.append(stag('td', html_user(users[sub.user_id])))
        tr.append(stag('td', html_date(sub.date_submitted)))
        s = sub.submission_status.complete and "complete" or "incomplete"
        tr.append(stag('td', s))
        s = sub.submission_status.result
        tr.append(stag('td', s))
        span = Tag(name='span')
        names = sorted(sub.submission_status.step2job)

        for k in names:
            job_id = sub.submission_status.step2job[k]
            status = sub.submission_status.step2status.get(k, None)
            span.append(k + ': ')
            span.append(html_job_id(job_id, status))
            span.append(' ')

        # s = str(sub.submission_status.step2job)
        tr.append(stag('td', span))

        # tr.append(stag('td', str(sub.submission_status.next_steps)))
        #
        # tr.append(stag('td', html_date(sub.last_status_change)))
        # tr.append(stag('td', sub.user_image or "-"))
        tr.append(stag('td', sub.user_label or "-"))
        # tr.append(stag('td', sub.user_payload or '-'))

        table.append(tr)

    table.append(BeautifulSoup(extra_head, 'lxml'))
    return table


# language=html
extra_head = """
        <style>
           
        </style>
    """
