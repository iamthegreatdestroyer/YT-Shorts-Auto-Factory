"""
Input validation utilities for the YouTube Shorts Factory.

This module provides validation functions for:
- YouTube video/channel IDs
- Filenames and titles
- URLs and emails
- Video specifications (duration, resolution)
- Content sanitization

Example:
    >>> from src.utils.validators import validate_url, sanitize_filename
    >>> validate_url("https://youtube.com")
    True
    >>> sanitize_filename("My Video: Test! (2024).mp4")
    'My_Video_Test_2024.mp4'
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


# =============================================================================
# YouTube Validation
# =============================================================================


def validate_youtube_video_id(video_id: str) -> bool:
    """
    Check if string matches YouTube video ID format.

    YouTube video IDs are 11 characters containing alphanumeric,
    dash (-), and underscore (_) characters.

    Args:
        video_id: String to validate.

    Returns:
        True if valid YouTube video ID format.

    Example:
        >>> validate_youtube_video_id("dQw4w9WgXcQ")
        True
        >>> validate_youtube_video_id("invalid!")
        False
    """
    if not video_id or not isinstance(video_id, str):
        return False
    return bool(re.match(r"^[A-Za-z0-9_-]{11}$", video_id))


def validate_youtube_channel_id(channel_id: str) -> bool:
    """
    Check if string matches YouTube channel ID format.

    Channel IDs start with "UC" and are 24 characters.

    Args:
        channel_id: String to validate.

    Returns:
        True if valid YouTube channel ID format.
    """
    if not channel_id or not isinstance(channel_id, str):
        return False
    return bool(re.match(r"^UC[A-Za-z0-9_-]{22}$", channel_id))


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID

    Args:
        url: YouTube URL.

    Returns:
        Video ID if found, None otherwise.
    """
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",  # Just the ID
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# =============================================================================
# Filename Sanitization
# =============================================================================


def sanitize_filename(
    filename: str,
    max_length: int = 255,
    replacement: str = "_",
) -> str:
    """
    Remove invalid characters for filenames.

    Removes:
    - Invalid filesystem characters (<>:"/\\|?*)
    - Path traversal attempts (..)
    - Control characters
    - Leading/trailing whitespace and dots

    Args:
        filename: Original filename.
        max_length: Maximum length (default 255 for most filesystems).
        replacement: Character to replace invalid chars with.

    Returns:
        Sanitized filename safe for any filesystem.

    Example:
        >>> sanitize_filename("My Video: Test! (2024).mp4")
        'My_Video_Test_2024.mp4'
        >>> sanitize_filename("../../../etc/passwd")
        'etc_passwd'
    """
    if not filename:
        return "unnamed"

    # Remove path traversal
    filename = filename.replace("..", "")

    # Remove invalid filesystem characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, replacement, filename)

    # Replace multiple spaces/underscores with single
    filename = re.sub(r"[_\s]+", replacement, filename)

    # Remove leading/trailing dots and whitespace
    filename = filename.strip(". \t\n\r")

    # Truncate to max length while preserving extension
    if len(filename) > max_length:
        path = Path(filename)
        extension = path.suffix[:20]  # Max 20 char extension
        stem_max = max_length - len(extension)
        filename = path.stem[:stem_max] + extension

    # Ensure not empty after sanitization
    if not filename or filename == replacement:
        filename = "unnamed"

    return filename


def sanitize_title(
    title: str,
    max_length: int = 100,
) -> str:
    """
    Sanitize title for YouTube compatibility.

    YouTube forbids:
    - < and > characters
    - Leading/trailing whitespace
    - Titles over 100 characters

    Args:
        title: Original title.
        max_length: Maximum length (YouTube limit is 100).

    Returns:
        Sanitized title safe for YouTube.

    Example:
        >>> sanitize_title("How to Code <Python> Tutorial!!!")
        'How to Code Python Tutorial!!!'
    """
    if not title:
        return "Untitled"

    # Remove < and >
    title = re.sub(r"[<>]", "", title)

    # Normalize whitespace
    title = " ".join(title.split())

    # Strip
    title = title.strip()

    # Truncate
    if len(title) > max_length:
        title = title[: max_length - 3].rsplit(" ", 1)[0] + "..."

    return title or "Untitled"


