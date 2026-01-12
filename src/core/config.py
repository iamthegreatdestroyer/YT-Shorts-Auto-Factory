"""
Configuration management using Pydantic Settings.

This module provides a comprehensive configuration system for the YouTube Shorts
Automation Factory, supporting environment variables, .env files, and sensible defaults.

Example:
    >>> from src.core.config import settings
    >>> print(settings.app_name)
    'YouTube Shorts Factory'
    >>> print(settings.youtube.api_key)  # From YOUTUBE_API_KEY env var
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# Enums for Configuration Options
# =============================================================================


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging level options."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TTSProvider(str, Enum):
    """Text-to-speech provider options."""

    GTTS = "gtts"
    ELEVENLABS = "elevenlabs"
    AZURE = "azure"
    LOCAL = "local"


class ImageProvider(str, Enum):
    """Image generation provider options."""

    STABLE_DIFFUSION = "stable_diffusion"
    DALLE = "dalle"
    STOCK = "stock"
    LOCAL = "local"


class VideoQuality(str, Enum):
    """Output video quality presets."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


# =============================================================================
# Base Settings Configuration
# =============================================================================


class BaseSettingsConfig(BaseSettings):
    """Base settings with common configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# =============================================================================
# Application Settings
# =============================================================================


class AppSettings(BaseSettingsConfig):
    """Core application settings."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )

    # Application Identity
    name: str = Field(
        default="YouTube Shorts Factory",
        description="Application name",
    )
    version: str = Field(
        default="0.1.0",
        description="Application version",
    )
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level",
    )

    # Processing Settings
    max_concurrent_jobs: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum concurrent video generation jobs",
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts for failed operations",
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        description="Delay between retry attempts in seconds",
    )


# =============================================================================
# YouTube API Settings
# =============================================================================


class YouTubeSettings(BaseSettingsConfig):
    """YouTube API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="YOUTUBE_",
        env_file=".env",
        extra="ignore",
    )

    # API Credentials
    api_key: SecretStr = Field(
        default=SecretStr(""),
        description="YouTube Data API key",
    )
    client_secrets_file: Path = Field(
        default=Path("credentials/client_secrets.json"),
        description="Path to OAuth client secrets",
    )
    token_file: Path = Field(
        default=Path("credentials/token.pickle"),
        description="Path to stored OAuth token",
    )

    # Channel Settings
    channel_id: str = Field(
        default="",
        description="YouTube channel ID for uploads",
    )
    default_privacy: str = Field(
        default="private",
        description="Default video privacy (public, private, unlisted)",
    )

    # Upload Settings
    auto_upload: bool = Field(
        default=False,
        description="Automatically upload generated videos",
    )
    notify_subscribers: bool = Field(
        default=False,
        description="Notify subscribers on upload",
    )

    # Rate Limiting
    daily_upload_limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum daily uploads",
    )
    api_quota_limit: int = Field(
        default=10000,
        ge=100,
        description="Daily API quota limit",
    )

    @field_validator("default_privacy")
    @classmethod
    def validate_privacy(cls, v: str) -> str:
        """Validate privacy setting."""
        valid_options = {"public", "private", "unlisted"}
        if v.lower() not in valid_options:
            raise ValueError(f"Privacy must be one of: {valid_options}")
        return v.lower()


# =============================================================================
# Content Generation Settings
# =============================================================================


class ContentSettings(BaseSettingsConfig):
    """Content generation configuration."""

    model_config = SettingsConfigDict(
        env_prefix="CONTENT_",
        env_file=".env",
        extra="ignore",
    )

    # Niche Configuration
    niche: str = Field(
        default="tech",
        description="Content niche/category",
    )
    content_style: str = Field(
        default="informative",
        description="Content style (informative, entertaining, educational)",
    )
    target_audience: str = Field(
        default="general",
        description="Target audience demographic",
    )

    # Video Parameters
    min_duration: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Minimum video duration in seconds",
    )
    max_duration: int = Field(
        default=60,
        ge=15,
        le=180,
        description="Maximum video duration in seconds",
    )
    target_duration: int = Field(
        default=45,
        ge=10,
        le=60,
        description="Target video duration in seconds",
    )

    # Output Quality
    quality: VideoQuality = Field(
        default=VideoQuality.HIGH,
        description="Output video quality preset",
    )
    resolution_width: int = Field(
        default=1080,
        description="Video width in pixels",
    )
    resolution_height: int = Field(
        default=1920,
        description="Video height in pixels (vertical for Shorts)",
    )
    fps: int = Field(
        default=30,
        ge=24,
        le=60,
        description="Frames per second",
    )
    bitrate: str = Field(
        default="8M",
        description="Video bitrate (e.g., '8M', '12M')",
    )

    @model_validator(mode="after")
    def validate_durations(self) -> "ContentSettings":
        """Ensure duration constraints are valid."""
        if self.min_duration > self.max_duration:
            raise ValueError("min_duration cannot exceed max_duration")
        if not (self.min_duration <= self.target_duration <= self.max_duration):
            raise ValueError("target_duration must be between min and max")
        return self


# =============================================================================
# Text-to-Speech Settings
# =============================================================================


class TTSSettings(BaseSettingsConfig):
    """Text-to-speech configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TTS_",
        env_file=".env",
        extra="ignore",
    )

    # Provider Selection
    provider: TTSProvider = Field(
        default=TTSProvider.GTTS,
        description="TTS provider to use",
    )

    # gTTS Settings
    gtts_language: str = Field(
        default="en",
        description="gTTS language code",
    )
    gtts_slow: bool = Field(
        default=False,
        description="Use slow speech mode in gTTS",
    )

    # ElevenLabs Settings
    elevenlabs_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="ElevenLabs API key",
    )
    elevenlabs_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="ElevenLabs voice ID",
    )
    elevenlabs_model: str = Field(
        default="eleven_monolingual_v1",
        description="ElevenLabs model ID",
    )
    elevenlabs_stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0.0-1.0)",
    )
    elevenlabs_similarity_boost: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Voice similarity boost (0.0-1.0)",
    )

    # Audio Output Settings
    audio_format: str = Field(
        default="mp3",
        description="Audio output format",
    )
    sample_rate: int = Field(
        default=44100,
        description="Audio sample rate in Hz",
    )


