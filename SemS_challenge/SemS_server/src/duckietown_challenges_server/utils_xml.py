# coding=utf-8
import traceback

import decorator
from bs4 import Tag, NavigableString, BeautifulSoup


def stag(name, text, _class=None, _id=None, href=None):
    """ If text is none, it is replaced by the empty string. """
    if text is None:
        text = ''
    t = Tag(name=name)
    if isinstance(text, Tag):
        t.append(text)
    else:
        t.append(NavigableString(text))
    if _class is not None:
        t['class'] = _class
    if _id is not None:
        t['id'] = _id

    if href is not None:
        t['href'] = href
    return t


def get_minimal_html(title=None):
    html = Tag(name='html')
    head = Tag(name='head')
    body = Tag(name='body')
    html.append(head)
    html.append(body)

    if title:
        head.append(stag('title', title))

    bs = BeautifulSoup(extra_head, 'lxml')
    for x in bs.contents:
        head.append(x.__copy__())

    bs = BeautifulSoup(header, 'lxml')
    for x in bs.contents:
        body.append(x.__copy__())

    return html


def transpose_table(table):
    rows = []

    trs = [_ for _ in table.select('tr') if _.parent == table or (_.parent.name == 'thead')]
    for tr in trs:
        row = []
        for td in [_ for _ in tr.select('td') if _.parent == tr]:
            row.append(td)
        rows.append(row)

    if not rows:
        table2 = Tag(name='table')
        return table2

    nrows = len(rows)
    ncols = len(rows[0])
    table2 = Tag(name='table')
    for i in range(ncols):
        tr2 = Tag(name='tr')
        for j in range(nrows):
            if len(rows[j]) > i:
                cell = rows[j][i]
            else:
                cell = Tag(name='td')
            tr2.append(cell)

        table2.append(tr2)
    return table2


