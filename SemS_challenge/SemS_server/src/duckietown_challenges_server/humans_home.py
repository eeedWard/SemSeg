# coding=utf-8
import time
import traceback
from collections import OrderedDict, namedtuple

from bs4 import BeautifulSoup, Tag
from duckietown_challenges import __version__ as version_dtc
from pyramid.response import Response
from pyramid.view import view_config

from . import __version__ as version_dtcs, cslogger
from .constants import ChallengeServerConstants
from .database import db_connection
from .db_challenges import read_challenges
from .db_evaluators import read_evaluators, read_evaluation_features
from .db_users import read_users, make_rest_request1
from .humans_evaluators import format_evaluators
from .humans_html import html_challenge
from .humans_leaderboards import format_leaderboard_2
from .my_logging import get_logs
from .rest_leaderboards_data import get_leaderboard3
from .utils_xml import get_minimal_html, stag

version_info = 'DTC: %s DTCS: %s' % (version_dtc, version_dtcs)
# language=html
index0 = """<section>


<p>Welcome to the Duckietown Challenges server (v{version_info}).</p>

{other}

<style>
table#main td {{
vertical-align: top;
margin-right: 3em;
}}
</style>
<table id='main'>
<tr>
<td>

<td>
<h2>Active evaluators</h2>
<div id='here'></div>
</td>
</tr>
</section>

<style>
table.evaluator-table td:nth-child(14),
table.evaluator-table td:nth-child(15),
table.evaluator-table td:nth-child(16),
table.evaluator-table td:nth-child(17),
table.evaluator-table td:nth-child(18),
table.evaluator-table td:nth-child(19),
table.evaluator-table td:nth-child(20),
table.evaluator-table td:nth-child(21),
table.evaluator-table td:nth-child(22),
table.evaluator-table td:nth-child(23),
table.evaluator-table td:nth-child(24),
table.evaluator-table td:nth-child(25),
table.evaluator-table td:nth-child(26),
table.evaluator-table td:nth-child(27),
table.evaluator-table td:nth-child(28),
table.evaluator-table td:nth-child(29),
table.evaluator-table td:nth-child(30),
table.evaluator-table td:nth-child(31),
table.evaluator-table td:nth-child(32),
table.evaluator-table td:nth-child(33) {{
display: none;
}}
 
</style>

"""


@view_config(route_name='dashboard')
def dashboard(request):
    html = get_minimal_html(title='Dashboard')
    html.body.attrs['class'] = 'page-dashboard'
    html.head.append(stag('base', '', href='..'))

    s = ""
    if ChallengeServerConstants.insecure:
        s += '<p>Warning: this is an insecure server. Everybody is considered an admin.</p>'

    if not ChallengeServerConstants.s3:
        s += '<p>Warning: AWS login data not available; S3 upload disabled.</p>'

    index = index0.format(version_info=version_info, other=s)
    html.body.append(BeautifulSoup(index, 'lxml'))

    with db_connection(request) as cursor:
        evaluators = read_evaluators(cursor, start=0, limit=25)

        users = read_users(cursor)
        evaluation_features = read_evaluation_features(cursor)
        _num, logs_section = get_logs(cursor, category_id=1, start=0, limit=10)

    evaluators = OrderedDict((k, v) for (k, v) in evaluators.items()
                             if v.status == 'active')

    d = Tag(name='section')

    if not evaluators:
        d.append(stag('p', 'Warning: no evaluators active.'))
    else:
        d.append(stag('p', 'These are the currently active evaluators:'))
        d.append(format_evaluators(evaluators, users, evaluation_features))

    p = Tag(name='p')
    p.append('See more details ')
    a = stag('a', 'here', href='humans/evaluators')
    p.append(a)
    p.append('.')
    d.append(p)
    where = html.find(id='here')

    assert where is not None

    where.append(d)

    html.body.append(stag('h2', 'Recent logs'))
    html.body.append(logs_section)
    p = Tag(name='p')
    p.append('See the rest of the logs ')
    a = stag('a', 'here', href='humans/logs')
    p.append(a)
    p.append('.')
    html.body.append(p)
    return Response(str(html))


