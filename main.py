# coding=utf-8
# (c) Jim Blackler
# Offered as free software under the GNU General Public License v3
import re
import calendar
import time
import datetime

import praw
import dateutil.parser
from isodate import parse_duration
from praw.helpers import comment_stream
from praw.errors import APIException, OAuthInvalidToken

from praw_auth import auth
from youtube import YouTubeInfo
from db import get_db


user_blacklist = set(line.strip().lower() for line in open("data/user_blacklist.txt"))
user_blacklist |= set(line.strip().lower() for line in open("data/requested_user_blacklist.txt"))
subreddit_blacklist = set(line.strip().lower() for line in open("data/subreddit_blacklist.txt"))

youtube = YouTubeInfo()


db = get_db()

if db:
  cursor = db.cursor()
  cursor.execute(open("schema.sql").read())
  db.commit()

  cursor.execute("SELECT user_name FROM stop_requests")
  print "----"
  for result in cursor.fetchall():
    print result[0]
    user_blacklist.add(result[0])
  print "----"
else:
  cursor = None

log_activity = False

pattern = re.compile("(?:http[s]?://www\.youtube\.com/watch\?v=|http://youtu.be/)([0-9A-Za-z\-_]*)")

r = praw.Reddit('youtubefactsbot')


def reauth():
  auth(r, ['identity', 'submit', 'edit', 'privatemessages'])


reauth()
user = r.get_me()
print user.name


def too_old_time():
  return datetime.datetime.now() - datetime.timedelta(hours=1)


def now_seconds():
  return calendar.timegm(time.gmtime())


def look_at_replies():
  print "Looking at replies"
  for comment in r.get_unread(limit=None):
    command = comment.body.strip().lower()
    if command == "stop" or command == "leave me alone":
      try:
        user_blacklist.add(comment.author.name)
        cursor.execute(
            "INSERT INTO stop_requests (user_name, comment_id, time) VALUES (%s, %s, NOW())",
            [comment.author.name, comment.name])
        db.commit()
      except:
        db.rollback()


def delete_downvoted_comments():
  print "Deleting any downvoted comments"

  for comment in user.get_comments(limit=None):
    if comment.score < 1:
      try:
        cursor.execute(
            "INSERT INTO removed_comments (id, parent_id, time) VALUES (%s, %s, NOW())",
            [comment.name, comment.parent_id])
        db.commit()
        comment.delete()
      except Exception:
        db.rollback()

  # Clean up the downvoted comments list.
  try:
    cursor.execute(
        "DELETE FROM removed_comments WHERE time <  %s", [too_old_time()])
    db.commit()
  except Exception as e:
    print e
    db.rollback()


