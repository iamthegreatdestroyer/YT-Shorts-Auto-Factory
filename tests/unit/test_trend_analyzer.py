"""
Unit tests for TrendAnalyzer.

Tests the main trend analysis orchestrator including
scoring, selection, and caching functionality.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.trend_analysis.analyzer import TrendAnalyzer
from src.trend_analysis.cache import TrendCache
from src.trend_analysis.models import (
    CompetitionLevel,
    ScrapingResult,
    TrendCategory,
    TrendData,
    TrendSource,
)


@pytest.fixture
def mock_settings():
    """Create mock settings for analyzer."""
    settings = MagicMock()
    
    # Trends settings
    settings.trends.enable_youtube_trends = True
    settings.trends.enable_reddit = True
    settings.trends.reddit_client_id = ""
    settings.trends.reddit_client_secret.get_secret_value.return_value = ""
    settings.trends.reddit_subreddits = "technology"
    settings.trends.subreddits_list = ["technology"]
    settings.trends.cache_ttl_minutes = 30
    settings.trends.max_trends_per_source = 10
    settings.trends.min_trend_score = 0.3
    
    # YouTube settings
    settings.youtube.api_key.get_secret_value.return_value = ""
    
    # Content settings
    settings.content.niche = "technology"
    
    # Storage settings
    settings.storage.cache_dir = Path(tempfile.mkdtemp())
    
    return settings


@pytest.fixture
def sample_trends():
    """Create sample trends for testing."""
    return [
        TrendData(
            keyword="AI breakthrough",
            source=TrendSource.YOUTUBE,
            score=0.8,
            volume=100000,
            growth_rate=50.0,
            competition=CompetitionLevel.MEDIUM,
            category=TrendCategory.TECHNOLOGY,
        ),
        TrendData(
            keyword="New gaming console",
            source=TrendSource.REDDIT,
            score=0.7,
            volume=50000,
            growth_rate=80.0,
            competition=CompetitionLevel.HIGH,
            category=TrendCategory.GAMING,
        ),
        TrendData(
            keyword="Space discovery",
            source=TrendSource.YOUTUBE,
            score=0.6,
            volume=30000,
            growth_rate=40.0,
            competition=CompetitionLevel.LOW,
            category=TrendCategory.SCIENCE,
        ),
    ]


class TestTrendAnalyzer:
    """Tests for TrendAnalyzer class."""

    def test_init(self, mock_settings):
        """Test analyzer initialization."""
        analyzer = TrendAnalyzer(mock_settings)
        
        assert analyzer.settings == mock_settings
        assert TrendSource.YOUTUBE in analyzer._scrapers
        assert TrendSource.REDDIT in analyzer._scrapers

    def test_normalize_keyword(self, mock_settings):
        """Test keyword normalization."""
        analyzer = TrendAnalyzer(mock_settings)
        
        assert analyzer._normalize_keyword("Test Keyword!") == "test keyword"
        assert analyzer._normalize_keyword("  AI  Technology  ") == "ai technology"
        assert analyzer._normalize_keyword("Tech-News") == "technews"

    def test_calculate_score_high_volume(self, mock_settings):
        """Test score calculation for high volume trend."""
        analyzer = TrendAnalyzer(mock_settings)
        
        trend = TrendData(
            keyword="popular topic",
            source=TrendSource.YOUTUBE,
            volume=1000000,
            growth_rate=100.0,
            competition=CompetitionLevel.LOW,
            category=TrendCategory.TECHNOLOGY,
            timestamp=datetime.utcnow(),
        )
        
        score = analyzer._calculate_score(trend)
        
        assert 0.5 <= score <= 1.0  # Should be high due to good metrics

    def test_calculate_score_low_volume(self, mock_settings):
        """Test score calculation for low volume trend."""
        analyzer = TrendAnalyzer(mock_settings)
        
        trend = TrendData(
            keyword="obscure topic",
            source=TrendSource.YOUTUBE,
            volume=100,
            growth_rate=10.0,
            competition=CompetitionLevel.VERY_HIGH,
            category=TrendCategory.GENERAL,
            timestamp=datetime.utcnow() - timedelta(hours=48),
        )
        
        score = analyzer._calculate_score(trend)
        
        assert 0 <= score <= 0.5  # Should be lower due to poor metrics

    def test_calculate_score_viral_bonus(self, mock_settings):
        """Test that viral trends get a score bonus."""
        analyzer = TrendAnalyzer(mock_settings)
        
        trend = TrendData(
            keyword="viral topic",
            source=TrendSource.YOUTUBE,
            volume=50000,
            growth_rate=50.0,
            competition=CompetitionLevel.MEDIUM,
            category=TrendCategory.TECHNOLOGY,
            is_viral=True,
        )
        
        trend_non_viral = TrendData(
            keyword="normal topic",
            source=TrendSource.YOUTUBE,
            volume=50000,
            growth_rate=50.0,
            competition=CompetitionLevel.MEDIUM,
            category=TrendCategory.TECHNOLOGY,
            is_viral=False,
        )
        
        viral_score = analyzer._calculate_score(trend)
        normal_score = analyzer._calculate_score(trend_non_viral)
        
        assert viral_score > normal_score

    def test_calculate_niche_relevance_direct_match(self, mock_settings):
        """Test niche relevance for direct keyword match."""
        analyzer = TrendAnalyzer(mock_settings)
        
        trend = TrendData(
            keyword="technology trends 2025",
            source=TrendSource.YOUTUBE,
        )
        
        relevance = analyzer._calculate_niche_relevance(trend)
        
        assert relevance == 1.0

    def test_calculate_niche_relevance_category_match(self, mock_settings):
        """Test niche relevance for category match."""
        analyzer = TrendAnalyzer(mock_settings)
        
        trend = TrendData(
            keyword="random keyword",
            source=TrendSource.YOUTUBE,
            category=TrendCategory.TECHNOLOGY,
        )
        
        relevance = analyzer._calculate_niche_relevance(trend)
        
        assert relevance == 0.8

    def test_calculate_niche_relevance_no_match(self, mock_settings):
        """Test niche relevance for unrelated content."""
        analyzer = TrendAnalyzer(mock_settings)
        
        trend = TrendData(
            keyword="cooking recipes",
            source=TrendSource.YOUTUBE,
            category=TrendCategory.LIFESTYLE,
        )
        
        relevance = analyzer._calculate_niche_relevance(trend)
        
        assert relevance == 0.2  # Baseline

    def test_select_best_trend(self, mock_settings, sample_trends):
        """Test selecting best trend."""
        analyzer = TrendAnalyzer(mock_settings)
        
        # Score the trends first
        for trend in sample_trends:
            trend.score = analyzer._calculate_score(trend)
        
        selected = analyzer.select_best_trend(sample_trends)
        
        assert selected is not None
        assert selected.previously_used is True

    def test_select_best_trend_empty_list(self, mock_settings):
        """Test selection with empty trend list."""
        analyzer = TrendAnalyzer(mock_settings)
        
        selected = analyzer.select_best_trend([])
        
        assert selected is None

    def test_select_best_trend_excludes_recent(self, mock_settings, sample_trends):
        """Test that recently used trends are excluded."""
        analyzer = TrendAnalyzer(mock_settings)
        
        # Mark first trend as used
        analyzer._mark_trend_used(sample_trends[0])
        
        # Score the trends
        for trend in sample_trends:
            trend.score = analyzer._calculate_score(trend)
        
        selected = analyzer.select_best_trend(sample_trends)
        
        # Should not select the first one (recently used)
        assert selected != sample_trends[0]

    def test_mark_trend_used(self, mock_settings, sample_trends):
        """Test marking trend as used."""
        analyzer = TrendAnalyzer(mock_settings)
        
        trend = sample_trends[0]
        analyzer._mark_trend_used(trend)
        
        assert trend.previously_used is True
        
        keyword_key = analyzer._normalize_keyword(trend.keyword)
        assert keyword_key in analyzer._used_trends

    def test_aggregate_results_deduplication(self, mock_settings):
        """Test that aggregation deduplicates trends."""
        analyzer = TrendAnalyzer(mock_settings)
        
        results = [
            ScrapingResult(
                success=True,
                source=TrendSource.YOUTUBE,
                trends=[
                    TrendData(keyword="AI News", source=TrendSource.YOUTUBE, volume=1000),
                    TrendData(keyword="Tech Update", source=TrendSource.YOUTUBE, volume=500),
                ],
            ),
            ScrapingResult(
                success=True,
                source=TrendSource.REDDIT,
                trends=[
                    TrendData(keyword="ai news", source=TrendSource.REDDIT, volume=800),  # Duplicate
                    TrendData(keyword="Gaming Release", source=TrendSource.REDDIT, volume=600),
                ],
            ),
        ]
        
        aggregated = analyzer._aggregate_results(results)
        
        # Should have 3 unique trends (AI News deduplicated)
        assert len(aggregated) == 3
        
        # Check that the higher volume one was kept
        ai_trend = next(t for t in aggregated if "ai" in t.keyword.lower())
        assert ai_trend.volume == 1000

    def test_get_niche_keywords(self, mock_settings):
        """Test getting niche keywords."""
        analyzer = TrendAnalyzer(mock_settings)
        
        keywords = analyzer._get_niche_keywords("tech")
        
        assert "ai" in keywords
        assert "software" in keywords
        assert "programming" in keywords

    @pytest.mark.asyncio
    async def test_get_trending_topics_uses_cache(self, mock_settings, sample_trends):
        """Test that cached trends are used when available."""
        analyzer = TrendAnalyzer(mock_settings)
        
        # Pre-populate caches for both sources (as get_combined_trends checks these)
        analyzer._cache.save_trends(sample_trends[:2], TrendSource.YOUTUBE)
        analyzer._cache.save_trends(sample_trends[2:], TrendSource.REDDIT)
        
        # Should use cache, not fetch
        with patch.object(analyzer, '_fetch_all_sources') as mock_fetch:
            trends = await analyzer.get_trending_topics()
            
            # Should not have called fetch
            mock_fetch.assert_not_called()
            
            # Should have returned cached trends
            assert len(trends) >= 2  # At least some trends from cache

    @pytest.mark.asyncio
    async def test_close(self, mock_settings):
        """Test cleanup of scraper connections."""
        analyzer = TrendAnalyzer(mock_settings)
        
        # Should not raise
        await analyzer.close()


class TestTrendCache:
    """Tests for TrendCache class."""

    @pytest.fixture
    def cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_init(self, cache_dir):
        """Test cache initialization."""
        cache = TrendCache(cache_dir, default_ttl_minutes=60)
        
        assert cache.cache_dir == cache_dir
        assert cache.cache_dir.exists()

    def test_save_and_get_trends(self, cache_dir, sample_trends):
        """Test saving and retrieving trends."""
        cache = TrendCache(cache_dir)
        
        # Save trends
        result = cache.save_trends(sample_trends, TrendSource.YOUTUBE)
        assert result is True
        
        # Retrieve trends
        retrieved = cache.get_trends(TrendSource.YOUTUBE)
        
        assert retrieved is not None
        assert len(retrieved) == len(sample_trends)
        assert retrieved[0].keyword == sample_trends[0].keyword

    def test_get_trends_expired(self, cache_dir, sample_trends):
        """Test that expired cache returns None."""
        cache = TrendCache(cache_dir, default_ttl_minutes=0)  # Immediate expiry
        
        cache.save_trends(sample_trends, TrendSource.YOUTUBE)
        
        # Wait a moment for expiry
        import time
        time.sleep(0.1)
        
        # Should return None due to expiry
        retrieved = cache.get_trends(TrendSource.YOUTUBE)
        
        assert retrieved is None

    def test_get_trends_not_found(self, cache_dir):
        """Test cache miss when file doesn't exist."""
        cache = TrendCache(cache_dir)
        
        retrieved = cache.get_trends(TrendSource.YOUTUBE)
        
        assert retrieved is None

    def test_invalidate_source(self, cache_dir, sample_trends):
        """Test invalidating specific source cache."""
        cache = TrendCache(cache_dir)
        
        cache.save_trends(sample_trends, TrendSource.YOUTUBE)
        cache.save_trends(sample_trends, TrendSource.REDDIT)
        
        # Invalidate YouTube only
        cache.invalidate(TrendSource.YOUTUBE)
        
        assert cache.get_trends(TrendSource.YOUTUBE) is None
        assert cache.get_trends(TrendSource.REDDIT) is not None

    def test_invalidate_all(self, cache_dir, sample_trends):
        """Test invalidating all caches."""
        cache = TrendCache(cache_dir)
        
        cache.save_trends(sample_trends, TrendSource.YOUTUBE)
        cache.save_trends(sample_trends, TrendSource.REDDIT)
        
        # Invalidate all
        cache.invalidate()
        
        assert cache.get_trends(TrendSource.YOUTUBE) is None
        assert cache.get_trends(TrendSource.REDDIT) is None

    def test_get_cache_stats(self, cache_dir, sample_trends):
        """Test getting cache statistics."""
        cache = TrendCache(cache_dir)
        
        cache.save_trends(sample_trends, TrendSource.YOUTUBE)
        
        stats = cache.get_cache_stats()
        
        assert "cache_dir" in stats
        assert "total_trends" in stats
        assert stats["total_trends"] == len(sample_trends)
        assert TrendSource.YOUTUBE.value in stats["sources"]

    def test_get_combined_trends(self, cache_dir, sample_trends):
        """Test getting combined trends from multiple sources."""
        cache = TrendCache(cache_dir)
        
        youtube_trends = sample_trends[:2]
        reddit_trends = sample_trends[1:]  # Overlapping trend
        
        cache.save_trends(youtube_trends, TrendSource.YOUTUBE)
        cache.save_trends(reddit_trends, TrendSource.REDDIT)
        
        combined = cache.get_combined_trends()
        
        # Should deduplicate
        assert len(combined) <= len(youtube_trends) + len(reddit_trends)
