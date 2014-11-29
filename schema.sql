CREATE TABLE IF NOT EXISTS errors (
  time timestamp NOT NULL,
  exception text NOT NULL,
  activity text NOT NULL,
  target_id char(11) NOT NULL DEFAULT '',
  subreddit text
);

CREATE TABLE IF NOT EXISTS replied (
  id char(11) NOT NULL DEFAULT '',
  time timestamp NOT NULL,
  subreddit text,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS removed_comments (
  id char(11) NOT NULL DEFAULT '',
  parent_id char(11) NOT NULL DEFAULT '',
  time timestamp NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS stop_requests (
  user_name TEXT,
  comment_id char(11) NOT NULL DEFAULT '',
  time timestamp NOT NULL,
  PRIMARY KEY (user_name)
);
