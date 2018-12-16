# coding=utf-8
from bs4 import Tag

from .utils_xml import stag, FA_CHALLENGE, FA_EVALUATOR, FA_USER, FA_JOB, FA_SUBMISSION, FA_SCORE


def html_sub_id(sub_id):
    return str(sub_id)


def url_challenge(challenge):
    href = 'humans/challenges/%s' % challenge.queue_name
    return href


def html_challenge_code(challenge):
    a = Tag(name='a')
    a['href'] = url_challenge(challenge)
    a.append(code(challenge.queue_name))
    return a


def html_challenge_title(challenge):
    s = Tag(name='span')
    s.attrs['class'] = 'indicator challenge'
    a = Tag(name='a')
    a.append(fa(FA_CHALLENGE))
    a['href'] = url_challenge(challenge)
    a.append(challenge.title)
    s.append(a)
    return s


html_challenge = html_challenge_title


def code(x):
    return stag('code', x)


def html_evaluator(ei):
    s = Tag(name='span')
    s.attrs['class'] = 'indicator evaluator %s' % ei.status
    a = Tag(name='a')
    a.append(fa(FA_EVALUATOR))
    href = 'humans/evaluators/%s' % ei.evaluator_id
    a['href'] = href
    # a.append(code('%s/%s' % (ei.machine_id, ei.process_id)))
    a.append(code(str(ei.evaluator_id)))
    s.append(a)
    return s


def html_submission(sub):
    s = Tag(name='span')
    classes = ['indicator', 'submission']
    ss = sub.submission_status
    classes.append(ss.complete and 'complete' or 'incomplete')
    if ss.complete:
        classes.append('result-%s' % ss.result)
    s.attrs['class'] = " ".join(classes)

    a = Tag(name='a')
    a.append(fa(FA_SUBMISSION))
    href = 'humans/submissions/%s' % sub.submission_id
    a['href'] = href
    a['class'] = 'dcs-submission-link'

    a.append(code(str(sub.submission_id)))
    s.append(a)
    return s


def html_user_plain(user, link=True):
    s = Tag(name='span')
    s.attrs['class'] = 'indicator user'
    if link:
        a = Tag(name='a')
        a.append(fa(FA_USER))
        href = 'humans/users/%s' % user.user_id
        a['href'] = href
        a.append(stag('span', user.display_name))
        s.append(a)
    else:
        s.append(fa(FA_USER))
        s.append(stag('span', user.display_name))
    return s


def html_user_avatar(user, link=True):
    s = Tag(name='span')
    s.attrs['class'] = 'indicator user'

    if link:
        a = Tag(name='a')
        a.append(fa(FA_USER))
        href = 'humans/users/%s' % user.user_id
        a['href'] = href
        a.append(stag('span', user.display_name))
        s.append(a)
    else:
        s.append(fa(FA_USER))
        s.append(stag('span', user.display_name))
    return s


def html_job_status(status):
    c = Tag(name='code')
    c.attrs['class'] = 'job-status-%s' % status
    c.append(status)
    return c


def html_submission_status(status):
    c = Tag(name='code')
    c.attrs['class'] = 'submission-status-%s' % status
    c.append(status)
    return c


def html_score(challenge, score, link=True):
    span = Tag(name='span')

    if link:
        a = Tag(name='a')

        a.attrs['href'] = url_challenge(challenge) + '#' + score.name
    else:
        a = Tag(name='span')
    a.append(fa(FA_SCORE))
    if score.short:
        a.append(score.short)
    else:
        a.append(stag('code', score.name))
    span.append(a)
    return span


def html_user(user, link=True):
    if user.extra_wordpress:
        s = Tag(name='span')
        avatar = user.extra_wordpress.avatar96
        img = Tag(name='img')
        img.attrs['src'] = avatar
        img.attrs['style'] = 'width: 1.3em; padding: 1px; margin-right: 3px; margin-bottom: -3px'
        s.append(img)

        if link:
            name = stag('span', user.extra_wordpress.name)
            a = stag('a', name, href='humans/users/%s' % user.user_id)
            s.append(a)
        else:
            s.append(stag('span', user.extra_wordpress.name))

        return s
    else:
        s = Tag(name='span')

        if link:
            name = stag('span', user.display_name)
            a = stag('a', fa(FA_USER), href='humans/users/%s' % user.user_id)

            a.append(name)
            s.append(a)
        else:
            s.append(fa(FA_USER))
            s.append(stag('span', user.display_name))
    return s


def html_job(job):
    return html_job_id(job.job_id, job.status)


def html_job_id(job_id, status):
    s = Tag(name='span')
    s.attrs['class'] = 'indicator job %s' % status

    a = Tag(name='a')
    a.append(fa(FA_JOB))
    href = 'humans/jobs/%s' % job_id
    a['href'] = href
    a.append(code(str(job_id)))
    s.append(a)
    return s


def html_step(step):
    from duckietown_challenges_server.db_challenges import EvaluationStep
    assert isinstance(step, EvaluationStep)
    return '%s' % step.step_name


def html_date(date):
    if date is None:
        return '-'
    else:
        return date_tag(date)


def html_date_md(date):
    if date is None:
        return '-'
    else:
        return date.strftime('%b %-d, %Y')


def date_tag(d):
    # <time class="timesince" datetime="2012-06-28T02:47:40Z">June 28, 2012</time>
    t = Tag(name='time')
    t.attrs['class'] = 'timesince'
    t.attrs['datetime'] = d.isoformat() + '+00:00'
    t.append(d.strftime('%Y-%m-%d %H:%M:%S+00:00'))
    return t


def fa(icon):
    i = Tag(name='i')
    i.attrs['class'] = 'fa fa-%s' % icon
    i.attrs['style'] = 'margin-right: 5px'
    return i