@view_config(route_name='home')
def home(request):
    html = get_minimal_html(title='Duckietown Challenges Server')
    html.body.attrs['class'] = 'page-home'
    # language=html
    contents = u"""

<table>
<tr>
<td>
<img id='aido-logo' src="https://www.duckietown.org/wp-content/uploads/2018/07/AIDO-768x512.png"/>
</td>
<td>
<p>Welcome to the NIPS 2018 AI Driving Olympics (AI-DO) challenges server.</p>

<p>You can find an introduction to AI-DO <a href="http://aido.duckietown.org">here</a>.</p>

<p> <a href="http://docs.duckietown.org/DT18/AIDO/out/">The reference manual</a> will get you started.</p>



</td>

</tr>

</table>
<p>AI-DO is brought to you by:</p>
<table >
<tr style="vertical-align: top">
<td>
<ul>
<li><a href="https://www.duckietown.org/">The Duckietown Foundation</a></li>
<li><a href="http://www.ethz.ch">ETH Zürich</a> | <a href="http://www.idsc.ethz.ch/">IDSC</a> | <a href="https://www.mavt.ethz.ch/">D-MAVT</a></li>
<li>University of Montréal | <a href="https://mila.quebec">MILA</a></li>
<li><a href="http://www.nctu.edu.tw/en">NCTU</a></li>
<li><a href="http://www.ttic.edu/">TTIC</a></li>
</ul>
</td>
<td>
<ul>
<li><a href="http://www.nutonomy.como">nuTonomy</a> | <a href="http://www.aptiv.com">Aptiv Mobility group</a></li>
<li><a href="http://aws.amazon.com/">Amazon Web Services</a></li>
</ul>
</td>
</tr></table>



<!--<p>This is a rather spartan experience.  For a more user-friendly experience, 
you can <a href='https://dashboard.duckietown.org'>sign up on the Duckietown Dashboard</a>.</p>-->
   
   
<style>
.challenge-leaderboard-box {
    border: solid 1px black;
    padding 1em;
    display: inline-block;
    min-height: 20em;
    margin: 1em
}

.challenge-title {
    text-align: center;
    color: darkred;
}

#leaderboard-title {
    
    
} 

#aido-logo {
    width: 20em;
}

</style> 
"""
    # html.head.append(stag('base', '', href='../..'))
    from duckietown_challenges_server.humans_challenges import get_markdown
    h = get_markdown(contents)

    html.body.append(h)

    html.body.append(get_posts_div())

    s = Tag(name='div')
    html.body.append(s)

    with db_connection(request) as cursor:

        challenges = read_challenges(cursor)
        uptodatejobs = {}
        leaderboards = get_leaderboards2(cursor, challenges=challenges, uptodatejobs=uptodatejobs)

    def write_boxes(dest, selection):
        for challenge in selection:
            sc = Tag(name='div')
            sc.attrs['class'] = 'challenge-leaderboard-box'
            h = Tag(name='h4')
            h.attrs['class'] = "challenge-title"
            h.append('Challenge ')
            h.append(html_challenge(challenge))

            sc.append(h)

            top10 = leaderboards[challenge.challenge_id]

            table = format_leaderboard_2(challenge, top10)

            sc.append(table)

            p = Tag(name='p')
            p.append('See also ')
            href = 'humans/challenges/%s/leaderboard' % challenge.queue_name
            p.append(stag('a', 'the extended leaderboard', href=href))
            p.append('.')
            sc.append(p)

            dest.append(sc)

    groups = get_challenges_groups(challenges)
    for g in groups:
        if g.challenges:
            if g.hide:
                details = Tag(name='details')
                summary = Tag(name='summary')
                summary.append(stag('span', g.title, _id='leaderboard-title'))

                details.append(stag('h3', g.title, _id='leaderboard-title'))
                details.append(get_markdown(g.description))

                details.append(summary)
                write_boxes(details, g.challenges)
                s.append(details)

            else:

                s.append(stag('h3', g.title, _id='leaderboard-title'))
                s.append(get_markdown(g.description))

                write_boxes(s, g.challenges)

    return Response(str(html))


