# coding=utf-8
from bs4 import Tag
from pyramid.response import Response
from pyramid.view import view_config

from .my_logging import get_logs
from .database import db_connection
from .utils_xml import get_minimal_html, stag


@view_config(route_name='humans_logs')
def humans_logs(request):
    html = get_minimal_html(title='Logs')
    html.body.attrs['class'] = 'page-logs'
    html.head.append(stag('base', '', href='..'))
    body = html.body
    page = int(request.params.get("page", 0))
    limit = int(request.params.get("limit", 100))
    start = limit * page
    category_id = request.params.get('category_id', 1)
    # cslogger.info('category id %s' % category_id)
    with db_connection(request) as cursor:
        num, logs_section = get_logs(cursor, start=start, limit=limit, category_id=category_id)

        body.append(stag('h2', 'Logs'))

        p1, p2 = get_page_navigation('humans/logs', page, limit, num)

        body.append(p1)

        body.append(logs_section)

        body.append(p2)

    return Response(str(html))


def get_page_navigation(base_url, page, limit, num):
    p1 = Tag(name='p')
    if page > 0:
        a = Tag(name='a')
        a.attrs['href'] = '%s?page=%s&limit=%s' % (base_url, page - 1, limit)
        a.append('page %d' % (page - 1 + 1))
        p1.append(a)
    else:
        p1.append(' ')

    p2 = Tag(name='p')

    if num == limit:
        a = Tag(name='a')
        a.attrs['href'] = '%s?page=%s&limit=%s' % (base_url, page + 1, limit)
        a.append('page %d' % (page + 1 + 1))
        p2.append(a)
    else:
        p2.append(' ')
    return p1, p2

