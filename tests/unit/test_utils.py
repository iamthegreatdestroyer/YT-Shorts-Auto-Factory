"""
Unit tests for utility functions.

Tests file manager, validators, and decorators.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest


# =============================================================================
# File Manager Tests
# =============================================================================


class TestEnsureDirectory:
    """Test ensure_directory function."""

    def test_creates_single_directory(self, temp_dir: Path):
        """Test creating a single directory."""
        from src.utils.file_manager import ensure_directory

        new_dir = temp_dir / "new_folder"
        result = ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_creates_nested_directories(self, temp_dir: Path):
        """Test creating nested directories."""
        from src.utils.file_manager import ensure_directory

        nested = temp_dir / "level1" / "level2" / "level3"
        result = ensure_directory(nested)

        assert nested.exists()
        assert result == nested

    def test_existing_directory_no_error(self, temp_dir: Path):
        """Test that existing directory doesn't raise error."""
        from src.utils.file_manager import ensure_directory

        # Create directory first
        existing = temp_dir / "existing"
        existing.mkdir()

        # Should not raise
        result = ensure_directory(existing)
        assert result == existing


class TestGetFileSize:
    """Test get_file_size function."""

    def test_returns_correct_size(self, temp_dir: Path):
        """Test returns correct file size."""
        from src.utils.file_manager import get_file_size

        test_file = temp_dir / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)

        size = get_file_size(test_file)
        assert size == len(content)

    def test_missing_file_returns_zero(self, temp_dir: Path):
        """Test missing file returns 0."""
        from src.utils.file_manager import get_file_size

        missing = temp_dir / "does_not_exist.txt"
        size = get_file_size(missing)
        assert size == 0


class TestCleanupOldFiles:
    """Test cleanup_old_files function."""

    def test_deletes_old_files(self, temp_dir: Path):
        """Test deletes files older than max_age."""
        from src.utils.file_manager import cleanup_old_files
        import os

        # Create old file
        old_file = temp_dir / "old_file.txt"
        old_file.write_text("old content")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        # Create new file
        new_file = temp_dir / "new_file.txt"
        new_file.write_text("new content")

        # Cleanup files older than 5 days
        deleted = cleanup_old_files(temp_dir, max_age_days=5)

        assert deleted == 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_dry_run_doesnt_delete(self, temp_dir: Path):
        """Test dry_run doesn't actually delete."""
        from src.utils.file_manager import cleanup_old_files
        import os

        old_file = temp_dir / "old_file.txt"
        old_file.write_text("old content")

        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        deleted = cleanup_old_files(temp_dir, max_age_days=5, dry_run=True)

        assert deleted == 1
        assert old_file.exists()  # Still exists


class TestGetUniqueFilename:
    """Test get_unique_filename function."""

    def test_returns_original_if_unique(self, temp_dir: Path):
        """Test returns original name if no conflict."""
        from src.utils.file_manager import get_unique_filename

        result = get_unique_filename(temp_dir, "video", "mp4")
        assert result == temp_dir / "video.mp4"

    def test_adds_counter_if_exists(self, temp_dir: Path):
        """Test adds counter if file exists."""
        from src.utils.file_manager import get_unique_filename

        # Create existing file
        (temp_dir / "video.mp4").write_text("existing")

        result = get_unique_filename(temp_dir, "video", "mp4")
        assert result == temp_dir / "video_001.mp4"

    def test_increments_counter(self, temp_dir: Path):
        """Test increments counter for multiple conflicts."""
        from src.utils.file_manager import get_unique_filename

        (temp_dir / "video.mp4").write_text("existing")
        (temp_dir / "video_001.mp4").write_text("existing")
        (temp_dir / "video_002.mp4").write_text("existing")

        result = get_unique_filename(temp_dir, "video", "mp4")
        assert result == temp_dir / "video_003.mp4"


# =============================================================================
# Validator Tests
# =============================================================================


class TestSanitizeFilename:
    """Test sanitize_filename function."""

    def test_removes_invalid_characters(self):
        """Test removes invalid filesystem characters."""
        from src.utils.validators import sanitize_filename

        result = sanitize_filename('test<>:"/\\|?*.txt')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_removes_path_traversal(self):
        """Test removes path traversal attempts."""
        from src.utils.validators import sanitize_filename

        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result

    def test_replaces_spaces(self):
        """Test replaces spaces with underscores."""
        from src.utils.validators import sanitize_filename

        result = sanitize_filename("my video file.mp4")
        assert " " not in result or "_" in result

    def test_truncates_long_names(self):
        """Test truncates to max_length."""
        from src.utils.validators import sanitize_filename

        long_name = "a" * 300 + ".mp4"
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50


