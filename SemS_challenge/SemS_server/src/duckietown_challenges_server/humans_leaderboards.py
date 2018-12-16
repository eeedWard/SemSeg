# -*- coding: utf-8 -*-
import json
import time

from bs4 import Tag, BeautifulSoup
from duckietown_challenges.challenge import Score
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config

from .database import db_connection
from .db_challenges import read_challenges
from .humans_html import html_user, html_submission, html_score
from .utils_xml import get_minimal_html, stag, catch_ui_render_problem


def challenge_id_from_name(cursor, cname):
    cmd = "select challenge_id from aido_challenges where queue_name = %s "
    cursor.execute(cmd, (cname,))
    if cursor.rowcount == 0:
        msg = 'Could not find challenge %r' % cname
        raise HTTPNotFound(msg)
    challenge_id, = cursor.fetchone()
    return challenge_id


#
#
# def return_text_response(text, request):
#     d = ImageDraw.Draw(img)
#     d.text((10, 10), "Hello World %s" % cname, fill=(255, 255, 0))
#     from PIL import Image
#     img = Image.new('RGB', (100, 30), color=(73, 109, 137))
#
#     s = StringIO.StringIO()
#     img.save(s, format='png')
#     data = s.getvalue()
#
#     mime = 'image/png'
#     return response_data(request=request, data=data, content_type=mime)


@view_config(route_name='humans_leaderboards_image')
def humans_leaderboards_image(request):
    cname = request.matchdict['cname']
    html = get_minimal_html()

    body = html.body
    with db_connection(request) as cursor:
        challenge_id = challenge_id_from_name(cursor, cname)
        challenges = read_challenges(cursor)
        uptodatejobs = {}
        challenge = challenges[challenge_id]
        from .rest_leaderboards_data import get_leaderboard3
        top10 = get_leaderboard3(cursor, challenge, challenges=challenges, uptodatejobs=uptodatejobs)

    table = format_leaderboard_2(challenge, top10, max_entries=15)
    body.append(table)

    style = Tag(name='style')
    # language=css
    style.append("""
    body { width: 20cm; }
    @page { size: 20cm 10cm }
    a { color: inherit; text-decoration: none}
    td:nth-child(3),
    td:nth-child(4) { display: none; }
    """)
    body.append(style)

    for e in body.select('.header'):
        e.extract()

    mime = 'image/png'
    # todo: cache it
    data = return_response_html_as_png(cname, request, html)
    return response_data(request=request, data=data, content_type=mime)


def return_response_html_as_png(cname, request, html):
    tmpf = '%s.html' % cname
    with open(tmpf, 'w') as f:
        f.write(str(html))

    pdf = '%s.pdf' % cname
    cmd = ['prince', '-o', pdf, tmpf]
    subprocess.check_call(cmd, stderr=sys.stderr, stdout=sys.stdout)
    png = '%s.png' % cname
    cmd = ['convert', '-density', '300', pdf + '[0]', '-resize', '640x', png]
    subprocess.check_call(cmd, stderr=sys.stderr, stdout=sys.stdout)
    with open(png) as f:
        data = f.read()
    return data


import sys, subprocess
from pyramid.response import FileResponse  # @UnresolvedImport


def response_data(request, data, content_type):
    import tempfile
    with tempfile.NamedTemporaryFile() as tf:
        fn = tf.name
        with open(fn, 'wb') as f:
            f.write(data)
        response = FileResponse(fn, request=request, content_type=content_type)

    return response


@view_config(route_name='humans_leaderboards_secret')
def humans_leaderboards_one_secret(request):
    # language=html
    extra_head = """
        <style>

            td {
                border: 1px;
                padding: 5px; 
            }

        </style>
    """

    cname = request.matchdict['cname']

    html = get_minimal_html()
    html.body.attrs['class'] = 'page-challenges'
    body = html.body
    head = html.head

    head.append(stag('base', '', href='../../..'))

    head.append(BeautifulSoup(extra_head, 'lxml'))
    section = Tag(name='section')
    body.append(section)

    with db_connection(request) as cursor:
        challenge_id = challenge_id_from_name(cursor, cname)
        challenges = read_challenges(cursor)
        uptodatejobs = {}
        challenge = challenges[challenge_id]

        from .rest_leaderboards_data import get_leaderboard3
        top10 = get_leaderboard3(cursor, challenge, challenges=challenges, uptodatejobs=uptodatejobs)

    pre = Tag(name='pre')
    code = Tag(name='code')

    # code.append(str(top10))
    s = ""
    for i, entry in enumerate(top10):
        submission = entry['submission']

        label = 'Copy of #%d: sub %s by %s (%s)' % (
            i + 1, submission.submission_id, entry['user_name'], submission.user_label)
        meta = json.dumps({'submission_id': submission.submission_id})
        s += "\n dts challenges submit --challenge %s --image %s --user-meta '%s' --user-label '%s'" % (
            cname, submission.user_image, meta, label)

    code.append(s)
    pre.append(code)
    section.append(pre)

    return Response(str(html))


