# coding=utf-8
class ChallengeServerConstants(object):
    mysql_pwd = None
    mysql_uid = None
    mysql_host = None
    mysql_db = None

    s3 = False
    bucket_name = None
    aws_access_key_id = None
    aws_secret_access_key = None
    s3_prefix = None

    insecure = False

    wordpress_rest = None
    wordpress_token = None

    JOB_TIMEOUT_MINUTES = 30
