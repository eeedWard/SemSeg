# coding=utf-8

import time
import traceback
from collections import defaultdict
from contextlib import contextmanager

from pymysql import OperationalError
from pymysql.cursors import Cursor
from pyramid.httpexceptions import HTTPServiceUnavailable

from . import cslogger
from .constants import ChallengeServerConstants


@contextmanager
def db_connection(request):
    try:
        db = wordpress_connect()
    except OperationalError:
        cslogger.error(traceback.format_exc())
        msg = 'The database is not available. Try again later.'
        raise HTTPServiceUnavailable(msg)

    cursor = get_cursor(db, request)
    try:
        yield cursor
        db.commit()
    finally:
        cursor.close()
        db.close()


def wordpress_connect():
    import pymysql.cursors
    UID = ChallengeServerConstants.mysql_uid
    PWD = ChallengeServerConstants.mysql_pwd
    host = ChallengeServerConstants.mysql_host
    dbname = ChallengeServerConstants.mysql_db
    db = pymysql.connect(host, UID, PWD, dbname, charset='utf8mb4')
    return db


class MyCursor(Cursor):
    serial = 0

    def __init__(self, *args, **kwargs):
        Cursor.__init__(self, *args, **kwargs)
        self.t0 = time.time()
        self.n = 0
        self.query2number = defaultdict(int)
        self.request = None
        self.serial = MyCursor.serial
        MyCursor.serial += 1

    def _get_prefix(self):
        if self.request:
            return '%s %s: ' % (self.serial, self.request.path_qs)
        else:
            return '%s: ' % self.serial
        # if request is not None:
        #     cursor.debug('req %s from %s %s' % (request.path_qs, request.client_addr, request.user_agent))

    def info(self, s):
        prefix = self._get_prefix()
        cslogger.info('%s%s' % (prefix, s))

    def debug(self, s):
        prefix = self._get_prefix()
        cslogger.debug('%s%s' % (prefix, s))

    def error(self, s):
        prefix = self._get_prefix()
        cslogger.error('%s%s' % (prefix, s))

    def time_since_start(self):
        return time.time() - self.t0

    def execute(self, query, args=None):

        # q = query
        # if '%s' in q:
        #     q = q % args

        self.n += 1
        try:
            res = Cursor.execute(self, query, args)
        except:
            msg = 'Error while executing query:\n\n%s\n\nwith params\n%s' % (query, args)
            self.error(msg)
            raise
        self.query2number[query] += 1

        # cslogger.debug('query %d %s' % (self.n, q.replace('\n', '')))
        self.n += 1
        return res

    def close(self):

        Cursor.close(self)
        for k, v in self.query2number.items():
            if v > 1:
                msg = 'Repeated %s: %s ' % (v, k)
                self.debug(msg)
        delta = time.time() - self.t0

        if self.request is not None:
            path = self.request.path_qs
        else:
            path = ""

        self.debug('%d queries, %.2f s for %s' % (self.n, delta, path))


def get_cursor(db, request):
    cursor = db.cursor(cursor=MyCursor)
    cursor.request = request
    if request is not None:
        cursor.debug('client: %s %s' % (request.client_addr, request.user_agent))
    cursor.execute("SET NAMES utf8mb4;")  # or utf8 or any other charset you want to handle
    cursor.execute("SET CHARACTER SET utf8mb4;")  # same as above
    cursor.execute("SET character_set_connection=utf8mb4;")  # same as above
    return cursor
