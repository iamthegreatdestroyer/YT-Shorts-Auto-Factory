"""
Trend sources - Individual platform scrapers and API clients.

Contains implementations for:
- YouTubeTrendsScraper: Scrapes YouTube trending page and uses API
- RedditScraper: Fetches hot posts from configured subreddits
"""

from src.trend_analysis.sources.reddit_scraper import RedditScraper
from src.trend_analysis.sources.youtube_trends import YouTubeTrendsScraper

__all__ = [
    "YouTubeTrendsScraper",
    "RedditScraper",
]
