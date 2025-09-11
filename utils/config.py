"""
Reddit Radar - Configuration Management
======================================

Handles loading and validation of configuration from environment variables.

Author: Reddit Radar Team
Date: 2025
"""

import os
from typing import Optional, List
from dotenv import load_dotenv
import logging


class Config:
    """Configuration class for Reddit Radar application"""
    
    def __init__(self, env_file: str = '.env'):
        """
        Initialize configuration by loading environment variables
        
        Args:
            env_file: Path to environment file (default: .env)
        """
        # Load environment variables from .env file
        load_dotenv(env_file)
        # General Configuration
        self.DEBUG = os.getenv('DEBUG').lower() == 'true'
        # Reddit API Configuration
        self.REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
        self.REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
        self.REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'RedditRadar:v1.0 (by /u/YourUsername)')
        
        # Database Configuration
        self.DUCKDB_PATH = os.getenv('DUCKDB_PATH', 'duckdb/reddit_radar.db')
        
        # Data Processing Configuration
        self.RAW_DATA_DIR = os.getenv('RAW_DATA_DIR', 'data_ingestion/raw_data')
        self.PROCESSED_DATA_DIR = os.getenv('PROCESSED_DATA_DIR', 'data_processing/processed_data')
        
        # Scraping Configuration
        self.DEFAULT_POSTS_LIMIT = int(os.getenv('DEFAULT_POSTS_LIMIT', '100'))
        self.RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', '1.0'))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/reddit_radar.log')
        
        # Validate required configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate that required configuration is present"""
        required_vars = {
            'REDDIT_CLIENT_ID': self.REDDIT_CLIENT_ID,
            'REDDIT_CLIENT_SECRET': self.REDDIT_CLIENT_SECRET,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please check your .env file."
            )
    
    def get_subreddit_list(self, env_var: str = 'TARGET_SUBREDDITS') -> List[str]:
        """
        Get list of subreddits from environment variable
        
        Args:
            env_var: Environment variable name containing comma-separated subreddits
            
        Returns:
            List of subreddit names
        """
        subreddits_str = os.getenv(env_var, '')
        if subreddits_str:
            return [sub.strip() for sub in subreddits_str.split(',')]
        return []
    
    def __repr__(self) -> str:
        """String representation of config (excluding secrets)"""
        return (
            f"Config(user_agent='{self.REDDIT_USER_AGENT}', "
            f"duckdb_path='{self.DUCKDB_PATH}', "
            f"log_level='{self.LOG_LEVEL}')"
        )

class CommentCollectionConfig:
    """Configuration for comment collection"""
    
    def __init__(self, env_file: str = '.env'):
        # Load environment variables from .env file
        load_dotenv(env_file)

        self.MAX_COMMENTS_PER_POST = int(os.getenv('MAX_COMMENTS_PER_POST'))
        self.MIN_COMMENT_SCORE = int(os.getenv('MIN_COMMENT_SCORE'))
        self.MAX_COMMENT_DEPTH = int(os.getenv('MAX_COMMENT_DEPTH'))
        self.INCLUDE_CONTROVERSIAL = os.getenv('INCLUDE_CONTROVERSIAL').lower() == 'true'
        self.SORT_COMMENT_BY = os.getenv('COMMENT_SORT_BY')  # Options: 'top', 'new', 'controversial', etc.
        self.COLLECT_REPLIES = os.getenv('COLLECT_REPLIES').lower() == 'true'
        self.SKIP_REPLIES = os.getenv('SKIP_REPLIES').lower() == 'true'
        self.SKIP_DELETED = os.getenv('SKIP_DELETED').lower() == 'true'
        self.SKIP_AUTOMOD = os.getenv('SKIP_AUTOMOD').lower() == 'true'

    def __repr__(self) -> str:
        """String representation of comment collection config"""
        return (
            f"CommentCollectionConfig(max_comments_per_post={self.MAX_COMMENTS_PER_POST}, "
            f"min_comment_score={self.MIN_COMMENT_SCORE}, "
            f"max_comment_depth={self.MAX_COMMENT_DEPTH}, "
            f"include_controversial={self.INCLUDE_CONTROVERSIAL}, "
            f"sort_comment_by='{self.SORT_COMMENT_BY}', "
            f"collect_replies={self.COLLECT_REPLIES}, "
            f"skip_replies={self.SKIP_REPLIES}, "
            f"skip_deleted={self.SKIP_DELETED}, "
            f"skip_automod={self.SKIP_AUTOMOD})"
        )


# Example .env file template
ENV_TEMPLATE = """
# Reddit API Credentials
# Get these from https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=RedditRadar:v1.0 (by /u/YourUsername)

# Target Subreddits (comma-separated)
TARGET_SUBREDDITS=programming,MachineLearning,webdev,javascript,Python,technology

# Data Storage Paths
DUCKDB_PATH=duckdb/reddit_radar.db
RAW_DATA_DIR=data_ingestion/raw_data
PROCESSED_DATA_DIR=data_processing/processed_data

# Scraping Configuration
DEFAULT_POSTS_LIMIT=100
RATE_LIMIT_DELAY=1.0

# Comment Collection Configuration
COLLECT_COMMENTS=true
MAX_COMMENTS_PER_POST=50
MIN_COMMENT_SCORE=1
MAX_COMMENT_DEPTH=3
COMMENT_SORT_BY=top
SKIP_AUTOMOD_COMMENTS=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/reddit_radar.log
"""


# def create_env_template(filepath: str = '.env.example') -> None:
#     """
#     Create an example .env file template
    
#     Args:
#         filepath: Path where to create the template file
#     """
#     with open(filepath, 'w') as f:
#         f.write(ENV_TEMPLATE.strip())
    
#     print(f"Created environment template at {filepath}")
#     print("Copy this to '.env' and fill in your Reddit API credentials")


# if __name__ == "__main__":
#     # Create example .env file
#     create_env_template()