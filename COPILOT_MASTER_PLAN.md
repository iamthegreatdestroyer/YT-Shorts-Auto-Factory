# GitHub Copilot Master Action Plan
## Project: YouTube Shorts Automation Factory

> **INSTRUCTIONS FOR GITHUB COPILOT:**  
> This document provides step-by-step implementation instructions for building the YouTube Shorts Automation Factory. Follow each phase sequentially, implementing all components with production-ready code, comprehensive error handling, and full test coverage.

---

## 🎯 Project Overview

**Goal**: Build a fully autonomous system that generates, compiles, and uploads YouTube Shorts (15-60s videos) daily with zero manual intervention after initial setup.

**Tech Stack**: Python 3.11+, MoviePy, YouTube Data API v3, BeautifulSoup, Selenium, APScheduler, Pydantic, Loguru, Poetry

**Repository**: https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory.git

**Target Timeline**: 12 weeks to production-ready system

---

## 📋 Pre-Development Setup Checklist

Before generating any code, ensure the following structure exists:

```bash
# Create base directory structure
mkdir -p src/{core,trend_analysis,content_generation,media_creation,video_compilation,metadata,upload,monitoring,utils}
mkdir -p src/trend_analysis/sources
mkdir -p src/media_creation/{tts,image_generation}
mkdir -p src/content_generation/templates
mkdir -p tests/{unit,integration,fixtures}
mkdir -p config assets/{templates,music,fonts,images,logos}
mkdir -p data/{cache/trends,cache/generated,archives,temp}
mkdir -p scripts docker docs logs

# Create all __init__.py files
find src tests -type d -exec touch {}/__init__.py \;
```

---

## 🚀 PHASE 1: Foundation (Weeks 1-2)

### Week 1: Core Infrastructure

#### Task 1.1: Initialize Poetry Project

**File**: `pyproject.toml`

```toml
# COPILOT: Generate complete Poetry configuration with all dependencies
# Include: moviepy, google-api-python-client, google-auth-oauthlib, Pillow,
# beautifulsoup4, selenium, apscheduler, pydantic, pydantic-settings, loguru,
# requests, aiohttp, jinja2, pyyaml, python-dotenv, ffmpeg-python, pydub, gTTS
# Dev dependencies: pytest, pytest-cov, pytest-asyncio, pytest-mock, black, ruff, mypy
# Version constraints: Python ^3.11, all others use latest stable
# Add extras for: ai (diffusers, transformers, torch), database (sqlalchemy, alembic)
```

**Action**: Run `poetry install` after generation

---

#### Task 1.2: Configuration System

**File**: `src/core/config.py`

```python
# COPILOT: Create comprehensive configuration system using Pydantic v2
# 
# Requirements:
# 1. Create nested config classes for:
#    - AppConfig (name, version, environment, debug, log_level)
#    - ContentConfig (niche, videos_per_day, min/max/target_duration, video_resolution, fps)
#    - ScheduleConfig (generation_time, upload_time, timezone, max_retries, retry_delay)
#    - TrendConfig (sources dict, reddit_subreddits list, min_trend_score, cache settings)
#    - AIConfig (tts_engine, tts_language, tts_speed, image_model, inference_steps)
#    - YouTubeConfig (channel_id, privacy_status, category_id, default_language)
#    - SEOConfig (title_max_length, description_template, max_tags, default_hashtags)
#    - StorageConfig (paths for assets, temp, cache, archives)
#    - MonitoringConfig (log settings, metrics, alerts, webhooks)
#
# 2. Main Config class that:
#    - Inherits from BaseSettings
#    - Has all nested config as fields
#    - Computes Path objects for all directories relative to project root
#    - Implements @classmethod load(config_path) to load from YAML
#    - Implements save(config_path) to write to YAML
#    - Validates all paths exist or creates them
#
# 3. Add type hints for all fields
# 4. Use Field() for defaults and descriptions
# 5. Add validators for critical fields (durations, URLs, paths)
```

**File**: `config/config.yaml`

```yaml
# COPILOT: Generate default configuration matching all Config classes
# Use sensible defaults for development
# Include detailed comments explaining each section
```

---

#### Task 1.3: Custom Exceptions

**File**: `src/core/exceptions.py`

