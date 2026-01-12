"""
Data models for trend analysis.

This module defines the core data structures used throughout the
trend analysis system for representing trends, sources, and scoring.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field


class TrendSource(str, Enum):
    """Available trend data sources."""

    YOUTUBE = "youtube"
    GOOGLE_TRENDS = "google_trends"
    REDDIT = "reddit"
    TWITTER = "twitter"
    COMBINED = "combined"  # Aggregated from multiple sources


class TrendCategory(str, Enum):
    """Content categories for trends."""

    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    GAMING = "gaming"
    SCIENCE = "science"
    EDUCATION = "education"
    NEWS = "news"
    LIFESTYLE = "lifestyle"
    FINANCE = "finance"
    SPORTS = "sports"
    MUSIC = "music"
    GENERAL = "general"


class CompetitionLevel(str, Enum):
    """Competition level for a trend."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TrendData(BaseModel):
    """
    Represents a single trending topic with metadata.

    This is the core data structure for trend information,
    containing all relevant metadata for scoring and selection.
    """

    # Core Identity
    keyword: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Primary trending keyword or phrase",
    )
    source: TrendSource = Field(
        ...,
        description="Source where trend was discovered",
    )

    # Metrics
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized trend score (0-1)",
    )
    volume: int = Field(
        default=0,
        ge=0,
        description="Search/mention volume",
    )
    growth_rate: float = Field(
        default=0.0,
        description="Growth rate percentage (e.g., 150 = 150% increase)",
    )
    competition: CompetitionLevel = Field(
        default=CompetitionLevel.MEDIUM,
        description="Estimated competition level",
    )

    # Classification
    category: TrendCategory = Field(
        default=TrendCategory.GENERAL,
        description="Content category",
    )
    related_keywords: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Related/associated keywords",
    )
    hashtags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Associated hashtags",
    )

    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the trend was captured",
    )
    url: Optional[str] = Field(
        default=None,
        description="Source URL for reference",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Brief description of the trend",
    )
    raw_data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Raw data from source API",
    )

    # Flags
    is_viral: bool = Field(
        default=False,
        description="Whether trend is considered viral",
    )
    is_evergreen: bool = Field(
        default=False,
        description="Whether topic has lasting relevance",
    )
    previously_used: bool = Field(
        default=False,
        description="Whether this trend was used before",
    )

    @computed_field
    @property
    def age_hours(self) -> float:
        """Calculate age of trend in hours."""
        delta = datetime.utcnow() - self.timestamp
        return delta.total_seconds() / 3600

    @computed_field
    @property
    def freshness_score(self) -> float:
        """Calculate freshness (1.0 = just now, 0.0 = very old)."""
        hours = self.age_hours
        if hours <= 1:
            return 1.0
        elif hours <= 6:
            return 0.9
        elif hours <= 12:
            return 0.7
        elif hours <= 24:
            return 0.5
        elif hours <= 48:
            return 0.3
        return 0.1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = self.model_dump()
        data["timestamp"] = self.timestamp.isoformat()
        data["source"] = self.source.value
        data["category"] = self.category.value
        data["competition"] = self.competition.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrendData":
        """Create from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("source"), str):
            data["source"] = TrendSource(data["source"])
        if isinstance(data.get("category"), str):
            data["category"] = TrendCategory(data["category"])
        if isinstance(data.get("competition"), str):
            data["competition"] = CompetitionLevel(data["competition"])
        return cls(**data)


class TrendBatch(BaseModel):
    """
    A batch of trends from a single analysis run.

    Used for caching and tracking trend analysis results.
    """

    trends: list[TrendData] = Field(
        default_factory=list,
        description="List of discovered trends",
    )
    source: TrendSource = Field(
        ...,
        description="Primary source of this batch",
    )
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When trends were fetched",
    )
    expires_at: datetime = Field(
        ...,
        description="When this batch expires",
    )
    query: Optional[str] = Field(
        default=None,
        description="Query used to fetch trends",
    )

    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if batch has expired."""
        return datetime.utcnow() >= self.expires_at

    @computed_field
    @property
    def count(self) -> int:
        """Number of trends in batch."""
        return len(self.trends)

    def get_top_n(self, n: int = 5) -> list[TrendData]:
        """Get top N trends by score."""
        sorted_trends = sorted(self.trends, key=lambda t: t.score, reverse=True)
        return sorted_trends[:n]


class ScrapingResult(BaseModel):
    """
    Result from a scraping operation.

    Contains both successful data and error information.
    """

    success: bool = Field(
        ...,
        description="Whether scraping was successful",
    )
    source: TrendSource = Field(
        ...,
        description="Source that was scraped",
    )
    trends: list[TrendData] = Field(
        default_factory=list,
        description="Scraped trends",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Time taken to scrape",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When scraping occurred",
    )

    @computed_field
    @property
    def count(self) -> int:
        """Number of trends retrieved."""
        return len(self.trends)
