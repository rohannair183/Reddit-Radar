"""
Reddit Radar - Data Ingestion Module
====================================

This module handles Reddit data collection using PRAW (Python Reddit API Wrapper).
Implements rate limiting, error handling, and data validation.

Author: Rohan Nair
Date: 20250910
"""

import os
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set, Tuple
from praw.models import MoreComments

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import csv

import praw
from praw.exceptions import RedditAPIException, PRAWException
import pandas as pd

# Import project utilities
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import Config, CommentCollectionConfig
from utils.logger import setup_logger
import traceback
# Data Models

@dataclass
class RedditComment:
    """Data class for Reddit comment structure"""
    id: str
    post_id: str  # Links back to the original post
    parent_id: str  # Parent comment ID (or post ID if top-level)
    author: str
    body: str
    score: int
    created_utc: float
    permalink: str
    is_submitter: bool  # True if comment author is post author
    depth: int  # Comment nesting level (0 = top-level)
    controversiality: int  # Reddit's controversy score
    distinguished: Optional[str]  # mod/admin status
    edited: bool
    retrieved_at: str
    subreddit: str  # Which subreddit this comment is from

    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary"""
        return asdict(self)


@dataclass
class RedditPost:
    """Data class for standardized Reddit post structure"""
    id: str
    title: str
    selftext: str
    subreddit: str
    author: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: float
    url: str
    permalink: str
    link_flair_text: Optional[str]
    is_self: bool
    over_18: bool
    spoiler: bool
    stickied: bool
    locked: bool
    distinguished: Optional[str]
    retrieved_at: str

    # Comment-related metadata
    comments_collected: int  # How many comments we actually collected
    top_comment_score: Optional[int]  # Score of highest-rated comment
    avg_comment_score: Optional[float]  # Average score of collected comments

    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary"""
        return asdict(self)

# @dataclass
# class CommentCollectionConfig:
#     """Configuration for comment collection behavior"""
#     max_comments_per_post: int = 50
#     min_comment_score: int = 1
#     max_comment_depth: int = 3
#     include_controversial: bool = True
#     sort_by: str = 'top'           # 'top' | 'best' | 'new' | 'controversial'
#     collect_replies: bool = True   # (handled implicitly by .list())
#     skip_deleted: bool = True
#     skip_automod: bool = True

