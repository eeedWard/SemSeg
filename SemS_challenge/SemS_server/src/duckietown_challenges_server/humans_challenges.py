# coding=utf-8
from collections import OrderedDict

from bs4 import BeautifulSoup, Tag
from pyramid.response import Response
from pyramid.view import view_config

from duckietown_challenges.utils import safe_yaml_dump
from .db_evaluators import read_evaluation_features
from .humans_home import get_challenges_groups
from .my_logging import bs
from .database import db_connection
from .db_challenges import read_challenges, Challenge, EvaluationStep
from .db_submissions import read_submissions2
from .db_users import read_users
from .humans_html import html_challenge_title, html_challenge_code, html_date_md, html_score
from .humans_submissions import format_submissions
from .utils_xml import stag, get_minimal_html, catch_ui_render_problem


@view_config(route_name='humans_challenges')
def humans_challenges(request):
    html = get_minimal_html(title='Challenges')
    body = html.body
    body.attrs['class'] = 'page-challenges'
    index = """
    """
    body.append(BeautifulSoup(index, 'lxml'))

    html.head.append(stag('base', '', href='..'))

    with db_connection(request) as cursor:
        challenges = read_challenges(cursor)
        body.append(stag('h1', "List of challenges"))
        body.append(format_list_of_challenges(challenges))

    return Response(str(html))


@view_config(route_name='humans_challenges_one')
def humans_challenges_one(request):
    challenge_name = request.matchdict['cname']

    with db_connection(request) as cursor:
        from .humans_leaderboards import challenge_id_from_name
        challenge_id = challenge_id_from_name(cursor, challenge_name)
        uptodatejobs = {}
        challenges = read_challenges(cursor)
        challenge = challenges[challenge_id]

        submissions = read_submissions2(cursor, challenges=challenges, uptodatejobs=uptodatejobs)
        submissions_his = OrderedDict([(k, v) for (k, v) in submissions.items() if v.challenge_id == challenge_id])
        users = read_users(cursor)
        evaluation_features = read_evaluation_features(cursor)

        html = get_minimal_html(title='Challenge "%s"' % challenge.title)
        html.head.append(stag('base', '', href='../..'))
        body = html.body

        body.append(stag('h1', 'Challenge "%s"' % challenge.title))

        d = Tag(name='section')

        d.append(stag('h2', 'Challenge description'))

        style = Tag(name='style')
        style.append("""

dd {

}
:target {
    background-color: yellow;  
} 
.container {
    max-width: 30em;

}       
        """)
        body.append(style)
        div = Tag(name='div')
        div.attrs['class'] = 'challenge-description'
        md = get_markdown(challenge.description or "(No description.)")
        div.append(md)
        d.append(div)

        d.append(stag('h2', 'Scoring', _id='scoring'))
        scoring = challenge.scoring

        if not scoring.scores:
            d.append(stag('p', 'No scores defined'))
        else:
            d.append(stag('p', 'These are the metrics defined:'))
            dl = Tag(name='dl')
            for score in scoring.scores:
                s = Tag(name='div')
                s.attrs['class'] ='container'
                s.attrs['id'] = score.name
                dt = Tag(name='dt')

                dt.attrs['style'] = 'font-weight: bold'
                # if score.short:
                #     dt.append(score.short)
                #     dt.append(' (')
                #     dt.append(stag('code', score.name))
                #     dt.append(')')
                # else:
                #     dt = stag('dt', stag('code', score.name))
                dt.append(html_score(challenge, score, link=False))

                dd = stag('dd', stag('p', get_markdown(score.description or "-")))
                s.append(dt)
                s.append(dd)
                dl.append(s)
            d.append(dl)

        d.append(stag('h2', 'Challenge logistics'))

        ul = Tag(name='ul')

        a_leader = stag('a', "Leaderboard", href='humans/challenges/%s/leaderboard' % challenge.queue_name)

        li = Tag(name='li')
        li.append(a_leader)
        ul.append(li)

        li = Tag(name='li')
        li.append('Opens: ')
        li.append(html_date_md(challenge.date_open))
        ul.append(li)
        li = Tag(name='li')
        li.append('Closes: ')
        li.append(html_date_md(challenge.date_close))
        ul.append(li)

        d.append(ul)

        assert isinstance(challenge, Challenge)
        # challenges0 = {challenge_id: challenge}
        # table = format_list_of_challenges(challenges0)
        #
        # d.append(transpose_table(table))

        #
        # d.append(stag('p', challenge.description))

        d.append(stag('h2', 'Evaluation steps details', _id='steps'))

        ul = Tag(name='ul')
        for md_step in challenge.transitions.steps_explanation():
            ul.append(stag('li', get_markdown(md_step)))
        d.append(ul)

        # order by creation id
        for step_id in sorted(challenge.steps):
            step = challenge.steps[step_id]
            assert isinstance(step, EvaluationStep)

            h3 = stag('h3', 'Evaluation step ', _id=step.step_name)
            h3.append(stag('code', step.step_name))

            d.append(h3)

            if step.step_description:
                md = get_markdown(step.step_description)
                d.append(stag('div', md))
            # md.dissolve()

            d.append(stag('p', 'This is the Docker Compose configuration skeleton:'))

            d.append(stag('blockquote', stag('pre', stag('code', safe_yaml_dump(step.evaluation_parameters)))))

            d.append(
                stag('p', get_markdown('The text `SUBMISSION_CONTAINER` will be replaced with the user containter.')))

            # d.append(stag('pre', str(features)))

            d.append(stag('h4', 'Resources required for evaluating this step'))
            if not step.features_required_by_id:
                d.append(stag('p', 'No particular resources required.'))
            else:
                table = Tag(name='table')

                for feature_id, amount in step.features_required_by_id.items():
                    tr = Tag(name='tr')
                    feature = evaluation_features[feature_id]

                    tr.append(stag('td', feature.short or "?"))
                    tr.append(stag('td', str(amount)))
                    table.append(tr)

                d.append(table)

        # d.append(stag('pre', stag('code', challenge.transitions.__repr__())))

        d.append(stag('h2', 'Submissions received'))

        table = format_submissions(submissions_his, challenges, users)
        d.append(table)

    body.append(d)

    return Response(str(html))