ChallengeGroup = namedtuple('ChallengeGroup', 'title description challenges hide')

from .misc import timedb


class MyStorage(object):
    last = None
    last_timestamp = None


def get_leaderboards2(cursor, challenges, uptodatejobs):
    now = time.time()
    delta = 10000 if MyStorage.last_timestamp is None else now - MyStorage.last_timestamp
    if MyStorage.last is None or (delta > 60 * 30):
        cslogger.debug('fresh because delta %s' % delta)
        MyStorage.last = get_leaderboards_fresh2(cursor, challenges=challenges, uptodatejobs=uptodatejobs)
        MyStorage.last_timestamp = now

    else:
        cslogger.debug('using cached leaderboards')
    return MyStorage.last


ENTRIES_TO_DISPLAY_IN_HOME = 15


@timedb
def get_leaderboards_fresh2(cursor, challenges, uptodatejobs):
    res = OrderedDict()
    for challenge_id, challenge in challenges.items():
        res[challenge_id] = get_leaderboard3(cursor, challenge=challenge, challenges=challenges,
                                             uptodatejobs=uptodatejobs,
                                             max_entries=ENTRIES_TO_DISPLAY_IN_HOME,
                                             only_ranked=True)
        if len(res[challenge_id]) < ENTRIES_TO_DISPLAY_IN_HOME:
            res[challenge_id] = get_leaderboard3(cursor, challenge=challenge, challenges=challenges,
                                                 uptodatejobs=uptodatejobs,
                                                 max_entries=ENTRIES_TO_DISPLAY_IN_HOME,
                                                 only_ranked=False)

    return res