class RedditScraper:
    """
    Reddit data collection class with rate limiting and error handling
    """
    
    # Target tech/developer subreddits for trend analysis
    DEFAULT_SUBREDDITS = [
        'programming', 'MachineLearning', 'webdev', 'javascript',
        'Python', 'technology', 'artificial', 'datascience',
        'DevOps', 'reactjs', 'learnpython', 'compsci'
    ]
    
    def __init__(self, config: Optional[Config] = None, comment_config: Optional[CommentCollectionConfig] = None):
        """
        Initialize Reddit scraper with configuration
        
        Args:
            config: Configuration object with Reddit API credentials
        """
        self.config = Config()
        self.comment_config = CommentCollectionConfig()
        self.logger = setup_logger(__name__)
        self.reddit = None
        self._initialize_reddit_client()
        
        # Rate limiting and error tracking
        self.request_count = 0
        self.comment_request_count = 0
        self.last_request_time = 0
        self.failed_requests = 0
        self.max_retries = 3
        self.retry_delay = 5  # seconds

        # Statistics
        self.total_comments_collected = 0
        self.skipped_comments = 0
        
    def _initialize_reddit_client(self) -> None:
        """Initialize Reddit API client with proper authentication"""
        try:
            self.reddit = praw.Reddit(
                client_id=self.config.REDDIT_CLIENT_ID,
                client_secret=self.config.REDDIT_CLIENT_SECRET,
                user_agent=self.config.REDDIT_USER_AGENT,
                ratelimit_seconds=600  # PRAW built-in rate limiting
            )
            
            # Test authentication
            self.reddit.user.me()
            self.logger.info("Reddit API client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit client: {e}")
            raise
    
    def _rate_limit(self, comment_request: bool = False) -> None:
        """Implement custom rate limiting (1s for posts, 1.5s for comments)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        min_delay = 1.5 if comment_request else 1.0
        if time_since_last < min_delay:
            time.sleep(min_delay - time_since_last)

        self.last_request_time = time.time()
        self.request_count += 1
        if comment_request:
            self.comment_request_count += 1


    
    def _extract_post_data(self, submission) -> RedditPost:
        """
        Extract relevant data from Reddit submission
        
        Args:
            submission: PRAW submission object
            
        Returns:
            RedditPost object with extracted data
        """
        return RedditPost(
            id=submission.id,
            title=submission.title or "",
            selftext=submission.selftext or "",
            subreddit=str(submission.subreddit),
            author=str(submission.author) if submission.author else "[deleted]",
            score=submission.score,
            upvote_ratio=submission.upvote_ratio,
            num_comments=submission.num_comments,
            created_utc=submission.created_utc,
            url=submission.url,
            permalink=f"https://reddit.com{submission.permalink}",
            link_flair_text=submission.link_flair_text,
            is_self=submission.is_self,
            over_18=submission.over_18,
            spoiler=submission.spoiler,
            stickied=submission.stickied,
            locked=submission.locked,
            distinguished=submission.distinguished,
            retrieved_at=datetime.now(timezone.utc).isoformat(),

            # Comment metadata (will be populated later)
            comments_collected=0,
            top_comment_score=None,
            avg_comment_score=None
        )
    
    def _calculate_comment_depth(self, comment) -> int:
        """Calculate comment nesting depth (uses native depth if present)."""
        if hasattr(comment, 'depth') and isinstance(comment.depth, int):
            return max(0, int(comment.depth))
        depth = 0
        try:
            parent = comment.parent()
            while hasattr(parent, 'parent'):
                parent = parent.parent()
                depth += 1
                if depth > 10:
                    break
        except Exception:
            pass
        return depth


    def _should_skip_comment(self, comment) -> Tuple[bool, str]:
        """Apply filters from comment_config to decide if a comment should be skipped."""
        if isinstance(comment, MoreComments):
            return True, "MoreComments object"

        if self.comment_config.SKIP_DELETED and (
            getattr(comment, 'body', None) in ['[deleted]', '[removed]'] or
            comment.author is None
        ):
            return True, "deleted/removed"

        if (self.comment_config.SKIP_AUTOMOD and comment.author and
                str(comment.author).lower() == 'automoderator'):
            return True, "AutoModerator"

        if getattr(comment, 'score', 0) < self.comment_config.MIN_COMMENT_SCORE:
            return True, f"low score ({getattr(comment, 'score', 0)})"

        depth = self._calculate_comment_depth(comment)
        if depth > self.comment_config.MAX_COMMENT_DEPTH:
            return True, f"too deep (depth {depth})"

        return False, ""


    def _extract_comment_data(self, comment, post_id: str, subreddit: str) -> RedditComment:
        """Turn a PRAW comment into our RedditComment dataclass."""
        try:
            parent = comment.parent()
            parent_id = post_id if hasattr(parent, 'title') else getattr(parent, 'id', post_id)
        except Exception:
            parent_id = post_id

        return RedditComment(
            id=comment.id,
            post_id=post_id,
            parent_id=parent_id,
            author=str(comment.author) if comment.author else "[deleted]",
            body=getattr(comment, 'body', "") or "",
            score=getattr(comment, 'score', 0),
            created_utc=getattr(comment, 'created_utc', 0.0),
            permalink=f"https://reddit.com{getattr(comment, 'permalink', '')}",
            is_submitter=getattr(comment, 'is_submitter', False),
            depth=self._calculate_comment_depth(comment),
            controversiality=getattr(comment, 'controversiality', 0),
            distinguished=getattr(comment, 'distinguished', None),
            edited=bool(getattr(comment, 'edited', False)),
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            subreddit=subreddit
        )

    def collect_comments_for_post(self, post_id: str, subreddit: str) -> List[RedditComment]:
        """Collect filtered comments for a specific post."""
        self._rate_limit(comment_request=True)
        try:
            submission = self.reddit.submission(id=post_id)

            # Set sort order
            submission.comment_sort = self.comment_config.SORT_COMMENT_BY

            # Keep cost predictable
            submission.comments.replace_more(limit=0)

            comments: List[RedditComment] = []
            processed_count = 0

            for c in submission.comments.list():
                if len(comments) >= self.comment_config.MAX_COMMENTS_PER_POST:
                    break
                processed_count += 1

                skip, reason = self._should_skip_comment(c)
                if skip:
                    self.skipped_comments += 1
                    continue

                try:
                    comments.append(self._extract_comment_data(c, post_id, subreddit))
                    self.total_comments_collected += 1
                except Exception as e:
                    self.logger.warning(f"Error extracting comment {getattr(c, 'id', '?')}: {e}")
                    continue

            self.logger.debug(f"Collected {len(comments)} comments for post {post_id} "
                            f"(processed {processed_count})")
            return comments

        except Exception as e:
            self.logger.error(f"Error collecting comments for post {post_id}: {e}")
            return []

    def scrape_subreddit(self,
                    subreddit_name: str,
                    limit: int = 100,
                    time_filter: str = 'day',
                    sort_type: str = 'hot',
                    collect_comments: bool = True
                    ) -> Tuple[List[RedditPost], List[RedditComment]]: 
        """
        Scrape posts and comments from a single subreddit

        Args:
            subreddit_name: Name of the subreddit to scrape
            limit: Number of posts to retrieve
            time_filter: Time filter for 'top' sort (hour, day, week, month
            sort_type: Sorting method (hot, new, top, rising)
            collect_comments: Whether to collect comments for each post
        Returns:
            Tuple of (list of RedditPost, list of RedditComment)
        """
        posts: List[RedditPost] = []
        all_comments: List[RedditComment] = []

        try:
            self.logger.info(f"Scraping r/{subreddit_name} - {sort_type} posts "
                            f"(limit: {limit}, comments: {collect_comments})")
            subreddit = self.reddit.subreddit(subreddit_name)

            if sort_type == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort_type == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort_type == 'top':
                submissions = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort_type == 'rising':
                submissions = subreddit.rising(limit=limit)
            else:
                raise ValueError(f"Invalid sort_type: {sort_type}")

            for submission in submissions:
                self._rate_limit()

                try:
                    post = self._extract_post_data(submission)  # your existing extractor is fine
                    post_comments: List[RedditComment] = []

                    if collect_comments and not submission.locked:
                        post_comments = self.collect_comments_for_post(post.id, subreddit_name)
                        post.comments_collected = len(post_comments)
                        if post_comments:
                            scores = [c.score for c in post_comments]
                            post.top_comment_score = max(scores)
                            post.avg_comment_score = sum(scores) / len(scores)

                    posts.append(post)
                    all_comments.extend(post_comments)

                except Exception as e:
                    self.logger.warning(f"Error processing submission {submission.id}: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(posts)} posts and "
                            f"{len(all_comments)} comments from r/{subreddit_name}")

        except RedditAPIException as e:
            self.logger.error(f"Reddit API error for r/{subreddit_name}: {e}")
            self.failed_requests += 1
        except Exception as e:
            self.logger.error(f"Unexpected error scraping r/{subreddit_name}: {e}")
            self.failed_requests += 1

        return posts, all_comments

    
    def scrape_multiple_subreddits(self,
                                 subreddit_names: Optional[List[str]] = None,
                                 limit_per_subreddit: int = 100,
                                 time_filter: str = 'day',
                                 sort_type: str = 'hot') -> Dict[str, List[RedditPost]]:
        """
        Scrape posts from multiple subreddits
        
        Args:
            subreddit_names: List of subreddit names (uses default if None)
            limit_per_subreddit: Posts per subreddit
            time_filter: Time filter for 'top' sort
            sort_type: Sorting method
            
        Returns:
            Dictionary mapping subreddit names to lists of RedditPost objects
        """
        if subreddit_names is None:
            subreddit_names = self.config.get_subreddit_list()
        
        all_posts = {}
        all_comments = {}

        self.logger.info(f"Starting bulk scraping of {len(subreddit_names)} subreddits")
        start_time = time.time()
        
        for subreddit_name in subreddit_names:
            try:
                posts, comments = self.scrape_subreddit(
                    subreddit_name=subreddit_name,
                    limit=limit_per_subreddit,
                    time_filter=time_filter,
                    sort_type=sort_type
                )
                all_posts[subreddit_name] = posts
                all_comments[subreddit_name] = comments
                # Brief pause between subreddits
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Failed to scrape r/{subreddit_name}: {e}")
                all_posts[subreddit_name] = []
        
        total_posts = sum(len(posts) for posts in all_posts.values())
        total_comments = sum(len(comments) for comments in all_comments.values())
        elapsed_time = time.time() - start_time

        self.logger.info(f"Bulk scraping complete: {total_posts} total posts and {total_comments} total comments in {elapsed_time:.2f}s")
        self.logger.info(f"API requests made: {self.request_count}, Failed: {self.failed_requests}")
        
        return all_posts, all_comments
    
    def save_posts_to_csv(self, posts: List[RedditPost], filepath: str) -> None:
        """
        Save posts to CSV file
        
        Args:
            posts: List of RedditPost objects
            filepath: Output file path
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Convert posts to dictionaries
            post_dicts = [post.to_dict() for post in posts]
            
            # Save to CSV
            df = pd.DataFrame(post_dicts)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            self.logger.info(f"Saved {len(posts)} posts to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving posts to CSV: {e}")
    
    def save_posts_to_json(self, posts: List[RedditPost], filepath: str) -> None:
        """
        Save posts to JSON file
        
        Args:
            posts: List of RedditPost objects
            filepath: Output file path
        """
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Convert posts to dictionaries
            post_dicts = [post.to_dict() for post in posts]
            
            # Save to JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(post_dicts, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(posts)} posts to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving posts to JSON: {e}")
    
    def save_comments_to_csv(self, comments: List[RedditComment], filepath: str) -> None:
        """Save comments to CSV file."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame([c.to_dict() for c in comments])
            df.to_csv(filepath, index=False, encoding='utf-8')
            self.logger.info(f"Saved {len(comments)} comments to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving comments to CSV: {e}")


    def save_posts_and_comments(self, posts: List[RedditPost], comments: List[RedditComment],
                                base_filename: str) -> None:
        """Save both posts and comments to CSV files with a common base filename."""
        try:
            posts_file = f"{base_filename}_posts.csv"
            self.save_posts_to_csv(posts, posts_file)
            if comments:
                comments_file = f"{base_filename}_comments.csv"
                self.save_comments_to_csv(comments, comments_file)
        except Exception as e:
            self.logger.error(f"Error saving posts and comments: {e}")

    def save_post_and_comments_from_all_subreddits(self, all_posts: Dict[str, List[RedditPost]],
                                                  all_comments: Dict[str, List[RedditComment]],
                                                    base_dir: str) -> None:
        """Save posts and comments from multiple subreddits into separate files."""
        for subreddit, posts in all_posts.items():
            try:
                comments = all_comments.get(subreddit, [])
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_filename = os.path.join(base_dir, f"{subreddit}_{timestamp}")
                self.save_posts_and_comments(posts, comments, base_filename)
            except Exception as e:
                self.logger.error(f"Error saving posts and comments for {subreddit}: {e}")

    def get_collection_stats(self) -> Dict[str, float]:
        """
        Get collection statistics
        
        Returns:
            Dictionary with scraping metrics
        """
        total_req = max(self.request_count, 1)
        return {
            'total_requests': self.request_count,
            'comment_requests': self.comment_request_count,
            'failed_requests': self.failed_requests,
            'total_comments_collected': self.total_comments_collected,
            'skipped_comments': self.skipped_comments,
            'success_rate': (self.request_count - self.failed_requests) / total_req
        }



def main():
    """
    Example usage and testing
    """
    try:
        scraper = RedditScraper()

        posts, comments = scraper.scrape_multiple_subreddits(limit_per_subreddit=10)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent / 'raw_data'


        base = str(output_dir / f"{timestamp}")

        scraper.save_post_and_comments_from_all_subreddits(posts, comments, base)
        print(scraper.get_collection_stats())

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        if Config().DEBUG:
            print(traceback.format_exc())


if __name__ == "__main__":
    main()