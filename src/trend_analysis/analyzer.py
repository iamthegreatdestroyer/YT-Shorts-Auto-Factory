"""
Trend Analyzer - Main orchestrator for trend analysis.

Aggregates, scores, and selects trending topics from multiple sources
for content generation.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from src.trend_analysis.cache import TrendCache
from src.trend_analysis.models import (
    CompetitionLevel,
    ScrapingResult,
    TrendCategory,
    TrendData,
    TrendSource,
)
from src.trend_analysis.sources.reddit_scraper import RedditScraper
from src.trend_analysis.sources.youtube_trends import YouTubeTrendsScraper

if TYPE_CHECKING:
    from src.core.config import Settings


class TrendAnalyzer:
    """
    Main trend analysis orchestrator.

    Coordinates multiple scrapers, aggregates results, applies scoring,
    and selects optimal trends for content creation.

    Features:
    - Multi-source aggregation (YouTube, Reddit, etc.)
    - Intelligent scoring algorithm
    - Caching with TTL
    - Niche relevance filtering
    - Deduplication and ranking
    - Historical tracking to avoid repeats
    """

    def __init__(self, settings: "Settings") -> None:
        """
        Initialize the trend analyzer.

        Args:
            settings: Application settings.
        """
        self.settings = settings

        # Initialize scrapers
        self._scrapers = {
            TrendSource.YOUTUBE: YouTubeTrendsScraper(settings),
            TrendSource.REDDIT: RedditScraper(settings),
        }

        # Initialize cache
        cache_dir = settings.storage.cache_dir / "trends"
        self._cache = TrendCache(
            cache_dir=cache_dir,
            default_ttl_minutes=settings.trends.cache_ttl_minutes,
        )

        # Track used trends (in-memory for now, could persist)
        self._used_trends: dict[str, datetime] = {}

        # Scoring weights
        self._weights = {
            "volume": 0.25,
            "growth": 0.25,
            "freshness": 0.20,
            "niche_relevance": 0.20,
            "competition_inverse": 0.10,
        }

    async def get_trending_topics(
        self,
        force_refresh: bool = False,
        max_results: int = 20,
    ) -> list[TrendData]:
        """
        Get current trending topics from all enabled sources.

        Args:
            force_refresh: Bypass cache and fetch fresh data.
            max_results: Maximum trends to return.

        Returns:
            List of TrendData sorted by score.
        """
        logger.info("Fetching trending topics")

        # Check cache first
        if not force_refresh:
            cached = self._cache.get_combined_trends(
                max_age_minutes=self.settings.trends.cache_ttl_minutes
            )
            if cached:
                logger.info(f"Using {len(cached)} cached trends")
                # Re-score and sort
                for trend in cached:
                    trend.score = self._calculate_score(trend)
                cached.sort(key=lambda t: t.score, reverse=True)
                return cached[:max_results]

        # Fetch from all enabled sources concurrently
        results = await self._fetch_all_sources()

        # Aggregate trends
        all_trends = self._aggregate_results(results)

        if not all_trends:
            logger.warning("No trends found from any source")
            # Fall back to expired cache if available
            cached = self._cache.get_combined_trends(max_age_minutes=1440)
            if cached:
                logger.info(f"Using {len(cached)} expired cached trends as fallback")
                return cached[:max_results]
            return []

        # Score trends
        for trend in all_trends:
            trend.score = self._calculate_score(trend)

        # Sort by score
        all_trends.sort(key=lambda t: t.score, reverse=True)

        # Cache results
        self._cache.save_trends(all_trends, TrendSource.COMBINED)

        logger.info(f"Found {len(all_trends)} trends, top score: {all_trends[0].score:.3f}")

        return all_trends[:max_results]

    async def _fetch_all_sources(self) -> list[ScrapingResult]:
        """
        Fetch trends from all enabled sources concurrently.

        Returns:
            List of ScrapingResult from each source.
        """
        tasks = []
        max_per_source = self.settings.trends.max_trends_per_source

        for source, scraper in self._scrapers.items():
            if scraper.enabled:
                tasks.append(scraper.safe_fetch(max_results=max_per_source))
            else:
                logger.debug(f"Scraper {source.value} is disabled")

        if not tasks:
            logger.warning("No trend sources are enabled")
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results: list[ScrapingResult] = []
        for result in results:
            if isinstance(result, ScrapingResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraper error: {result}")

        return valid_results

    def _aggregate_results(
        self,
        results: list[ScrapingResult],
    ) -> list[TrendData]:
        """
        Aggregate trends from multiple sources.

        Deduplicates and merges similar trends.

        Args:
            results: Scraping results from all sources.

        Returns:
            Deduplicated list of trends.
        """
        all_trends: list[TrendData] = []
        for result in results:
            if result.success:
                all_trends.extend(result.trends)
                # Cache individual source
                self._cache.save_trends(result.trends, result.source)

        # Deduplicate by keyword similarity
        seen: dict[str, TrendData] = {}
        for trend in all_trends:
            key = self._normalize_keyword(trend.keyword)

            if key in seen:
                # Merge with existing (keep higher volume)
                existing = seen[key]
                if trend.volume > existing.volume:
                    # Merge related keywords
                    combined_related = list(set(
                        existing.related_keywords + trend.related_keywords
                    ))
                    trend.related_keywords = combined_related[:10]
                    seen[key] = trend
                else:
                    # Add this trend's related keywords to existing
                    combined_related = list(set(
                        existing.related_keywords + trend.related_keywords
                    ))
                    existing.related_keywords = combined_related[:10]
            else:
                seen[key] = trend

        return list(seen.values())

    def _normalize_keyword(self, keyword: str) -> str:
        """
        Normalize keyword for deduplication.

        Args:
            keyword: Raw keyword.

        Returns:
            Normalized string.
        """
        import re
        # Lowercase, remove special chars, collapse spaces
        normalized = keyword.lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()

    def _calculate_score(self, trend: TrendData) -> float:
        """
        Calculate comprehensive trend score.

        Scoring formula:
            score = (volume_score × 0.25) +
                    (growth_score × 0.25) +
                    (freshness_score × 0.20) +
                    (niche_relevance × 0.20) +
                    (competition_inverse × 0.10)

        Args:
            trend: Trend to score.

        Returns:
            Normalized score between 0 and 1.
        """
        # Volume score (logarithmic normalization)
        import math
        if trend.volume > 0:
            volume_score = min(math.log10(trend.volume + 1) / 7, 1.0)
        else:
            volume_score = 0.1

        # Growth rate score
        growth_score = min(trend.growth_rate / 100, 1.0) if trend.growth_rate > 0 else 0.1

        # Freshness score (from computed property)
        freshness_score = trend.freshness_score

        # Niche relevance
        niche_relevance = self._calculate_niche_relevance(trend)

        # Competition inverse (low competition = high score)
        competition_map = {
            CompetitionLevel.LOW: 1.0,
            CompetitionLevel.MEDIUM: 0.7,
            CompetitionLevel.HIGH: 0.4,
            CompetitionLevel.VERY_HIGH: 0.2,
        }
        competition_score = competition_map.get(trend.competition, 0.5)

        # Weighted sum
        final_score = (
            volume_score * self._weights["volume"] +
            growth_score * self._weights["growth"] +
            freshness_score * self._weights["freshness"] +
            niche_relevance * self._weights["niche_relevance"] +
            competition_score * self._weights["competition_inverse"]
        )

        # Apply bonuses/penalties
        if trend.is_viral:
            final_score *= 1.15
        if trend.previously_used:
            final_score *= 0.5

        return round(min(final_score, 1.0), 4)

    def _calculate_niche_relevance(self, trend: TrendData) -> float:
        """
        Calculate how relevant a trend is to configured niche.

        Args:
            trend: Trend to evaluate.

        Returns:
            Relevance score between 0 and 1.
        """
        niche = self.settings.content.niche.lower()
        keyword_lower = trend.keyword.lower()

        # Direct niche match
        if niche in keyword_lower:
            return 1.0

        # Category-based relevance
        niche_category_map = {
            "tech": [TrendCategory.TECHNOLOGY, TrendCategory.SCIENCE],
            "technology": [TrendCategory.TECHNOLOGY, TrendCategory.SCIENCE],
            "gaming": [TrendCategory.GAMING, TrendCategory.ENTERTAINMENT],
            "science": [TrendCategory.SCIENCE, TrendCategory.EDUCATION],
            "education": [TrendCategory.EDUCATION, TrendCategory.SCIENCE],
            "entertainment": [TrendCategory.ENTERTAINMENT, TrendCategory.MUSIC],
            "finance": [TrendCategory.FINANCE],
            "news": [TrendCategory.NEWS],
            "sports": [TrendCategory.SPORTS],
            "lifestyle": [TrendCategory.LIFESTYLE],
        }

        relevant_categories = niche_category_map.get(niche, [])
        if trend.category in relevant_categories:
            return 0.8

        # Keyword-based partial matching
        niche_keywords = self._get_niche_keywords(niche)
        matches = sum(1 for kw in niche_keywords if kw in keyword_lower)
        if matches > 0:
            return min(0.3 + (matches * 0.2), 0.7)

        return 0.2  # Baseline for general content

    def _get_niche_keywords(self, niche: str) -> list[str]:
        """Get keywords associated with a niche."""
        niche_keywords = {
            "tech": ["ai", "software", "app", "programming", "developer", "computer"],
            "technology": ["ai", "software", "app", "programming", "developer"],
            "gaming": ["game", "esports", "streamer", "playstation", "xbox", "nintendo"],
            "science": ["research", "discovery", "space", "physics", "biology"],
            "education": ["learn", "tutorial", "course", "study", "knowledge"],
            "finance": ["stock", "crypto", "investment", "money", "trading"],
            "entertainment": ["movie", "show", "celebrity", "music", "concert"],
        }
        return niche_keywords.get(niche, [])

    def select_best_trend(
        self,
        trends: list[TrendData],
        exclude_recent_hours: int = 24,
    ) -> Optional[TrendData]:
        """
        Select the best trend for content creation.

        Applies additional filtering:
        - Excludes recently used trends
        - Ensures minimum score threshold
        - Prefers diverse categories

        Args:
            trends: List of scored trends.
            exclude_recent_hours: Hours to exclude recently used trends.

        Returns:
            Best trend or None if none qualify.
        """
        if not trends:
            logger.warning("No trends available for selection")
            return None

        min_score = self.settings.trends.min_trend_score
        cutoff = datetime.utcnow() - timedelta(hours=exclude_recent_hours)

        qualified: list[TrendData] = []
        for trend in trends:
            # Check score threshold
            if trend.score < min_score:
                continue

            # Check if recently used
            keyword_key = self._normalize_keyword(trend.keyword)
            last_used = self._used_trends.get(keyword_key)
            if last_used and last_used > cutoff:
                continue

            qualified.append(trend)

        if not qualified:
            logger.warning(
                f"No trends meet criteria (min_score={min_score}). "
                f"Using highest scoring trend."
            )
            # Fall back to highest scoring trend
            return trends[0] if trends else None

        # Select top trend
        selected = qualified[0]

        # Mark as used
        self._mark_trend_used(selected)

        logger.info(f"Selected trend: '{selected.keyword}' (score: {selected.score:.3f})")
        return selected

    def _mark_trend_used(self, trend: TrendData) -> None:
        """Mark a trend as used."""
        keyword_key = self._normalize_keyword(trend.keyword)
        self._used_trends[keyword_key] = datetime.utcnow()
        trend.previously_used = True

        # Cleanup old entries (older than 7 days)
        cutoff = datetime.utcnow() - timedelta(days=7)
        self._used_trends = {
            k: v for k, v in self._used_trends.items()
            if v > cutoff
        }

    def get_trends_by_category(
        self,
        category: TrendCategory,
        max_results: int = 10,
    ) -> list[TrendData]:
        """
        Get trends filtered by category.

        Args:
            category: Category to filter by.
            max_results: Maximum results.

        Returns:
            Filtered and sorted trends.
        """
        all_trends = self._cache.get_combined_trends()
        if not all_trends:
            return []

        filtered = [t for t in all_trends if t.category == category]
        filtered.sort(key=lambda t: t.score, reverse=True)
        return filtered[:max_results]

    async def refresh_source(self, source: TrendSource) -> ScrapingResult:
        """
        Refresh trends from a specific source.

        Args:
            source: Source to refresh.

        Returns:
            Scraping result.
        """
        scraper = self._scrapers.get(source)
        if not scraper:
            return ScrapingResult(
                success=False,
                source=source,
                error=f"Unknown source: {source.value}",
            )

        result = await scraper.safe_fetch(
            max_results=self.settings.trends.max_trends_per_source
        )

        if result.success:
            self._cache.save_trends(result.trends, source)

        return result

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self._cache.get_cache_stats()

    def clear_cache(self, source: Optional[TrendSource] = None) -> None:
        """Clear trend cache."""
        self._cache.invalidate(source)

    async def close(self) -> None:
        """Close all scraper connections."""
        for scraper in self._scrapers.values():
            if hasattr(scraper, 'close'):
                await scraper.close()
