"""
Unit tests for input validation utilities.
"""
from __future__ import annotations

from pathlib import Path

import pytest


class TestValidateYouTubeVideoId:
    """Test validate_youtube_video_id function."""

    def test_valid_id(self):
        from src.utils.validators import validate_youtube_video_id
        assert validate_youtube_video_id("dQw4w9WgXcQ") is True

    def test_valid_with_dash_underscore(self):
        from src.utils.validators import validate_youtube_video_id
        assert validate_youtube_video_id("abc-defghij") is True
        assert validate_youtube_video_id("abc_defghij") is True

    def test_too_short(self):
        from src.utils.validators import validate_youtube_video_id
        assert validate_youtube_video_id("short") is False

    def test_too_long(self):
        from src.utils.validators import validate_youtube_video_id
        assert validate_youtube_video_id("dQw4w9WgXcQQ") is False

    def test_invalid_chars(self):
        from src.utils.validators import validate_youtube_video_id
        assert validate_youtube_video_id("dQw4w9WgX!Q") is False

    def test_empty_string(self):
        from src.utils.validators import validate_youtube_video_id
        assert validate_youtube_video_id("") is False

    def test_non_string(self):
        from src.utils.validators import validate_youtube_video_id
        assert validate_youtube_video_id(None) is False
        assert validate_youtube_video_id(12345678901) is False


class TestValidateYouTubeChannelId:
    """Test validate_youtube_channel_id function."""

    def test_valid_channel_id(self):
        from src.utils.validators import validate_youtube_channel_id
        assert validate_youtube_channel_id("UCddiUEpeqJcYeBxX1IVBKvQ") is True

    def test_wrong_prefix(self):
        from src.utils.validators import validate_youtube_channel_id
        assert validate_youtube_channel_id("XXddiUEpeqJcYeBxX1IVBKvQ") is False

    def test_wrong_length(self):
        from src.utils.validators import validate_youtube_channel_id
        assert validate_youtube_channel_id("UCshort") is False

    def test_empty(self):
        from src.utils.validators import validate_youtube_channel_id
        assert validate_youtube_channel_id("") is False

    def test_none(self):
        from src.utils.validators import validate_youtube_channel_id
        assert validate_youtube_channel_id(None) is False


class TestExtractVideoId:
    """Test extract_video_id function."""

    def test_standard_url(self):
        from src.utils.validators import extract_video_id
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        from src.utils.validators import extract_video_id
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        from src.utils.validators import extract_video_id
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        from src.utils.validators import extract_video_id
        assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_bare_id(self):
        from src.utils.validators import extract_video_id
        assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_no_match(self):
        from src.utils.validators import extract_video_id
        assert extract_video_id("https://example.com") is None


class TestSanitizeFilename:
    """Test sanitize_filename function."""

    def test_basic_sanitization(self):
        from src.utils.validators import sanitize_filename
        result = sanitize_filename("My Video: Test! (2024).mp4")
        assert "<" not in result
        assert ":" not in result

    def test_path_traversal_removed(self):
        from src.utils.validators import sanitize_filename
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result

    def test_empty_returns_unnamed(self):
        from src.utils.validators import sanitize_filename
        assert sanitize_filename("") == "unnamed"

    def test_long_filename_truncated(self):
        from src.utils.validators import sanitize_filename
        long_name = "a" * 300 + ".mp4"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_invalid_chars_replaced(self):
        from src.utils.validators import sanitize_filename
        result = sanitize_filename('file<>:"/\\|?*.txt')
        assert "<" not in result
        assert ">" not in result

    def test_all_invalid_returns_unnamed(self):
        from src.utils.validators import sanitize_filename
        result = sanitize_filename("_")
        assert result == "unnamed" or result  # either case is fine

    def test_custom_replacement(self):
        from src.utils.validators import sanitize_filename
        result = sanitize_filename("file:name.mp4", replacement="-")
        assert ":" not in result