```python
# COPILOT: Create exception hierarchy for the project
#
# Base exception: YTShortsFactoryError(Exception)
#
# Specific exceptions inheriting from base:
# - ConfigurationError: Invalid config or missing required settings
# - TrendAnalysisError: Trend scraping or analysis failures
# - ScriptGenerationError: Script generation failures
# - MediaCreationError: TTS, image generation, or audio failures
# - VideoCompilationError: MoviePy rendering failures
# - UploadError: YouTube API upload failures
# - AuthenticationError: OAuth or API key issues
# - RateLimitError: API rate limit exceeded
# - StorageError: Disk space or file I/O issues
# - ValidationError: Input validation failures
#
# Each exception should:
# - Accept message and optional context dict
# - Override __str__ to include context
# - Have docstring explaining when to use it
```

---

#### Task 1.4: Constants and Enums

**File**: `src/core/constants.py`

```python
# COPILOT: Define all project constants and enums
#
# Create Enums for:
# - VideoQuality: LOW, MEDIUM, HIGH, ULTRA
# - PrivacyStatus: PUBLIC, UNLISTED, PRIVATE
# - TTSEngine: GTTS, PYTTSX3, COQUI
# - ImageSource: STABLE_DIFFUSION, STOCK, CUSTOM
# - TrendSource: YOUTUBE, REDDIT, TWITTER
# - VideoCategory: EDUCATION(27), ENTERTAINMENT(24), HOWTO(26), etc.
#
# Define constants for:
# - YouTube API quotas and limits
# - Video specs (max file size, supported formats, bitrates)
# - Scraping timeouts and retry limits
# - Cache expiration times
# - Default prompts and templates
# - API endpoints
# - File size limits
# - Supported file extensions
#
# Use typing.Final for immutable constants
# Group related constants in classes (e.g., YouTubeConstants, VideoConstants)
```

---

#### Task 1.5: Logging System

**File**: `src/monitoring/logger.py`

```python
# COPILOT: Create production-ready logging system using Loguru
#
# Function: setup_logging(config: Config) -> logger
#
# Requirements:
# 1. Remove default loguru handler
# 2. Add console handler with:
#    - Color-coded output (green time, colored level, cyan module/function)
#    - Format: "{time:HH:mm:ss} | {level:<8} | {name}:{function} | {message}"
#    - Level from config.monitoring.log_level
#
# 3. Add file handler with:
#    - Path from config.monitoring.log_file
#    - Rotation based on config (default "500 MB")
#    - Retention based on config (default "30 days")
#    - Compression: gz
#    - JSON serialization for structured logs
#    - Always log DEBUG level to file
#    - Thread-safe (enqueue=True)
#
# 4. Add error-only file handler:
#    - Separate errors.log file
#    - Only ERROR and above
#    - Include full tracebacks
#    - Backtrace and diagnose enabled
#
# 5. Add context manager for request tracing:
#    - Bind request_id to logger context
#    - Auto-generate UUID if not provided
#
# 6. Create helper decorators:
#    - @log_execution_time: Log function duration
#    - @log_errors: Catch and log exceptions
#
# 7. Initialize logger and log startup message
# 8. Return configured logger instance
```

---

#### Task 1.6: Main Entry Point

**File**: `src/main.py`

```python
# COPILOT: Create main CLI entry point with argument parsing
#
# Requirements:
# 1. Import argparse, asyncio, pathlib, sys
# 2. Import Config, Pipeline, setup_logging
#
# 3. Create async function run_once(config: Config) -> VideoResult:
#    - Set up logging
#    - Log startup message with config summary
#    - Initialize Pipeline(config)
#    - Call await pipeline.run()
#    - Log success/failure with details
#    - Return result
#
# 4. Create async function run_daemon(config: Config):
#    - Set up logging
#    - Import AsyncIOScheduler from apscheduler
#    - Parse generation_time from config
#    - Schedule run_once as cron job
#    - Add health check job (every 5 minutes)
#    - Start scheduler
#    - Log schedule details
#    - Wait on asyncio.Event() to run forever
#    - Handle KeyboardInterrupt gracefully
#    - Shutdown scheduler on exit
#
# 5. Create function main():
#    - ArgumentParser with description
#    - Add arguments:
#      --config PATH: Custom config file
#      --once: Run pipeline once and exit
#      --daemon: Run as daemon with scheduling
#      --test: Test mode (no actual upload)
#      --no-upload: Generate video but don't upload
#      --dry-run: Validate config and exit
#      --version: Print version and exit
#    - Load config from args.config or default
#    - Validate config
#    - If --dry-run: print config and exit
#    - If --version: print version and exit
#    - If --once or --test: run run_once
#    - If --daemon: run run_daemon
#    - Else: print help
#    - Handle all exceptions with logging
#    - Exit with appropriate code (0=success, 1=error)
#
# 6. Add if __name__ == "__main__": call main()
```

