"""
Unit tests for configuration system.

Tests configuration loading, validation, and defaults.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.core.config import (
    Settings,
    AppSettings,
    Environment,
    LogLevel,
    TrendSettings,
    StorageSettings,
)


class TestSettingsStructure:
    """Test settings object structure."""

    def test_settings_has_app_section(self):
        """Test Settings has app configuration section."""
        settings = Settings()
        assert hasattr(settings, 'app')
        assert isinstance(settings.app, AppSettings)

    def test_settings_has_trends_section(self):
        """Test Settings has trends configuration section."""
        settings = Settings()
        assert hasattr(settings, 'trends')
        assert isinstance(settings.trends, TrendSettings)

    def test_settings_has_storage_section(self):
        """Test Settings has storage configuration section."""
        settings = Settings()
        assert hasattr(settings, 'storage')
        assert isinstance(settings.storage, StorageSettings)

    def test_app_name_default(self):
        """Test default app name is set."""
        settings = Settings()
        assert settings.app.name == "YouTube Shorts Factory"

    def test_app_version_exists(self):
        """Test app version is defined."""
        settings = Settings()
        assert settings.app.version
        assert "." in settings.app.version


class TestAppSettings:
    """Test AppSettings defaults and behavior."""

    def test_default_environment_is_development(self):
        """Test default environment is development."""
        app_settings = AppSettings()
        assert app_settings.environment == Environment.DEVELOPMENT

    def test_default_debug_is_false(self):
        """Test debug is False by default."""
        app_settings = AppSettings()
        assert app_settings.debug is False

    def test_default_log_level_is_info(self):
        """Test default log level is INFO."""
        app_settings = AppSettings()
        assert app_settings.log_level == LogLevel.INFO

    def test_max_concurrent_jobs_default(self):
        """Test default max concurrent jobs."""
        app_settings = AppSettings()
        assert app_settings.max_concurrent_jobs == 3


class TestEnvironmentVariables:
    """Test configuration from environment variables."""

    def test_app_debug_from_env(self):
        """Test debug flag from environment."""
        with patch.dict(os.environ, {"APP_DEBUG": "true"}):
            app_settings = AppSettings()
            assert app_settings.debug is True

    def test_app_log_level_from_env(self):
        """Test log level from environment."""
        with patch.dict(os.environ, {"APP_LOG_LEVEL": "WARNING"}):
            app_settings = AppSettings()
            assert app_settings.log_level == LogLevel.WARNING

    def test_app_environment_from_env(self):
        """Test environment from env var."""
        with patch.dict(os.environ, {"APP_ENVIRONMENT": "production"}):
            app_settings = AppSettings()
            assert app_settings.environment == Environment.PRODUCTION


class TestSettingsHelpers:
    """Test Settings helper methods."""

    def test_is_production(self):
        """Test is_production property."""
        settings = Settings()
        original = settings.app.environment
        
        settings.app.environment = Environment.PRODUCTION
        assert settings.is_production is True
        
        settings.app.environment = Environment.DEVELOPMENT
        assert settings.is_production is False
        
        settings.app.environment = original

    def test_is_development(self):
        """Test is_development property."""
        settings = Settings()
        original = settings.app.environment
        
        settings.app.environment = Environment.DEVELOPMENT
        assert settings.is_development is True
        
        settings.app.environment = Environment.PRODUCTION
        assert settings.is_development is False
        
        settings.app.environment = original

    def test_is_testing(self):
        """Test is_testing property."""
        settings = Settings()
        original = settings.app.environment
        
        settings.app.environment = Environment.TESTING
        assert settings.is_testing is True
        
        settings.app.environment = original

    def test_get_log_level(self):
        """Test get_log_level method."""
        settings = Settings()
        original = settings.app.log_level
        
        settings.app.log_level = LogLevel.DEBUG
        assert settings.get_log_level() == "DEBUG"
        
        settings.app.log_level = LogLevel.WARNING
        assert settings.get_log_level() == "WARNING"
        
        settings.app.log_level = original


class TestTrendSettings:
    """Test TrendSettings configuration."""

    def test_trend_sources_default(self):
        """Test default trend sources."""
        trend_settings = TrendSettings()
        assert trend_settings.enable_youtube_trends is True
        assert trend_settings.enable_reddit is False

    def test_cache_ttl_default(self):
        """Test default cache TTL."""
        trend_settings = TrendSettings()
        assert trend_settings.cache_ttl_minutes > 0
        assert trend_settings.cache_ttl_minutes <= 60

    def test_reddit_settings_default(self):
        """Test default Reddit settings."""
        trend_settings = TrendSettings()
        assert trend_settings.enable_reddit is False
        assert isinstance(trend_settings.reddit_subreddits, str)


class TestStorageSettings:
    """Test StorageSettings configuration."""

    def test_default_paths_exist(self):
        """Test default paths are defined."""
        storage_settings = StorageSettings()
        assert storage_settings.base_path is not None
        assert storage_settings.cache_path is not None


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_log_level_raises(self):
        """Test that invalid log level raises validation error."""
        with patch.dict(os.environ, {"APP_LOG_LEVEL": "INVALID_LEVEL"}):
            with pytest.raises(Exception):
                AppSettings()

    def test_max_concurrent_jobs_bounds(self):
        """Test max concurrent jobs has bounds."""
        with patch.dict(os.environ, {"APP_MAX_CONCURRENT_JOBS": "5"}):
            app_settings = AppSettings()
            assert app_settings.max_concurrent_jobs == 5
        
        with patch.dict(os.environ, {"APP_MAX_CONCURRENT_JOBS": "100"}):
            with pytest.raises(Exception):
                AppSettings()


class TestApiKeyValidation:
    """Test API key validation."""

    def test_validate_api_keys_returns_dict(self):
        """Test validate_api_keys returns status dict."""
        settings = Settings()
        api_status = settings.validate_api_keys()
        
        assert isinstance(api_status, dict)
        assert "youtube" in api_status
        assert "reddit" in api_status

    def test_to_safe_dict_returns_dict(self):
        """Test to_safe_dict returns dictionary."""
        settings = Settings()
        safe_dict = settings.to_safe_dict()
        assert isinstance(safe_dict, dict)


@pytest.mark.parametrize("env,expected", [
    ("development", Environment.DEVELOPMENT),
    ("staging", Environment.STAGING),
    ("production", Environment.PRODUCTION),
    ("testing", Environment.TESTING),
])
def test_environment_parsing(env: str, expected: Environment):
    """Test environment string parsing."""
    with patch.dict(os.environ, {"APP_ENVIRONMENT": env}):
        app_settings = AppSettings()
        assert app_settings.environment == expected


@pytest.mark.parametrize("level,expected", [
    ("DEBUG", LogLevel.DEBUG),
    ("INFO", LogLevel.INFO),
    ("WARNING", LogLevel.WARNING),
    ("ERROR", LogLevel.ERROR),
])
def test_log_level_parsing(level: str, expected: LogLevel):
    """Test log level string parsing."""
    with patch.dict(os.environ, {"APP_LOG_LEVEL": level}):
        app_settings = AppSettings()
        assert app_settings.log_level == expected
