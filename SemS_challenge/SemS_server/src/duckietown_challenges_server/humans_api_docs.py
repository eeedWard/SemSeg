# coding=utf-8
from bs4 import BeautifulSoup
from pyramid.response import Response
from pyramid.view import view_config

from .utils_xml import get_minimal_html, stag


# noinspection PyUnusedLocal
@view_config(route_name='docs')
def req_docs(request):
    html = get_minimal_html(title='Docs')
    html.body.attrs['class'] = 'page-docs'
    html.head.append(stag('base', '', href='..'))
    content = """
    
# Documentation
    
    

## Database visualization

<p>Visualization for humans:</p>
<ul>
    <li><a href='humans/challenges'>Challenges</a></li>
    <li><a href='humans/submissions'>Submissions</a></li>
    <li><a href='humans/evaluators'>Evaluators</a></li>
    <li>Regarding jobs:
    <ul>
    <li><a href='humans/queue'>Job queue </a></li>
    <li><a href='humans/jobs'>Jobs running and finished</a></li>
    </ul>
    </li>
    <li><a href='humans/users'>Users</a></li>
</ul>

## For developers

See the <a href='humans/api-docs'>REST API Docs</a>.

    
    
    
    """

    from duckietown_challenges_server.humans_challenges import get_markdown
    html.body.append(get_markdown(content))

    return Response(str(html))


@view_config(route_name='api-docs')
def api_docs(request):
    html = get_minimal_html(title='API Docs')

    html.head.append(stag('base', '', href='..'))
    html.body.append(BeautifulSoup(index, 'lxml'))


    return Response(str(html))


# language=html
index = """<section>
    <style>
       
    </style>

<h1>Duckietown Challenges REST API, version 1</h1>

<h2>Public endpoints</h2>

For these endpoints, no authorization is necessary.

<h3>List the challenges</h3>

<a href="challenges"><code>/challenges</code></a>

<p>Sample response:</p>

<pre><code>
{
    "challenges": [
        {
            "challenge_id": 1, 
            "challenge_name": "aido1_luck", 
            "description": "A test of luck."
        }
    ], 
    "ok": true
}
</code></pre>

<h3>List the submission for each challenge</h3>

<a href="subs-by-challenge/1"><code>/subs-by-challenge/{challenge_id}</code></a>


<p>Sample response:</p>

<pre><code>
{
    "submissions": [
        {
            "status": "success", 
            "submission_id": 1, 
            "date_submitted": "2018-08-25T19:02:39", 
            "user_id": 7, 
            "last_status_change": "2018-08-25T20:18:31"
        }, 
        {
            "status": "evaluating", 
            "submission_id": 2, 
            "date_submitted": "2018-08-25T20:16:09", 
            "user_id": 7, 
            "last_status_change": "2018-08-25T21:11:12"
        }, 
        {
            "status": "retired", 
            "submission_id": 3, 
            "date_submitted": "2018-08-25T20:41:14", 
            "user_id": 3, 
            "last_status_change": "2018-08-25T20:41:14"
        }, 
    ], 
    "ok": true
}
</code></pre>

<p>Each submission has a <code>status</code>, which can be one of:</p>

<ul>
    <li><code>submitted</code>: just created</li>
    <li><code>success</code>: evaluated with success</li>
    <li><code>failed</code>: evaluated with failure</li>
    <li><code>evaluating</code>: in the process of being evaluated</li>
    <li><code>retired</code>: retired by the user</li>
    <li><code>aborted</code>: aborted by the admins</li>
</ul>

 <p>Other attributes:</p>
 <ul>
 <li><code>submission_id</code>: unique name (int)</li>
 <li><code>user_id</code>: submitter id</li>
 <li><code>date_submitte</code>: datetime in which it was created </li>
 <li><code>last_status_change</code>: datetime for last status change</li>
</ul>

<h3>List the evaluation jobs for each submission</h3>

<a href="jobs-by-submission/1"><code>/jobs-by-submission/{submission_id}</code></a>

<p>Sample response:</p>
<pre><code>
{
    "jobs": [ 
        {
            "job_id": 10, 
            "status": "success", 
            "date_started": "2018-08-25T20:18:26"
            "date_completed": "2018-08-25T20:18:30", 
            "executor_id": 7, 
            "stats": { 
                "resources": {
                    "wall": 0.02040410041809082, 
                    "clock": 0.004125999999999991
                }, 
                "scores": {
                    "score1": 52.978883685576136
                }
            }, 
        }
    ], 
    "ok": true
}

</code></pre>


<p>Other attributes:</p>
 <ul>
 <li><code>job_id</code>: unique identifier for the job</li>
 <li><code>status</code>: <code>evaluating</code> or <code>success</code></li>
 <li><code>executor_id</code>: the user id that is evaluating the submission</li>
 <li><code>date_started</code>: datetime at which the job started</li>
 <li><code>date_completed</code>: datetime in which the job was completed (or null) </li>
 <li><code>stats</code>: statistics, as below </li>
</ul>

<p>The statistics reported (in evolution):</p>

<ul>
<li><code>stats['resources']['wall']</code>: elapsed wall time</li>
<li><code>stats['resources']['clock']</code>: elapsed clock time</li>
<li><code>stats['scores']</code>: dictionary str->float of various scores (challenge specific)</li>
</ul>


<h2>Personal submissions endpoints</h2>

<p>These endpoints are used by the Duckietown Shell to submit submissions.</p>

<p>It is required that <a href="#authorization">authorization</a>
 is in place with the Duckietown Token.</p>

<p>In brief:</p>

<ul>
<li><code>/info</code>: describes authenticated user info</li>
<li><code>/submissions</code> - GET: lists submissions for the authenticated user</li>
<li><code>/submissions</code> - POST: adds a submission</li>
<li><code>/submissions</code> - DELETE: retires a submission</li>

</ul>


<h2>Executor endpoints</h2>

<p>These endpoints are used by the <a href="http://github.com/duckietown/challenges-executor">challenges executor</a> to take jobs and evaluate submissions.</p>

<p>It is required that <a href="#authorization">authorization</a>
 is in place with the Duckietown Token.</p>


<ul>
<li><code>/take-submission</code> - GET: gets a submission to execute</li>
<li><code>/take-submission</code> - POST: reports the results of a submission</li>
</ul>

<h2 id="authorization">Authorization</h2>

<p>Users are authorized using the Duckietown Token.</p>

<p>The token must be passed to each request using the header "<code>X-Messaging-Token</code>".</p>


<h3>Code example</h3>

<p>Here's a Python code example for  the <code>/info</code> endpoint.</p>
<pre><code>
import urllib2, json

token = "XXX your token here"
url = "https://challenges.duckietown.org/v1/info"
headers = {'X-Messaging-Token': token}
req = urllib2.Request(url, headers=headers)
res = urllib2.urlopen(req)
data = res.read()
result = json.loads(data)
print result
</code></pre>

</section>"""
