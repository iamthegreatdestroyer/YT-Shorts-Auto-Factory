"""
Constants and enumerations for the YouTube Shorts Automation Factory.

This module defines all immutable values, API limits, video specifications,
and enumeration types used throughout the application.

Usage:
    >>> from src.core.constants import VIDEO_DURATION_MIN, VideoFormat
    >>> print(VIDEO_DURATION_MIN)
    15
    >>> print(VideoFormat.MP4.value)
    'mp4'
"""

from __future__ import annotations

import re
from enum import Enum, IntEnum, auto
from pathlib import Path
from typing import Final


# =============================================================================
# Application Constants
# =============================================================================


class AppConstants:
    """Application-level constants."""

    # Application Identity
    APP_NAME: Final[str] = "YouTube Shorts Factory"
    APP_VERSION: Final[str] = "0.1.0"
    APP_DESCRIPTION: Final[str] = (
        "Automated YouTube Shorts content generation and publishing"
    )

    # Project Paths
    PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent
    SRC_DIR: Final[Path] = PROJECT_ROOT / "src"
    CONFIG_DIR: Final[Path] = PROJECT_ROOT / "config"
    ASSETS_DIR: Final[Path] = PROJECT_ROOT / "assets"
    DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
    LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"

    # File Markers
    GITKEEP: Final[str] = ".gitkeep"
    ENV_FILE: Final[str] = ".env"
    CONFIG_FILE: Final[str] = "config.yaml"


# =============================================================================
# Video Constants
# =============================================================================


# Duration constraints (in seconds)
VIDEO_DURATION_MIN: Final[int] = 15  # YouTube Shorts minimum
VIDEO_DURATION_MAX: Final[int] = 60  # YouTube Shorts maximum
VIDEO_DURATION_DEFAULT: Final[int] = 45  # Optimal duration

# Resolution (vertical format for Shorts)
VIDEO_WIDTH: Final[int] = 1080
VIDEO_HEIGHT: Final[int] = 1920
VIDEO_ASPECT_RATIO: Final[str] = "9:16"

# Frame rates
VIDEO_FPS_MIN: Final[int] = 24
VIDEO_FPS_DEFAULT: Final[int] = 30
VIDEO_FPS_MAX: Final[int] = 60

# Bitrates (in bits per second)
VIDEO_BITRATE_LOW: Final[str] = "4M"
VIDEO_BITRATE_MEDIUM: Final[str] = "8M"
VIDEO_BITRATE_HIGH: Final[str] = "12M"
VIDEO_BITRATE_ULTRA: Final[str] = "20M"

# File size limits
VIDEO_MAX_FILE_SIZE_MB: Final[int] = 256
VIDEO_MAX_FILE_SIZE_BYTES: Final[int] = VIDEO_MAX_FILE_SIZE_MB * 1024 * 1024


class VideoConstants:
    """Video processing constants."""

    # Resolution presets
    RESOLUTIONS: Final[dict[str, tuple[int, int]]] = {
        "360p": (360, 640),
        "480p": (480, 854),
        "720p": (720, 1280),
        "1080p": (1080, 1920),
        "1440p": (1440, 2560),
        "4k": (2160, 3840),
    }

    # Codec options
    VIDEO_CODEC: Final[str] = "libx264"
    AUDIO_CODEC: Final[str] = "aac"
    PIXEL_FORMAT: Final[str] = "yuv420p"

    # Encoding presets
    ENCODING_PRESETS: Final[list[str]] = [
        "ultrafast",
        "superfast",
        "veryfast",
        "faster",
        "fast",
        "medium",
        "slow",
        "slower",
        "veryslow",
    ]

    # CRF (Constant Rate Factor) for quality
    CRF_HIGH_QUALITY: Final[int] = 18
    CRF_BALANCED: Final[int] = 23
    CRF_LOW_QUALITY: Final[int] = 28

    # FFmpeg constants
    FFMPEG_LOGLEVEL: Final[str] = "warning"
    FFMPEG_THREADS: Final[int] = 0  # Auto-detect


# =============================================================================
# Audio Constants
# =============================================================================


