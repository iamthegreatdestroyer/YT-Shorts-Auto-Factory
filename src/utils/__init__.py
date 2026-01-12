"""
Utilities module - Shared helper functions and utilities.

This module contains:
- File system utilities
- HTTP client helpers
- Data validation utilities
- Retry and resilience utilities
- Date/time helpers
"""

from src.utils.file_manager import (
    ensure_directory,
    get_file_size,
    get_file_size_human,
    get_available_space,
    cleanup_old_files,
    archive_file,
    safe_delete,
    get_unique_filename,
    compute_file_hash,
    download_file,
    copy_file,
    get_directory_size,
)

from src.utils.validators import (
    validate_youtube_video_id,
    validate_youtube_channel_id,
    extract_video_id,
    sanitize_filename,
    sanitize_title,
    sanitize_description,
    validate_url,
    validate_email,
    validate_video_file,
    validate_duration,
    validate_resolution,
    validate_aspect_ratio,
    validate_tags,
    contains_prohibited_content,
    validate_path,
    is_safe_path,
)

from src.utils.decorators import (
    retry,
    timeout,
    cache_result,
    measure_time,
    handle_errors,
    deprecated,
    rate_limit,
    singleton,
)

__all__ = [
    # File manager
    "ensure_directory",
    "get_file_size",
    "get_file_size_human",
    "get_available_space",
    "cleanup_old_files",
    "archive_file",
    "safe_delete",
    "get_unique_filename",
    "compute_file_hash",
    "download_file",
    "copy_file",
    "get_directory_size",
    # Validators
    "validate_youtube_video_id",
    "validate_youtube_channel_id",
    "extract_video_id",
    "sanitize_filename",
    "sanitize_title",
    "sanitize_description",
    "validate_url",
    "validate_email",
    "validate_video_file",
    "validate_duration",
    "validate_resolution",
    "validate_aspect_ratio",
    "validate_tags",
    "contains_prohibited_content",
    "validate_path",
    "is_safe_path",
    # Decorators
    "retry",
    "timeout",
    "cache_result",
    "measure_time",
    "handle_errors",
    "deprecated",
    "rate_limit",
    "singleton",
]

__all__: list[str] = []
