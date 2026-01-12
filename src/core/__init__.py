"""
Core module - Foundation components for the YT-Shorts-Auto-Factory.

This module contains essential components including:
- Configuration management
- Custom exceptions
- Application constants
- Logging infrastructure
- Base classes and protocols
"""

from src.core.exceptions import (
    YTShortsError,
    ConfigurationError,
    APIError,
    ContentGenerationError,
    MediaCreationError,
    UploadError,
    ValidationError,
)
from src.core.constants import (
    VIDEO_DURATION_MIN,
    VIDEO_DURATION_MAX,
    SUPPORTED_FORMATS,
    API_RATE_LIMITS,
)

__all__ = [
    # Exceptions
    "YTShortsError",
    "ConfigurationError",
    "APIError",
    "ContentGenerationError",
    "MediaCreationError",
    "UploadError",
    "ValidationError",
    # Constants
    "VIDEO_DURATION_MIN",
    "VIDEO_DURATION_MAX",
    "SUPPORTED_FORMATS",
    "API_RATE_LIMITS",
]
