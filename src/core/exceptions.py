"""
Custom exceptions for the YouTube Shorts Automation Factory.

This module defines a comprehensive exception hierarchy for handling
errors across all components of the application.

Exception Hierarchy:
    YTShortsError (base)
    ├── ConfigurationError
    ├── ValidationError
    ├── APIError
    │   ├── YouTubeAPIError
    │   ├── RateLimitError
    │   ├── QuotaExceededError
    │   └── AuthenticationError
    ├── ContentGenerationError
    │   ├── ScriptGenerationError
    │   └── TemplateError
    ├── MediaCreationError
    │   ├── TTSError
    │   ├── ImageGenerationError
    │   └── AudioProcessingError
    ├── VideoCompilationError
    │   ├── FFmpegError
    │   ├── RenderingError
    │   └── ThumbnailError
    ├── UploadError
    │   ├── NetworkError
    │   └── FileTransferError
    ├── StorageError
    │   ├── DiskSpaceError
    │   └── FilePermissionError
    ├── TrendAnalysisError
    │   ├── ScrapingError
    │   └── ParsingError
    └── PipelineError
        ├── StageError
        └── TimeoutError

Example:
    >>> from src.core.exceptions import YouTubeAPIError
    >>> raise YouTubeAPIError(
    ...     "Upload failed",
    ...     status_code=403,
    ...     video_id="abc123"
    ... )
"""

from __future__ import annotations

from typing import Any, Optional


# =============================================================================
# Base Exception
# =============================================================================


class YTShortsError(Exception):
    """
    Base exception for all YouTube Shorts Factory errors.

    All custom exceptions in this project inherit from this class,
    allowing for catch-all exception handling when needed.

    Attributes:
        message: Human-readable error description.
        context: Additional context information as key-value pairs.
        original_error: The original exception that caused this error.
    """

    def __init__(
        self,
        message: str = "An error occurred in YouTube Shorts Factory",
        *,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Human-readable error description.
            context: Additional context information.
            original_error: The original exception if wrapping another error.
        """
        self.message = message
        self.context = context or {}
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message with context."""
        if self.context:
            context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} [{context_str}]"
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"context={self.context!r}, "
            f"original_error={self.original_error!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert exception to dictionary for logging/serialization.

        Returns:
            Dictionary with error details.
        """
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "original_error": str(self.original_error) if self.original_error else None,
        }


# =============================================================================
# Configuration Exceptions
# =============================================================================


class ConfigurationError(YTShortsError):
    """
    Raised when configuration is invalid or missing.

    Use for:
    - Missing required configuration values
    - Invalid configuration format
    - Environment variable issues
    - Config file parsing errors
    """

    def __init__(
        self,
        message: str = "Configuration error",
        *,
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize configuration error.

        Args:
            message: Error description.
            config_key: The configuration key that caused the error.
            expected_type: Expected type for the configuration value.
            actual_value: The actual value that was provided.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if config_key:
            context["config_key"] = config_key
        if expected_type:
            context["expected_type"] = expected_type
        if actual_value is not None:
            context["actual_value"] = actual_value
        super().__init__(message, context=context, **kwargs)


class ValidationError(YTShortsError):
    """
    Raised when input validation fails.

    Use for:
    - Invalid user input
    - Data format validation failures
    - Schema validation errors
    - Business rule violations
    """

    def __init__(
        self,
        message: str = "Validation error",
        *,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize validation error.

        Args:
            message: Error description.
            field: The field that failed validation.
            value: The invalid value.
            constraint: The validation constraint that was violated.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = value
        if constraint:
            context["constraint"] = constraint
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# API Exceptions
# =============================================================================


class APIError(YTShortsError):
    """
    Base exception for API-related errors.

    Use for:
    - External API communication failures
    - Unexpected API responses
    - Service availability issues
    """

    def __init__(
        self,
        message: str = "API error",
        *,
        service: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize API error.

        Args:
            message: Error description.
            service: The API service name.
            status_code: HTTP status code if applicable.
            response_body: Response body from the API.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if service:
            context["service"] = service
        if status_code is not None:
            context["status_code"] = status_code
        if response_body:
            context["response_body"] = response_body[:500]  # Truncate long responses
        super().__init__(message, context=context, **kwargs)


class YouTubeAPIError(APIError):
    """
    Raised when YouTube API operations fail.

    Use for:
    - Upload failures
    - Metadata update failures
    - Video/channel operations
    """

    def __init__(
        self,
        message: str = "YouTube API error",
        *,
        video_id: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize YouTube API error.

        Args:
            message: Error description.
            video_id: The video ID involved.
            operation: The operation that failed (upload, update, etc.).
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if video_id:
            context["video_id"] = video_id
        if operation:
            context["operation"] = operation
        context["service"] = "youtube"
        super().__init__(message, context=context, **kwargs)


class RateLimitError(APIError):
    """
    Raised when API rate limits are exceeded.

    Use for:
    - HTTP 429 responses
    - Quota-based rate limiting
    - Retry-after scenarios
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Error description.
            retry_after: Seconds until rate limit resets.
            limit: The rate limit ceiling.
            remaining: Remaining requests in the current window.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if retry_after is not None:
            context["retry_after"] = retry_after
        if limit is not None:
            context["limit"] = limit
        if remaining is not None:
            context["remaining"] = remaining
        super().__init__(message, context=context, **kwargs)
        self.retry_after = retry_after


