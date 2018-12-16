# coding=utf-8
import functools
import time

import decorator
import termcolor


@decorator.decorator
def timedb(f, *args, **kwargs):
    t0 = time.time()
    res = f(*args, **kwargs)
    t1 = time.time()
    cursor = args[0]
    cursor.debug('timedb: %d ms for %s' % ((t1 - t0) * 1000, f.__name__))
    return res


def result_success(data, total=None, user_msg=None):
    """
    user_msg is a message that will be visualized to the user.

    For example "note that this server is experimental".

    """
    d = dict(
            ok=True,
            result=data,
            user_msg=make_user_msg(user_msg),
    )
    if total:
        d['total'] = total
    return d


def result_failure(error_msg, user_msg=None):
    return dict(
            ok=False,
            user_msg=make_user_msg(user_msg),
            msg=error_msg
    )


def make_user_msg(cmd_user_msg=None):
    from duckietown_challenges_server.humans_home import get_posts
    posts = get_posts(refresh=30000)
    if posts:
        post = posts[0]
        title = post['title']['rendered']
        link = post['link']  # 📰
        notice = u'Last blog post:\n\n  %s\n%s ' % (title, href(link))
    else:
        notice = u''

    if cmd_user_msg:
        return cmd_user_msg.strip() + '\n\n~~~\n\n' + notice.strip()
    else:
        return notice.strip()


def href(x):
    return termcolor.colored(x, 'blue', attrs=['underline'])


class memoized_db_operation(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.

    first value is ignored for caching
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, cursor, *args):
        try:
            res = self.cache[args]
            # print('using cache for %s' % self.func)
            return res
        except KeyError:
            value = self.func(cursor, *args)
            self.cache[args] = value
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__

    def __get__(self, obj, objtype):  # @UnusedVariable
        """Support instance methods."""
        fn = functools.partial(self.__call__, obj)
        fn.reset = self._reset
        return fn

    def _reset(self):
        self.cache = {}
