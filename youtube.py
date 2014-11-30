# coding=utf-8
# (c) Jim Blackler
# Offered as free software under the GNU General Public License v3

import httplib2
from googleapiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run


class YouTubeInfo(object):
  """
  Authenticates users to the YouTube API via the Google API Client library.
  Provides information services about supplied videos.
  """

  @staticmethod
  def get_authenticated_service():
    scope = "https://www.googleapis.com/auth/youtube.readonly"

    storage = Storage("tokens/google.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
      flow = flow_from_clientsecrets("secrets/google_client_secrets.json",
                                     scope=scope)
      credentials = run(flow, storage)

    return build("youtube", "v3", http=credentials.authorize(httplib2.Http()))

  def category_name(self, id):
    if id in self.categoryNames:
      return self.categoryNames[id]
    info = self.youtube.videoCategories().list(part="id,snippet",id=id).execute()
    try:
      name = info['items'][0]['snippet']['title']
      self.categoryNames[id] = name
      return name
    except KeyError:
      return None

  def info(self, _id, parts):
    response = self.youtube.videos().list(part=parts, id=_id).execute()
    # Only one result is expected,
    if len(response['items']) != 1:
      return None
    return response['items'][0]

  def __init__(self):
    self.categoryNames = {}
    self.youtube = self.get_authenticated_service()