# language=html
extra_head = """
<script src="https://code.jquery.com/jquery-3.3.1.min.js"></script>

    <link rel="stylesheet" type="text/css" href="https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css"/>
    <script>
        /**
       * timesince is a live-updating implementation of Django's timesince filter
       * in jQuery.
       *
       * This will automatically keep the timestamps updated as the page
       * is opened, instead of showing the time as it was when the page was rendered.
       * This is a better user experience, and also helps with caching (both
       * browser and server-side).
       *
       * This is based both on Django's timesince filter
       * (http://www.djangoproject.com/), and parts of Ryan McGeary's timeago
       * jQuery plugin (http://timeago.yarp.com/).
       *
       * See https://github.com/chipx86/jquery-timesince for the latest.
       *
       * @name timesince
       * @version 0.2
       * @requires jQuery v1.2.3+
       * @author Christian Hammond
       * @license MIT License - http://www.opensource.org/licenses/mit-license.php
       *
       * Copyright (c) 2012, Christian Hammond (chipx86@chipx86.com)
       * Copyright (c) 2013, Beanbag, Inc.
       */
      (function(factory) {
          if (typeof define === 'function' && define.amd) {
              // AMD. Register as anonymous module.
              define(['jquery'], factory);
          } else {
              // Browser globals.
              factory(jQuery);
          }
      }(function($) {
          $.timesince = function(timestamp) {
              if (timestamp instanceof Date) {
                  return timeSince(timestamp);
              } else if (typeof timestamp === 'string') {
                  return timeSince($.timesince.parse(timestamp));
              } else if (typeof timestamp === 'number') {
                  return timeSince(new Date(timestamp));
              } else {
                  // It's an element.
                  return timeSince($.timesince.datetime($(timestamp)));
              }
          };

          $.extend($.timesince, {
              options: {
                refreshMs: 5000, // 1 minute
                strings: {
                    prefixAgo: null,
                    prefixFromNow: null,
                    suffixAgo: "",
                    suffixFromNow: "",
                    minute: "m",
                    minutes: "m",
                    second: "s",
                    seconds: "s",
                    hour: "h",
                    hours: "h",
                    day: "day",
                    days: "days",
                    week: "week",
                    weeks: "weeks",
                    month: "month",
                    months: "months",
                    year: "year",
                    years: "years"
                }
            },
            chunks: [
                [60 * 60 * 24 * 365, "year", "years"],
                [60 * 60 * 24 * 30, "month", "months"],
                [60 * 60 * 24 * 7, "week", "weeks"],
                [60 * 60 * 24, "day", "days"],
                [60 * 60, "hour", "hours"],
                [60, "minute", "minutes"],
                [1, "second", "seconds"],
            ],

              timeSince: function(deltaMs) {
                  var strings = this.options.strings,
                      seconds = Math.abs(deltaMs) / 1000,
                      prefix,
                      suffix,
                      i;

                  if (deltaMs < 0) {
                      prefix = strings.prefixFromNow;
                      suffix = strings.suffixFromNow;
                  } else {
                      prefix = strings.prefixAgo;
                      suffix = strings.suffixAgo;
                  }

                  prefix = (prefix ? prefix + " " : "");
                  suffix = (suffix ? " " + suffix : "");

                  if (seconds < 60) {
                      return prefix + "0 " + strings.minutes + suffix;
                  }

                  for (i = 0; i < this.chunks.length; i++) {
                      var chunk = this.chunks[i],
                          chunkSecs = chunk[0],
                          count = Math.floor(seconds / chunkSecs);

                      if (count != 0) {
                          var s = prefix + this.getChunkText(chunk, count);

                          if (i + 1 < this.chunks.length) {
                              // Get the second item.
                              var chunk2 = this.chunks[i + 1],
                                  count2 = Math.floor(
                                      (seconds - (chunkSecs * count)) / chunk2[0]);

                              if (count2 != 0) {
                                  s += ", " + this.getChunkText(chunk2, count2);
                              }
                          }

                          return s + suffix;
                      }
                  }

                  // We shouldn't have reached here.
                  return ''
              },
              getChunkText: function(chunk, n) {
                  var type = (n === 1 ? chunk[1] : chunk[2]);

                  return n + " " + this.options.strings[type];
              },
              parse: function(iso8601) {
                  var s = $.trim(iso8601);
                  s = s.replace(/\.\d\d\d+/,""); // remove milliseconds
                  s = s.replace(/-/,"/").replace(/-/,"/");
                  s = s.replace(/T/," ").replace(/Z/," UTC");
                  s = s.replace(/([\+\-]\d\d)\:?(\d\d)/," $1$2"); // -04:00 -> -0400
                  return new Date(s);
              },
              datetime: function(el) {
                  var iso8601 = this.isTime(el)
                                ? el.attr("datetime")
                                : el.attr("title");
                  return this.parse(iso8601);
              },
              isTime: function(el) {
                  // jQuery's `is()` doesn't play well with HTML5 in IE
                  return el[0].tagName.toLowerCase() === "time";
              }
          });

          $.fn.timesince = function(options) {
              var self = this,
                  timerCnx,
                  refreshMs;

              options = $.extend(options, $.timesince.options);
              refreshMs = options.refreshMs;

              if (refreshMs > 0) {
                  timerCnx = setInterval(function() {
                      self.each(function() {
                          refresh($(this), timerCnx);
                      });
                  }, refreshMs);
              }

              return this.each(function() {
                  var el = $(this),
                      text = $.trim(el.text());

                  el.data('timesince', {
                      datetime: $.timesince.datetime(el)
                  });

                  if (text.length > 0 && (!$.timesince.isTime(el) ||
                                          !el.attr("title"))) {
                      el.attr("title", text);
                  }

                  refresh(el);
              });
          };

          function refresh(el, timerCnx) {
              var data = el.data('timesince');

              if (data) {
                  el.text($.timesince.timeSince(
                      new Date().getTime() - data.datetime.getTime()));
              } else {
                  clearInterval(timerCnx);
              }

              return el;
          }

          // IE6 doesn't understand the <time> tag, so create it.
          document.createElement("time");
      }));</script>

      <script>
      $(document).ready(function() {
          $("time.timesince").timesince();
          $("span.timesince").timesince();
      });
      </script>
      
      <style>
        
        body {
        margin-left: 3em;
        font-size: 16px;
        font-family: Tahoma, sans;
        /* background-color: #ffd54b;*/
        }
        
        h1{margin: 1em; margin-left: 0em;}
        h2{margin-top: 1em; color: darkred;}
      
        table thead { 
            font-weight: bold;
            font-size: smaller;
        }
        table td {
         padding: 3px;
        }
        
        table.logs td {
        vertical-align: top; 
        /*border: solid 1px black*/
        padding: 2px;
        }
        table.logs td.log_level {
          font-size: smaller; 
            padding-right: 1em;
        }
        table.logs td.timestamp {
          font-size: smaller; 
          padding-right: 1em;
        }
        
        table.logs tr:nth-child(2n) {
            background-color: #f8f5e6;
        }
        table.logs tr:nth-child(2n+1) {
            /* background-color: #fcf9c0;*/
        }
        
        table.logs details:not([open]) {
        display: inline;
        margin-left: 1em;
        }
        
            tr.evaluating {
                
            }
            tr.evaluating td.status {
                font-weight: bold;
                color:blue;
            }
            
            
            
            tr.error {
                background-color: #fee;
            }
            tr.error td.status {
                font-weight: bold;
                color: purple;
            }
            
            tr.failed {
                background-color: #fee;
            }
            tr.failed td.status {
                font-weight: bold;
                color: red;
            }
            
            tr.success {
                background-color: #efe;
            }
            tr.success td.status {
                font-weight: bold;
                color: green;
            }

            tr.timeout {
                background-color: #ddd;
            }
            tr.timeout td.status {

            }

            tr.aborted {
                background-color: #ddd;
            }
            tr.aborted td.status {
                color: grey;
            }

            tr.retired {
                background-color: #ddd;
            }
            tr.retired td.status {
                color: #5c5cff;
            }
            
            td { 
                padding: 10px; 
            }
            td.challenge {
                font-family: monospace;
            }
            td.status,  dt.step {
                font-variant: small-caps;
            }
            
            
            td { 
                padding: 10px; 
            }
            td.challenge {
                font-family: monospace;
            }
            td.status,  dt.step {
                font-variant: small-caps;
            }
            
            td.artefact-rpath {
                font-family: monospace;
                font-size: 80%;
            }
            td.artefact-size {
                text-align: right;
                font-family: monospace;
                font-size: 80%;
            }
        
        
       div.header td { white-space: pre;}
       
       div.header i { margin-right: 0.3em; }
       div.header a { padding: 4px; color:black; text-decoration: none; }  
       div.header a:hover { background-color: #fff18a; }
       
       .header {
        width: 80vw;
        margin-left: -3em;
         padding: 5px;
         /*background-color: #ffd54c;*/
        }
        .header #title {
        font-weight: bold;
        font-size: 150%;
        border: 0;
        }
        .header td {
        padding-left: 5px;
        padding-right: 5px;
        border-bottom: 1px solid black; 
        }
        
        tr.not-uptodate {
            color: gray;l
        }
        
        body.page-home td.page-home,
        body.page-dashboard td.page-dashboard,
        body.page-logs td.page-logs,
        body.page-challenges td.page-challenges,
        body.page-submissions td.page-submissions,
        body.page-evaluators td.page-evaluators,
        body.page-jobs td.page-jobs,
        body.page-users td.page-users,
        body.page-docs td.page-docs
         { 
            color: green;
            
            background-color: #feeffe; 
        }
        
        .indicator.submission.complete.result-success {
            color: green;
        }
        .indicator.submission.complete.result-error {
            color: red;
        }
        .indicator.submission.complete.result-failed {
            color: purple;
        }
        .indicator.job.error {
           color: red;
        }
        .indicator.job.failed {
            color: red;
        }
        .indicator.job.success{
            color: green;
        }
        .indicator.job.aborted {
            color: purple;
        }
        .indicator.job.timeout {
            color: gray;
        }
        .indicator.job.evaluating {
            color: blue;
        }
        .indicator.evaluator.active {
            color: green;
        }
        .indicator a {
            color: inherit;
            text-decoration: none;
        }
        .indicator a:hover {
            background-color: #ddddff;
           }
      </style>

"""

