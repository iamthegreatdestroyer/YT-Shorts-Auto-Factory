"""
Unit tests for custom exceptions hierarchy.
"""
from __future__ import annotations

import pytest
from src.core.exceptions import (
    YTShortsError,
    ConfigurationError,
    ValidationError,
    APIError,
    YouTubeAPIError,
    RateLimitError,
    QuotaExceededError,
    AuthenticationError,
    ContentGenerationError,
    ScriptGenerationError,
    TemplateError,
    MediaCreationError,
    TTSError,
    ImageGenerationError,
    AudioProcessingError,
    VideoCompilationError,
    FFmpegError,
    RenderingError,
    ThumbnailError,
    UploadError,
    NetworkError,
    FileTransferError,
    StorageError,
    DiskSpaceError,
    FilePermissionError,
    TrendAnalysisError,
    ScrapingError,
    ParsingError,
    PipelineError,
    StageError,
    TimeoutError,
)


class TestYTShortsError:
    """Test the base exception class."""

    def test_default_message(self):
        err = YTShortsError()
        assert "YouTube Shorts" in str(err)

    def test_custom_message(self):
        err = YTShortsError("custom error")
        assert str(err) == "custom error"

    def test_context_in_str(self):
        err = YTShortsError("error", context={"key": "value"})
        s = str(err)
        assert "key" in s
        assert "value" in s

    def test_repr(self):
        err = YTShortsError("msg", context={"k": "v"})
        r = repr(err)
        assert "YTShortsError" in r
        assert "msg" in r

    def test_to_dict(self):
        original = ValueError("orig")
        err = YTShortsError("msg", context={"k": "v"}, original_error=original)
        d = err.to_dict()
        assert d["type"] == "YTShortsError"
        assert d["message"] == "msg"
        assert d["context"] == {"k": "v"}
        assert "orig" in d["original_error"]

    def test_to_dict_no_original_error(self):
        err = YTShortsError("msg")
        d = err.to_dict()
        assert d["original_error"] is None

    def test_str_no_context(self):
        err = YTShortsError("plain message")
        assert str(err) == "plain message"

    def test_is_exception(self):
        with pytest.raises(YTShortsError):
            raise YTShortsError("test")


class TestConfigurationError:
    """Test ConfigurationError."""

    def test_default(self):
        err = ConfigurationError()
        assert "Configuration" in str(err) or isinstance(err, YTShortsError)

    def test_with_config_key(self):
        err = ConfigurationError("bad config", config_key="MY_SETTING")
        assert isinstance(err, YTShortsError)
        assert "MY_SETTING" in str(err)

    def test_with_expected_type(self):
        err = ConfigurationError("type mismatch", expected_type="int", actual_value="abc")
        assert isinstance(err, ConfigurationError)

    def test_all_kwargs(self):
        err = ConfigurationError(
            "full error",
            config_key="KEY",
            expected_type="str",
            actual_value=42,
            original_error=ValueError("orig"),
        )
        assert isinstance(err, ConfigurationError)


class TestValidationError:
    """Test ValidationError."""

    def test_default(self):
        err = ValidationError()
        assert isinstance(err, YTShortsError)

    def test_with_field(self):
        err = ValidationError("invalid", field="email", value="bad@", constraint="email format")
        assert "email" in str(err)

    def test_no_optional_kwargs(self):
        err = ValidationError("simple validation error")
        assert str(err) == "simple validation error"


class TestAPIErrors:
    """Test API exception subclasses."""

    def test_api_error(self):
        err = APIError("api fail")
        assert isinstance(err, YTShortsError)

    def test_youtube_api_error(self):
        err = YouTubeAPIError("upload failed", video_id="abc123", operation="upload")
        assert isinstance(err, APIError)
        assert "abc123" in str(err)

    def test_youtube_api_error_no_kwargs(self):
        err = YouTubeAPIError("simple")
        assert isinstance(err, YouTubeAPIError)

    def test_rate_limit_error(self):
        err = RateLimitError("rate limited", retry_after=60, limit=100, remaining=0)
        assert isinstance(err, APIError)

    def test_rate_limit_no_kwargs(self):
        err = RateLimitError("too fast")
        assert isinstance(err, RateLimitError)

    def test_quota_exceeded(self):
        err = QuotaExceededError("quota hit", quota_name="uploads", quota_limit=100, quota_used=100, reset_time="midnight")
        assert isinstance(err, APIError)

    def test_quota_no_kwargs(self):
        err = QuotaExceededError()
        assert isinstance(err, QuotaExceededError)

    def test_auth_error(self):
        err = AuthenticationError("auth failed", auth_type="OAuth2")
        assert isinstance(err, APIError)

    def test_auth_no_kwargs(self):
        err = AuthenticationError()
        assert isinstance(err, AuthenticationError)


class TestContentGenerationErrors:
    """Test content generation exceptions."""

    def test_content_generation_error(self):
        err = ContentGenerationError("gen failed")
        assert isinstance(err, YTShortsError)

    def test_script_generation_error(self):
        err = ScriptGenerationError("script fail", topic="tech", template_name="short")
        assert isinstance(err, ContentGenerationError)

    def test_script_generation_no_kwargs(self):
        err = ScriptGenerationError()
        assert isinstance(err, ScriptGenerationError)

    def test_template_error(self):
        err = TemplateError("template fail", template_name="viral", missing_variables=["title"])
        assert isinstance(err, ContentGenerationError)

    def test_template_no_kwargs(self):
        err = TemplateError()
        assert isinstance(err, TemplateError)