class AudioConstants:
    """Audio processing constants."""

    # Sample rates (Hz)
    SAMPLE_RATE_LOW: Final[int] = 22050
    SAMPLE_RATE_STANDARD: Final[int] = 44100
    SAMPLE_RATE_HIGH: Final[int] = 48000

    # Bitrates (kbps)
    AUDIO_BITRATE_LOW: Final[str] = "128k"
    AUDIO_BITRATE_MEDIUM: Final[str] = "192k"
    AUDIO_BITRATE_HIGH: Final[str] = "320k"

    # Channels
    MONO: Final[int] = 1
    STEREO: Final[int] = 2

    # TTS speed range
    TTS_SPEED_MIN: Final[float] = 0.5
    TTS_SPEED_MAX: Final[float] = 2.0
    TTS_SPEED_DEFAULT: Final[float] = 1.0

    # Volume normalization
    TARGET_LOUDNESS: Final[int] = -16  # LUFS
    MUSIC_VOLUME_DEFAULT: Final[float] = 0.15  # 15% background music volume


# =============================================================================
# Image Constants
# =============================================================================


class ImageConstants:
    """Image processing constants."""

    # Image dimensions for Shorts
    IMAGE_WIDTH: Final[int] = 1080
    IMAGE_HEIGHT: Final[int] = 1920

    # Thumbnail dimensions
    THUMBNAIL_WIDTH: Final[int] = 1280
    THUMBNAIL_HEIGHT: Final[int] = 720

    # Compression quality
    JPEG_QUALITY: Final[int] = 95
    PNG_COMPRESSION: Final[int] = 6
    WEBP_QUALITY: Final[int] = 90

    # Image generation
    SD_DEFAULT_STEPS: Final[int] = 30
    SD_DEFAULT_CFG: Final[float] = 7.5
    SD_MAX_STEPS: Final[int] = 150

    # Size limits
    MAX_IMAGE_SIZE_MB: Final[int] = 10


# =============================================================================
# API Rate Limits
# =============================================================================


class APIRateLimits:
    """API rate limit configurations."""

    # YouTube Data API v3
    YOUTUBE_DAILY_QUOTA: Final[int] = 10000  # Default quota units/day
    YOUTUBE_UPLOAD_COST: Final[int] = 1600  # Quota cost per upload
    YOUTUBE_LIST_COST: Final[int] = 1  # Quota cost per list operation
    YOUTUBE_UPDATE_COST: Final[int] = 50  # Quota cost per update

    # Reddit API
    REDDIT_REQUESTS_PER_MINUTE: Final[int] = 60
    REDDIT_REQUESTS_PER_SECOND: Final[int] = 1

    # ElevenLabs
    ELEVENLABS_CHARS_PER_REQUEST: Final[int] = 5000
    ELEVENLABS_REQUESTS_PER_SECOND: Final[int] = 2

    # Stock APIs
    PEXELS_REQUESTS_PER_MONTH: Final[int] = 200
    PIXABAY_REQUESTS_PER_MINUTE: Final[int] = 100
    UNSPLASH_REQUESTS_PER_HOUR: Final[int] = 50

    # General scraping
    SCRAPE_DELAY_SECONDS: Final[float] = 2.0
    SCRAPE_MAX_RETRIES: Final[int] = 3


# Convenience alias
API_RATE_LIMITS = APIRateLimits


# =============================================================================
# File Format Enumerations
# =============================================================================


class VideoFormat(str, Enum):
    """Supported video file formats."""

    MP4 = "mp4"
    WEBM = "webm"
    MOV = "mov"
    AVI = "avi"
    MKV = "mkv"

    @classmethod
    def from_path(cls, path: Path | str) -> "VideoFormat":
        """Get format from file path."""
        suffix = Path(path).suffix.lower().lstrip(".")
        try:
            return cls(suffix)
        except ValueError:
            raise ValueError(f"Unsupported video format: {suffix}")


class AudioFormat(str, Enum):
    """Supported audio file formats."""

    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    AAC = "aac"
    FLAC = "flac"
    M4A = "m4a"


