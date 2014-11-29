# coding=utf-8
# (c) Jim Blackler
# Offered as free software under the GNU General Public License v3

import json
import pickle
from threading import Event, Thread
import uuid
import webbrowser

from flask import Flask, request


app = Flask(__name__)


@app.route('/authorize_callback')
def authorized():
    token = request.args.get('code', '')
    returned_state = request.args.get('state', '')
    if state != returned_state:
      return "Wrong context"
    info = r.get_access_information(token)
    f = open('tokens/reddit.bin', 'wb')
    pickle.dump({"scope": scope, "info": info}, f)
    f.close()
    user = r.get_me()
    event.set()
    func = request.environ.get('werkzeug.server.shutdown')
    func()
    return "Logged in: " + user.name


def auth(_r, _scope):
  """
  Attempts to authenticate a user to Reddit via PRAW (using the supplied PRAW
  object r).
  Attempt to refresh using existing tokens, else opens a local web browser and
  web server (via Flask) to allow the user to grant access using Reddit's OAuth
  flow. Requires a Reddit application to be registered and secrets put in
  secrets/reddit_secrets.json.
  """
  global r
  r = _r
  global scope
  scope = _scope

  port = 65010
  f = open("secrets/reddit_secrets.json")
  info = json.load(f)
  f.close()

  r.set_oauth_app_info(info['client_id'], info['client_secret'],
                    redirect_uri='http://127.0.0.1:' + str(port) + '/authorize_callback')

  try:
    f = open('tokens/reddit.bin', 'rb')
    data = pickle.load(f)
    if data['scope'] == scope:
      f.close()
      info = data['info']
      info = r.refresh_access_information(info['refresh_token'])
      r.set_access_credentials(**info)
      return
  except:
    pass

  global event
  event = Event()

  def start():
    app.run(port=port)

  server = Thread(target=start)
  server.start()

  global state
  state = str(uuid.uuid4())
  webbrowser.open(r.get_authorize_url(state, scope=scope, refreshable=True))

  event.wait()