---

#### Task 1.7: Pipeline Orchestrator Skeleton

**File**: `src/core/pipeline.py`

```python
# COPILOT: Create main pipeline orchestration class
#
# Import all necessary types and modules
# Import future component classes (will be implemented later)
#
# Create dataclass VideoGenerationResult with fields:
# - video_id: Optional[str]
# - video_path: Path
# - thumbnail_path: Path
# - title: str
# - description: str
# - tags: List[str]
# - duration: float
# - success: bool
# - error: Optional[str]
# - execution_time: float
# - timestamp: datetime
#
# Create Pipeline class:
#
# __init__(self, config: Config):
#   - Store config
#   - Initialize all component instances:
#     * self.trend_analyzer = TrendAnalyzer(config)  # TODO: implement
#     * self.script_generator = ScriptGenerator(config)  # TODO: implement
#     * self.tts_engine = get_tts_engine(config)  # TODO: implement
#     * self.image_generator = get_image_generator(config)  # TODO: implement
#     * self.video_compiler = VideoCompiler(config)  # TODO: implement
#     * self.seo_optimizer = SEOOptimizer(config)  # TODO: implement
#     * self.youtube_uploader = YouTubeUploader(config)  # TODO: implement
#     * self.metrics_collector = MetricsCollector(config)  # TODO: implement
#   - Log initialization
#
# async def run(self) -> VideoGenerationResult:
#   - Start timer
#   - Try/except with comprehensive error handling
#   - Log each stage with emoji prefixes
#   - Call each stage in sequence:
#     1. await self._analyze_trends()
#     2. await self._generate_script(trend)
#     3. await self._create_media(script)
#     4. await self._compile_video(script, media)
#     5. await self._optimize_metadata(script, trend)
#     6. await self._upload_video(video_path, metadata)
#   - Calculate execution time
#   - Log metrics
#   - Cleanup temp files
#   - Return VideoGenerationResult
#
# Create placeholder methods for each stage:
# - async def _analyze_trends(self) -> TrendData
# - async def _generate_script(self, trend) -> Script
# - async def _create_media(self, script) -> MediaAssets
# - async def _compile_video(self, script, media) -> VideoFile
# - async def _optimize_metadata(self, script, trend) -> Metadata
# - async def _upload_video(self, video, metadata) -> str
# - async def _cleanup_temp_files(self, paths: List[Path])
#
# Each placeholder should:
# - Log that it's not yet implemented
# - Return mock data with correct type
# - Include TODO comment for future implementation
#
# Add docstrings to all methods explaining their purpose
```

---

#### Task 1.8: Utility Functions

**File**: `src/utils/file_manager.py`

```python
# COPILOT: Create file management utilities
#
# Functions to implement:
#
# 1. def ensure_directory(path: Path) -> Path:
#    - Create directory if it doesn't exist
#    - Create parent directories as needed
#    - Return the path
#    - Raise StorageError on failure
#
# 2. def get_file_size(path: Path) -> int:
#    - Return file size in bytes
#    - Handle missing files gracefully
#
# 3. def get_available_space(path: Path) -> int:
#    - Return available disk space in bytes
#    - Cross-platform (Windows/Linux/macOS)
#
# 4. def cleanup_old_files(directory: Path, max_age_days: int):
#    - Delete files older than max_age_days
#    - Skip directories
#    - Log deletions
#    - Return count of deleted files
#
# 5. def archive_file(source: Path, archive_dir: Path) -> Path:
#    - Move file to archive with timestamp prefix
#    - Create archive_dir if needed
#    - Return new path
#
# 6. def safe_delete(path: Path):
#    - Delete file with error handling
#    - Log deletion
#    - Don't raise if file doesn't exist
#
# 7. def get_unique_filename(directory: Path, base_name: str, extension: str) -> Path:
#    - Generate unique filename by adding counter if exists
#    - Format: base_name_001.extension
#
# 8. async def download_file(url: str, destination: Path, timeout: int = 30) -> Path:
#    - Download file from URL using aiohttp
#    - Show progress if file is large
#    - Validate download
#    - Return destination path
#
# Add type hints, docstrings, and error handling to all functions
```

**File**: `src/utils/validators.py`

