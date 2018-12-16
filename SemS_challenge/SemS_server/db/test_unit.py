
#  export PATH=$PATH:/usr/local/mysql-8.0.12-macos10.13-x86_64/bin/
# mysql -u root -p


import pymysql
import pymysql.cursors


def wordpress_connect():
    UID = 'dstest'
    PWD = 'dstest'
    host = 'localhost'
    dbname = 'dstest'
    # Open database connection
    db = pymysql.connect(host, UID, PWD, dbname, charset='utf8mb4')
    return db

def get_cursor(db):
    cursor = db.cursor()
    cursor.execute("SET NAMES utf8mb4;")  # or utf8 or any other charset you want to handle
    cursor.execute("SET CHARACTER SET utf8mb4;")  # same as above
    cursor.execute("SET character_set_connection=utf8mb4;")  # same as above
    return cursor


db = wordpress_connect()
cursor = get_cursor(db)


cursor.execute(open('fake_db.sql').read())
cursor.execute(open('schema.sql').read())