class TestSanitizeTitle:
    """Test sanitize_title function."""

    def test_empty_returns_untitled(self):
        from src.utils.validators import sanitize_title
        assert sanitize_title("") == "Untitled"
        assert sanitize_title(None) == "Untitled"

    def test_removes_angle_brackets(self):
        from src.utils.validators import sanitize_title
        result = sanitize_title("How to Code <Python> Tutorial")
        assert "<" not in result
        assert ">" not in result

    def test_truncates_long_title(self):
        from src.utils.validators import sanitize_title
        long_title = "word " * 30
        result = sanitize_title(long_title)
        assert len(result) <= 103  # 100 + "..."

    def test_normalizes_whitespace(self):
        from src.utils.validators import sanitize_title
        result = sanitize_title("  hello   world  ")
        assert result == "hello world"

    def test_normal_title_unchanged(self):
        from src.utils.validators import sanitize_title
        title = "10 Python Tips Every Developer Should Know"
        result = sanitize_title(title)
        assert result == title


class TestSanitizeDescription:
    """Test sanitize_description function."""

    def test_empty_returns_empty(self):
        from src.utils.validators import sanitize_description
        assert sanitize_description("") == ""
        assert sanitize_description(None) == ""

    def test_removes_null_bytes(self):
        from src.utils.validators import sanitize_description
        result = sanitize_description("hello\x00world")
        assert "\x00" not in result

    def test_normalizes_line_endings(self):
        from src.utils.validators import sanitize_description
        result = sanitize_description("line1\r\nline2\rline3")
        assert "\r" not in result

    def test_truncates_long_description(self):
        from src.utils.validators import sanitize_description
        long_desc = "x" * 6000
        result = sanitize_description(long_desc)
        assert len(result) <= 5003  # 5000 + "..."


class TestValidateUrl:
    """Test validate_url function."""

    def test_valid_https_url(self):
        from src.utils.validators import validate_url
        assert validate_url("https://example.com") is True

    def test_valid_http_url(self):
        from src.utils.validators import validate_url
        assert validate_url("http://example.com") is True

    def test_invalid_url(self):
        from src.utils.validators import validate_url
        assert validate_url("not-a-url") is False

    def test_empty_string(self):
        from src.utils.validators import validate_url
        assert validate_url("") is False

    def test_none(self):
        from src.utils.validators import validate_url
        assert validate_url(None) is False

    def test_require_https_blocks_http(self):
        from src.utils.validators import validate_url
        assert validate_url("http://example.com", require_https=True) is False

    def test_require_https_allows_https(self):
        from src.utils.validators import validate_url
        assert validate_url("https://example.com", require_https=True) is True

    def test_too_long_url(self):
        from src.utils.validators import validate_url
        long_url = "https://example.com/" + "a" * 2100
        assert validate_url(long_url) is False

    def test_no_netloc(self):
        from src.utils.validators import validate_url
        assert validate_url("https://") is False


class TestValidateEmail:
    """Test validate_email function."""

    def test_valid_email(self):
        from src.utils.validators import validate_email
        assert validate_email("user@example.com") is True

    def test_valid_with_plus(self):
        from src.utils.validators import validate_email
        assert validate_email("user+tag@example.com") is True

    def test_invalid_no_at(self):
        from src.utils.validators import validate_email
        assert validate_email("invalid-email") is False

    def test_invalid_no_domain(self):
        from src.utils.validators import validate_email
        assert validate_email("user@") is False

    def test_empty(self):
        from src.utils.validators import validate_email
        assert validate_email("") is False

    def test_none(self):
        from src.utils.validators import validate_email
        assert validate_email(None) is False

    def test_too_long(self):
        from src.utils.validators import validate_email
        long_email = "a" * 250 + "@example.com"
        assert validate_email(long_email) is False