# =============================================================================
# Image Generation Settings
# =============================================================================


class ImageSettings(BaseSettingsConfig):
    """Image generation configuration."""

    model_config = SettingsConfigDict(
        env_prefix="IMAGE_",
        env_file=".env",
        extra="ignore",
    )

    # Provider Selection
    provider: ImageProvider = Field(
        default=ImageProvider.STOCK,
        description="Image provider to use",
    )

    # Stable Diffusion Settings
    sd_api_url: str = Field(
        default="http://127.0.0.1:7860",
        description="Stable Diffusion API URL",
    )
    sd_model: str = Field(
        default="sd_xl_base_1.0",
        description="Stable Diffusion model name",
    )
    sd_steps: int = Field(
        default=30,
        ge=1,
        le=150,
        description="Number of inference steps",
    )
    sd_cfg_scale: float = Field(
        default=7.5,
        ge=1.0,
        le=30.0,
        description="Classifier-free guidance scale",
    )
    sd_sampler: str = Field(
        default="DPM++ 2M Karras",
        description="Sampling method",
    )

    # DALL-E Settings
    dalle_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API key for DALL-E",
    )
    dalle_model: str = Field(
        default="dall-e-3",
        description="DALL-E model version",
    )
    dalle_quality: str = Field(
        default="standard",
        description="Image quality (standard, hd)",
    )

    # Stock Image Settings
    pexels_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Pexels API key",
    )
    pixabay_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Pixabay API key",
    )
    unsplash_access_key: SecretStr = Field(
        default=SecretStr(""),
        description="Unsplash access key",
    )

    # Image Processing
    default_width: int = Field(
        default=1080,
        description="Default image width",
    )
    default_height: int = Field(
        default=1920,
        description="Default image height",
    )
    image_format: str = Field(
        default="png",
        description="Output image format",
    )
    compression_quality: int = Field(
        default=95,
        ge=1,
        le=100,
        description="Image compression quality",
    )


# =============================================================================
# Trend Analysis Settings
# =============================================================================


