"""
Unit tests for TrendCache — covering missing lines in trend_analysis/cache.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.trend_analysis.models import TrendBatch, TrendData, TrendSource


def _make_trend(keyword: str = "python") -> TrendData:
    return TrendData(
        keyword=keyword,
        score=0.8,
        source=TrendSource.YOUTUBE,
        trend_type="rising",
    )


class TestTrendCacheGetTrends:
    """Test TrendCache.get_trends."""

    def test_cache_miss_file_not_found(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        result = cache.get_trends(TrendSource.YOUTUBE)
        assert result is None

    def test_cache_hit_returns_trends(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path, default_ttl_minutes=60)

        trends = [_make_trend("python"), _make_trend("django")]
        assert cache.save_trends(trends, TrendSource.YOUTUBE) is True

        result = cache.get_trends(TrendSource.YOUTUBE)
        assert result is not None
        assert len(result) == 2

    def test_cache_miss_expired(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path, default_ttl_minutes=1)

        trends = [_make_trend()]
        cache.save_trends(trends, TrendSource.YOUTUBE)

        # Manually expire the batch by editing the cache file
        import json
        cache_file = cache._get_cache_file(TrendSource.YOUTUBE)
        with open(cache_file) as f:
            data = json.load(f)
        # Set expires_at to the past
        data["expires_at"] = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        with open(cache_file, "w") as f:
            json.dump(data, f)

        result = cache.get_trends(TrendSource.YOUTUBE)
        assert result is None

    def test_cache_miss_max_age_override(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path, default_ttl_minutes=120)

        trends = [_make_trend()]
        cache.save_trends(trends, TrendSource.YOUTUBE)

        # Edit fetched_at to be 2 hours ago
        import json
        cache_file = cache._get_cache_file(TrendSource.YOUTUBE)
        with open(cache_file) as f:
            data = json.load(f)
        data["fetched_at"] = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        with open(cache_file, "w") as f:
            json.dump(data, f)

        # Request with max_age_minutes=30 → should be too old
        result = cache.get_trends(TrendSource.YOUTUBE, max_age_minutes=30)
        assert result is None

    def test_cache_invalid_json_returns_none(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)

        # Write corrupt cache file
        cache_file = cache._get_cache_file(TrendSource.YOUTUBE)
        cache_file.write_text("not valid json {{{")

        result = cache.get_trends(TrendSource.YOUTUBE)
        assert result is None

    def test_combined_source_default(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        # No combined cache → miss
        result = cache.get_trends()  # source=None → COMBINED
        assert result is None


class TestTrendCacheSaveTrends:
    """Test TrendCache.save_trends."""

    def test_save_and_retrieve(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        trends = [_make_trend("rust"), _make_trend("go")]
        ok = cache.save_trends(trends, TrendSource.REDDIT)
        assert ok is True

        result = cache.get_trends(TrendSource.REDDIT)
        assert result is not None
        keywords = [t.keyword for t in result]
        assert "rust" in keywords

    def test_save_with_ttl_override(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        trends = [_make_trend()]
        ok = cache.save_trends(trends, TrendSource.YOUTUBE, ttl_minutes=120)
        assert ok is True

    def test_save_creates_metadata(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.save_trends([_make_trend()], TrendSource.YOUTUBE)
        assert cache._get_metadata_file().exists()


class TestTrendCacheGetCombinedTrends:
    """Test TrendCache.get_combined_trends."""

    def test_empty_when_no_cache(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        result = cache.get_combined_trends()
        assert result == []

    def test_combines_multiple_sources(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.save_trends([_make_trend("python")], TrendSource.YOUTUBE)
        cache.save_trends([_make_trend("rust")], TrendSource.REDDIT)

        result = cache.get_combined_trends()
        keywords = [t.keyword for t in result]
        assert "python" in keywords
        assert "rust" in keywords

    def test_deduplicates_keywords(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.save_trends([_make_trend("python")], TrendSource.YOUTUBE)
        cache.save_trends([_make_trend("python")], TrendSource.REDDIT)

        result = cache.get_combined_trends()
        keywords = [t.keyword for t in result]
        assert keywords.count("python") == 1

    def test_specific_sources(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.save_trends([_make_trend("python")], TrendSource.YOUTUBE)

        result = cache.get_combined_trends(sources=[TrendSource.YOUTUBE])
        assert len(result) == 1


class TestTrendCacheInvalidate:
    """Test TrendCache.invalidate."""

    def test_invalidate_specific_source(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.save_trends([_make_trend()], TrendSource.YOUTUBE)

        cache.invalidate(source=TrendSource.YOUTUBE)
        assert not cache._get_cache_file(TrendSource.YOUTUBE).exists()

    def test_invalidate_nonexistent_source(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.invalidate(source=TrendSource.YOUTUBE)  # file doesn't exist

    def test_invalidate_all(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.save_trends([_make_trend()], TrendSource.YOUTUBE)
        cache.save_trends([_make_trend("js")], TrendSource.REDDIT)

        cache.invalidate()

        assert not cache._get_cache_file(TrendSource.YOUTUBE).exists()
        assert not cache._get_cache_file(TrendSource.REDDIT).exists()


class TestTrendCacheCleanupExpired:
    """Test TrendCache.cleanup_expired."""

    def test_cleanup_removes_expired(self, tmp_path):
        import json
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.save_trends([_make_trend()], TrendSource.YOUTUBE)

        # Expire the file
        cache_file = cache._get_cache_file(TrendSource.YOUTUBE)
        with open(cache_file) as f:
            data = json.load(f)
        data["expires_at"] = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        with open(cache_file, "w") as f:
            json.dump(data, f)

        count = cache.cleanup_expired()
        assert count >= 1

    def test_cleanup_skips_nonexistent(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        count = cache.cleanup_expired()
        assert count == 0

    def test_cleanup_removes_corrupt_files(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)

        # Write corrupt file
        cache_file = cache._get_cache_file(TrendSource.YOUTUBE)
        cache_file.write_text("corrupted {{{")

        count = cache.cleanup_expired()
        assert count >= 1
        assert not cache_file.exists()


class TestTrendCacheGetStats:
    """Test TrendCache.get_cache_stats."""

    def test_empty_cache_stats(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        stats = cache.get_cache_stats()
        assert stats["total_trends"] == 0
        assert stats["total_size_bytes"] == 0

    def test_stats_with_cached_data(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache.save_trends([_make_trend("python"), _make_trend("rust")], TrendSource.YOUTUBE)

        stats = cache.get_cache_stats()
        assert stats["total_trends"] == 2
        assert TrendSource.YOUTUBE.value in stats["sources"]

    def test_stats_with_corrupt_cache(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache_file = cache._get_cache_file(TrendSource.YOUTUBE)
        cache_file.write_text("corrupt {{{")

        stats = cache.get_cache_stats()
        assert "error" in stats["sources"].get(TrendSource.YOUTUBE.value, {})


class TestUpdateMetadata:
    """Test TrendCache._update_metadata."""

    def test_creates_metadata_file(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache._update_metadata(TrendSource.YOUTUBE, 5)
        assert cache._get_metadata_file().exists()

    def test_updates_existing_metadata(self, tmp_path):
        from src.trend_analysis.cache import TrendCache
        cache = TrendCache(cache_dir=tmp_path)
        cache._update_metadata(TrendSource.YOUTUBE, 5)
        cache._update_metadata(TrendSource.YOUTUBE, 10)

        import json
        with open(cache._get_metadata_file()) as f:
            data = json.load(f)
        assert data[TrendSource.YOUTUBE.value]["count"] == 10
