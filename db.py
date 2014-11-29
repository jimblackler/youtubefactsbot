# coding=utf-8
import os
from urlparse import urlparse
import MySQLdb
import psycopg2
import secrets.local_db_info


def get_db():
  if False:
    return MySQLdb.connect(user="root", db="reddit_bot")
  else:
    try:
      url = urlparse(os.environ["DATABASE_URL"])
      return psycopg2.connect(database=url.path[1:],
                              user=url.username,
                              password=url.password,
                              host=url.hostname,
                              port=url.port)
    except KeyError:
      return psycopg2.connect(secrets.local_db_info.connect_string)
