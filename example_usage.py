"""
Reddit Radar - Example Usage
============================

Demonstrates how to use the Reddit scraper for different scenarios.

Author: Rohan Nair
Date: 20250910
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion.reddit_scraper import RedditScraper
from utils.config import Config
from utils.logger import setup_logger


def example_single_subreddit():
    """Example: Scrape a single subreddit"""
    logger = setup_logger('example_single')
    logger.info("=== Single Subreddit Scraping Example ===")
    
    # Initialize scraper
    scraper = RedditScraper()
    
    # Scrape programming subreddit
    posts = scraper.scrape_subreddit(
        subreddit_name='programming',
        limit=50,
        sort_type='hot'
    )
    
    logger.info(f"Retrieved {len(posts)} posts from r/programming")
    
    # Display first few posts
    for i, post in enumerate(posts[:3], 1):
        logger.info(f"Post {i}: {post.title[:80]}...")
        logger.info(f"  Score: {post.score}, Comments: {post.num_comments}")
    
    return posts


def example_multiple_subreddits():
    """Example: Scrape multiple subreddits"""
    logger = setup_logger('example_multiple')
    logger.info("=== Multiple Subreddits Scraping Example ===")
    
    scraper = RedditScraper()
    
    # Define target subreddits
    subreddits = ['python', 'javascript', 'MachineLearning', 'webdev']
    
    # Scrape all subreddits
    all_posts = scraper.scrape_multiple_subreddits(
        subreddit_names=subreddits,
        limit_per_subreddit=25,
        sort_type='hot'
    )
    
    # Summary
    total_posts = sum(len(posts) for posts in all_posts.values())
    logger.info(f"Retrieved {total_posts} total posts from {len(subreddits)} subreddits")
    
    for subreddit, posts in all_posts.items():
        logger.info(f"  r/{subreddit}: {len(posts)} posts")
    
    return all_posts


def example_trending_topics():
    """Example: Find trending topics by scraping 'top' posts from last week"""
    logger = setup_logger('example_trending')
    logger.info("=== Trending Topics Example ===")
    
    scraper = RedditScraper()
    
    # Get top posts from the past week across tech subreddits
    trending_subreddits = ['technology', 'programming', 'artificial']
    
    trending_posts = {}
    for subreddit in trending_subreddits:
        posts = scraper.scrape_subreddit(
            subreddit_name=subreddit,
            limit=20,
            sort_type='top',
            time_filter='week'
        )
        trending_posts[subreddit] = posts
    
    # Analyze trending topics
    logger.info("Top trending posts this week:")
    for subreddit, posts in trending_posts.items():
        if posts:
            top_post = max(posts, key=lambda p: p.score)
            logger.info(f"r/{subreddit}: '{top_post.title[:60]}...' (Score: {top_post.score})")
    
    return trending_posts


def example_save_data():
    """Example: Save scraped data to files"""
    logger = setup_logger('example_save')
    logger.info("=== Data Saving Example ===")
    
    scraper = RedditScraper()
    
    # Scrape some posts
    posts = scraper.scrape_subreddit('datascience', limit=30)
    
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path('data_ingestion/raw_data')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save in different formats
    csv_file = output_dir / f'datascience_{timestamp}.csv'
    json_file = output_dir / f'datascience_{timestamp}.json'
    
    scraper.save_posts_to_csv(posts, str(csv_file))
    scraper.save_posts_to_json(posts, str(json_file))
    
    logger.info(f"Data saved to:")
    logger.info(f"  CSV: {csv_file}")
    logger.info(f"  JSON: {json_file}")
    
    return posts


def example_custom_filtering():
    """Example: Custom filtering and analysis of scraped posts"""
    logger = setup_logger('example_filtering')
    logger.info("=== Custom Filtering Example ===")
    
    scraper = RedditScraper()
    
    # Scrape posts
    posts = scraper.scrape_subreddit('MachineLearning', limit=100)
    
    # Filter high-engagement posts
    high_engagement = [p for p in posts if p.score > 50 and p.num_comments > 10]
    logger.info(f"High engagement posts: {len(high_engagement)}/{len(posts)}")
    
    # Filter by keywords (simple example)
    ai_keywords = ['GPT', 'transformer', 'neural', 'AI', 'artificial intelligence', 'LLM']
    ai_posts = []
    for post in posts:
        title_text = (post.title + ' ' + post.selftext).lower()
        if any(keyword.lower() in title_text for keyword in ai_keywords):
            ai_posts.append(post)
    
    logger.info(f"AI-related posts: {len(ai_posts)}")
    
    # Display top AI posts
    ai_posts_sorted = sorted(ai_posts, key=lambda p: p.score, reverse=True)
    for i, post in enumerate(ai_posts_sorted[:3], 1):
        logger.info(f"Top AI Post {i}: {post.title[:60]}... (Score: {post.score})")
    
    return high_engagement, ai_posts


def example_error_handling():
    """Example: Demonstrate error handling with invalid subreddit"""
    logger = setup_logger('example_errors')
    logger.info("=== Error Handling Example ===")
    
    scraper = RedditScraper()
    
    # Try to scrape non-existent subreddit
    invalid_posts = scraper.scrape_subreddit('this_subreddit_definitely_does_not_exist_12345')
    logger.info(f"Invalid subreddit returned: {len(invalid_posts)} posts")
    
    # Try to scrape private/banned subreddit (example)
    # Note: Replace with actual private subreddit name if testing
    private_posts = scraper.scrape_subreddit('private_test_subreddit', limit=10)
    logger.info(f"Private subreddit returned: {len(private_posts)} posts")
    
    # Show scraping statistics
    stats = scraper.get_scraping_stats()
    logger.info(f"Scraping stats: {stats}")


def example_complete_workflow():
    """Example: Complete workflow from scraping to saving"""
    logger = setup_logger('example_workflow')
    logger.info("=== Complete Workflow Example ===")
    
    try:
        # Initialize
        config = Config()
        scraper = RedditScraper(config)
        
        # Define target subreddits for tech trend analysis
        tech_subreddits = [
            'programming', 'Python', 'javascript', 'MachineLearning',
            'webdev', 'technology', 'artificial', 'datascience'
        ]
        
        logger.info(f"Starting scraping workflow for {len(tech_subreddits)} subreddits")
        
        # Scrape all subreddits
        all_posts = scraper.scrape_multiple_subreddits(
            subreddit_names=tech_subreddits,
            limit_per_subreddit=50,
            sort_type='hot'
        )
        
        # Flatten all posts
        all_posts_flat = []
        for subreddit_posts in all_posts.values():
            all_posts_flat.extend(subreddit_posts)
        
        logger.info(f"Total posts collected: {len(all_posts_flat)}")
        
        # Basic analysis
        if all_posts_flat:
            avg_score = sum(p.score for p in all_posts_flat) / len(all_posts_flat)
            avg_comments = sum(p.num_comments for p in all_posts_flat) / len(all_posts_flat)
            
            logger.info(f"Average score: {avg_score:.1f}")
            logger.info(f"Average comments: {avg_comments:.1f}")
            
            # Find top posts overall
            top_posts = sorted(all_posts_flat, key=lambda p: p.score, reverse=True)[:5]
            logger.info("Top 5 posts overall:")
            for i, post in enumerate(top_posts, 1):
                logger.info(f"  {i}. r/{post.subreddit}: {post.title[:50]}... (Score: {post.score})")
        
        # Save data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('data_ingestion/raw_data')
        
        # Save individual subreddit files
        for subreddit, posts in all_posts.items():
            if posts:
                filename = f"{subreddit}_{timestamp}.csv"
                scraper.save_posts_to_csv(posts, str(output_dir / filename))
        
        # Save combined file
        combined_filename = f"tech_trends_{timestamp}.csv"
        scraper.save_posts_to_csv(all_posts_flat, str(output_dir / combined_filename))
        
        # Final statistics
        stats = scraper.get_scraping_stats()
        logger.info(f"Workflow complete. Final stats: {stats}")
        
        return all_posts_flat
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        raise


def main():
    """Run all examples"""
    logger = setup_logger('main')
    
    print("Reddit Radar - Scraper Examples")
    print("=" * 40)
    
    # Check if .env file exists
    if not Path('.env').exists():
        logger.error("No .env file found. Please create one with your Reddit API credentials.")
        logger.info("Run 'python utils/config.py' to create a template .env file.")
        return
    
    try:
        # Run examples
        logger.info("Running example 1: Single subreddit")
        example_single_subreddit()
        
        logger.info("\nRunning example 2: Multiple subreddits")
        example_multiple_subreddits()
        
        logger.info("\nRunning example 3: Trending topics")
        example_trending_topics()
        
        logger.info("\nRunning example 4: Save data")
        example_save_data()
        
        logger.info("\nRunning example 5: Custom filtering")
        example_custom_filtering()
        
        logger.info("\nRunning example 6: Error handling")
        example_error_handling()
        
        logger.info("\nRunning example 7: Complete workflow")
        example_complete_workflow()
        
        logger.info("\nAll examples completed successfully!")
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        logger.error("Make sure you have valid Reddit API credentials in your .env file")


if __name__ == "__main__":
    main()