# coding=utf-8
# (c) Jim Blackler
# Offered as free software under the GNU General Public License v3
import re

import praw
import dateutil.parser
from isodate import parse_duration
import MySQLdb
from praw.helpers import comment_stream
from praw.errors import APIException
from requests import ConnectionError, HTTPError

from praw_auth import auth
from youtube import YouTubeInfo

user_blacklist = set(line.strip() for line in open("data/user_blacklist.txt"))
subreddit_whitelist = set(line.strip() for line in open("data/subreddit_whitelist.txt"))

youtube = YouTubeInfo()
db = MySQLdb.connect(user="root", db="reddit_bot")
cursor = db.cursor()

pattern = re.compile("https://www\.youtube\.com/watch\?v=([0-9A-Za-z\-]*)")

r = praw.Reddit('youtubefactsbot')

auth(r, ['identity', 'submit'])

user = r.get_me()
print user.name


def handle_comments(comments):
  for comment in comments:
    print comment.id
    if comment.author is None:
      continue
    # Policy : bot doesn't reply to itself
    if comment.author.name == user.name:
      continue

    # Policy : bot doesn't reply to downvoted comments
    if comment.score < 1:
      continue

    # Policy : bot doesn't reply to users in the blacklist
    if comment.author.name in user_blacklist:
      continue

    # Policy : bot doesn't reply to users with the word 'bot' in their name
    if 'bot' in comment.author.name.lower():
      continue

    # Policy : only very short comments are replied to
    if len(comment.body) > 56:
      continue

    # Any links to extract?
    ids = list(pattern.findall(comment.body))
    if len(ids) == 0:
      continue

    # Policy : bot doesn't reply to comments that already have replies
    if len(comment.replies) > 0:
      continue

    cursor.execute("SELECT time FROM replied WHERE id = %s", [comment.id])
    result = cursor.fetchone()
    if result is not None:
      continue

    subreddit = comment.subreddit

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
      if False:  # Policy; the bot is not currently adding the description.
        reply += ">>" + snippet['description'].replace("\n", "\n\n>>") + "\n\n"
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
      print "POSTING"
      comment.reply(reply)
      cursor.execute(
        "INSERT INTO replied (id, subreddit, time) VALUES (%s, %s, NOW())",
        [comment.id, subreddit])
      db.commit()
    except APIException as e:
      print e
      cursor.execute(
        "INSERT INTO errors (exception, target_id, subreddit, activity, time) VALUES (%s, %s, %s, %s, NOW())",
        [str(e), comment.id, subreddit, "Adding comment"])
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
      #comments = comment_stream(r, "+".join(subreddit_whitelist))
      comments = comment_stream(r, "random")
      handle_comments(comments)
    except ConnectionError as e:
      print e

cursor.close()
db.close()