class TrendSettings(BaseSettingsConfig):
    """Trend analysis and content discovery configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TRENDS_",
        env_file=".env",
        extra="ignore",
    )

    # Enable/Disable Sources
    enable_youtube_trends: bool = Field(
        default=True,
        description="Enable YouTube trends analysis",
    )
    enable_google_trends: bool = Field(
        default=True,
        description="Enable Google Trends analysis",
    )
    enable_reddit: bool = Field(
        default=False,
        description="Enable Reddit trend analysis",
    )
    enable_twitter: bool = Field(
        default=False,
        description="Enable Twitter/X trend analysis",
    )

    # Reddit Settings
    reddit_client_id: str = Field(
        default="",
        description="Reddit API client ID",
    )
    reddit_client_secret: SecretStr = Field(
        default=SecretStr(""),
        description="Reddit API client secret",
    )
    reddit_subreddits: str = Field(
        default="technology,programming,gadgets",
        description="Comma-separated list of subreddits to monitor",
    )

    # Twitter Settings
    twitter_bearer_token: SecretStr = Field(
        default=SecretStr(""),
        description="Twitter API bearer token",
    )

    # Analysis Parameters
    trend_lookback_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Hours to look back for trends",
    )
    min_trend_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum trend score to consider",
    )
    max_trends_per_source: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum trends to fetch per source",
    )
    cache_ttl_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Trend cache TTL in minutes",
    )

    @property
    def subreddits_list(self) -> list[str]:
        """Get subreddits as a list."""
        return [s.strip() for s in self.reddit_subreddits.split(",") if s.strip()]


# =============================================================================
# Scheduling Settings
# =============================================================================


class ScheduleSettings(BaseSettingsConfig):
    """Video generation and upload scheduling configuration."""

    model_config = SettingsConfigDict(
        env_prefix="SCHEDULE_",
        env_file=".env",
        extra="ignore",
    )

    # Scheduler Settings
    enabled: bool = Field(
        default=False,
        description="Enable scheduled generation",
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for scheduling",
    )

    # Generation Schedule (cron format)
    generation_cron: str = Field(
        default="0 */4 * * *",
        description="Cron expression for video generation",
    )
    upload_cron: str = Field(
        default="0 9,12,17 * * *",
        description="Cron expression for video uploads",
    )
    trend_analysis_cron: str = Field(
        default="0 */2 * * *",
        description="Cron expression for trend analysis",
    )
    cleanup_cron: str = Field(
        default="0 3 * * *",
        description="Cron expression for temp file cleanup",
    )

    # Batching
    videos_per_batch: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Videos to generate per batch",
    )
    batch_interval_minutes: int = Field(
        default=60,
        ge=15,
        le=1440,
        description="Minutes between batches",
    )


# =============================================================================
# Storage Settings
# =============================================================================


class StorageSettings(BaseSettingsConfig):
    """File storage and path configuration."""

    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        env_file=".env",
        extra="ignore",
    )

    # Base Paths
    base_path: Path = Field(
        default=Path("."),
        description="Base project path",
    )
    data_path: Path = Field(
        default=Path("data"),
        description="Data directory path",
    )
    output_path: Path = Field(
        default=Path("output"),
        description="Generated video output path",
    )
    temp_path: Path = Field(
        default=Path("data/temp"),
        description="Temporary files path",
    )
    cache_path: Path = Field(
        default=Path("data/cache"),
        description="Cache directory path",
    )
    logs_path: Path = Field(
        default=Path("logs"),
        description="Log files path",
    )
    assets_path: Path = Field(
        default=Path("assets"),
        description="Static assets path",
    )
    templates_path: Path = Field(
        default=Path("templates"),
        description="Template files path",
    )

    # Cleanup Settings
    temp_file_max_age_hours: int = Field(
        default=24,
        ge=1,
        description="Max age for temp files before cleanup",
    )
    archive_after_days: int = Field(
        default=30,
        ge=1,
        description="Days before archiving old outputs",
    )
    max_cache_size_gb: float = Field(
        default=10.0,
        ge=0.1,
        description="Maximum cache size in GB",
    )

    def ensure_directories(self) -> None:
        """Create all required directories."""
        directories = [
            self.data_path,
            self.output_path,
            self.temp_path,
            self.cache_path,
            self.logs_path,
            self.assets_path,
            self.templates_path,
            self.data_path / "archives",
            self.cache_path / "trends",
            self.cache_path / "generated",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Monitoring Settings
# =============================================================================


class MonitoringSettings(BaseSettingsConfig):
    """Monitoring, metrics, and alerting configuration."""

    model_config = SettingsConfigDict(
        env_prefix="MONITORING_",
        env_file=".env",
        extra="ignore",
    )

    # Metrics
    metrics_enabled: bool = Field(
        default=True,
        description="Enable metrics collection",
    )
    metrics_port: int = Field(
        default=9090,
        ge=1024,
        le=65535,
        description="Prometheus metrics port",
    )

    # Health Checks
    health_check_enabled: bool = Field(
        default=True,
        description="Enable health check endpoint",
    )
    health_check_port: int = Field(
        default=8080,
        ge=1024,
        le=65535,
        description="Health check endpoint port",
    )

    # Alerting
    alerts_enabled: bool = Field(
        default=False,
        description="Enable alerting",
    )
    alert_email: str = Field(
        default="",
        description="Alert notification email",
    )
    slack_webhook_url: str = Field(
        default="",
        description="Slack webhook for alerts",
    )
    discord_webhook_url: str = Field(
        default="",
        description="Discord webhook for alerts",
    )

    # Error Tracking
    sentry_dsn: str = Field(
        default="",
        description="Sentry DSN for error tracking",
    )
    sentry_environment: str = Field(
        default="development",
        description="Sentry environment name",
    )


# =============================================================================
# Database Settings
# =============================================================================


class DatabaseSettings(BaseSettingsConfig):
    """Database connection configuration."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        extra="ignore",
    )

    # Database Type
    type: str = Field(
        default="sqlite",
        description="Database type (sqlite, postgresql)",
    )

    # SQLite Settings
    sqlite_path: Path = Field(
        default=Path("data/factory.db"),
        description="SQLite database file path",
    )

    # PostgreSQL Settings
    postgres_host: str = Field(
        default="localhost",
        description="PostgreSQL host",
    )
    postgres_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="PostgreSQL port",
    )
    postgres_user: str = Field(
        default="shorts_factory",
        description="PostgreSQL username",
    )
    postgres_password: SecretStr = Field(
        default=SecretStr(""),
        description="PostgreSQL password",
    )
    postgres_database: str = Field(
        default="shorts_factory",
        description="PostgreSQL database name",
    )

    # Connection Pool
    pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Connection pool size",
    )
    pool_max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Max pool overflow connections",
    )

    @property
    def connection_url(self) -> str:
        """Get database connection URL."""
        if self.type == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        elif self.type == "postgresql":
            password = self.postgres_password.get_secret_value()
            return (
                f"postgresql://{self.postgres_user}:{password}"
                f"@{self.postgres_host}:{self.postgres_port}"
                f"/{self.postgres_database}"
            )
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


