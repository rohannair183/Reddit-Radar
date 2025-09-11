-- Main posts table (raw data)
CREATE TABLE IF NOT EXISTS `reddit-radar-471816.reddit_posts` (
  id STRING NOT NULL,
  title STRING,
  selftext STRING,
  subreddit STRING,
  author STRING,
  score INT64,
  upvote_ratio FLOAT64,
  num_comments INT64,
  created_utc TIMESTAMP,
  url STRING,
  permalink STRING,
  link_flair_text STRING,
  is_self BOOL,
  over_18 BOOL,
  spoiler BOOL,
  stickied BOOL,
  locked BOOL,
  distinguished STRING,
  retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  -- Comment metadata
  comments_collected INT64 DEFAULT 0,
  top_comment_score INT64,
  avg_comment_score FLOAT64
)
PARTITION BY DATE(created_utc)
CLUSTER BY subreddit;

-- Main Comments Table
CREATE TABLE IF NOT EXISTS `reddit_radar.reddit_comments` (
  id STRING NOT NULL,
  post_id STRING NOT NULL,
  parent_id STRING,
  author STRING,
  body STRING,
  score INT64,
  created_utc TIMESTAMP,
  permalink STRING,
  is_submitter BOOL,
  depth INT64,
  controversiality INT64,
  distinguished STRING,
  edited BOOL,
  retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  subreddit STRING
)
PARTITION BY DATE(created_utc)
CLUSTER BY post_id, depth;