@view_config(route_name='humans_leaderboards_one')
def humans_leaderboards_one(request):
    # language=html
    extra_head = """
        <style>

            td {
                border: 1px;
                padding: 5px; 
            }

        </style>
    """

    cname = request.matchdict['cname']

    html = get_minimal_html()
    html.body.attrs['class'] = 'page-challenges'
    body = html.body
    head = html.head

    head.append(stag('base', '', href='../../..'))

    head.append(BeautifulSoup(extra_head, 'lxml'))
    section = Tag(name='section')
    body.append(section)

    max_entries = 500

    with db_connection(request) as cursor:
        challenge_id = challenge_id_from_name(cursor, cname)
        challenges = read_challenges(cursor)
        uptodatejobs = {}
        challenge = challenges[challenge_id]

        from .rest_leaderboards_data import get_leaderboard3
        t0 = time.time()
        top10 = get_leaderboard3(cursor, challenge, challenges=challenges, uptodatejobs=uptodatejobs,
                                 max_entries=15, only_ranked=True)
        t1 = time.time()
        complete = get_leaderboard3(cursor, challenge, challenges=challenges, uptodatejobs=uptodatejobs,
                                    max_entries=max_entries, only_ranked=False)

        delta1 = time.time() - t0
        delta2 = time.time() - t1
        msg = 'Small: %d ms;  big: %d ms' % (delta1 * 1000, delta2 * 1000)
        cursor.debug(msg)

    h1 = Tag(name='h1')
    h1.append('Leaderboard for challenge "')
    h1.append(challenge.title)
    h1.append('"')
    section.append(h1)

    table = format_leaderboard_2(challenge, top10, only_ranked=True)
    section.append(table)

    section.append(stag('h2', 'Extended leaderboard'))
    section.append(
        stag('p', 'This list includes repeated entries from the same user and the entries from the organizers.'))

    table = format_leaderboard_2(challenge, complete, only_ranked=False)
    section.append(table)

    return Response(str(html))


@catch_ui_render_problem
def format_leaderboard_2(challenge, top10, only_ranked=True):
    if only_ranked:
        top10 = [_ for _ in top10 if 'rank' in _]
    if not top10:
        msg = 'No entries to display.'
        return stag('p', msg)

    table = Tag(name='table')

    th = Tag(name='tr')

    th.append(stag('td', 'Rank'))

    th.append(stag('td', 'User'))

    th.append(stag('td', 'Submission'))

    th.append(stag('td', 'User label'))

    # th.append(stag('td', 'Date'))

    keys = []
    for score in challenge.scoring.scores:
        keys.append(score.name)

        td = Tag(name='td')
        span = html_score(challenge, score)
        #
        # span = Tag(name='span')
        # if score.short:
        #     span.append(score.short)
        # else:
        #     span.append(stag('code', score.name))
        # span.append(Tag(name='br'))
        span.append(u"↑" if score.order == Score.HIGHER_IS_BETTER else u" ↓")

        td.append(span)
        th.append(td)

    table.append(stag('thead', th))

    for i, entry in enumerate(top10):

        user = entry['user']
        sub = entry['submission']
        scores = entry['scores']

        tr = Tag(name='tr')

        if 'rank' in entry:
            s = '%s' % entry['rank']
        else:
            from .rest_leaderboards_data import WHY_NOT_RANKED
            s = entry[WHY_NOT_RANKED]
        # rank = str(i + 1)
        tr.append(stag('td', s))
        tr.append(stag('td', html_user(user, link=False)))
        tr.append(stag('td', html_submission(sub)))

        td = Tag(name='td')
        if sub.user_label is not None:
            s = str(sub.user_label)
        else:
            s = ""

        td.append(s)
        tr.append(td)

        # td = Tag(name='td')
        # td.append(html_date(sub.date_submitted))
        # tr.append(td)

        for k in keys:
            td = Tag(name='td')
            if k in scores:
                if isinstance(scores[k], float):
                    ks = '%f' % scores[k]
                    if '.' in ks:
                        ks = ks.rstrip('0')
                else:
                    ks = '%s' % scores[k]
            else:
                ks = 'n/a'
            td.append(ks)
            tr.append(td)

        table.append(tr)
    return table


def format_leaderboard(submissions, users):
    table = Tag(name='table')
    keys = set()
    for sub in submissions:
        keys.update(sub['scores'])
    keys = sorted(keys)

    th = Tag(name='tr')

    td = Tag(name='td')
    td.append('User')
    th.append(td)

    td = Tag(name='td')
    td.append('Submission')
    th.append(td)

    for k in keys:
        td = Tag(name='td')
        td.append(k)
        th.append(td)

    td = Tag(name='td')
    td.append('date')
    th.append(td)

    table.append(th)

    for sub in submissions:
        tr = Tag(name='tr')

        tr.append(stag('td', html_user(users[sub.user_id])))

        td = Tag(name='td')
        td.append(str(sub['submission_id']))
        tr.append(td)

        for k in keys:
            td = Tag(name='td')
            if k in sub['scores']:
                ks = '%.3f' % sub['scores'][k]
            else:
                ks = 'n/a'
            td.append(ks)
            tr.append(td)

        td = Tag(name='td')
        td.append(str(sub['date_submitted']))
        tr.append(td)

        table.append(tr)
    return table
