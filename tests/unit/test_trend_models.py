"""
Unit tests for trend analysis models.

Tests the data models used for trend representation,
including TrendData, TrendBatch, and ScrapingResult.
"""

from datetime import datetime, timedelta

import pytest

from src.trend_analysis.models import (
    CompetitionLevel,
    ScrapingResult,
    TrendBatch,
    TrendCategory,
    TrendData,
    TrendSource,
)


class TestTrendData:
    """Tests for TrendData model."""

    def test_create_minimal(self):
        """Test creating TrendData with minimal fields."""
        trend = TrendData(
            keyword="test keyword",
            source=TrendSource.YOUTUBE,
        )
        
        assert trend.keyword == "test keyword"
        assert trend.source == TrendSource.YOUTUBE
        assert trend.score == 0.0
        assert trend.volume == 0
        assert trend.competition == CompetitionLevel.MEDIUM
        assert trend.category == TrendCategory.GENERAL

    def test_create_full(self):
        """Test creating TrendData with all fields."""
        now = datetime.utcnow()
        trend = TrendData(
            keyword="AI technology",
            source=TrendSource.REDDIT,
            score=0.85,
            volume=50000,
            growth_rate=150.0,
            competition=CompetitionLevel.LOW,
            category=TrendCategory.TECHNOLOGY,
            related_keywords=["machine learning", "GPT"],
            hashtags=["AI", "tech"],
            timestamp=now,
            url="https://example.com",
            description="Test trend",
            is_viral=True,
            is_evergreen=False,
        )
        
        assert trend.keyword == "AI technology"
        assert trend.source == TrendSource.REDDIT
        assert trend.score == 0.85
        assert trend.volume == 50000
        assert trend.growth_rate == 150.0
        assert trend.competition == CompetitionLevel.LOW
        assert trend.category == TrendCategory.TECHNOLOGY
        assert len(trend.related_keywords) == 2
        assert trend.is_viral is True

    def test_age_hours_property(self):
        """Test age_hours computed property."""
        old_time = datetime.utcnow() - timedelta(hours=5)
        trend = TrendData(
            keyword="test",
            source=TrendSource.YOUTUBE,
            timestamp=old_time,
        )
        
        assert 4.9 <= trend.age_hours <= 5.1

    def test_freshness_score_new(self):
        """Test freshness_score for new trends."""
        trend = TrendData(
            keyword="test",
            source=TrendSource.YOUTUBE,
            timestamp=datetime.utcnow(),
        )
        
        assert trend.freshness_score == 1.0

    def test_freshness_score_old(self):
        """Test freshness_score for old trends."""
        old_time = datetime.utcnow() - timedelta(hours=48)
        trend = TrendData(
            keyword="test",
            source=TrendSource.YOUTUBE,
            timestamp=old_time,
        )
        
        # 48 hours is at the boundary - could be 0.3 or 0.1 depending on exact timing
        assert trend.freshness_score <= 0.3

    def test_to_dict(self):
        """Test serialization to dictionary."""
        trend = TrendData(
            keyword="test",
            source=TrendSource.YOUTUBE,
            category=TrendCategory.TECHNOLOGY,
            competition=CompetitionLevel.LOW,
        )
        
        data = trend.to_dict()
        
        assert data["keyword"] == "test"
        assert data["source"] == "youtube"
        assert data["category"] == "technology"
        assert data["competition"] == "low"
        assert "timestamp" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "keyword": "test keyword",
            "source": "reddit",
            "category": "gaming",
            "competition": "high",
            "score": 0.75,
            "volume": 1000,
            "timestamp": "2025-01-12T10:00:00",
        }
        
        trend = TrendData.from_dict(data)
        
        assert trend.keyword == "test keyword"
        assert trend.source == TrendSource.REDDIT
        assert trend.category == TrendCategory.GAMING
        assert trend.competition == CompetitionLevel.HIGH
        assert trend.score == 0.75

    def test_keyword_validation_min_length(self):
        """Test keyword minimum length validation."""
        with pytest.raises(ValueError):
            TrendData(
                keyword="",  # Empty string
                source=TrendSource.YOUTUBE,
            )


class TestTrendBatch:
    """Tests for TrendBatch model."""

    def test_create_batch(self):
        """Test creating a trend batch."""
        trends = [
            TrendData(keyword=f"trend{i}", source=TrendSource.YOUTUBE)
            for i in range(5)
        ]
        
        batch = TrendBatch(
            trends=trends,
            source=TrendSource.YOUTUBE,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        assert batch.count == 5
        assert batch.source == TrendSource.YOUTUBE
        assert not batch.is_expired

    def test_batch_expired(self):
        """Test batch expiration check."""
        batch = TrendBatch(
            trends=[],
            source=TrendSource.YOUTUBE,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        
        assert batch.is_expired is True

    def test_get_top_n(self):
        """Test getting top N trends by score."""
        trends = [
            TrendData(keyword=f"trend{i}", source=TrendSource.YOUTUBE, score=i * 0.1)
            for i in range(10)
        ]
        
        batch = TrendBatch(
            trends=trends,
            source=TrendSource.YOUTUBE,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        top_3 = batch.get_top_n(3)
        
        assert len(top_3) == 3
        assert top_3[0].score == pytest.approx(0.9)
        assert top_3[1].score == pytest.approx(0.8)
        assert top_3[2].score == pytest.approx(0.7)


class TestScrapingResult:
    """Tests for ScrapingResult model."""

    def test_successful_result(self):
        """Test creating a successful scraping result."""
        trends = [
            TrendData(keyword="test", source=TrendSource.REDDIT)
        ]
        
        result = ScrapingResult(
            success=True,
            source=TrendSource.REDDIT,
            trends=trends,
            duration_seconds=1.5,
        )
        
        assert result.success is True
        assert result.count == 1
        assert result.error is None
        assert result.duration_seconds == 1.5

    def test_failed_result(self):
        """Test creating a failed scraping result."""
        result = ScrapingResult(
            success=False,
            source=TrendSource.YOUTUBE,
            error="API rate limit exceeded",
            duration_seconds=0.5,
        )
        
        assert result.success is False
        assert result.count == 0
        assert result.error == "API rate limit exceeded"


class TestTrendEnums:
    """Tests for trend-related enums."""

    def test_trend_source_values(self):
        """Test TrendSource enum values."""
        assert TrendSource.YOUTUBE.value == "youtube"
        assert TrendSource.REDDIT.value == "reddit"
        assert TrendSource.COMBINED.value == "combined"

    def test_trend_category_values(self):
        """Test TrendCategory enum values."""
        assert TrendCategory.TECHNOLOGY.value == "technology"
        assert TrendCategory.GAMING.value == "gaming"
        assert TrendCategory.GENERAL.value == "general"

    def test_competition_level_values(self):
        """Test CompetitionLevel enum values."""
        assert CompetitionLevel.LOW.value == "low"
        assert CompetitionLevel.MEDIUM.value == "medium"
        assert CompetitionLevel.HIGH.value == "high"
        assert CompetitionLevel.VERY_HIGH.value == "very_high"