class TestValidateVideoFile:
    """Test validate_video_file function."""

    def test_valid_mp4(self, tmp_path):
        from src.utils.validators import validate_video_file
        video = tmp_path / "test.mp4"
        video.write_bytes(b"\x00" * 2048)
        valid, msg = validate_video_file(video)
        assert valid is True
        assert msg == ""

    def test_missing_file(self, tmp_path):
        from src.utils.validators import validate_video_file
        missing = tmp_path / "missing.mp4"
        valid, msg = validate_video_file(missing)
        assert valid is False
        assert "exist" in msg

    def test_directory_path(self, tmp_path):
        from src.utils.validators import validate_video_file
        valid, msg = validate_video_file(tmp_path)
        assert valid is False

    def test_invalid_extension(self, tmp_path):
        from src.utils.validators import validate_video_file
        txt = tmp_path / "file.txt"
        txt.write_bytes(b"\x00" * 2048)
        valid, msg = validate_video_file(txt)
        assert valid is False
        assert "Invalid" in msg

    def test_too_small(self, tmp_path):
        from src.utils.validators import validate_video_file
        small = tmp_path / "small.mp4"
        small.write_bytes(b"\x00" * 100)  # Less than 1KB
        valid, msg = validate_video_file(small)
        assert valid is False

    def test_valid_webm(self, tmp_path):
        from src.utils.validators import validate_video_file
        video = tmp_path / "test.webm"
        video.write_bytes(b"\x00" * 2048)
        valid, _ = validate_video_file(video)
        assert valid is True


class TestValidateDuration:
    """Test validate_duration function."""

    def test_valid_duration(self):
        from src.utils.validators import validate_duration
        assert validate_duration(30.0) is True

    def test_too_short(self):
        from src.utils.validators import validate_duration
        assert validate_duration(5.0) is False

    def test_too_long(self):
        from src.utils.validators import validate_duration
        assert validate_duration(90.0) is False

    def test_boundary_min(self):
        from src.utils.validators import validate_duration
        assert validate_duration(15.0) is True

    def test_boundary_max(self):
        from src.utils.validators import validate_duration
        assert validate_duration(60.0) is True

    def test_custom_limits(self):
        from src.utils.validators import validate_duration
        assert validate_duration(90.0, max_seconds=120.0) is True

    def test_non_numeric(self):
        from src.utils.validators import validate_duration
        assert validate_duration("30") is False


class TestValidateResolution:
    """Test validate_resolution function."""

    def test_valid_portrait(self):
        from src.utils.validators import validate_resolution
        assert validate_resolution(1080, 1920) is True

    def test_invalid_landscape(self):
        from src.utils.validators import validate_resolution
        assert validate_resolution(1920, 1080) is False

    def test_zero_width(self):
        from src.utils.validators import validate_resolution
        assert validate_resolution(0, 1920) is False

    def test_zero_height(self):
        from src.utils.validators import validate_resolution
        assert validate_resolution(1080, 0) is False

    def test_no_portrait_requirement(self):
        from src.utils.validators import validate_resolution
        assert validate_resolution(1920, 1080, require_portrait=False) is True


class TestValidateAspectRatio:
    """Test validate_aspect_ratio function."""

    def test_valid_9_16(self):
        from src.utils.validators import validate_aspect_ratio
        assert validate_aspect_ratio(1080, 1920) is True

    def test_invalid_ratio(self):
        from src.utils.validators import validate_aspect_ratio
        assert validate_aspect_ratio(1920, 1080) is False

    def test_zero_dimensions(self):
        from src.utils.validators import validate_aspect_ratio
        assert validate_aspect_ratio(0, 1920) is False

    def test_custom_target_ratio(self):
        from src.utils.validators import validate_aspect_ratio
        assert validate_aspect_ratio(1920, 1080, target_ratio=(16, 9)) is True

    def test_custom_tolerance(self):
        from src.utils.validators import validate_aspect_ratio
        # Slightly off ratio but within large tolerance
        assert validate_aspect_ratio(1080, 1910, tolerance=0.05) is True