def get_challenges_groups(challenges):
    groups = []

    aido_embodied = []
    aido_amod = []
    aido_prev = []
    testing = []

    for challenge_id, challenge in challenges.items():

        if challenge.queue_name in ['aido1_LF1_r3-v3', 'aido1_LFV_r1-v3']:
            aido_embodied.append(challenge)

        elif challenge.queue_name in ['aido1_amod_efficiency_r1-v3', 'aido1_amod_fleet_size_r1-v3',
                                      'aido1_amod_service_quality_r1-v3']:
            aido_amod.append(challenge)

        elif 'aido1' in challenge.tags:
            aido_prev.append(challenge)

        elif 'testing' in challenge.tags:
            testing.append(challenge)

    used = set()
    desc = """

In these challenges, the participants must guide a Duckiebot 
through the streets of Duckietown. The only input available is a camera.

<table>
<tr>
<td>
<video autoplay="1" controls="1" loop="1" style="border: solid 1px black" width="240">
  <source src="http://duckietown-ai-driving-olympics-1.s3.amazonaws.com/v3/testing/by-value/sha256/202beaa343b33249c9f5c8541605dbbe8e1acf6302dc943ec67c69ffd81c2bcf" type="video/mp4"/>
</video>
<style>
.gh { font-family: monospace; font-size: 100%;}

</style>
</td>
<td style='vertical-align:top'>
<details>
<summary>Repositories</summary>
<table>
<tr>
<td><strong>Challenge definition</strong></td>
<td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1">challenge-aido1_LF1</a></td>
</tr>
<tr><td colspan=2><strong>Submission templates</strong></td>
<tr><td>Agent template</td><td>-</td><td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1-template-random">challenge-aido1_LF1-template-random</a></td></tr>
<tr><td>Pytorch template</td><td>PyTorch</td><td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1-template-pytorch">challenge-aido1_LF1-template-pytorch</a></td></tr>
<tr><td>Tensorflow template</td><td>Tensorflow</td><td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1-template-tensorflow">challenge-aido1_LF1-template-tensorflow</a></td></tr>
<tr><td>ROS template</td><td>ROS</td><td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1-template-ros">challenge-aido1_LF1-template-ros</a></td></tr>
<tr><td colspan=2><strong>Baseline solutions</strong></td>

<tr><td>Imitation learning from real logs</td><td>Tensorflow</td><td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1-baseline-IL-logs-tensorflow">challenge-aido1_LF1-baseline-IL-logs-tensorflow</a></td></tr>
<tr><td>Imitation learning from simulation</td><td>Tensorflow</td><td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1-baseline-IL-sim-tensorflow">challenge-aido1_LF1-baseline-IL-sim-tensorflow</a></td></tr>
<tr><td>Reinforcement learning from simulation</td><td>PyTorch</td><td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1-baseline-RL-sim-pytorch">challenge-aido1_LF1-baseline-RL-sim-pytorch</a></td></tr>
<tr><td>Traditional Duckietown pipeline</td><td>ROS</td><td><i class="fa fa-github"/> <a class="gh" href="https://github.com/duckietown/challenge-aido1_LF1-baseline-duckietown">challenge-aido1_LF1-baseline-duckietown</a></td></tr> 
</table>
</details>
</tr>
</table>



        """
    groups.append(ChallengeGroup("AI-DO 1 - Embodied tasks", desc, aido_embodied, hide=False))

    desc = """

In these challenges, the participant must coordinate a fleet of robo-taxis
in various cities environments.

<img style="width: 360px" src="http://duckietown-ai-driving-olympics-1.s3.amazonaws.com/v3/testing/by-value/sha256/77c4a04c4f3a52a2904471cf69752357db8005a51ae7383544798b90e75f1556"/>


    """
    groups.append(ChallengeGroup("AI-DO 1 - Autonomous mobility on demand", desc, aido_amod, hide=False))
    desc = """
    
These are previous versions of the AI-DO tasks.

    """

    groups.append(ChallengeGroup("Test challenges", "Test challenges", testing, hide=True))

    for g in groups:
        used.update(g.challenges)
    others = []

    for challenge in challenges.values():
        if not challenge in used:
            others.append(challenge)

    groups.append(ChallengeGroup("Others", "Other challenges", others, hide=True))

    groups.append(ChallengeGroup("AI-DO 1 - outdated versions of challenges ", desc, aido_prev, hide=True))
    return groups


def get_posts_div():
    div = Tag(name='div')
    MINUTES = 60
    posts = get_posts(refresh=20 * MINUTES)
    if posts:
        div.append(stag('h3', 'News and updates'))
        table = Tag(name='table')
        for post in posts:
            tr = Tag(name='tr')
            td = stag('td', post['date_gmt'][:10])
            tr.append(td)
            title = post['title']['rendered']
            link = post['link']
            td = stag('td', stag('a', title, href=link))
            tr.append(td)
            table.append(tr)
        div.append(table)
    return div


class Storage:
    data = None
    timestamp = None


def get_posts(refresh):
    """

    :param refresh: refresh time
    :return:
    """
    if Storage.timestamp is not None:
        delta = time.time() - Storage.timestamp
        if delta < refresh:
            to_update = False
        else:
            to_update = True
    else:
        delta = 0
        to_update = True

    if to_update:
        try:
            cslogger.debug('Getting fresh posts (delta = %s).' % delta)
            Storage.data = get_posts_fresh()
            # cslogger.debug('Read %d posts' % len(Storage.data))
            Storage.timestamp = time.time()
        except BaseException as e:
            cslogger.error(traceback.format_exc(e))
    else:
        cslogger.debug('Using cached posts  (delta = %s < %s)' % (delta, refresh))
    return Storage.data


def get_posts_fresh():
    base = ChallengeServerConstants.wordpress_rest
    if base is None:
        return None

    endpoint = 'posts?tags=5'
    url = base + endpoint
    token = ChallengeServerConstants.wordpress_token

    try:
        data = make_rest_request1(token, url, data=None, timeout=3)
        # cslogger.info(json.dumps(data, indent=4))
        return data
    except BaseException as e:
        return None