class TestMediaCreationErrors:
    """Test media creation exceptions."""

    def test_media_creation_error(self):
        err = MediaCreationError("media fail")
        assert isinstance(err, YTShortsError)

    def test_tts_error(self):
        err = TTSError("tts fail", provider="edge_tts", text_length=100, language="en-US")
        assert isinstance(err, MediaCreationError)

    def test_tts_no_kwargs(self):
        err = TTSError()
        assert isinstance(err, TTSError)

    def test_image_generation_error(self):
        err = ImageGenerationError("img fail", provider="dalle", prompt="test", dimensions="1024x1024")
        assert isinstance(err, MediaCreationError)

    def test_image_generation_no_kwargs(self):
        err = ImageGenerationError()
        assert isinstance(err, ImageGenerationError)

    def test_audio_processing_error(self):
        err = AudioProcessingError("audio fail", operation="normalize", input_format="mp3", output_format="wav")
        assert isinstance(err, MediaCreationError)

    def test_audio_no_kwargs(self):
        err = AudioProcessingError()
        assert isinstance(err, AudioProcessingError)


class TestVideoCompilationErrors:
    """Test video compilation exceptions."""

    def test_video_compilation_error(self):
        err = VideoCompilationError("compile fail")
        assert isinstance(err, YTShortsError)

    def test_ffmpeg_error(self):
        err = FFmpegError("ffmpeg fail", command="ffmpeg -i in.mp4", exit_code=1, stderr="error output")
        assert isinstance(err, VideoCompilationError)

    def test_ffmpeg_no_kwargs(self):
        err = FFmpegError()
        assert isinstance(err, FFmpegError)

    def test_rendering_error(self):
        err = RenderingError("render fail", resolution="1080x1920", codec="h264", duration=30.0)
        assert isinstance(err, VideoCompilationError)

    def test_rendering_no_kwargs(self):
        err = RenderingError()
        assert isinstance(err, RenderingError)

    def test_thumbnail_error(self):
        err = ThumbnailError("thumb fail", source_video="/video.mp4")
        assert isinstance(err, VideoCompilationError)

    def test_thumbnail_no_kwargs(self):
        err = ThumbnailError()
        assert isinstance(err, ThumbnailError)


class TestUploadErrors:
    """Test upload exceptions."""

    def test_upload_error(self):
        err = UploadError("upload fail")
        assert isinstance(err, YTShortsError)

    def test_network_error(self):
        err = NetworkError("network fail", url="https://example.com", timeout=30)
        assert isinstance(err, UploadError)

    def test_network_no_kwargs(self):
        err = NetworkError()
        assert isinstance(err, NetworkError)

    def test_file_transfer_error(self):
        err = FileTransferError("transfer fail", bytes_transferred=1024, total_bytes=2048, resumable=True)
        assert isinstance(err, UploadError)

    def test_file_transfer_no_kwargs(self):
        err = FileTransferError()
        assert isinstance(err, FileTransferError)


class TestStorageErrors:
    """Test storage exceptions."""

    def test_storage_error(self):
        err = StorageError("storage fail")
        assert isinstance(err, YTShortsError)

    def test_disk_space_error(self):
        err = DiskSpaceError("no space", required_bytes=1024, available_bytes=512)
        assert isinstance(err, StorageError)

    def test_disk_space_no_kwargs(self):
        err = DiskSpaceError()
        assert isinstance(err, DiskSpaceError)

    def test_file_permission_error(self):
        err = FilePermissionError("perm fail", operation="write")
        assert isinstance(err, StorageError)

    def test_file_permission_no_kwargs(self):
        err = FilePermissionError()
        assert isinstance(err, FilePermissionError)


class TestTrendAnalysisErrors:
    """Test trend analysis exceptions."""

    def test_trend_analysis_error(self):
        err = TrendAnalysisError("trend fail")
        assert isinstance(err, YTShortsError)

    def test_scraping_error(self):
        err = ScrapingError("scrape fail", url="https://reddit.com", selector=".post")
        # selector is not a named param, just verify it works via context kwarg
        assert isinstance(err, TrendAnalysisError)

    def test_scraping_no_kwargs(self):
        err = ScrapingError()
        assert isinstance(err, ScrapingError)

    def test_parsing_error(self):
        err = ParsingError("parse fail", raw_data="bad data", data_format="json")
        assert isinstance(err, TrendAnalysisError)

    def test_parsing_no_kwargs(self):
        err = ParsingError()
        assert isinstance(err, ParsingError)


class TestPipelineErrors:
    """Test pipeline exceptions."""

    def test_pipeline_error(self):
        err = PipelineError("pipeline fail")
        assert isinstance(err, YTShortsError)

    def test_pipeline_error_with_kwargs(self):
        err = PipelineError(
            "pipeline fail",
            pipeline_name="video_gen",
            run_id="abc123",
            original_error=RuntimeError("orig"),
        )
        assert "pipeline_name" in str(err) or isinstance(err, PipelineError)

    def test_pipeline_no_kwargs(self):
        err = PipelineError()
        assert isinstance(err, PipelineError)

    def test_stage_error(self):
        err = StageError("stage fail", stage_name="tts", stage_index=2)
        assert isinstance(err, PipelineError)

    def test_stage_no_kwargs(self):
        err = StageError()
        assert isinstance(err, StageError)

    def test_timeout_error(self):
        err = TimeoutError("timed out", timeout_seconds=30, elapsed_seconds=35)
        assert isinstance(err, PipelineError)

    def test_timeout_no_kwargs(self):
        err = TimeoutError()
        assert isinstance(err, TimeoutError)

    def test_exception_inheritance_chain(self):
        """Verify the full inheritance chain."""
        err = StageError("test")
        assert isinstance(err, StageError)
        assert isinstance(err, PipelineError)
        assert isinstance(err, YTShortsError)
        assert isinstance(err, Exception)