def sanitize_description(
    description: str,
    max_length: int = 5000,
) -> str:
    """
    Sanitize description for YouTube compatibility.

    Args:
        description: Original description.
        max_length: Maximum length (YouTube limit is 5000).

    Returns:
        Sanitized description.
    """
    if not description:
        return ""

    # Remove null characters
    description = description.replace("\x00", "")

    # Normalize line endings
    description = description.replace("\r\n", "\n").replace("\r", "\n")

    # Truncate
    if len(description) > max_length:
        description = description[: max_length - 3] + "..."

    return description


# =============================================================================
# URL Validation
# =============================================================================


def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Check if string is valid HTTP/HTTPS URL.

    Args:
        url: String to validate.
        require_https: If True, only accept HTTPS URLs.

    Returns:
        True if valid URL.

    Example:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("not-a-url")
        False
    """
    if not url or not isinstance(url, str):
        return False

    try:
        result = urlparse(url)
        schemes = ("https",) if require_https else ("http", "https")
        return (
            result.scheme in schemes
            and result.netloc != ""
            and len(url) <= 2048  # Reasonable URL length limit
        )
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """
    Check if string is valid email format.

    Uses a practical regex that catches most invalid emails
    without being overly strict.

    Args:
        email: String to validate.

    Returns:
        True if valid email format.

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        return False

    # Practical email regex
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email)) and len(email) <= 254


# =============================================================================
# Video Validation
# =============================================================================


def validate_video_file(path: Path) -> tuple[bool, str]:
    """
    Check if file exists and is a valid video format.

    Args:
        path: Path to video file.

    Returns:
        Tuple of (is_valid, error_message).

    Example:
        >>> validate_video_file(Path("video.mp4"))
        (True, "")
        >>> validate_video_file(Path("missing.mp4"))
        (False, "File does not exist")
    """
    if not path.exists():
        return False, "File does not exist"

    if not path.is_file():
        return False, "Path is not a file"

    # Check extension
    valid_extensions = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv"}
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid video format: {path.suffix}"

    # Check file is readable
    try:
        with open(path, "rb") as f:
            f.read(1)
    except OSError as e:
        return False, f"Cannot read file: {e}"

    # Check minimum size (at least 1KB)
    if path.stat().st_size < 1024:
        return False, "File too small to be a valid video"

    return True, ""


def validate_duration(
    duration: float,
    min_seconds: float = 15.0,
    max_seconds: float = 60.0,
) -> bool:
    """
    Check if duration is within YouTube Shorts limits.

    Default limits: 15-60 seconds for Shorts.

    Args:
        duration: Duration in seconds.
        min_seconds: Minimum allowed duration.
        max_seconds: Maximum allowed duration.

    Returns:
        True if duration is within limits.

    Example:
        >>> validate_duration(30.0)
        True
        >>> validate_duration(90.0)
        False
    """
    if not isinstance(duration, (int, float)):
        return False
    return min_seconds <= duration <= max_seconds


def validate_resolution(
    width: int,
    height: int,
    require_portrait: bool = True,
) -> bool:
    """
    Check if resolution is valid for YouTube Shorts.

    Shorts require 9:16 aspect ratio (portrait).

    Args:
        width: Video width in pixels.
        height: Video height in pixels.
        require_portrait: If True, enforce 9:16 aspect ratio.

    Returns:
        True if resolution is valid.

    Example:
        >>> validate_resolution(1080, 1920)  # 9:16 portrait
        True
        >>> validate_resolution(1920, 1080)  # 16:9 landscape
        False
    """
    if width <= 0 or height <= 0:
        return False

    if require_portrait:
        # Check 9:16 aspect ratio with some tolerance
        expected_ratio = 9 / 16
        actual_ratio = width / height
        return abs(actual_ratio - expected_ratio) < 0.01

    return True