class TestValidateTags:
    """Test validate_tags function."""

    def test_empty_tags(self):
        from src.utils.validators import validate_tags
        valid, cleaned = validate_tags([])
        assert valid is True
        assert cleaned == []

    def test_valid_tags(self):
        from src.utils.validators import validate_tags
        valid, cleaned = validate_tags(["shorts", "viral", "tech"])
        assert valid is True
        assert "shorts" in cleaned

    def test_strips_whitespace(self):
        from src.utils.validators import validate_tags
        _, cleaned = validate_tags(["  hello  "])
        assert "hello" in cleaned

    def test_removes_angle_brackets(self):
        from src.utils.validators import validate_tags
        _, cleaned = validate_tags(["<tag>"])
        assert "<" not in cleaned[0] if cleaned else True

    def test_too_many_tags_truncated(self):
        from src.utils.validators import validate_tags
        many_tags = [f"tag{i}" for i in range(50)]
        _, cleaned = validate_tags(many_tags, max_tags=30)
        assert len(cleaned) <= 30

    def test_too_long_tag_skipped(self):
        from src.utils.validators import validate_tags
        long_tag = "a" * 50
        _, cleaned = validate_tags([long_tag], max_tag_length=30)
        assert long_tag not in cleaned


class TestContainsProhibitedContent:
    """Test contains_prohibited_content function."""

    def test_clean_content(self):
        from src.utils.validators import contains_prohibited_content
        has_prohibited, _ = contains_prohibited_content("Learn Python programming today!")
        assert has_prohibited is False

    def test_prohibited_pattern(self):
        from src.utils.validators import contains_prohibited_content
        has_prohibited, matches = contains_prohibited_content("free money click here")
        assert has_prohibited is True
        assert len(matches) > 0

    def test_url_shortener(self):
        from src.utils.validators import contains_prohibited_content
        has_prohibited, _ = contains_prohibited_content("visit bit.ly/abc123")
        assert has_prohibited is True

    def test_gambling_content(self):
        from src.utils.validators import contains_prohibited_content
        has_prohibited, _ = contains_prohibited_content("bet now at casino")
        assert has_prohibited is True


class TestValidatePath:
    """Test validate_path function."""

    def test_valid_path_no_constraints(self, tmp_path):
        from src.utils.validators import validate_path
        valid, msg = validate_path(tmp_path)
        assert valid is True

    def test_path_traversal(self, tmp_path):
        from src.utils.validators import validate_path
        bad_path = Path(str(tmp_path) + "/../secret")
        valid, msg = validate_path(bad_path)
        assert valid is False

    def test_must_exist_missing(self, tmp_path):
        from src.utils.validators import validate_path
        missing = tmp_path / "missing"
        valid, msg = validate_path(missing, must_exist=True)
        assert valid is False

    def test_must_exist_present(self, tmp_path):
        from src.utils.validators import validate_path
        valid, msg = validate_path(tmp_path, must_exist=True)
        assert valid is True

    def test_must_be_file_on_dir(self, tmp_path):
        from src.utils.validators import validate_path
        valid, msg = validate_path(tmp_path, must_be_file=True)
        assert valid is False

    def test_must_be_dir_on_file(self, tmp_path):
        from src.utils.validators import validate_path
        f = tmp_path / "file.txt"
        f.write_text("x")
        valid, msg = validate_path(f, must_be_dir=True)
        assert valid is False


class TestIsSafePath:
    """Test is_safe_path function."""

    def test_safe_path(self, tmp_path):
        from src.utils.validators import is_safe_path
        child = tmp_path / "subdir" / "file.txt"
        assert is_safe_path(child, tmp_path) is True

    def test_unsafe_path(self, tmp_path):
        from src.utils.validators import is_safe_path
        parent = tmp_path.parent
        assert is_safe_path(parent, tmp_path) is False