def get_markdown(md):
    import markdown

    extensions = ['extra', 'smarty']
    html = markdown.markdown(md, extensions=extensions, output_format='html5')

    res = bs(html)
    return res


@catch_ui_render_problem
def format_list_of_challenges(challenges):
    if not challenges:
        msg = 'No challenges.'
        return stag('p', msg)

    table = Tag(name='table')

    th = Tag(name='tr')

    th.append(stag('td', 'Challenge'))

    th.append(stag('td', 'Leaderboard'))
    th.append(stag('td', 'From'))
    th.append(stag('td', 'To'))
    th.append(stag('td', 'Open'))
    th.append(stag('td', 'Days to go'))
    th.append(stag('td', 'Protocol'))
    th.append(stag('td', 'Code'))
    th.append(stag('td', 'Tags'))
    # th.append(stag('td', 'Description'))

    table.append(stag('thead', th))

    groups = get_challenges_groups(challenges)

    for group in groups:
        if not group.challenges:
            continue
        tr = Tag(name='tr')
        td = Tag(name='td')
        td.attrs['style'] = 'color: darkred; padding-top: 1em;'
        td.append(group.title)
        tr.append(td)
        table.append(td)

        for challenge in group.challenges:
            tr = Tag(name='tr')
            tr.append(stag('td', html_challenge_title(challenge)))

            #
            # h.append('- %s' % challenge.title)
            # d.append(h)
            # d.append(stag('p', challenge.description))
            a = stag('a', "Leaderboard", href='humans/challenges/%s/leaderboard' % challenge.queue_name)
            tr.append(stag('td', a))
            tr.append(stag('td', html_date_md(challenge.date_open)))

            tr.append(stag('td', html_date_md(challenge.date_close)))
            tr.append(stag('td', "yes" if challenge.is_open else "no"))
            tr.append(stag('td', str(challenge.days_remaining) if challenge.is_open else ""))
            # tr.append(stag('td', challenge.description))
            tr.append(stag('td', stag('code', challenge.protocol)))
            tr.append(stag('td', html_challenge_code(challenge)))
            tr.append(stag('td', u", ".join(sorted(challenge.tags, key=lambda x: x.lower()))))
            table.append(tr)
    return table
