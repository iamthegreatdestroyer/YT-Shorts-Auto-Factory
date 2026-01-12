"""
Base scraper interface for trend sources.

This module defines the abstract base class that all trend scrapers
must implement, ensuring consistent behavior across different sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from src.trend_analysis.models import ScrapingResult, TrendData, TrendSource

if TYPE_CHECKING:
    from src.core.config import Settings


class BaseScraper(ABC):
    """
    Abstract base class for trend scrapers.

    All trend source scrapers (YouTube, Reddit, Twitter, etc.) must
    inherit from this class and implement the required methods.

    Attributes:
        source: The TrendSource this scraper handles.
        settings: Application settings.
        enabled: Whether this scraper is enabled.
    """

    source: TrendSource

    def __init__(self, settings: "Settings") -> None:
        """
        Initialize the scraper.

        Args:
            settings: Application settings instance.
        """
        self.settings = settings
        self._last_fetch: Optional[datetime] = None
        self._rate_limit_remaining: int = 100
        self._rate_limit_reset: Optional[datetime] = None

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Check if this scraper is enabled in settings."""
        ...

    @property
    def name(self) -> str:
        """Human-readable scraper name."""
        return f"{self.source.value.title()}Scraper"

    @abstractmethod
    async def fetch_trends(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
    ) -> ScrapingResult:
        """
        Fetch trending topics from this source.

        Args:
            query: Optional search query to filter trends.
            max_results: Maximum number of trends to return.

        Returns:
            ScrapingResult containing trends or error information.
        """
        ...

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """
        Validate that API credentials are configured and working.

        Returns:
            True if credentials are valid, False otherwise.
        """
        ...

    async def safe_fetch(
        self,
        query: Optional[str] = None,
        max_results: int = 10,
    ) -> ScrapingResult:
        """
        Fetch trends with error handling and logging.

        Wraps fetch_trends with exception handling and metrics.

        Args:
            query: Optional search query.
            max_results: Maximum results to return.

        Returns:
            ScrapingResult, always returns (never throws).
        """
        start_time = datetime.utcnow()

        if not self.enabled:
            logger.debug(f"{self.name} is disabled, skipping")
            return ScrapingResult(
                success=False,
                source=self.source,
                error="Scraper is disabled",
            )

        try:
            logger.info(f"Fetching trends from {self.name}")
            result = await self.fetch_trends(query=query, max_results=max_results)

            duration = (datetime.utcnow() - start_time).total_seconds()
            result.duration_seconds = duration

            if result.success:
                logger.info(
                    f"{self.name} fetched {result.count} trends in {duration:.2f}s"
                )
            else:
                logger.warning(f"{self.name} fetch failed: {result.error}")

            self._last_fetch = datetime.utcnow()
            return result

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.exception(f"{self.name} fetch error: {e}")
            return ScrapingResult(
                success=False,
                source=self.source,
                error=str(e),
                duration_seconds=duration,
            )

    def _create_trend(
        self,
        keyword: str,
        **kwargs: Any,
    ) -> TrendData:
        """
        Helper to create a TrendData instance.

        Args:
            keyword: The trending keyword.
            **kwargs: Additional TrendData fields.

        Returns:
            TrendData instance.
        """
        return TrendData(
            keyword=keyword,
            source=self.source,
            timestamp=datetime.utcnow(),
            **kwargs,
        )

    def _estimate_competition(self, volume: int, growth_rate: float) -> str:
        """
        Estimate competition level based on metrics.

        Args:
            volume: Search/mention volume.
            growth_rate: Growth rate percentage.

        Returns:
            Competition level string.
        """
        from src.trend_analysis.models import CompetitionLevel

        # High volume + low growth = saturated market
        if volume > 100000:
            if growth_rate < 20:
                return CompetitionLevel.VERY_HIGH
            return CompetitionLevel.HIGH
        elif volume > 10000:
            if growth_rate > 50:
                return CompetitionLevel.MEDIUM
            return CompetitionLevel.HIGH
        elif volume > 1000:
            return CompetitionLevel.MEDIUM
        return CompetitionLevel.LOW

    def _categorize_keyword(self, keyword: str) -> str:
        """
        Attempt to categorize a keyword.

        Args:
            keyword: The keyword to categorize.

        Returns:
            TrendCategory value.
        """
        from src.trend_analysis.models import TrendCategory

        keyword_lower = keyword.lower()

        # Category keyword mappings
        mappings = {
            TrendCategory.TECHNOLOGY: [
                "tech", "ai", "software", "app", "phone", "computer",
                "programming", "code", "developer", "startup", "gadget",
            ],
            TrendCategory.GAMING: [
                "game", "gaming", "playstation", "xbox", "nintendo",
                "esports", "twitch", "streamer", "gamer",
            ],
            TrendCategory.SCIENCE: [
                "science", "research", "study", "discovery", "space",
                "physics", "biology", "chemistry", "nasa",
            ],
            TrendCategory.ENTERTAINMENT: [
                "movie", "film", "tv", "show", "celebrity", "actor",
                "netflix", "disney", "marvel", "music", "album",
            ],
            TrendCategory.FINANCE: [
                "stock", "crypto", "bitcoin", "investment", "market",
                "economy", "money", "finance", "trading",
            ],
            TrendCategory.SPORTS: [
                "sports", "football", "basketball", "soccer", "nfl",
                "nba", "olympics", "athlete", "championship",
            ],
            TrendCategory.NEWS: [
                "breaking", "news", "politics", "election", "government",
            ],
            TrendCategory.EDUCATION: [
                "learn", "tutorial", "how to", "course", "education",
                "university", "student",
            ],
            TrendCategory.LIFESTYLE: [
                "lifestyle", "health", "fitness", "diet", "wellness",
                "travel", "fashion", "beauty",
            ],
        }

        for category, keywords in mappings.items():
            if any(kw in keyword_lower for kw in keywords):
                return category

        return TrendCategory.GENERAL
