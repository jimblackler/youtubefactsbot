# coding=utf-8
# (c) Jim Blackler
# Offered as free software under the GNU General Public License v3
import re

import praw
import dateutil.parser
from isodate import parse_duration
import MySQLdb
from praw.errors import APIException

from praw_auth import auth
from youtube import YouTubeInfo

user_blacklist = set(line.strip() for line in open("data/user_blacklist.txt"))

youtube = YouTubeInfo()
db = MySQLdb.connect(user="root", db="reddit_bot")
cursor = db.cursor()

pattern = re.compile("https://www\.youtube\.com/watch\?v=([0-9A-Za-z\-]*)")

r = praw.Reddit('youtubefactsbot')

auth(r, ['identity', 'submit'])

user = r.get_me()
print user.name


comments = r.get_comments('test', limit=50000)
for comment in comments:
  if comment.author is None:
    continue
  # Policy : bot doesn't reply to itself
  if comment.author.name == user.name:
    continue

  # Policy : bot doesn't reply to downvoted comments
  if comment.score < 1:
    continue

  # Policy : bot doesn't reply to comments that already have replies
  if len(comment.replies) > 0:
    continue

  # Policy : bot doesn't reply to users in the blacklist
  if comment.author.id in user_blacklist:
    continue

  # Policy : only very short comments are replied to
  if len(comment.body) > 60:
    continue

  # Any links to extract?
  ids = list(pattern.findall(comment.body))
  if len(ids) == 0:
    continue

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
    contentDetails = info['contentDetails']
    datetime = dateutil.parser.parse(snippet['publishedAt'])
    duration = parse_duration(contentDetails['duration'])
    channelUrl = "https://www.youtube.com/channel/" + snippet['channelId']
    videoUrl = "https://www.youtube.com/watch?v=" + videoId
    nice_duration = str(duration.seconds // 60) + ":" +\
                    str(duration.seconds % 60).zfill(2)
    reply += ">[**" + snippet['title']
    reply += " [" + nice_duration + "]**](" + videoUrl + ")\n\n"
    if False:  # Policy; the bot is not currently adding the description.
      reply += ">>" + snippet['description'].replace("\n", "\n\n>>") + "\n\n"
    reply += ">*^{:,}".format(int(statistics['viewCount'])) + " ^views ^since "
    reply += datetime.strftime('^%b ^%Y') + "*"
    reply += " [*^" + snippet['channelTitle'].replace(" ", " ^")
    reply += "*](" + channelUrl + ")"
    reply += "\n\n"
    number_usable += 1

  if number_usable == 0:
    continue

  reply = "[Information](http://www.reddit.com/r/youtubefactsbot/wiki/index) " +\
          "about the linked " +\
          ("video" if number_usable == 1 else "videos") + ":\n" + reply

  try:
    comment.reply(reply)
    cursor.execute("INSERT INTO replied (id, time) VALUES (%s, NOW())",
                   [comment.id])
    db.commit()
  except APIException as e:
    print e
    cursor.execute("INSERT INTO errors (exception, target_id, activity, time) VALUES (%s, %s, %s, NOW())",
                   [str(e), comment.id, "Adding comment"])
    db.commit()


cursor.close()
db.close()
