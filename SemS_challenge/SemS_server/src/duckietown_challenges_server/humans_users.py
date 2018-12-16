# coding=utf-8

from bs4 import Tag
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config

from .database import db_connection
from .db_challenges import read_challenges
from .db_evaluators import read_evaluators, read_evaluation_features
from .db_submissions import read_submissions2
from .db_users import read_users, User, read_user
from .humans_evaluators import format_evaluators
from .humans_html import html_user
from .humans_submissions import format_submissions
from .utils_xml import stag, get_minimal_html


@view_config(route_name='humans_users')
def human_users(request):
    html = get_minimal_html(title='Users')
    html.body.attrs['class'] = 'page-users'
    html.head.append(stag('base', '', href='..'))

    with db_connection(request) as cursor:
        users = read_users(cursor)
        d = Tag(name='section')
        d.append(stag('h1', 'Users'))
        p = Tag(name='p')
        p.append('These are the users that submitted to this server.')
        d.append(p)
        table = format_users(users)
        d.append(table)
        html.body.append(d)

    return Response(str(html))


@view_config(route_name='humans_users_one')
def human_users_one(request):
    user_id = int(request.matchdict['user_id'])

    html = get_minimal_html(title='User %s' % user_id)
    html.body.attrs['class'] = 'page-users'
    html.head.append(stag('base', '', href='../..'))
    body = html.body

    with db_connection(request) as cursor:
        challenges = read_challenges(cursor)
        uptodatejobs = {}

        try:
            user = read_user(cursor, user_id)
        except:

            msg = 'No user with ID %s found' % user_id
            msg += '\nTry in a while.'
            raise HTTPNotFound(msg)

        body.append(stag('h1', 'User %s' % user_id))
        d = Tag(name='section')
        users = {user_id: user}
        d.append(format_users(users))
        body.append(d)

        his_submissions = read_submissions2(cursor, challenges=challenges, uptodatejobs=uptodatejobs, user_id=user_id)
        evaluation_features = read_evaluation_features(cursor)
        evaluators_his = read_evaluators(cursor, user_id=user_id)

        body.append(stag('h2', 'Submissions'))
        body.append(format_submissions(his_submissions, challenges, users))

        body.append(stag('h2', 'Evaluators'))
        body.append(format_evaluators(evaluators_his, users, evaluation_features))

    return Response(str(html))


def format_users(users):
    if not users:
        msg = 'No users to display.'
        return stag('p', msg)

    table = Tag(name='table')
    thead = Tag(name='thead')
    tr = Tag(name='tr')
    tr.append(stag('td', 'ID'))
    tr.append(stag('td', 'name'))
    tr.append(stag('td', 'profile'))
    thead.append(tr)
    table.append(thead)

    for uid, user in users.items():
        assert isinstance(user, User)
        tr = Tag(name='tr')
        tr.append(stag('td', str(user.user_id)))
        # tr.append(stag('td', user.display_name))
        tr.append(stag('td', html_user(user)))
        a = stag('a', 'profile', href=user.user_url)
        tr.append(stag('td', a))
        table.append(tr)

    return table
