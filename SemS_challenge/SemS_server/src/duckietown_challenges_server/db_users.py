# coding=utf-8
import json
import subprocess
import time
import traceback
from collections import OrderedDict

from duckietown_challenges_server.database import db_connection
from duckietown_challenges_server.misc import timedb
from . import cslogger
from .constants import ChallengeServerConstants


class User(object):

    def __init__(self, user_id, display_name, user_url, user_login, extra_wordpress):
        self.user_id = user_id
        self.display_name = display_name
        self.user_url = user_url
        self.extra_wordpress = extra_wordpress
        self.user_login = user_login

    def __repr__(self):
        return 'User(%s)' % self.__dict__

    extra_info = {}


class WordpressExtraInfo(object):
    def __init__(self, data):
        # print(json.dumps(data, indent=4))
        self.avatar96 = data['avatar_urls']['96']
        self.name = data['name']
        self.link = data['link']
        self.slug = data['slug']

    def __repr__(self):
        return 'WordpressExtraInfo(%s)' % self.__dict__


class StorageUser(object):
    last_request = time.time()


def get_users_thread():
    cslogger.info('Starting users thread')
    while True:
        for i in range(10):
            with db_connection(request=None) as cursor:
                users = read_users(cursor)
                # cmd = 'select ID from wp_users'
                # cursor.execute(cmd)
                # for user_id, in cursor.fetchall():
                for user_id in users:
                    get_wordpress_extra_info(cursor, user_id)

            time.sleep(10)
        cslogger.debug('extra_info: %s' % User.extra_info)

def get_wordpress_extra_info(cursor, user_id):
    if user_id in User.extra_info:
        return User.extra_info[user_id]

    base = ChallengeServerConstants.wordpress_rest
    if base is None:
        cslogger.debug('Wordpress not enabled')
        # User.extra_info[user_id] = None
        return None

    endpoint = 'users/%s' % user_id
    url = base + endpoint

    token = ChallengeServerConstants.wordpress_token
    now = time.time()
    if StorageUser.last_request and now - StorageUser.last_request < 3 or \
            cursor.time_since_start() > 1:
        # return None without caching
        # cslogger.debug('Avoiding request because too soon')
        return None

    StorageUser.last_request = now
    try:
        # t0 = time.time()
        data = make_rest_request1(token, url, data=None, timeout=3)
        StorageUser.last_request = time.time()
        # delta = time.time() - t0
        # cslogger.info('%d ms for %s' % (delta * 1000, url))
        # cslogger.info(data)
        if data is None:
            # User.extra_info[user_id] = None
            return None
        res = WordpressExtraInfo(data)
        msg = 'Obtained %s %s for user_id = %s' % (url, data, user_id)
        cslogger.info(msg)
        if "Censi" in res.name and user_id != 3:
            msg2 = 'Wait, why did I get this for user?'
            msg2 += '\n' + msg
            cslogger.error(msg2)
            return None
    except BaseException as e:
        cslogger.error('Could not get data for %s: %s' % (user_id, e))
        # User.extra_info[user_id] = None
    else:
        User.extra_info[user_id] = res
        return res


def read_user(cursor, user_id):
    """ Raises KeyError if not found. """
    cmd = """
        select ID, display_name, user_login 
        from wp_users  
        where ID = %s
    """
    cursor.execute(cmd, (user_id,))
    if cursor.rowcount == 0:
        msg = 'Could not find user %s' % user_id
        raise KeyError(msg)

    ID, display_name, user_login = cursor.fetchone()
    user_url = 'https://www.duckietown.org/site/pm_profile?uid=%s' % user_id
    extra_wordpress = get_wordpress_extra_info(cursor, user_id)
    if extra_wordpress is not None:
        display_name = extra_wordpress.name
        user_login = extra_wordpress.slug
    u = User(user_id, display_name, user_url, user_login=user_login, extra_wordpress=extra_wordpress)
    return u


@timedb
def read_users(cursor):
    res = OrderedDict()
    cmd = """

        select ID, display_name, user_login 
        from wp_users, aido_submissions 
        where aido_submissions.user_id = wp_users.ID 
        ORDER BY ID
        """
    cursor.execute(cmd)

    first = list(cursor.fetchall())

    cmd = """
        select ID, display_name, user_login
        from wp_users, aido_evaluators 
        where aido_evaluators.uid = wp_users.ID 
        ORDER BY ID
    """
    cursor.execute(cmd)
    second = list(cursor.fetchall())

    for _ in first + second:
        user_id, display_name, user_login = _
        user_url = 'https://www.duckietown.org/site/pm_profile?uid=%s' % user_id
        extra_wordpress = get_wordpress_extra_info(cursor, user_id)
        u = User(user_id, display_name, user_url, user_login=user_login, extra_wordpress=extra_wordpress)

        res[user_id] = u

    return res


class RESTException(Exception):
    pass


def make_rest_request1(token, url, data=None, timeout=2):
    cmd = ['curl', '-m', str(timeout), "--silent", "--show-error", "--fail"]
    cmd += ['--header', "Authorization: Basic %s" % token]
    cmd += [url]
    try:
        t0 = time.time()
        cslogger.debug('GET %s' % url)
        output = subprocess.check_output(cmd)
        delta = time.time() - t0
        cslogger.debug('%s ms %s' % (delta * 1000, url))
    except subprocess.CalledProcessError as e:
        cslogger.error(e)
        return None
    try:
        return json.loads(output)
    except BaseException as e:
        cslogger.error(traceback.format_exc(e))
        return None