class QuotaExceededError(APIError):
    """
    Raised when API quota is exhausted.

    Use for:
    - Daily/monthly quota limits
    - Token-based quotas
    - Usage limit exceeded
    """

    def __init__(
        self,
        message: str = "Quota exceeded",
        *,
        quota_name: Optional[str] = None,
        quota_limit: Optional[int] = None,
        quota_used: Optional[int] = None,
        reset_time: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize quota exceeded error.

        Args:
            message: Error description.
            quota_name: Name of the quota that was exceeded.
            quota_limit: The quota limit.
            quota_used: Amount of quota used.
            reset_time: When the quota resets.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if quota_name:
            context["quota_name"] = quota_name
        if quota_limit is not None:
            context["quota_limit"] = quota_limit
        if quota_used is not None:
            context["quota_used"] = quota_used
        if reset_time:
            context["reset_time"] = reset_time
        super().__init__(message, context=context, **kwargs)


class AuthenticationError(APIError):
    """
    Raised when authentication fails.

    Use for:
    - Invalid credentials
    - Expired tokens
    - Permission denied
    - OAuth flow failures
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        *,
        auth_type: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize authentication error.

        Args:
            message: Error description.
            auth_type: Type of authentication that failed (oauth, api_key, etc.).
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if auth_type:
            context["auth_type"] = auth_type
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Content Generation Exceptions
# =============================================================================


class ContentGenerationError(YTShortsError):
    """
    Base exception for content generation failures.

    Use for:
    - Script generation failures
    - Content quality issues
    - Generation timeout
    """

    def __init__(
        self,
        message: str = "Content generation error",
        *,
        content_type: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize content generation error.

        Args:
            message: Error description.
            content_type: Type of content (script, caption, etc.).
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if content_type:
            context["content_type"] = content_type
        super().__init__(message, context=context, **kwargs)


class ScriptGenerationError(ContentGenerationError):
    """
    Raised when script generation fails.

    Use for:
    - AI/LLM script generation failures
    - Template rendering issues
    - Script validation failures
    """

    def __init__(
        self,
        message: str = "Script generation failed",
        *,
        template_name: Optional[str] = None,
        topic: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize script generation error.

        Args:
            message: Error description.
            template_name: The template that was used.
            topic: The topic for the script.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if template_name:
            context["template_name"] = template_name
        if topic:
            context["topic"] = topic
        context["content_type"] = "script"
        super().__init__(message, context=context, **kwargs)


class TemplateError(ContentGenerationError):
    """
    Raised when template processing fails.

    Use for:
    - Template not found
    - Template syntax errors
    - Variable substitution failures
    """

    def __init__(
        self,
        message: str = "Template error",
        *,
        template_name: Optional[str] = None,
        missing_variables: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize template error.

        Args:
            message: Error description.
            template_name: The template that failed.
            missing_variables: Variables that were missing.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if template_name:
            context["template_name"] = template_name
        if missing_variables:
            context["missing_variables"] = missing_variables
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Media Creation Exceptions
# =============================================================================


class MediaCreationError(YTShortsError):
    """
    Base exception for media creation failures.

    Use for:
    - Audio generation failures
    - Image generation failures
    - Media processing errors
    """

    def __init__(
        self,
        message: str = "Media creation error",
        *,
        media_type: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize media creation error.

        Args:
            message: Error description.
            media_type: Type of media (audio, image, video).
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if media_type:
            context["media_type"] = media_type
        super().__init__(message, context=context, **kwargs)


class TTSError(MediaCreationError):
    """
    Raised when text-to-speech conversion fails.

    Use for:
    - TTS API failures
    - Audio file generation issues
    - Voice/language not supported
    """

    def __init__(
        self,
        message: str = "TTS conversion failed",
        *,
        provider: Optional[str] = None,
        text_length: Optional[int] = None,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize TTS error.

        Args:
            message: Error description.
            provider: TTS provider name.
            text_length: Length of text that failed.
            language: Target language.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if provider:
            context["provider"] = provider
        if text_length is not None:
            context["text_length"] = text_length
        if language:
            context["language"] = language
        context["media_type"] = "audio"
        super().__init__(message, context=context, **kwargs)


class ImageGenerationError(MediaCreationError):
    """
    Raised when image generation fails.

    Use for:
    - AI image generation failures
    - Stock image fetch failures
    - Image processing errors
    """

    def __init__(
        self,
        message: str = "Image generation failed",
        *,
        provider: Optional[str] = None,
        prompt: Optional[str] = None,
        dimensions: Optional[tuple[int, int]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize image generation error.

        Args:
            message: Error description.
            provider: Image provider name.
            prompt: Generation prompt.
            dimensions: Target image dimensions.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if provider:
            context["provider"] = provider
        if prompt:
            context["prompt"] = prompt[:200]  # Truncate long prompts
        if dimensions:
            context["dimensions"] = f"{dimensions[0]}x{dimensions[1]}"
        context["media_type"] = "image"
        super().__init__(message, context=context, **kwargs)


class AudioProcessingError(MediaCreationError):
    """
    Raised when audio processing fails.

    Use for:
    - Audio format conversion failures
    - Audio mixing errors
    - FFmpeg audio operations
    """

    def __init__(
        self,
        message: str = "Audio processing failed",
        *,
        operation: Optional[str] = None,
        input_format: Optional[str] = None,
        output_format: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize audio processing error.

        Args:
            message: Error description.
            operation: The operation that failed.
            input_format: Source audio format.
            output_format: Target audio format.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if operation:
            context["operation"] = operation
        if input_format:
            context["input_format"] = input_format
        if output_format:
            context["output_format"] = output_format
        context["media_type"] = "audio"
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Video Compilation Exceptions
# =============================================================================


class VideoCompilationError(YTShortsError):
    """
    Base exception for video compilation failures.

    Use for:
    - Video assembly failures
    - Rendering errors
    - Timeline issues
    """

    def __init__(
        self,
        message: str = "Video compilation error",
        *,
        stage: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize video compilation error.

        Args:
            message: Error description.
            stage: The compilation stage that failed.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if stage:
            context["stage"] = stage
        super().__init__(message, context=context, **kwargs)


class FFmpegError(VideoCompilationError):
    """
    Raised when FFmpeg operations fail.

    Use for:
    - FFmpeg command failures
    - Codec issues
    - Format incompatibilities
    """

    def __init__(
        self,
        message: str = "FFmpeg error",
        *,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        stderr: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize FFmpeg error.

        Args:
            message: Error description.
            command: The FFmpeg command that failed.
            exit_code: FFmpeg exit code.
            stderr: FFmpeg error output.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if command:
            context["command"] = command[:200]  # Truncate long commands
        if exit_code is not None:
            context["exit_code"] = exit_code
        if stderr:
            context["stderr"] = stderr[:500]  # Truncate long errors
        super().__init__(message, context=context, **kwargs)


class RenderingError(VideoCompilationError):
    """
    Raised when video rendering fails.

    Use for:
    - Final video export failures
    - Encoding issues
    - Resource exhaustion during render
    """

    def __init__(
        self,
        message: str = "Rendering failed",
        *,
        resolution: Optional[str] = None,
        codec: Optional[str] = None,
        duration: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize rendering error.

        Args:
            message: Error description.
            resolution: Video resolution.
            codec: Video codec.
            duration: Video duration.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if resolution:
            context["resolution"] = resolution
        if codec:
            context["codec"] = codec
        if duration is not None:
            context["duration"] = duration
        context["stage"] = "rendering"
        super().__init__(message, context=context, **kwargs)


class ThumbnailError(VideoCompilationError):
    """
    Raised when thumbnail generation fails.

    Use for:
    - Thumbnail extraction failures
    - Image composition errors
    - Text overlay issues
    """

    def __init__(
        self,
        message: str = "Thumbnail generation failed",
        *,
        source_video: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize thumbnail error.

        Args:
            message: Error description.
            source_video: The source video path.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if source_video:
            context["source_video"] = source_video
        context["stage"] = "thumbnail"
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Upload Exceptions
# =============================================================================


class UploadError(YTShortsError):
    """
    Base exception for upload-related failures.

    Use for:
    - Video upload failures
    - Network issues during upload
    - Platform-specific upload errors
    """

    def __init__(
        self,
        message: str = "Upload error",
        *,
        platform: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize upload error.

        Args:
            message: Error description.
            platform: Target platform (youtube, etc.).
            file_path: Path to the file being uploaded.
            file_size: File size in bytes.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if platform:
            context["platform"] = platform
        if file_path:
            context["file_path"] = file_path
        if file_size is not None:
            context["file_size_mb"] = round(file_size / (1024 * 1024), 2)
        super().__init__(message, context=context, **kwargs)


class NetworkError(UploadError):
    """
    Raised when network operations fail.

    Use for:
    - Connection timeouts
    - DNS failures
    - SSL/TLS errors
    """

    def __init__(
        self,
        message: str = "Network error",
        *,
        url: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize network error.

        Args:
            message: Error description.
            url: The URL that failed.
            timeout: The timeout value.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if url:
            context["url"] = url
        if timeout is not None:
            context["timeout"] = timeout
        super().__init__(message, context=context, **kwargs)


class FileTransferError(UploadError):
    """
    Raised when file transfer fails.

    Use for:
    - Partial upload failures
    - Checksum mismatches
    - Resumable upload failures
    """

    def __init__(
        self,
        message: str = "File transfer failed",
        *,
        bytes_transferred: Optional[int] = None,
        total_bytes: Optional[int] = None,
        resumable: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize file transfer error.

        Args:
            message: Error description.
            bytes_transferred: Bytes successfully transferred.
            total_bytes: Total file size.
            resumable: Whether upload can be resumed.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if bytes_transferred is not None:
            context["bytes_transferred"] = bytes_transferred
        if total_bytes is not None:
            context["total_bytes"] = total_bytes
            if bytes_transferred is not None:
                context["progress_percent"] = round(
                    (bytes_transferred / total_bytes) * 100, 2
                )
        context["resumable"] = resumable
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Storage Exceptions
# =============================================================================


class StorageError(YTShortsError):
    """
    Base exception for storage-related failures.

    Use for:
    - File system errors
    - Storage space issues
    - Permission problems
    """

    def __init__(
        self,
        message: str = "Storage error",
        *,
        path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize storage error.

        Args:
            message: Error description.
            path: The file/directory path involved.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if path:
            context["path"] = path
        super().__init__(message, context=context, **kwargs)


class DiskSpaceError(StorageError):
    """
    Raised when disk space is insufficient.

    Use for:
    - Out of disk space
    - Quota exceeded
    - Temp directory full
    """

    def __init__(
        self,
        message: str = "Insufficient disk space",
        *,
        required_bytes: Optional[int] = None,
        available_bytes: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize disk space error.

        Args:
            message: Error description.
            required_bytes: Space needed in bytes.
            available_bytes: Space available in bytes.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if required_bytes is not None:
            context["required_mb"] = round(required_bytes / (1024 * 1024), 2)
        if available_bytes is not None:
            context["available_mb"] = round(available_bytes / (1024 * 1024), 2)
        super().__init__(message, context=context, **kwargs)


class FilePermissionError(StorageError):
    """
    Raised when file permissions are insufficient.

    Use for:
    - Read permission denied
    - Write permission denied
    - Delete permission denied
    """

    def __init__(
        self,
        message: str = "Permission denied",
        *,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize file permission error.

        Args:
            message: Error description.
            operation: The operation that was denied (read, write, delete).
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if operation:
            context["operation"] = operation
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Trend Analysis Exceptions
# =============================================================================


class TrendAnalysisError(YTShortsError):
    """
    Base exception for trend analysis failures.

    Use for:
    - Trend data fetch failures
    - Analysis errors
    - Source unavailability
    """

    def __init__(
        self,
        message: str = "Trend analysis error",
        *,
        source: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize trend analysis error.

        Args:
            message: Error description.
            source: The trend source (reddit, twitter, etc.).
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if source:
            context["source"] = source
        super().__init__(message, context=context, **kwargs)


class ScrapingError(TrendAnalysisError):
    """
    Raised when web scraping fails.

    Use for:
    - Page fetch failures
    - Anti-bot detection
    - Selector not found
    """

    def __init__(
        self,
        message: str = "Scraping failed",
        *,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize scraping error.

        Args:
            message: Error description.
            url: The URL being scraped.
            selector: The CSS/XPath selector that failed.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if url:
            context["url"] = url
        if selector:
            context["selector"] = selector
        super().__init__(message, context=context, **kwargs)


class ParsingError(TrendAnalysisError):
    """
    Raised when data parsing fails.

    Use for:
    - JSON parsing errors
    - HTML parsing errors
    - Unexpected data format
    """

    def __init__(
        self,
        message: str = "Parsing failed",
        *,
        data_format: Optional[str] = None,
        raw_data: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize parsing error.

        Args:
            message: Error description.
            data_format: Expected data format.
            raw_data: Sample of the raw data.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if data_format:
            context["data_format"] = data_format
        if raw_data:
            context["raw_data_sample"] = raw_data[:100]  # Truncate
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Pipeline Exceptions
# =============================================================================


class PipelineError(YTShortsError):
    """
    Base exception for pipeline execution failures.

    Use for:
    - Pipeline stage failures
    - Pipeline orchestration errors
    - Workflow interruptions
    """

    def __init__(
        self,
        message: str = "Pipeline error",
        *,
        pipeline_name: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize pipeline error.

        Args:
            message: Error description.
            pipeline_name: Name of the pipeline.
            run_id: Unique run identifier.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if pipeline_name:
            context["pipeline_name"] = pipeline_name
        if run_id:
            context["run_id"] = run_id
        super().__init__(message, context=context, **kwargs)


class StageError(PipelineError):
    """
    Raised when a pipeline stage fails.

    Use for:
    - Individual stage failures
    - Stage timeout
    - Stage dependency failures
    """

    def __init__(
        self,
        message: str = "Pipeline stage failed",
        *,
        stage_name: Optional[str] = None,
        stage_index: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize stage error.

        Args:
            message: Error description.
            stage_name: Name of the failed stage.
            stage_index: Index of the stage in the pipeline.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if stage_name:
            context["stage_name"] = stage_name
        if stage_index is not None:
            context["stage_index"] = stage_index
        super().__init__(message, context=context, **kwargs)


class TimeoutError(PipelineError):
    """
    Raised when an operation times out.

    Use for:
    - Stage timeout
    - API timeout
    - Processing timeout
    """

    def __init__(
        self,
        message: str = "Operation timed out",
        *,
        timeout_seconds: Optional[float] = None,
        elapsed_seconds: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize timeout error.

        Args:
            message: Error description.
            timeout_seconds: The timeout limit.
            elapsed_seconds: Time elapsed before timeout.
            **kwargs: Additional context.
        """
        context = kwargs.pop("context", {})
        if timeout_seconds is not None:
            context["timeout_seconds"] = timeout_seconds
        if elapsed_seconds is not None:
            context["elapsed_seconds"] = elapsed_seconds
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Base
    "YTShortsError",
    # Configuration
    "ConfigurationError",
    "ValidationError",
    # API
    "APIError",
    "YouTubeAPIError",
    "RateLimitError",
    "QuotaExceededError",
    "AuthenticationError",
    # Content Generation
    "ContentGenerationError",
    "ScriptGenerationError",
    "TemplateError",
    # Media Creation
    "MediaCreationError",
    "TTSError",
    "ImageGenerationError",
    "AudioProcessingError",
    # Video Compilation
    "VideoCompilationError",
    "FFmpegError",
    "RenderingError",
    "ThumbnailError",
    # Upload
    "UploadError",
    "NetworkError",
    "FileTransferError",
    # Storage
    "StorageError",
    "DiskSpaceError",
    "FilePermissionError",
    # Trend Analysis
    "TrendAnalysisError",
    "ScrapingError",
    "ParsingError",
    # Pipeline
    "PipelineError",
    "StageError",
    "TimeoutError",
]