def validate_aspect_ratio(
    width: int,
    height: int,
    target_ratio: tuple[int, int] = (9, 16),
    tolerance: float = 0.02,
) -> bool:
    """
    Check if dimensions match target aspect ratio.

    Args:
        width: Width in pixels.
        height: Height in pixels.
        target_ratio: Target ratio as (width, height) tuple.
        tolerance: Allowed deviation from target ratio.

    Returns:
        True if aspect ratio matches within tolerance.
    """
    if width <= 0 or height <= 0:
        return False

    target = target_ratio[0] / target_ratio[1]
    actual = width / height
    return abs(actual - target) <= tolerance


# =============================================================================
# Content Validation
# =============================================================================


def validate_tags(
    tags: list[str],
    max_tags: int = 30,
    max_tag_length: int = 30,
) -> tuple[bool, list[str]]:
    """
    Validate and clean YouTube tags.

    Args:
        tags: List of tags.
        max_tags: Maximum number of tags allowed.
        max_tag_length: Maximum length per tag.

    Returns:
        Tuple of (is_valid, cleaned_tags).
    """
    if not tags:
        return True, []

    cleaned = []
    for tag in tags[:max_tags]:
        # Clean tag
        tag = str(tag).strip()
        if tag and len(tag) <= max_tag_length:
            # Remove < and >
            tag = re.sub(r"[<>]", "", tag)
            if tag:
                cleaned.append(tag)

    return True, cleaned


def contains_prohibited_content(text: str) -> tuple[bool, list[str]]:
    """
    Check if text contains potentially prohibited content.

    Checks for common spam patterns and prohibited terms.
    This is a basic check - YouTube has more sophisticated filters.

    Args:
        text: Text to check.

    Returns:
        Tuple of (has_prohibited, list of matched patterns).
    """
    prohibited_patterns = [
        r"\b(free money|make money fast)\b",
        r"\b(click here|subscribe now)\b",
        r"(bit\.ly|tinyurl|shorturl)",
        r"\b(casino|gambling|bet now)\b",
        r"[^\x00-\x7F]{20,}",  # Long non-ASCII sequences
    ]

    matches = []
    text_lower = text.lower()

    for pattern in prohibited_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matches.append(pattern)

    return bool(matches), matches


# =============================================================================
# Path Validation
# =============================================================================


def validate_path(
    path: Path,
    must_exist: bool = False,
    must_be_file: bool = False,
    must_be_dir: bool = False,
) -> tuple[bool, str]:
    """
    Validate a file system path.

    Args:
        path: Path to validate.
        must_exist: If True, path must exist.
        must_be_file: If True, path must be a file.
        must_be_dir: If True, path must be a directory.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        # Check for path traversal
        resolved = path.resolve()
        if ".." in str(path):
            return False, "Path contains traversal patterns"

        if must_exist and not path.exists():
            return False, f"Path does not exist: {path}"

        if must_be_file and not path.is_file():
            return False, f"Path is not a file: {path}"

        if must_be_dir and not path.is_dir():
            return False, f"Path is not a directory: {path}"

        return True, ""

    except OSError as e:
        return False, f"Invalid path: {e}"


def is_safe_path(path: Path, base_dir: Path) -> bool:
    """
    Check if path is safely within base directory.

    Prevents path traversal attacks.

    Args:
        path: Path to check.
        base_dir: Base directory that path should be within.

    Returns:
        True if path is within base_dir.
    """
    try:
        resolved = path.resolve()
        base_resolved = base_dir.resolve()
        return str(resolved).startswith(str(base_resolved))
    except OSError:
        return False
