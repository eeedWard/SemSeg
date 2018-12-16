# coding=utf-8
import json

from ecdsa import BadSignatureError
from pyramid.httpexceptions import HTTPUnauthorized

from dt_shell.duckietown_tokens import get_verify_key
from duckietown_challenges_server.constants import ChallengeServerConstants
from duckietown_challenges_server.database import db_connection
from . import cslogger

HTTPUnauthorized.explanation = ''


# noinspection PyUnusedLocal
def valid_dt1_token(request, **kargs):
    header = 'X-Messaging-Token'
    htoken = request.headers.get(header)
    if htoken is None:
        msg = 'You need to pass the Duckietown token with the header X-Messaging-Token.'
        cslogger.error(msg)
        raise HTTPUnauthorized(msg)

    try:
        from dt_shell.duckietown_tokens import DuckietownToken
        token = DuckietownToken.from_string(htoken)
    except ValueError as e:
        msg = "Invalid token format: %s" % e
        cslogger.error(msg)
        raise HTTPUnauthorized(msg)

    vk = get_verify_key()
    try:
        ok = vk.verify(token.signature, token.payload)
    except BadSignatureError as e:
        msg = 'Invalid signature: %s' % e
        cslogger.error(msg)
        ok = False
    if not ok:
        msg = 'This is an invalid token; signature check failed.'
        cslogger.error(msg)
        raise HTTPUnauthorized(msg)

    try:
        data = json.loads(token.payload)
    except Exception as e:
        msg = 'Could not load payload: %s' % e
        cslogger.error(msg)
        raise HTTPUnauthorized(msg)

    cslogger.debug('Validated data %s from token.' % token)
    try:
        request.validated['uid'] = data['uid']
        request.validated['expiration'] = data['exp']
    except KeyError as e:
        msg = 'Could not find fields: %s' % e
        cslogger.error(msg)
        raise HTTPUnauthorized(msg)

    # TODO: check expiration date
    make_sure_uid_exists(request, data['uid'])


class Storage(object):
    known_ids = set()


def make_sure_uid_exists(request, uid):
    if uid in Storage.known_ids:
        # print('uid %r already known in %s' % (uid, Storage.known_ids))
        return

    cslogger.info('uid: %r' % uid)

    with db_connection(request) as cursor:
        cmd = "select ID from wp_users"
        cursor.execute(cmd)
        for ID, in cursor.fetchall():
            Storage.known_ids.add(ID)

        cslogger.info('known: %r' % Storage.known_ids)

        if uid not in Storage.known_ids:
            cslogger.info('Creating dummy user for ID = %s' % uid)
            cmd = """
                insert into wp_users(ID, user_login, user_pass, user_nicename,
                 display_name, user_email, user_url, user_registered)
                values (%s, %s, %s, %s, %s, %s, %s, UTC_TIMESTAMP())
            """
            user_login = 'user%d' % uid
            user_pass = 'xxx'
            user_email = ''
            user_nicename = user_login
            user_displayname = user_login
            user_url = ''
            args = (uid, user_login, user_pass, user_nicename, user_displayname, user_email, user_url)
            cursor.execute(cmd, args)
            Storage.known_ids.add(uid)


def is_superadmin(admin_id):
    allowed = [
        3,  # A.C.
        7,  # A.D
        365,  # manfred
        449,  # julian
    ]
    if ChallengeServerConstants.insecure:
        return True
    return admin_id in allowed
