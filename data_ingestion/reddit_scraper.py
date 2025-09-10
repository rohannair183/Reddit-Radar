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
from typing import List, Dict, Optional, Set
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
from utils.config import Config
from utils.logger import setup_logger


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

    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary"""
        return asdict(self)


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
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Reddit scraper with configuration
        
        Args:
            config: Configuration object with Reddit API credentials
        """
        self.config = config or Config()
        self.logger = setup_logger(__name__)
        self.reddit = None
        self._initialize_reddit_client()
        
        # Rate limiting and error tracking
        self.request_count = 0
        self.last_request_time = 0
        self.failed_requests = 0
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
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
    
    def _rate_limit(self) -> None:
        """Implement custom rate limiting (1 request per second)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < 1.0:  # Minimum 1 second between requests
            sleep_time = 1.0 - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
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
            retrieved_at=datetime.now(timezone.utc).isoformat()
        )
    
    def scrape_subreddit(self, 
                        subreddit_name: str, 
                        limit: int = 100,
                        time_filter: str = 'day',
                        sort_type: str = 'hot') -> List[RedditPost]:
        """
        Scrape posts from a specific subreddit
        
        Args:
            subreddit_name: Name of subreddit to scrape
            limit: Maximum number of posts to retrieve
            time_filter: Time filter ('hour', 'day', 'week', 'month', 'year', 'all')
            sort_type: Sort method ('hot', 'new', 'top', 'rising')
            
        Returns:
            List of RedditPost objects
        """
        posts = []
        
        try:
            self.logger.info(f"Scraping r/{subreddit_name} - {sort_type} posts (limit: {limit})")
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Select sorting method
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
            
            # Process submissions
            for submission in submissions:
                self._rate_limit()
                
                try:
                    post = self._extract_post_data(submission)
                    posts.append(post)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing submission {submission.id}: {e}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(posts)} posts from r/{subreddit_name}")
            
        except RedditAPIException as e:
            self.logger.error(f"Reddit API error for r/{subreddit_name}: {e}")
            self.failed_requests += 1
            
        except Exception as e:
            self.logger.error(f"Unexpected error scraping r/{subreddit_name}: {e}")
            self.failed_requests += 1
        
        return posts
    
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
            Dictionary mapping subreddit names to lists of posts
        """
        if subreddit_names is None:
            subreddit_names = self.DEFAULT_SUBREDDITS
        
        all_posts = {}
        
        self.logger.info(f"Starting bulk scraping of {len(subreddit_names)} subreddits")
        start_time = time.time()
        
        for subreddit_name in subreddit_names:
            try:
                posts = self.scrape_subreddit(
                    subreddit_name=subreddit_name,
                    limit=limit_per_subreddit,
                    time_filter=time_filter,
                    sort_type=sort_type
                )
                all_posts[subreddit_name] = posts
                
                # Brief pause between subreddits
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Failed to scrape r/{subreddit_name}: {e}")
                all_posts[subreddit_name] = []
        
        total_posts = sum(len(posts) for posts in all_posts.values())
        elapsed_time = time.time() - start_time
        
        self.logger.info(f"Bulk scraping complete: {total_posts} total posts in {elapsed_time:.2f}s")
        self.logger.info(f"API requests made: {self.request_count}, Failed: {self.failed_requests}")
        
        return all_posts
    
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
    
    def get_scraping_stats(self) -> Dict[str, int]:
        """
        Get scraping statistics
        
        Returns:
            Dictionary with scraping metrics
        """
        return {
            'total_requests': self.request_count,
            'failed_requests': self.failed_requests,
            'success_rate': (self.request_count - self.failed_requests) / max(self.request_count, 1)
        }


def main():
    """
    Example usage and testing
    """
    try:
        # Initialize scraper
        scraper = RedditScraper()
        
        # Test single subreddit
        posts = scraper.scrape_subreddit('programming', limit=50)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent / 'raw_data'
        
        scraper.save_posts_to_csv(posts, f"{output_dir}/programming_{timestamp}.csv")
        scraper.save_posts_to_json(posts, f"{output_dir}/programming_{timestamp}.json")
        
        # Print stats
        stats = scraper.get_scraping_stats()
        print(f"Scraping completed: {stats}")
        
    except Exception as e:
        logging.error(f"Error in main execution: {e}")


if __name__ == "__main__":
    main()