```python
# COPILOT: Create input validation utilities
#
# Functions to implement:
#
# 1. def validate_youtube_video_id(video_id: str) -> bool:
#    - Check if string matches YouTube video ID format
#    - Return True/False
#
# 2. def sanitize_filename(filename: str, max_length: int = 255) -> str:
#    - Remove invalid characters for filenames
#    - Remove path traversal attempts (..)
#    - Truncate to max_length
#    - Replace spaces with underscores
#
# 3. def sanitize_title(title: str, max_length: int = 100) -> str:
#    - Remove YouTube-forbidden characters
#    - Truncate to max_length
#    - Strip whitespace
#
# 4. def validate_url(url: str) -> bool:
#    - Check if string is valid HTTP/HTTPS URL
#    - Use regex or urllib.parse
#
# 5. def validate_email(email: str) -> bool:
#    - Check if string is valid email format
#
# 6. def validate_video_file(path: Path) -> tuple[bool, str]:
#    - Check if file exists and is readable
#    - Check if file is valid video format
#    - Return (is_valid, error_message)
#
# 7. def validate_duration(duration: float, min_sec: int = 15, max_sec: int = 60) -> bool:
#    - Check if duration is within YouTube Shorts limits
#
# 8. def validate_resolution(width: int, height: int) -> bool:
#    - Check if resolution is valid for Shorts (9:16 aspect ratio)
#
# Add comprehensive docstrings with examples
```

**File**: `src/utils/decorators.py`

```python
# COPILOT: Create utility decorators
#
# Decorators to implement:
#
# 1. def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
#    - Retry function on exception
#    - Exponential backoff between attempts
#    - Log each retry attempt
#    - Re-raise if all attempts fail
#    - Works with both sync and async functions
#
# 2. def timeout(seconds: int):
#    - Timeout function execution
#    - Raise TimeoutError if exceeded
#    - Works with async functions
#
# 3. def cache_result(ttl_seconds: int = 3600):
#    - Cache function result in memory
#    - Use function args as cache key
#    - Expire after ttl_seconds
#    - Thread-safe
#
# 4. def measure_time(log_result: bool = True):
#    - Measure function execution time
#    - Optionally log result
#    - Return original function result
#    - Add execution_time to result if it's a dict
#
# 5. def handle_errors(default_return=None):
#    - Catch all exceptions
#    - Log with full traceback
#    - Return default_return on error
#
# All decorators should:
# - Preserve function metadata using functools.wraps
# - Support both sync and async functions where applicable
# - Include comprehensive docstrings
```

---

#### Task 1.9: Initial Tests

**File**: `tests/conftest.py`

```python
# COPILOT: Create pytest configuration and shared fixtures
#
# Import pytest, tempfile, pathlib, datetime
# Import Config and other test dependencies
#
# Fixtures to create:
#
# @pytest.fixture
# def test_config() -> Config:
#    - Create minimal test configuration
#    - Use temporary directories
#    - Set debug=True, log_level="DEBUG"
#    - Return Config instance
#
# @pytest.fixture
# def temp_dir() -> Generator[Path, None, None]:
#    - Create temporary directory
#    - Yield Path
#    - Cleanup after test
#
# @pytest.fixture
# def sample_video_path(temp_dir) -> Path:
#    - Create dummy video file (empty or minimal)
#    - Return path
#
# @pytest.fixture
# def sample_audio_path(temp_dir) -> Path:
#    - Create dummy audio file
#    - Return path
#
# @pytest.fixture
# def sample_image_path(temp_dir) -> Path:
#    - Create dummy image file
#    - Return path
#
# @pytest.fixture
# def mock_youtube_client():
#    - Create mock YouTube API client
#    - Return MagicMock with expected methods
#
# @pytest.fixture(autouse=True)
# def setup_logging():
#    - Set up minimal logging for tests
#    - Capture logs
#    - Yield
#    - Cleanup
```

**File**: `tests/unit/test_config.py`

```python
# COPILOT: Create tests for configuration system
#
# Import pytest, Config, Path, yaml
#
# Test cases:
#
# 1. test_config_default_values():
#    - Create Config with no args
#    - Assert default values are correct
#    - Check all nested config objects exist
#
# 2. test_config_load_from_yaml(tmp_path):
#    - Create test YAML file
#    - Load Config from file
#    - Assert values match YAML
#
# 3. test_config_save_to_yaml(tmp_path):
#    - Create Config instance
#    - Save to file
#    - Load back and compare
#
# 4. test_config_validation_invalid_duration():
#    - Try to create Config with invalid duration
#    - Should raise ValidationError
#
# 5. test_config_paths_created():
#    - Create Config
#    - Check that all directory paths are created
#
# 6. test_config_nested_access():
#    - Create Config
#    - Access nested properties
#    - Assert values are correct
#
# Use parametrize for multiple test cases where appropriate
```

**File**: `tests/unit/test_pipeline.py`

