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
    flow = flow_from_clientsecrets("secrets/google_client_secrets.json",
                                   scope=scope)

    storage = Storage("tokens/google.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
      credentials = run(flow, storage)

    return build("youtube", "v3", http=credentials.authorize(httplib2.Http()))

  def info(self, _id):
    parts = "id,snippet,statistics,contentDetails"
    response = self.youtube.videos().list(part=parts, id=_id).execute()
    # Only one result is expected,
    if len(response['items']) != 1:
      return None
    return response['items'][0]

  def __init__(self):
    self.youtube = self.get_authenticated_service()
