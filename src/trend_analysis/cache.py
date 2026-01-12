"""
Trend data caching system.

Provides persistent caching for trend data with TTL support,
reducing API calls and enabling offline operation.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from src.trend_analysis.models import TrendBatch, TrendData, TrendSource

if TYPE_CHECKING:
    from src.core.config import Settings


def _trend_batch_to_dict(batch: TrendBatch) -> dict[str, Any]:
    """Convert TrendBatch to dictionary for JSON serialization."""
    return {
        "trends": [t.to_dict() for t in batch.trends],
        "source": batch.source.value,
        "fetched_at": batch.fetched_at.isoformat(),
        "expires_at": batch.expires_at.isoformat(),
        "query": batch.query,
    }


def _trend_batch_from_dict(data: dict[str, Any]) -> TrendBatch:
    """Create TrendBatch from dictionary."""
    trends = [TrendData.from_dict(t) for t in data.get("trends", [])]
    return TrendBatch(
        trends=trends,
        source=TrendSource(data["source"]),
        fetched_at=datetime.fromisoformat(data["fetched_at"]),
        expires_at=datetime.fromisoformat(data["expires_at"]),
        query=data.get("query"),
    )


class TrendCache:
    """
    Persistent cache for trend data.

    Features:
    - File-based JSON storage
    - TTL-based expiration
    - Source-specific caching
    - Automatic cleanup
    - Thread-safe operations

    Cache Structure:
        cache_dir/
            trends_youtube.json
            trends_reddit.json
            trends_combined.json
            metadata.json
    """

    def __init__(
        self,
        cache_dir: Path,
        default_ttl_minutes: int = 30,
    ) -> None:
        """
        Initialize trend cache.

        Args:
            cache_dir: Directory for cache files.
            default_ttl_minutes: Default cache TTL in minutes.
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_file(self, source: TrendSource) -> Path:
        """Get cache file path for a source."""
        return self.cache_dir / f"trends_{source.value}.json"

    def _get_metadata_file(self) -> Path:
        """Get metadata file path."""
        return self.cache_dir / "cache_metadata.json"

    def get_trends(
        self,
        source: Optional[TrendSource] = None,
        max_age_minutes: Optional[int] = None,
    ) -> Optional[list[TrendData]]:
        """
        Retrieve cached trends.

        Args:
            source: Specific source to retrieve, or None for combined.
            max_age_minutes: Maximum age override (uses default if None).

        Returns:
            List of TrendData if cache hit, None if miss/expired.
        """
        source = source or TrendSource.COMBINED
        cache_file = self._get_cache_file(source)

        if not cache_file.exists():
            logger.debug(f"Cache miss: {source.value} (file not found)")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            batch = _trend_batch_from_dict(data)

            # Check expiration
            if batch.is_expired:
                logger.debug(f"Cache miss: {source.value} (expired)")
                return None

            # Check max age override
            if max_age_minutes:
                max_age = timedelta(minutes=max_age_minutes)
                age = datetime.utcnow() - batch.fetched_at
                if age > max_age:
                    logger.debug(f"Cache miss: {source.value} (too old: {age})")
                    return None

            logger.debug(f"Cache hit: {source.value} ({batch.count} trends)")
            return batch.trends

        except Exception as e:
            logger.warning(f"Cache read error for {source.value}: {e}")
            return None

    def save_trends(
        self,
        trends: list[TrendData],
        source: TrendSource,
        ttl_minutes: Optional[int] = None,
    ) -> bool:
        """
        Save trends to cache.

        Args:
            trends: Trends to cache.
            source: Source of the trends.
            ttl_minutes: TTL override in minutes.

        Returns:
            True if saved successfully.
        """
        cache_file = self._get_cache_file(source)

        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
        now = datetime.utcnow()

        batch = TrendBatch(
            trends=trends,
            source=source,
            fetched_at=now,
            expires_at=now + ttl,
        )

        try:
            batch_dict = _trend_batch_to_dict(batch)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(batch_dict, f, indent=2, default=str)

            logger.debug(f"Cached {len(trends)} trends for {source.value}")
            self._update_metadata(source, len(trends))
            return True

        except Exception as e:
            logger.error(f"Cache write error for {source.value}: {e}")
            return False

    def get_combined_trends(
        self,
        sources: Optional[list[TrendSource]] = None,
        max_age_minutes: Optional[int] = None,
    ) -> list[TrendData]:
        """
        Get trends from multiple sources combined.

        Args:
            sources: Sources to combine, or all if None.
            max_age_minutes: Maximum age for each source.

        Returns:
            Combined list of trends, deduplicated.
        """
        if sources is None:
            sources = [TrendSource.YOUTUBE, TrendSource.REDDIT]

        all_trends: list[TrendData] = []

        for source in sources:
            trends = self.get_trends(source, max_age_minutes)
            if trends:
                all_trends.extend(trends)

        # Deduplicate by keyword
        seen: set[str] = set()
        unique_trends: list[TrendData] = []
        for trend in all_trends:
            key = trend.keyword.lower()
            if key not in seen:
                seen.add(key)
                unique_trends.append(trend)

        return unique_trends

    def invalidate(
        self,
        source: Optional[TrendSource] = None,
    ) -> None:
        """
        Invalidate cached data.

        Args:
            source: Specific source to invalidate, or all if None.
        """
        if source:
            cache_file = self._get_cache_file(source)
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Invalidated cache for {source.value}")
        else:
            # Invalidate all
            for src in TrendSource:
                cache_file = self._get_cache_file(src)
                if cache_file.exists():
                    cache_file.unlink()
            logger.debug("Invalidated all trend caches")

    def cleanup_expired(self) -> int:
        """
        Remove expired cache files.

        Returns:
            Number of files cleaned up.
        """
        cleaned = 0

        for source in TrendSource:
            cache_file = self._get_cache_file(source)
            if not cache_file.exists():
                continue

            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                batch = _trend_batch_from_dict(data)
                if batch.is_expired:
                    cache_file.unlink()
                    cleaned += 1
                    logger.debug(f"Cleaned expired cache: {source.value}")

            except Exception:
                # If we can't read it, it's probably corrupt - remove it
                cache_file.unlink()
                cleaned += 1

        return cleaned

    def _update_metadata(self, source: TrendSource, count: int) -> None:
        """Update cache metadata."""
        metadata_file = self._get_metadata_file()

        metadata: dict[str, Any] = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception:
                pass

        metadata[source.value] = {
            "last_updated": datetime.utcnow().isoformat(),
            "count": count,
        }
        metadata["last_access"] = datetime.utcnow().isoformat()

        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        except Exception:
            pass

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats.
        """
        stats = {
            "cache_dir": str(self.cache_dir),
            "default_ttl_minutes": int(self.default_ttl.total_seconds() / 60),
            "sources": {},
            "total_trends": 0,
            "total_size_bytes": 0,
        }

        for source in TrendSource:
            cache_file = self._get_cache_file(source)
            if cache_file.exists():
                size = cache_file.stat().st_size
                stats["total_size_bytes"] += size

                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    batch = _trend_batch_from_dict(data)

                    stats["sources"][source.value] = {
                        "count": batch.count,
                        "fetched_at": batch.fetched_at.isoformat(),
                        "expires_at": batch.expires_at.isoformat(),
                        "is_expired": batch.is_expired,
                        "size_bytes": size,
                    }
                    stats["total_trends"] += batch.count

                except Exception:
                    stats["sources"][source.value] = {
                        "error": "Failed to read",
                        "size_bytes": size,
                    }

        return stats
