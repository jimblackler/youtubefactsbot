# coding=utf-8
# (c) Jim Blackler
# Offered as free software under the GNU General Public License v3
import re

import praw
import dateutil.parser
from isodate import parse_duration
import MySQLdb
from praw.helpers import comment_stream
from praw.errors import APIException, OAuthInvalidToken

from praw_auth import auth
from youtube import YouTubeInfo

user_blacklist = set(line.strip().lower() for line in open("data/user_blacklist.txt"))
subreddit_blacklist = set(line.strip().lower() for line in open("data/subreddit_blacklist.txt"))
subreddit_whitelist = set(line.strip() for line in open("data/subreddit_whitelist.txt"))

youtube = YouTubeInfo()

if False:
  db = MySQLdb.connect(user="root", db="reddit_bot")
  cursor = db.cursor()
else:
  db = None
  cursor = None


pattern = re.compile("https://www\.youtube\.com/watch\?v=([0-9A-Za-z\-_]*)")

r = praw.Reddit('youtubefactsbot')

def reauth():
  auth(r, ['identity', 'submit'])

reauth()
user = r.get_me()
print user.name


def handle_comments(comments):
  for comment in comments:
    print comment.id
    if comment.author is None:
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
    if len(comment.body) > 54:
      continue

    # Any links to extract?
    ids = list(pattern.findall(comment.body))
    if len(ids) == 0:
      continue

    # Policy : bot doesn't reply to comments that already have replies
    if len(comment.replies) > 0:
      continue

    if cursor:
      cursor.execute("SELECT time FROM replied WHERE id = %s", [comment.id])
      result = cursor.fetchone()
      if result is not None:
        continue

    reply = ""

    number_usable = 0
    for videoId in ids:
      info = youtube.info(videoId)
      if info is None:
        continue
      snippet = info['snippet']
      statistics = info['statistics']
      content_details = info['contentDetails']
      datetime = dateutil.parser.parse(snippet['publishedAt'])
      duration = parse_duration(content_details['duration'])
      channel_url = "https://www.youtube.com/channel/" + snippet['channelId']
      video_url = "https://www.youtube.com/watch?v=" + videoId
      nice_duration = str(duration.seconds // 60) + ":" + \
                      str(duration.seconds % 60).zfill(2)
      reply += ">[**" + snippet['title']
      reply += " [" + nice_duration + "]**](" + video_url + ")\n\n"
      lines = snippet['description'].splitlines()
      if False:  # Policy; the bot is not currently adding the full description.
        reply += ">>" + snippet['description'].replace("\n", "\n\n>>") + "\n\n"
      elif len(lines) > 0 and "http" not in lines[0] and lines[0] != snippet['title']:  # But it is adding the first line only if it doesn't contain links.
        reply += ">>" + lines[0] + "\n\n"
      reply += ">*^{:,}".format(
        int(statistics['viewCount'])) + " ^views ^since "
      reply += datetime.strftime('^%b ^%Y') + "*"
      if False:  # Not currently linking to the channel
        reply += " [*^" + snippet['channelTitle'].replace(" ", " ^")
        reply += "*](" + channel_url + ")"
      reply += "\n\n"
      number_usable += 1

    if number_usable == 0:
      continue

    reply += "[^youtubefactsbot]"
    reply += "(http://www.reddit.com/r/youtubefactsbot/wiki/index)"

    try:
      print "POSTING in " + subreddit
      try:
        comment.reply(reply)
      except OAuthInvalidToken as e:
        print e
        reauth()
        comment.reply(reply)
      if cursor:
        cursor.execute(
          "INSERT INTO replied (id, subreddit, time) VALUES (%s, %s, NOW())",
          [comment.id, subreddit])

    except APIException as e:
      print e
      if cursor:
        cursor.execute(
          "INSERT INTO errors (exception, target_id, subreddit, activity, time) VALUES (%s, %s, %s, %s, NOW())",
          [str(e), comment.id, subreddit, "Adding comment"])

    if db:
      db.commit()

if False:
  for subreddit in subreddit_whitelist:
    try:
      print subreddit
      comments = r.get_comments(subreddit, limit=1000)
      handle_comments(comments)
    except StandardError as e:
      print e
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
