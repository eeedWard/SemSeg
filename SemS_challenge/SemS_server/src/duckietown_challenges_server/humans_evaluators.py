# coding=utf-8

from bs4 import Tag
from pyramid.response import Response
from pyramid.view import view_config

from duckietown_challenges import ChallengesConstants
from .database import db_connection
from .db_evaluators import read_evaluators, EvaluatorInfo, read_evaluation_features
from .db_jobs import read_jobs
from .db_submissions import read_submissions2
from .db_users import read_users
from .humans_html import html_evaluator, html_date, html_user
from .utils_xml import stag, get_minimal_html, transpose_table


@view_config(route_name='humans_evaluators')
def humans_evaluators(request):
    html = get_minimal_html(title='Evaluators')
    html.head.append(stag('base', '', href='..'))
    html.body.attrs['class'] = 'page-evaluators'

    page = int(request.params.get("page", 0))
    limit = int(request.params.get("limit", 25))
    start = limit * page

    with db_connection(request) as cursor:
        evaluators = read_evaluators(cursor, limit=limit, start=start)

        users = read_users(cursor)
        features = read_evaluation_features(cursor)
        d = Tag(name='section')
        d.append(stag('h1', 'Evaluators'))
        p = Tag(name='p')
        p.append('These are the evaluator machines that made contact with this server.')
        d.append(p)
        table = format_evaluators(evaluators, users, features)
        d.append(table)
        html.body.append(d)

    return Response(str(html))


from . import cslogger


@view_config(route_name='humans_evaluators_one')
def humans_evaluators_one(request):
    evaluator_id = int(request.matchdict['evaluator_id'])

    html = get_minimal_html(title='Evaluator %s' % evaluator_id)
    html.body.attrs['class'] = 'page-evaluators'
    html.head.append(stag('base', '', href='../..'))
    body = html.body

    with db_connection(request) as cursor:
        evaluators = read_evaluators(cursor, evaluator_ids=[evaluator_id])
        challenges = {}
        uptodatejobs = {}
        cslogger.debug('Read %s evaluators' % len(evaluators))
        jobs = read_jobs(cursor, evaluator_id=evaluator_id, no_artifacts=True)
        cslogger.debug('Evaluator has %s jobs' % len(jobs))

        submission_ids = list(set([job.submission_id for job_id, job in jobs.items()]))

        cslogger.debug('Which correspond to %s submissions' % len(submission_ids))

        submissions = read_submissions2(cursor, submission_ids=submission_ids, uptodatejobs=uptodatejobs,
                                        challenges=challenges)

        cslogger.debug('Now read %s submissions' % len(submissions))

        evaluator = evaluators[evaluator_id]
        users = read_users(cursor)
        features = read_evaluation_features(cursor)

    body.append(stag('h1', 'Evaluator %s' % evaluator_id))
    d = Tag(name='section')
    table = format_evaluators({evaluator_id: evaluator}, users, features)
    table2 = transpose_table(table)
    d.append(table2)
    body.append(d)

    body.append(stag('h2', 'Evaluator jobs'))
    from duckietown_challenges_server.humans_jobs import format_jobs
    body.append(format_jobs(jobs, challenges, submissions, evaluators))

    return Response(str(html))


def format_evaluators(evaluators, users, evaluation_features):
    if not evaluators:
        msg = 'No evaluators present.'
        return stag('p', msg)
    table = Tag(name='table')
    table.attrs['class'] = 'evaluator-table'
    thead = Tag(name='thead')
    tr = Tag(name='tr')
    tr.attrs['class'] = 'head'
    # tr.append(stag('td', 'npings'))

    # tr.append(stag('td', 'ID'))
    tr.append(stag('td', 'evaluator'))
    tr.append(stag('td', 'owner'))
    tr.append(stag('td', 'machine'))
    tr.append(stag('td', 'process'))
    tr.append(stag('td', 'version'))
    tr.append(stag('td', 'first heard'))
    tr.append(stag('td', 'last heard'))
    # tr.append(stag('td', 'seconds'))
    tr.append(stag('td', 'status'))

    ei = evaluators[list(evaluators)[0]]

    ks = list(ChallengesConstants.ALLOWED_JOB_STATUS)
    for k in ks:
        x = stag('span', '# %s' % k, _class='rotate')
        tr.append(stag('td', x, _class='rotate_parent'))

    evaluation_features_items = list(evaluation_features.items())
    for evaluation_feature_id, ef in evaluation_features_items:
        if ef.children: continue
        st = stag('td', stag('span', ef.short, _class='rotate'), _class='rotate_parent')
        tr.append(st)

    thead.append(tr)
    table.append(thead)
    for eid, ei in evaluators.items():
        assert isinstance(ei, EvaluatorInfo)
        tr = Tag(name='tr')

        # tr.append(stag('td', str(ei.evaluator_id)))
        tr.append(stag('td', html_evaluator(ei), _class='evaluator'))
        tr.append(stag('td', html_user(users[ei.uid])))
        tr.append(stag('td', ei.machine_id))
        tr.append(stag('td', ei.process_id))
        tr.append(stag('td', ei.evaluator_version))
        tr.append(stag('td', html_date(ei.first_heard)))

        tr.append(stag('td', html_date(ei.last_heard)))
        # tr.append(stag('td', ' %d s' % ei.last_heard_secs))

        tr.append(stag('td', ei.status))
        tr.attrs['class'] = ei.status

        for k in ks:
            num = ei.status2njobs[k]
            if num:
                s = str(num)
            else:
                s = ''
            tr.append(stag('td', s))

        for evaluation_feature_id, ef in evaluation_features_items:
            if ef.children: continue
            if evaluation_feature_id in ei.features:
                value = ei.features[evaluation_feature_id]
            else:
                value = ''

            tr.append(stag('td', str(value)))

        table.append(tr)

    style = Tag(name='style')
    # language=css
    style.append("""
    
td.evaluator { text-align: left; }
table.evaluator-table td {
    
    margin: 2px;
    text-align: center;
}
table.evaluator-table tbody tr:nth-child(2n) {
    background-color: #eef;
}
table.evaluator-table tbody tr:nth-child(2n+1) {
    background-color: #efe;
}
table.evaluator-table thead td {

    font-size: smaller;
    font-weight: bold;
    vertical-align: bottom; 
}
table.evaluator-table thead .rotate_parent {
    /* height: 10em; */
    vertical-align: bottom;
    padding-bottom: 5px;
    text-align: left; 
}
table.evaluator-table .rotate { 
    transform: rotate(-90deg);
    white-space: pre;
    display: block;
    width: 1.5em;
}
    
    """)
    table.append(style)
    return table