```python
# COPILOT: Create tests for pipeline orchestrator
#
# Import pytest, asyncio, Pipeline, Config, VideoGenerationResult
#
# Test cases:
#
# 1. test_pipeline_initialization(test_config):
#    - Create Pipeline instance
#    - Assert config is stored
#    - Assert all components are initialized
#
# 2. @pytest.mark.asyncio
#    async def test_pipeline_run_success(test_config):
#    - Create Pipeline
#    - Mock all stage methods to return success
#    - Call await pipeline.run()
#    - Assert result.success is True
#    - Assert all stages were called
#
# 3. @pytest.mark.asyncio
#    async def test_pipeline_run_failure(test_config):
#    - Create Pipeline
#    - Mock one stage to raise exception
#    - Call await pipeline.run()
#    - Assert result.success is False
#    - Assert error message is populated
#
# 4. @pytest.mark.asyncio
#    async def test_pipeline_cleanup_on_error(test_config, tmp_path):
#    - Create Pipeline
#    - Create temporary files
#    - Mock stage to fail
#    - Run pipeline
#    - Assert temp files are cleaned up
#
# Use pytest-asyncio for async tests
# Use pytest-mock for mocking
```

**File**: `tests/unit/test_utils.py`

```python
# COPILOT: Create tests for utility functions
#
# Import all utility modules
# Import pytest, pathlib, os
#
# Test file_manager utilities:
# - test_ensure_directory_creates_path
# - test_ensure_directory_exists_no_error
# - test_get_file_size
# - test_cleanup_old_files
# - test_get_unique_filename
#
# Test validators:
# - test_sanitize_filename_removes_invalid_chars
# - test_sanitize_filename_removes_path_traversal
# - test_validate_url_valid_urls
# - test_validate_url_invalid_urls
# - test_validate_duration_within_range
# - test_validate_duration_outside_range
#
# Test decorators:
# - test_retry_succeeds_after_failures
# - test_retry_exhausts_attempts
# - test_timeout_raises_error
# - test_cache_result_returns_cached_value
#
# Use parametrize for testing multiple inputs
# Use markers for slow tests
```

---

### Week 1 Completion Checklist

Run these commands to verify Week 1 completion:

```bash
# Install dependencies
poetry install

# Run linters
poetry run black src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/

# Run tests
poetry run pytest tests/unit/ -v --cov=src

# Verify imports
poetry run python -c "from src.core.config import Config; print('Config OK')"
poetry run python -c "from src.core.pipeline import Pipeline; print('Pipeline OK')"
poetry run python -c "from src.main import main; print('Main OK')"

# Test CLI
poetry run python -m src.main --help
poetry run python -m src.main --version
poetry run python -m src.main --dry-run
```

All commands should complete without errors. Test coverage should be >80% for implemented modules.

---

## 🔄 PHASE 1 Continues in Next Section...

**COPILOT**: You have now completed Week 1 of Phase 1. This establishes the foundation:
- ✅ Project structure
- ✅ Configuration system
- ✅ Logging infrastructure
- ✅ Main entry point
- ✅ Pipeline skeleton
- ✅ Utility functions
- ✅ Initial test suite

**Next**: Week 2 will implement the Trend Analysis system. Let me know when you're ready to proceed with Week 2 implementation instructions.

---

## 📝 Development Guidelines for All Phases

**Code Quality Standards:**
- ✅ Type hints on all function signatures
- ✅ Docstrings (Google style) on all public functions/classes
- ✅ Maximum line length: 100 characters
- ✅ Use async/await for I/O operations
- ✅ Handle all exceptions with specific error types
- ✅ Log all important operations
- ✅ Test coverage >80% for all modules

**Naming Conventions:**
- Classes: PascalCase (TrendAnalyzer, ScriptGenerator)
- Functions/methods: snake_case (analyze_trends, generate_script)
- Constants: UPPER_SNAKE_CASE (MAX_VIDEO_DURATION)
- Private methods: _leading_underscore (_internal_method)
- Async functions: Prefix with async, use await keyword

**Error Handling Pattern:**
```python
try:
    result = await some_operation()
    logger.info(f"Operation succeeded: {result}")
    return result
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise CustomError(f"Failed to complete operation: {e}") from e
finally:
    cleanup_resources()
```

**Logging Pattern:**
```python
logger.info("Starting operation", extra={"context": "value"})
logger.debug(f"Processing {count} items")
logger.warning(f"Potential issue: {details}")
logger.error(f"Operation failed: {error}", exc_info=True)
logger.success(f"Operation completed successfully")
```

---