class ImageFormat(str, Enum):
    """Supported image file formats."""

    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
    BMP = "bmp"


# Convenient sets for validation
SUPPORTED_VIDEO_FORMATS: Final[set[str]] = {f.value for f in VideoFormat}
SUPPORTED_AUDIO_FORMATS: Final[set[str]] = {f.value for f in AudioFormat}
SUPPORTED_IMAGE_FORMATS: Final[set[str]] = {f.value for f in ImageFormat}
SUPPORTED_FORMATS: Final[dict[str, set[str]]] = {
    "video": SUPPORTED_VIDEO_FORMATS,
    "audio": SUPPORTED_AUDIO_FORMATS,
    "image": SUPPORTED_IMAGE_FORMATS,
}


# =============================================================================
# YouTube Category IDs
# =============================================================================


class YouTubeCategory(IntEnum):
    """YouTube video category IDs."""

    FILM_ANIMATION = 1
    AUTOS_VEHICLES = 2
    MUSIC = 10
    PETS_ANIMALS = 15
    SPORTS = 17
    SHORT_MOVIES = 18
    TRAVEL_EVENTS = 19
    GAMING = 20
    VIDEOBLOGGING = 21
    PEOPLE_BLOGS = 22
    COMEDY = 23
    ENTERTAINMENT = 24
    NEWS_POLITICS = 25
    HOWTO_STYLE = 26
    EDUCATION = 27
    SCIENCE_TECH = 28
    NONPROFITS_ACTIVISM = 29

    @classmethod
    def from_name(cls, name: str) -> "YouTubeCategory":
        """Get category by name (case-insensitive)."""
        name = name.upper().replace(" ", "_").replace("&", "_")
        try:
            return cls[name]
        except KeyError:
            # Try partial match
            for member in cls:
                if name in member.name:
                    return member
            raise ValueError(f"Unknown YouTube category: {name}")


# =============================================================================
# Content Types and Styles
# =============================================================================


class ContentNiche(str, Enum):
    """Content niche categories."""

    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    GAMING = "gaming"
    LIFESTYLE = "lifestyle"
    BUSINESS = "business"
    SCIENCE = "science"
    HEALTH = "health"
    TRAVEL = "travel"
    FOOD = "food"
    SPORTS = "sports"
    NEWS = "news"
    COMEDY = "comedy"
    MUSIC = "music"
    ANIMALS = "animals"


class ContentStyle(str, Enum):
    """Content presentation styles."""

    INFORMATIVE = "informative"
    ENTERTAINING = "entertaining"
    EDUCATIONAL = "educational"
    DRAMATIC = "dramatic"
    HUMOROUS = "humorous"
    INSPIRATIONAL = "inspirational"
    CONTROVERSIAL = "controversial"