# =============================================================================
# Advanced Settings
# =============================================================================


class AdvancedSettings(BaseSettingsConfig):
    """Advanced configuration options."""

    model_config = SettingsConfigDict(
        env_prefix="ADVANCED_",
        env_file=".env",
        extra="ignore",
    )

    # Proxy Settings
    proxy_enabled: bool = Field(
        default=False,
        description="Enable proxy for requests",
    )
    proxy_url: str = Field(
        default="",
        description="Proxy URL (http://host:port)",
    )
    proxy_username: str = Field(
        default="",
        description="Proxy username",
    )
    proxy_password: SecretStr = Field(
        default=SecretStr(""),
        description="Proxy password",
    )

    # Rate Limiting
    global_rate_limit: int = Field(
        default=100,
        ge=1,
        description="Global requests per minute limit",
    )
    per_api_rate_limit: int = Field(
        default=30,
        ge=1,
        description="Per-API requests per minute limit",
    )

    # Performance Tuning
    ffmpeg_threads: int = Field(
        default=0,
        ge=0,
        description="FFmpeg thread count (0=auto)",
    )
    image_processing_threads: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Image processing thread count",
    )
    max_memory_mb: int = Field(
        default=4096,
        ge=512,
        description="Maximum memory usage in MB",
    )

    # Feature Flags
    experimental_features: bool = Field(
        default=False,
        description="Enable experimental features",
    )
    use_gpu: bool = Field(
        default=False,
        description="Enable GPU acceleration",
    )


