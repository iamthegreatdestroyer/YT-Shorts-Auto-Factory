"""
Unit tests for trend scrapers.

Tests YouTube and Reddit scrapers with mocked HTTP responses.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.trend_analysis.models import (
    CompetitionLevel,
    TrendCategory,
    TrendData,
    TrendSource,
)
from src.trend_analysis.sources.reddit_scraper import RedditScraper
from src.trend_analysis.sources.youtube_trends import YouTubeTrendsScraper


@pytest.fixture
def mock_settings():
    """Create mock settings for scrapers."""
    settings = MagicMock()
    
    # Trends settings
    settings.trends.enable_youtube_trends = True
    settings.trends.enable_reddit = True
    settings.trends.reddit_client_id = ""
    settings.trends.reddit_client_secret.get_secret_value.return_value = ""
    settings.trends.reddit_subreddits = "technology,programming"
    settings.trends.subreddits_list = ["technology", "programming"]
    
    # YouTube settings
    settings.youtube.api_key.get_secret_value.return_value = ""
    
    return settings


class TestYouTubeTrendsScraper:
    """Tests for YouTubeTrendsScraper."""

    def test_init(self, mock_settings):
        """Test scraper initialization."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        assert scraper.source == TrendSource.YOUTUBE
        assert scraper.enabled is True
        assert scraper.has_api_key is False

    def test_enabled_when_disabled(self, mock_settings):
        """Test enabled property when disabled in settings."""
        mock_settings.trends.enable_youtube_trends = False
        scraper = YouTubeTrendsScraper(mock_settings)
        
        assert scraper.enabled is False

    def test_has_api_key_with_key(self, mock_settings):
        """Test has_api_key with valid key."""
        mock_settings.youtube.api_key.get_secret_value.return_value = "AIza1234567890abcdefghij"
        scraper = YouTubeTrendsScraper(mock_settings)
        
        assert scraper.has_api_key is True

    def test_extract_keywords_from_title(self, mock_settings):
        """Test keyword extraction from video titles."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        title = "Amazing AI Technology Breaks the Internet | Official Video"
        keywords = scraper._extract_keywords_from_title(title)
        
        assert len(keywords) > 0
        # Should extract meaningful keywords (may be lowercased or uppercased)
        keywords_lower = [kw.lower() for kw in keywords]
        assert any("ai" in kw or "technology" in kw or "amazing" in kw for kw in keywords_lower)
        # Should not include stop words
        assert "the" not in keywords_lower

    def test_extract_keywords_filters_noise(self, mock_settings):
        """Test that keyword extraction filters noise patterns."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        title = "Topic Name | Channel Name - Extra Info [Official]"
        keywords = scraper._extract_keywords_from_title(title)
        
        # Should filter out content after | and -
        assert "Channel" not in keywords
        assert "Extra" not in keywords
        # Should filter [brackets]
        assert "Official" not in keywords

    def test_map_youtube_category(self, mock_settings):
        """Test YouTube category ID mapping."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        assert scraper._map_youtube_category("20") == TrendCategory.GAMING
        assert scraper._map_youtube_category("28") == TrendCategory.SCIENCE
        assert scraper._map_youtube_category("999") == TrendCategory.GENERAL

    def test_parse_view_count(self, mock_settings):
        """Test view count parsing."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        assert scraper._parse_view_count("1,234 views") == 1234
        assert scraper._parse_view_count("1.5K views") == 1500
        assert scraper._parse_view_count("2.5M views") == 2500000
        assert scraper._parse_view_count("1B views") == 1000000000
        assert scraper._parse_view_count("") == 0
        assert scraper._parse_view_count("invalid") == 0

    @pytest.mark.asyncio
    async def test_fetch_disabled(self, mock_settings):
        """Test fetch when scraper is disabled."""
        mock_settings.trends.enable_youtube_trends = False
        scraper = YouTubeTrendsScraper(mock_settings)
        
        result = await scraper.safe_fetch()
        
        assert result.success is False
        assert "disabled" in result.error.lower()

    @pytest.mark.asyncio
    async def test_validate_credentials_no_key(self, mock_settings):
        """Test credential validation without API key."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        result = await scraper.validate_credentials()
        
        assert result is False


class TestRedditScraper:
    """Tests for RedditScraper."""

    def test_init(self, mock_settings):
        """Test scraper initialization."""
        scraper = RedditScraper(mock_settings)
        
        assert scraper.source == TrendSource.REDDIT
        assert scraper.enabled is True
        assert scraper.has_credentials is False

    def test_subreddits_property(self, mock_settings):
        """Test subreddits list property."""
        scraper = RedditScraper(mock_settings)
        
        assert scraper.subreddits == ["technology", "programming"]

    def test_enabled_when_disabled(self, mock_settings):
        """Test enabled property when disabled."""
        mock_settings.trends.enable_reddit = False
        scraper = RedditScraper(mock_settings)
        
        assert scraper.enabled is False

    def test_extract_keywords_from_title(self, mock_settings):
        """Test keyword extraction from Reddit post titles."""
        scraper = RedditScraper(mock_settings)
        
        title = "[Discussion] The future of AI in software development"
        keywords = scraper._extract_keywords_from_title(title)
        
        assert len(keywords) > 0
        # Should filter [tags]
        assert "Discussion" not in keywords
        # Should include meaningful words
        assert any("AI" in kw or "future" in kw.lower() for kw in keywords)

    def test_extract_hashtags(self, mock_settings):
        """Test hashtag extraction."""
        scraper = RedditScraper(mock_settings)
        
        hashtags = scraper._extract_hashtags(
            "Check out #Python and #coding tips",
            "Tutorial"
        )
        
        assert "Python" in hashtags
        assert "coding" in hashtags
        assert "Tutorial" in hashtags

    def test_subreddit_to_category(self, mock_settings):
        """Test subreddit to category mapping."""
        scraper = RedditScraper(mock_settings)
        
        assert scraper._subreddit_to_category("technology") == TrendCategory.TECHNOLOGY
        assert scraper._subreddit_to_category("gaming") == TrendCategory.GAMING
        assert scraper._subreddit_to_category("science") == TrendCategory.SCIENCE
        assert scraper._subreddit_to_category("randomsubreddit") == TrendCategory.GENERAL

    def test_calculate_post_score(self, mock_settings):
        """Test post score calculation."""
        scraper = RedditScraper(mock_settings)
        
        # High engagement post
        high_score = scraper._calculate_post_score(
            score=10000,
            upvote_ratio=0.95,
            num_comments=500,
            hours_old=2.0,
        )
        
        # Low engagement post
        low_score = scraper._calculate_post_score(
            score=50,
            upvote_ratio=0.60,
            num_comments=5,
            hours_old=48.0,
        )
        
        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1

    @pytest.mark.asyncio
    async def test_fetch_no_subreddits(self, mock_settings):
        """Test fetch when no subreddits configured."""
        mock_settings.trends.subreddits_list = []
        scraper = RedditScraper(mock_settings)
        
        result = await scraper.fetch_trends()
        
        assert result.success is False
        assert "subreddits" in result.error.lower()

    @pytest.mark.asyncio
    async def test_validate_credentials_no_creds(self, mock_settings):
        """Test credential validation without credentials."""
        scraper = RedditScraper(mock_settings)
        
        # Public API should work without credentials
        result = await scraper.validate_credentials()
        
        assert result is True


class TestBaseScraperMethods:
    """Tests for base scraper methods."""

    def test_estimate_competition_low_volume(self, mock_settings):
        """Test competition estimation for low volume."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        result = scraper._estimate_competition(volume=500, growth_rate=30)
        
        assert result == CompetitionLevel.LOW

    def test_estimate_competition_high_volume_low_growth(self, mock_settings):
        """Test competition estimation for saturated market."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        result = scraper._estimate_competition(volume=200000, growth_rate=10)
        
        assert result == CompetitionLevel.VERY_HIGH

    def test_estimate_competition_high_volume_high_growth(self, mock_settings):
        """Test competition estimation for growing market."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        result = scraper._estimate_competition(volume=150000, growth_rate=80)
        
        assert result == CompetitionLevel.HIGH

    def test_categorize_keyword_tech(self, mock_settings):
        """Test keyword categorization for tech."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        result = scraper._categorize_keyword("new AI software released")
        
        assert result == TrendCategory.TECHNOLOGY

    def test_categorize_keyword_gaming(self, mock_settings):
        """Test keyword categorization for gaming."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        result = scraper._categorize_keyword("best gaming setup 2025")
        
        assert result == TrendCategory.GAMING

    def test_categorize_keyword_unknown(self, mock_settings):
        """Test keyword categorization for unknown category."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        result = scraper._categorize_keyword("random topic here")
        
        assert result == TrendCategory.GENERAL

    def test_create_trend(self, mock_settings):
        """Test trend creation helper."""
        scraper = YouTubeTrendsScraper(mock_settings)
        
        trend = scraper._create_trend(
            keyword="test keyword",
            volume=1000,
            category=TrendCategory.TECHNOLOGY,
        )
        
        assert trend.keyword == "test keyword"
        assert trend.source == TrendSource.YOUTUBE
        assert trend.volume == 1000
        assert trend.category == TrendCategory.TECHNOLOGY
        assert trend.timestamp is not None