class ContentTone(str, Enum):
    """Voice/tone for content."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENERGETIC = "energetic"
    CALM = "calm"
    SERIOUS = "serious"
    PLAYFUL = "playful"
    AUTHORITATIVE = "authoritative"


# =============================================================================
# Pipeline Stages
# =============================================================================


class PipelineStage(str, Enum):
    """Video generation pipeline stages."""

    TREND_ANALYSIS = "trend_analysis"
    CONTENT_PLANNING = "content_planning"
    SCRIPT_GENERATION = "script_generation"
    TTS_GENERATION = "tts_generation"
    IMAGE_GENERATION = "image_generation"
    VIDEO_COMPILATION = "video_compilation"
    THUMBNAIL_GENERATION = "thumbnail_generation"
    METADATA_OPTIMIZATION = "metadata_optimization"
    QUALITY_CHECK = "quality_check"
    UPLOAD = "upload"
    CLEANUP = "cleanup"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


# =============================================================================
# Trend Sources
# =============================================================================


class TrendSource(str, Enum):
    """Trend data sources."""

    YOUTUBE = "youtube"
    GOOGLE_TRENDS = "google_trends"
    REDDIT = "reddit"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    NEWS = "news"
    MANUAL = "manual"


# =============================================================================
# Regex Patterns
# =============================================================================


class RegexPatterns:
    """Compiled regex patterns for validation."""

    # YouTube patterns
    YOUTUBE_VIDEO_ID: Final[re.Pattern[str]] = re.compile(
        r"^[a-zA-Z0-9_-]{11}$"
    )
    YOUTUBE_CHANNEL_ID: Final[re.Pattern[str]] = re.compile(
        r"^UC[a-zA-Z0-9_-]{22}$"
    )
    YOUTUBE_PLAYLIST_ID: Final[re.Pattern[str]] = re.compile(
        r"^PL[a-zA-Z0-9_-]{32}$"
    )
    YOUTUBE_URL: Final[re.Pattern[str]] = re.compile(
        r"^(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/"
    )

    # File name patterns
    SAFE_FILENAME: Final[re.Pattern[str]] = re.compile(
        r'^[a-zA-Z0-9][a-zA-Z0-9_\-\.]*$'
    )
    TIMESTAMP: Final[re.Pattern[str]] = re.compile(
        r"^\d{4}-\d{2}-\d{2}[T_]\d{2}-\d{2}-\d{2}$"
    )

    # Content patterns
    HASHTAG: Final[re.Pattern[str]] = re.compile(r"#\w+")
    MENTION: Final[re.Pattern[str]] = re.compile(r"@\w+")
    URL: Final[re.Pattern[str]] = re.compile(
        r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}"
        r"\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
    )
    EMAIL: Final[re.Pattern[str]] = re.compile(
        r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )

    # Cleanup patterns
    MULTIPLE_SPACES: Final[re.Pattern[str]] = re.compile(r"\s+")
    SPECIAL_CHARS: Final[re.Pattern[str]] = re.compile(r"[^\w\s\-_.]")


# =============================================================================
# HTTP Constants
# =============================================================================


class HTTPConstants:
    """HTTP-related constants."""

    # Timeouts (in seconds)
    CONNECT_TIMEOUT: Final[int] = 10
    READ_TIMEOUT: Final[int] = 30
    UPLOAD_TIMEOUT: Final[int] = 600  # 10 minutes for uploads

    # Retry settings
    MAX_RETRIES: Final[int] = 3
    RETRY_BACKOFF_FACTOR: Final[float] = 2.0
    RETRY_STATUS_CODES: Final[frozenset[int]] = frozenset({
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    })

    # User agents
    DEFAULT_USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    BOT_USER_AGENT: Final[str] = (
        f"YTShortsFactory/{AppConstants.APP_VERSION} "
        "(+https://github.com/YTShortsFactory)"
    )

    # Headers
    ACCEPT_JSON: Final[str] = "application/json"
    ACCEPT_HTML: Final[str] = "text/html,application/xhtml+xml"
    CONTENT_TYPE_JSON: Final[str] = "application/json"
    CONTENT_TYPE_FORM: Final[str] = "application/x-www-form-urlencoded"


# =============================================================================
# Cache Constants
# =============================================================================


class CacheConstants:
    """Caching configuration constants."""

    # TTL values (in seconds)
    TREND_CACHE_TTL: Final[int] = 3600  # 1 hour
    SCRIPT_CACHE_TTL: Final[int] = 86400  # 24 hours
    IMAGE_CACHE_TTL: Final[int] = 604800  # 7 days
    API_CACHE_TTL: Final[int] = 300  # 5 minutes

    # Size limits
    MAX_CACHE_SIZE_MB: Final[int] = 1024  # 1 GB
    MAX_CACHE_ENTRIES: Final[int] = 10000


# =============================================================================
# Logging Constants
# =============================================================================


class LogConstants:
    """Logging configuration constants."""

    # Log file settings
    LOG_ROTATION: Final[str] = "10 MB"
    LOG_RETENTION: Final[str] = "30 days"
    LOG_COMPRESSION: Final[str] = "gz"

    # Log formats
    LOG_FORMAT_SIMPLE: Final[str] = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )
    LOG_FORMAT_DETAILED: Final[str] = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{name}:{function}:{line} | {message}"
    )
    LOG_FORMAT_JSON: Final[str] = "{message}"

    # Log colors
    LOG_COLORS: Final[dict[str, str]] = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bold",
    }


# =============================================================================
# Default Values
# =============================================================================


class Defaults:
    """Default values for various settings."""

    # Content
    DEFAULT_LANGUAGE: Final[str] = "en"
    DEFAULT_REGION: Final[str] = "US"
    DEFAULT_TIMEZONE: Final[str] = "UTC"

    # Video
    DEFAULT_PRIVACY: Final[str] = "private"
    DEFAULT_CATEGORY: Final[int] = YouTubeCategory.ENTERTAINMENT.value
    DEFAULT_HASHTAGS: Final[list[str]] = ["#shorts", "#viral", "#trending"]

    # Processing
    BATCH_SIZE: Final[int] = 3
    MAX_CONCURRENT_TASKS: Final[int] = 5
    TEMP_FILE_MAX_AGE_HOURS: Final[int] = 24

    # SEO
    TITLE_MAX_LENGTH: Final[int] = 100
    DESCRIPTION_MAX_LENGTH: Final[int] = 5000
    MAX_TAGS: Final[int] = 500


# =============================================================================
# Error Messages
# =============================================================================


class ErrorMessages:
    """Standard error message templates."""

    # Generic
    UNKNOWN_ERROR: Final[str] = "An unexpected error occurred: {error}"
    INVALID_INPUT: Final[str] = "Invalid input: {field} - {reason}"
    NOT_FOUND: Final[str] = "{resource_type} not found: {identifier}"
    PERMISSION_DENIED: Final[str] = "Permission denied: {action} on {resource}"

    # API
    API_ERROR: Final[str] = "API error from {service}: {message}"
    RATE_LIMIT: Final[str] = "Rate limit exceeded for {service}. Retry after {seconds}s"
    QUOTA_EXCEEDED: Final[str] = "Quota exceeded for {service}. Resets at {reset_time}"
    AUTH_FAILED: Final[str] = "Authentication failed for {service}: {reason}"

    # File operations
    FILE_NOT_FOUND: Final[str] = "File not found: {path}"
    DISK_SPACE: Final[str] = "Insufficient disk space: need {required}MB, have {available}MB"
    FILE_TOO_LARGE: Final[str] = "File too large: {size}MB exceeds limit of {max_size}MB"

    # Pipeline
    STAGE_FAILED: Final[str] = "Pipeline stage '{stage}' failed: {reason}"
    TIMEOUT: Final[str] = "Operation timed out after {seconds}s: {operation}"


# =============================================================================
# Export All Constants
# =============================================================================


__all__ = [
    # Classes
    "AppConstants",
    "VideoConstants",
    "AudioConstants",
    "ImageConstants",
    "APIRateLimits",
    "API_RATE_LIMITS",
    "RegexPatterns",
    "HTTPConstants",
    "CacheConstants",
    "LogConstants",
    "Defaults",
    "ErrorMessages",
    # Video constants
    "VIDEO_DURATION_MIN",
    "VIDEO_DURATION_MAX",
    "VIDEO_DURATION_DEFAULT",
    "VIDEO_WIDTH",
    "VIDEO_HEIGHT",
    "VIDEO_ASPECT_RATIO",
    "VIDEO_FPS_MIN",
    "VIDEO_FPS_DEFAULT",
    "VIDEO_FPS_MAX",
    "VIDEO_BITRATE_LOW",
    "VIDEO_BITRATE_MEDIUM",
    "VIDEO_BITRATE_HIGH",
    "VIDEO_BITRATE_ULTRA",
    "VIDEO_MAX_FILE_SIZE_MB",
    "VIDEO_MAX_FILE_SIZE_BYTES",
    # Format sets
    "SUPPORTED_VIDEO_FORMATS",
    "SUPPORTED_AUDIO_FORMATS",
    "SUPPORTED_IMAGE_FORMATS",
    "SUPPORTED_FORMATS",
    # Enums
    "VideoFormat",
    "AudioFormat",
    "ImageFormat",
    "YouTubeCategory",
    "ContentNiche",
    "ContentStyle",
    "ContentTone",
    "PipelineStage",
    "PipelineStatus",
    "TrendSource",
]