# STATUS_JOB_TIMEOUT = 'timeout'
# STATUS_JOB_EVALUATION = 'evaluating'
# STATUS_JOB_FAILED = 'failed'  # submission failed
# STATUS_JOB_ERROR = 'error'  # evaluation failed
# STATUS_JOB_SUCCESS = 'success'
# STATUS_JOB_ABORTED = 'aborted'
#

FA_LOGS = FA_LOG = 'list-alt'
FA_CHALLENGES = FA_CHALLENGE = 'trophy'
FA_SUBMISSIONS = FA_SUBMISSION = 'gift'
FA_EVALUATORS = FA_EVALUATOR = 'server'
FA_JOBS = FA_JOB = 'cogs'

FA_USER = 'user'
FA_SCORE = 'stopwatch'
FA_USERS = 'users'
FA_DOCS = 'book'

# language=html
header = """
<div class='header'>
<table><tr>
<td><span id='title'>AI Driving Olympics</span></td>
<td class='page-home'><a href='.'><i class='fa fa-home'/> Home</a></td>
<td class='page-dashboard'><a href='humans/dashboard'><i class='fa fa-dashboard'/> Dashboard</a></td>
<td class='page-logs'><a href='humans/logs'><i class='fa fa-{FA_LOGS}'/>Logs</a></td>
<td class='page-challenges'><a href='humans/challenges'><i class='fa fa-{FA_CHALLENGES}'/>Challenges</a></td>
<td class='page-submissions'><a href='humans/submissions'><i class='fa fa-{FA_SUBMISSIONS}'/>Submissions</a></td>
<td class='page-evaluators'><a href='humans/evaluators'><i class='fa fa-{FA_EVALUATORS}'/>Evaluators</a></td>
<td class='page-jobs'><a href='humans/jobs'><i class='fa fa-{FA_JOBS}'/>Jobs</a> (<a href='humans/queue'>TODO</a>)</td>
<td class='page-users'><a href='humans/users'><i class='fa fa-{FA_USERS}'/>Users</a></td>
<td class='page-docs'><a href='humans/docs'><i class='fa fa-{FA_DOCS}'/>Docs</a></td>
</tr></table>

</div>


    



""".format(FA_DOCS=FA_DOCS,
           FA_LOGS=FA_LOGS,
           FA_EVALUATORS=FA_EVALUATORS,
           FA_CHALLENGES=FA_CHALLENGES,
           FA_SUBMISSIONS=FA_SUBMISSIONS,
           FA_JOBS=FA_JOBS,
           FA_USERS=FA_USERS
           )


@decorator.decorator
def catch_ui_render_problem(f, *args, **kwargs):
    try:
        return f(*args, **kwargs)
    except BaseException as e:
        msg = traceback.format_exc(e)
        c = stag('pre', stag('code', msg))
        return c