class TestValidateUrl:
    """Test validate_url function."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://example.com", True),
            ("http://example.com", True),
            ("https://www.youtube.com/watch?v=abc123", True),
            ("ftp://example.com", False),
            ("not-a-url", False),
            ("", False),
            (None, False),
        ],
    )
    def test_validate_url(self, url, expected):
        """Test URL validation with various inputs."""
        from src.utils.validators import validate_url

        if url is None:
            assert validate_url(url) is False
        else:
            assert validate_url(url) is expected

    def test_require_https(self):
        """Test require_https parameter."""
        from src.utils.validators import validate_url

        assert validate_url("https://example.com", require_https=True) is True
        assert validate_url("http://example.com", require_https=True) is False


class TestValidateDuration:
    """Test validate_duration function."""

    @pytest.mark.parametrize(
        "duration,expected",
        [
            (30.0, True),   # Within range
            (15.0, True),   # Minimum
            (60.0, True),   # Maximum
            (14.9, False),  # Below minimum
            (61.0, False),  # Above maximum
            (45.5, True),   # Mid-range
        ],
    )
    def test_validate_duration(self, duration, expected):
        """Test duration validation."""
        from src.utils.validators import validate_duration

        assert validate_duration(duration) is expected

    def test_custom_limits(self):
        """Test custom min/max limits."""
        from src.utils.validators import validate_duration

        assert validate_duration(5.0, min_seconds=1.0, max_seconds=10.0) is True
        assert validate_duration(15.0, min_seconds=1.0, max_seconds=10.0) is False


class TestValidateYouTubeVideoId:
    """Test YouTube video ID validation."""

    @pytest.mark.parametrize(
        "video_id,expected",
        [
            ("dQw4w9WgXcQ", True),   # Valid ID
            ("abc123XYZ-_", True),   # Valid with special chars
            ("short", False),        # Too short
            ("toolongvideoidddd", False),  # Too long
            ("invalid!", False),     # Invalid character
            ("", False),             # Empty
            (None, False),           # None
        ],
    )
    def test_validate_youtube_video_id(self, video_id, expected):
        """Test YouTube video ID validation."""
        from src.utils.validators import validate_youtube_video_id

        if video_id is None:
            assert validate_youtube_video_id(video_id) is False
        else:
            assert validate_youtube_video_id(video_id) is expected


class TestValidateResolution:
    """Test resolution validation."""

    @pytest.mark.parametrize(
        "width,height,expected",
        [
            (1080, 1920, True),   # 9:16 portrait (Shorts)
            (720, 1280, True),   # 9:16 portrait
            (1920, 1080, False),  # 16:9 landscape
            (0, 0, False),        # Invalid
            (-1, 100, False),     # Negative
        ],
    )
    def test_validate_resolution(self, width, height, expected):
        """Test resolution validation for Shorts."""
        from src.utils.validators import validate_resolution

        assert validate_resolution(width, height) is expected


# =============================================================================
# Decorator Tests
# =============================================================================


class TestRetryDecorator:
    """Test retry decorator."""

    def test_succeeds_without_retry(self):
        """Test function succeeds on first try."""
        from src.utils.decorators import retry

        call_count = 0

        @retry(max_attempts=3)
        def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = always_succeeds()
        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure(self):
        """Test function retries on exception."""
        from src.utils.decorators import retry

        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Simulated failure")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert call_count == 3

    def test_exhausts_retries(self):
        """Test raises after all retries exhausted."""
        from src.utils.decorators import retry

        @retry(max_attempts=3, delay=0.01)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            always_fails()


class TestCacheDecorator:
    """Test cache_result decorator."""

    def test_caches_result(self):
        """Test result is cached."""
        from src.utils.decorators import cache_result

        call_count = 0

        @cache_result(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        # Second call with same args
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once

    def test_different_args_not_cached(self):
        """Test different args get different cache entries."""
        from src.utils.decorators import cache_result

        call_count = 0

        @cache_result(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count == 2


class TestMeasureTimeDecorator:
    """Test measure_time decorator."""

    def test_returns_correct_result(self):
        """Test decorated function returns correct result."""
        from src.utils.decorators import measure_time

        @measure_time()
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_logs_execution_time(self, capture_logs):
        """Test logs execution time."""
        from src.utils.decorators import measure_time

        @measure_time(log_result=True)
        def slow_function():
            time.sleep(0.01)
            return "done"

        result = slow_function()
        assert result == "done"


class TestHandleErrorsDecorator:
    """Test handle_errors decorator."""

    def test_returns_default_on_error(self):
        """Test returns default value on error."""
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=[])
        def failing_function():
            raise ValueError("Error")

        result = failing_function()
        assert result == []

    def test_returns_normal_on_success(self):
        """Test returns normal result on success."""
        from src.utils.decorators import handle_errors

        @handle_errors(default_return=[])
        def succeeding_function():
            return [1, 2, 3]

        result = succeeding_function()
        assert result == [1, 2, 3]


class TestAsyncDecorators:
    """Test decorators with async functions."""

    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Test retry works with async functions."""
        from src.utils.decorators import retry

        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        async def async_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail")
            return "success"

        result = await async_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_cache(self):
        """Test cache works with async functions."""
        from src.utils.decorators import cache_result

        call_count = 0

        @cache_result(ttl_seconds=60)
        async def async_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await async_function(5)
        result2 = await async_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1


# =============================================================================
# Integration Tests
# =============================================================================


class TestFileManagerIntegration:
    """Integration tests for file manager."""

    def test_full_file_workflow(self, temp_dir: Path):
        """Test complete file management workflow."""
        from src.utils.file_manager import (
            ensure_directory,
            get_file_size,
            get_unique_filename,
            safe_delete,
            archive_file,
        )

        # Create structure
        data_dir = ensure_directory(temp_dir / "data")
        archive_dir = ensure_directory(temp_dir / "archives")

        # Create file
        file_path = get_unique_filename(data_dir, "test", "txt")
        file_path.write_text("Test content")

        # Check size
        size = get_file_size(file_path)
        assert size > 0

        # Archive
        archived = archive_file(file_path, archive_dir)
        assert archived.exists()
        assert not file_path.exists()

        # Cleanup
        deleted = safe_delete(archived)
        assert deleted is True
        assert not archived.exists()