def handle_comments(comments):
  since_replies = 0
  since_deleting_downvoted = 0

  for comment in comments:
    if now_seconds() - since_replies > 60:
      since_replies = now_seconds()
      look_at_replies()
    if now_seconds() - since_deleting_downvoted > 60:
      since_deleting_downvoted = now_seconds()
      delete_downvoted_comments()

    print comment.name

    if "cmgxc69" in comment.name:
      pass

    if comment.author is None:
      continue

    comment_posted_at = datetime.datetime.fromtimestamp(comment.created_utc)
    if comment_posted_at < too_old_time():
      continue

    subreddit = comment.subreddit.display_name

    # Policy : bot doesn't post in blacklisted subreddits.
    if subreddit.lower() in subreddit_blacklist:
      continue

    # Policy : bot doesn't reply to itself
    if comment.author.name == user.name:
      continue

    # Policy : bot doesn't reply to downvoted comments
    if comment.score < 1:
      continue

    # Policy : bot doesn't reply to users in the blacklist
    if comment.author.name.lower() in user_blacklist:
      continue

    # Policy : bot doesn't reply to users with the word 'bot' in their name
    if 'bot' in comment.author.name.lower():
      continue

    # Policy : only very short comments are replied to
    if len(comment.body) > len("relevant! https://www.youtube.com/watch?v=npvcblAGVmU"):
      continue

    # Policy : nothing that looks like a user-supplied link description (hacky)
    if "[" in comment.body:
      continue

    # Any links to extract?
    ids = list(pattern.findall(comment.body))
    if len(ids) == 0:
      continue

    # Policy : bot doesn't reply to comments that already have replies
    if len(comment.replies) > 0:
      continue

    cursor.execute("SELECT time FROM removed_comments WHERE parent_id = %s", [comment.name])
    if cursor.fetchone() is not None:
      continue

    if log_activity:
      cursor.execute("SELECT time FROM replied WHERE id = %s", [comment.name])
      if cursor.fetchone() is not None:
        continue

    flat_comments = praw.helpers.flatten_tree(comment.submission.comments)

    # Policy : bot only comments once in any thread.
    bot_comments = sum(1 if hasattr(reply, 'author') and
                            reply.author is not None and
                            reply.author.name == user.name else 0
                       for reply in flat_comments)
    if bot_comments > 0:
      continue

    # Policy : bot doesn't reply in a thread if *anyone* on the user blacklist
    # has also commented.
    blacklisted_replies = sum(1 if hasattr(reply, 'author') and
                              reply.author is not None and
                              reply.author.name in user_blacklist else 0
                         for reply in flat_comments)
    if blacklisted_replies > 0:
      continue

    reply = ""

    number_usable = 0
    for videoId in ids:
      info = youtube.info(videoId, "id,snippet,statistics,contentDetails")
      if info is None:
        continue
      snippet = info['snippet']
      statistics = info['statistics']
      content_details = info['contentDetails']
      published_at = dateutil.parser.parse(snippet['publishedAt'])
      duration = parse_duration(content_details['duration'])
      channel_url = "https://www.youtube.com/channel/" + snippet['channelId']
      video_url = "http://youtu.be/" + videoId
      nice_duration = str(duration.seconds // 60) + ":" + \
                      str(duration.seconds % 60).zfill(2)
      reply += ">[**" + snippet['title']
      reply += " [" + nice_duration + "]**](" + video_url + ")\n\n"
      lines = snippet['description'].splitlines()
      if False:  # Policy; the bot is not currently adding the full description.
        reply += ">>" + snippet['description'].replace("\n", "\n\n>>") + "\n\n"
      # Don't want the bot to inadvertently spam links. Also, linky comments
      # tend to be promotional rather than informative. If the description is
      # the same as the video title don't include it as we'd repeat ourselves.
      elif (len(lines) > 0 and "http" not in lines[0]
            and "www." not in lines[0] and lines[0] != snippet['title']):
        reply += ">>" + lines[0] + "\n\n"
      if True:
        reply += "> [*^" + snippet['channelTitle'].replace(" ", " ^")
        reply += "*](" + channel_url + ")"
        category_name = youtube.category_name(info['snippet']['categoryId'])
        if category_name:
          reply += " ^in ^" + category_name.replace(" ", " ^")
        reply += "\n\n"
      reply += ">*^{:,}".format(
        int(statistics['viewCount'])) + " ^views ^since "
      reply += published_at.strftime('^%b ^%Y') + "*"
      reply += "\n\n"
      number_usable += 1

    if number_usable == 0:
      continue

    reply += "[^bot ^info]"
    reply += "(http://www.reddit.com/r/youtubefactsbot/wiki/index)"

    try:
      print "POSTING in " + subreddit
      if True:  # testing?
        try:
          comment.reply(reply)
        except OAuthInvalidToken as e:
          print e
          reauth()
          comment.reply(reply)
      if log_activity:
        cursor.execute(
          "INSERT INTO replied (id, subreddit, time) VALUES (%s, %s, NOW())",
          [comment.name, subreddit])

    except APIException as e:
      print e
      if log_activity:
        cursor.execute(
          "INSERT INTO errors (exception, target_id, subreddit, activity, time) VALUES (%s, %s, %s, %s, NOW())",
          [str(e), comment.name, subreddit, "Adding comment"])

    if db:
      db.commit()


if False:
  comments = r.get_comments("test", limit=1000)
  handle_comments(comments)
else:
  while True:
    print "Main loop begins"
    try:
      comments = comment_stream(r, "all")
      #comments = comment_stream(r, "test")
      handle_comments(comments)
    except EnvironmentError as e:
      print e

if db:
  cursor.close()
  db.close()