# =============================================================================
# Master Settings Class
# =============================================================================


class Settings(BaseSettingsConfig):
    """
    Master settings class that aggregates all configuration sections.

    This class provides a single point of access to all configuration
    settings for the YouTube Shorts Factory application.

    Example:
        >>> settings = Settings()
        >>> settings.app.name
        'YouTube Shorts Factory'
        >>> settings.youtube.api_key
        SecretStr('...')
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # Nested Settings
    app: AppSettings = Field(default_factory=AppSettings)
    youtube: YouTubeSettings = Field(default_factory=YouTubeSettings)
    content: ContentSettings = Field(default_factory=ContentSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    image: ImageSettings = Field(default_factory=ImageSettings)
    trends: TrendSettings = Field(default_factory=TrendSettings)
    schedule: ScheduleSettings = Field(default_factory=ScheduleSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    advanced: AdvancedSettings = Field(default_factory=AdvancedSettings)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings with optional overrides."""
        super().__init__(**kwargs)
        # Ensure required directories exist
        self.storage.ensure_directories()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.app.environment == Environment.TESTING

    def get_log_level(self) -> str:
        """Get current log level as string."""
        return self.app.log_level.value

    def validate_api_keys(self) -> dict[str, bool]:
        """
        Validate that required API keys are configured.

        Returns:
            Dictionary mapping API name to whether it's configured.
        """
        return {
            "youtube": bool(self.youtube.api_key.get_secret_value()),
            "elevenlabs": bool(self.tts.elevenlabs_api_key.get_secret_value()),
            "dalle": bool(self.image.dalle_api_key.get_secret_value()),
            "pexels": bool(self.image.pexels_api_key.get_secret_value()),
            "pixabay": bool(self.image.pixabay_api_key.get_secret_value()),
            "unsplash": bool(self.image.unsplash_access_key.get_secret_value()),
            "twitter": bool(self.trends.twitter_bearer_token.get_secret_value()),
            "reddit": bool(self.trends.reddit_client_id),
        }

    def to_safe_dict(self) -> dict[str, Any]:
        """
        Export settings as dictionary with secrets masked.

        Returns:
            Dictionary with all settings, secrets replaced with '***'.
        """
        data = self.model_dump()
        # Mask secret values
        self._mask_secrets(data)
        return data

    def _mask_secrets(self, data: dict[str, Any], mask: str = "***") -> None:
        """Recursively mask secret values in dictionary."""
        for key, value in data.items():
            if isinstance(value, dict):
                self._mask_secrets(value, mask)
            elif "key" in key.lower() or "secret" in key.lower() or "password" in key.lower() or "token" in key.lower():
                data[key] = mask


# =============================================================================
# Singleton Pattern for Settings
# =============================================================================


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are only loaded once.

    Returns:
        Settings: The application settings instance.

    Example:
        >>> settings = get_settings()
        >>> settings.app.name
        'YouTube Shorts Factory'
    """
    return Settings()


# Global settings instance for convenience
settings = get_settings()


# =============================================================================
# Utility Functions
# =============================================================================


def reload_settings() -> Settings:
    """
    Reload settings from environment/files.

    Clears the settings cache and returns a fresh instance.

    Returns:
        Settings: Fresh settings instance.
    """
    get_settings.cache_clear()
    return get_settings()


def override_settings(**kwargs: Any) -> Settings:
    """
    Create settings with overrides for testing.

    Args:
        **kwargs: Setting overrides to apply.

    Returns:
        Settings: New settings instance with overrides.
    """
    return Settings(**kwargs)


__all__ = [
    # Main Classes
    "Settings",
    "AppSettings",
    "YouTubeSettings",
    "ContentSettings",
    "TTSSettings",
    "ImageSettings",
    "TrendSettings",
    "ScheduleSettings",
    "StorageSettings",
    "MonitoringSettings",
    "DatabaseSettings",
    "AdvancedSettings",
    # Enums
    "Environment",
    "LogLevel",
    "TTSProvider",
    "ImageProvider",
    "VideoQuality",
    # Functions
    "get_settings",
    "reload_settings",
    "override_settings",
    # Global Instance
    "settings",
]
