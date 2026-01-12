# YouTube Shorts Factory - Technical Spec (Continued)

## Build System [REF:BS-006]

### Poetry Configuration (`pyproject.toml`)

```toml
[tool.poetry]
name = "yt-shorts-factory"
version = "0.1.0"
description = "Autonomous YouTube Shorts generation and upload system"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"
repository = "https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory"
keywords = ["youtube", "automation", "shorts", "video-generation", "ai"]

[tool.poetry.dependencies]
python = "^3.11"
moviepy = "^1.0.3"
google-api-python-client = "^2.108.0"
google-auth-oauthlib = "^1.1.0"
google-auth-httplib2 = "^0.1.1"
Pillow = "^10.1.0"
beautifulsoup4 = "^4.12.0"
selenium = "^4.15.0"
webdriver-manager = "^4.0.1"
apscheduler = "^3.10.4"
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
loguru = "^0.7.2"
requests = "^2.31.0"
aiohttp = "^3.9.0"
jinja2 = "^3.1.2"
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
ffmpeg-python = "^0.2.0"
pydub = "^0.25.1"

# TTS Options
gTTS = "^2.4.0"
pyttsx3 = "^2.90"
TTS = {version = "^0.22.0", optional = true}

# AI Generation (Optional)
diffusers = {version = "^0.25.0", optional = true}
transformers = {version = "^4.36.0", optional = true}
torch = {version = "^2.1.0", optional = true}
accelerate = {version = "^0.25.0", optional = true}

# Database (for scaling)
sqlalchemy = {version = "^2.0.0", optional = true}
alembic = {version = "^1.13.0", optional = true}

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.0"
pytest-mock = "^3.12.0"
black = "^23.12.0"
ruff = "^0.1.7"
mypy = "^1.7.0"
pre-commit = "^3.5.0"
ipython = "^8.18.0"
ipdb = "^0.13.13"

[tool.poetry.extras]
ai = ["diffusers", "transformers", "torch", "accelerate", "TTS"]
database = ["sqlalchemy", "alembic"]
full = ["diffusers", "transformers", "torch", "accelerate", "TTS", "sqlalchemy", "alembic"]

[tool.poetry.scripts]
yt-shorts = "src.main:main"
yt-shorts-setup = "scripts.install_dependencies:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "C4", "ISC", "PIE", "PYI", "RSE", "RET"]
ignore = ["E501"]  # Line too long (handled by black)

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=src --cov-report=html --cov-report=term-missing"
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Makefile

```makefile
.PHONY: help install install-dev install-ai test lint format clean run docker-build docker-run

help:
	@echo "YouTube Shorts Factory - Available Commands"
	@echo "==========================================="
	@echo "install        : Install production dependencies"
	@echo "install-dev    : Install development dependencies"
	@echo "install-ai     : Install AI generation dependencies"
	@echo "test           : Run test suite with coverage"
	@echo "lint           : Run linters (ruff, mypy)"
	@echo "format         : Format code with black"
	@echo "clean          : Remove build artifacts and cache"
	@echo "run            : Run the pipeline once"
	@echo "run-daemon     : Start scheduled daemon"
	@echo "docker-build   : Build Docker image"
	@echo "docker-run     : Run in Docker container"
	@echo "setup          : Run initial setup wizard"

install:
	poetry install --only main

install-dev:
	poetry install --with dev

install-ai:
	poetry install --extras ai

test:
	poetry run pytest tests/ -v

test-unit:
	poetry run pytest tests/unit/ -v

test-integration:
	poetry run pytest tests/integration/ -v

lint:
	poetry run ruff check src/ tests/
	poetry run mypy src/

format:
	poetry run black src/ tests/
	poetry run ruff check --fix src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov dist build

run:
	poetry run python -m src.main --once

run-daemon:
	poetry run python -m src.main --daemon

setup:
	poetry run python scripts/install_dependencies.py
	poetry run python scripts/download_models.py

docker-build:
	docker build -t yt-shorts-factory:latest -f docker/Dockerfile .

docker-run:
	docker-compose -f docker/docker-compose.yml up -d

docker-logs:
	docker-compose -f docker/docker-compose.yml logs -f

docker-stop:
	docker-compose -f docker/docker-compose.yml down
```

---

## CI/CD Pipeline [REF:CICD-007]

### GitHub Actions - Main CI (`.github/workflows/ci.yml`)

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"
  POETRY_VERSION: "1.7.0"

jobs:
  test:
    name: Test Suite
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Cache Poetry installation
        uses: actions/cache@v3
        with:
          path: ~/.local
          key: poetry-${{ runner.os }}-${{ env.POETRY_VERSION }}
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: ${{ env.POETRY_VERSION }}
          virtualenvs-create: true
          virtualenvs-in-project: true
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}
      
      - name: Install dependencies
        run: poetry install --with dev
      
      - name: Install system dependencies (Ubuntu)
        if: runner.os == 'Linux'
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg imagemagick
      
      - name: Install system dependencies (Windows)
        if: runner.os == 'Windows'
        run: |
          choco install ffmpeg imagemagick -y
      
      - name: Run linters
        run: |
          poetry run ruff check src/ tests/
          poetry run mypy src/
      
      - name: Run tests
        run: poetry run pytest tests/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: ${{ matrix.os }}
  
  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
      
      - name: Build package
        run: poetry build
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist-packages
          path: dist/
  
  docker:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Release Workflow (`.github/workflows/release.yml`)

```yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

env:
  PYTHON_VERSION: "3.11"

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
      
      - name: Build package
        run: poetry build
      
      - name: Generate changelog
        id: changelog
        uses: metcalfc/changelog-generator@v4.1.0
        with:
          myToken: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          body: ${{ steps.changelog.outputs.changelog }}
          files: dist/*
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Publish to PyPI
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
        run: poetry publish
```

### Security Scanning (`.github/workflows/security-scan.yml`)

```yaml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  push:
    branches: [main]

jobs:
  security:
    name: Security Checks
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Run Bandit security linter
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json
      
      - name: Upload Bandit results
        uses: actions/upload-artifact@v3
        with:
          name: bandit-security-report
          path: bandit-report.json
```

---

## Configuration Management [REF:CM-008]

### Main Configuration (`config/config.yaml`)

```yaml
# YouTube Shorts Factory Configuration
# Copy this to config/secrets.yaml and fill in your API keys

# ============================================
# GENERAL SETTINGS
# ============================================
app:
  name: "YouTube Shorts Factory"
  version: "0.1.0"
  environment: "production"  # development, staging, production
  debug: false
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR

# ============================================
# CONTENT GENERATION
# ============================================
content:
  # Primary niche for content generation
  niche: "historical_mystery"  # Options: historical_mystery, productivity_hack, obscure_fact
  
  # Videos to generate per day
  videos_per_day: 1
  
  # Video duration constraints (seconds)
  min_duration: 15
  max_duration: 60
  target_duration: 45
  
  # Quality settings
  video_resolution: [1080, 1920]  # Portrait 9:16 for Shorts
  video_fps: 30
  video_bitrate: "5000k"
  audio_bitrate: "192k"
  
  # Style preferences
  use_ai_images: true
  use_stock_images: false
  add_background_music: true
  add_captions: true
  caption_style: "modern"  # modern, minimal, bold

# ============================================
# SCHEDULING
# ============================================
schedule:
  # When to run generation (cron format or time)
  generation_time: "03:00"  # 3 AM daily
  timezone: "America/New_York"
  
  # Upload timing
  upload_immediately: false
  scheduled_upload_time: "12:00"  # Noon for optimal engagement
  
  # Retry settings
  max_retries: 3
  retry_delay: 300  # seconds

# ============================================
# TREND ANALYSIS
# ============================================
trends:
  # Sources to scrape
  sources:
    youtube: true
    reddit: true
    twitter: false  # Requires API key
  
  # Reddit subreddits to monitor
  reddit_subreddits:
    - "todayilearned"
    - "history"
    - "productivity"
    - "LifeProTips"
  
  # Trend scoring thresholds
  min_trend_score: 0.4
  max_trend_age_hours: 24
  
  # Cache settings
  cache_trends: true
  cache_duration_hours: 6

# ============================================
# AI GENERATION
# ============================================
ai:
  # TTS Engine: gtts, pyttsx3, coqui
  tts_engine: "gtts"
  tts_language: "en"
  tts_accent: "us"  # us, uk, au, in
  tts_speed: 1.1  # 0.5-2.0
  
  # Image generation
  image_model: "stable-diffusion"  # stable-diffusion, dall-e (future)
  sd_model_id: "runwayml/stable-diffusion-v1-5"
  images_per_video: 5
  image_width: 1080
  image_height: 1920
  
  # Prompt engineering
  base_style: "cinematic lighting, highly detailed, 4k quality, dramatic atmosphere"
  negative_prompt: "blurry, low quality, distorted, ugly, watermark, text"
  
  # Generation settings
  inference_steps: 25
  guidance_scale: 7.5
  use_cpu: false  # Set true if no GPU

# ============================================
# YOUTUBE SETTINGS
# ============================================
youtube:
  # Channel settings
  channel_id: ""  # Your channel ID
  default_playlist_id: ""  # Auto-add to playlist
  
  # Upload settings
  privacy_status: "public"  # public, unlisted, private
  category_id: "27"  # Education (see YouTube categories)
  default_language: "en"
  
  # Metadata
  add_end_screen: true
  add_cards: false
  made_for_kids: false
  
  # Hashtags (max 15)
  default_hashtags:
    - "#Shorts"
    - "#Education"
    - "#DidYouKnow"
  
  # Thumbnail settings
  thumbnail_template: "modern"  # modern, bold, minimal
  add_text_to_thumbnail: true

# ============================================
# SEO & OPTIMIZATION
# ============================================
seo:
  # Title generation
  title_max_length: 70
  include_trend_keyword: true
  use_clickbait: false
  
  # Description
  description_template: |
    {hook}
    
    {body}
    
    🔔 Subscribe for more {niche} content!
    
    #Shorts {hashtags}
  
  # Tags
  max_tags: 30
  always_include_tags:
    - "shorts"
    - "educational"
    - "trending"

# ============================================
# STORAGE & CLEANUP
# ============================================
storage:
  # Base directories
  assets_dir: "./assets"
  temp_dir: "./data/temp"
  cache_dir: "./data/cache"
  archive_dir: "./data/archives"
  
  # Cleanup settings
  keep_temp_files: false
  archive_uploaded_videos: true
  max_archive_days: 30
  max_cache_size_gb: 10

# ============================================
# MONITORING & ALERTS
# ============================================
monitoring:
  # Logging
  log_to_file: true
  log_file: "./logs/yt-shorts-factory.log"
  log_rotation: "500 MB"
  log_retention: "30 days"
  
  # Metrics
  track_metrics: true
  metrics_file: "./logs/metrics.json"
  
  # Alerts
  email_alerts: false
  email_on_error: true
  email_on_success: false
  
  # Webhooks
  webhook_url: ""  # Discord/Slack webhook
  webhook_on_upload: true

# ============================================
# PERFORMANCE
# ============================================
performance:
  # Concurrency
  max_concurrent_tasks: 2
  worker_threads: 4
  
  # Resource limits
  max_memory_mb: 4096
  max_temp_storage_gb: 20
  
  # Optimization
  use_gpu: true
  gpu_device: "cuda:0"  # cuda:0 or cpu
  enable_caching: true

# ============================================
# NICHE DEFINITIONS
# ============================================
niches:
  historical_mystery:
    keywords:
      - "mystery"
      - "history"
      - "ancient"
      - "unsolved"
      - "archaeological"
    hook_patterns:
      - "This {keyword} mystery has baffled historians for centuries"
      - "The truth about {keyword} will shock you"
      - "What really happened with {keyword}?"
    
  productivity_hack:
    keywords:
      - "productivity"
      - "efficiency"
      - "time management"
      - "work smarter"
      - "life hack"
    hook_patterns:
      - "This {keyword} trick changed my life"
      - "The ultimate {keyword} hack you need to know"
      - "Stop wasting time with this {keyword} method"
  
  obscure_fact:
    keywords:
      - "fact"
      - "trivia"
      - "science"
      - "nature"
      - "technology"
    hook_patterns:
      - "Did you know this about {keyword}?"
      - "The surprising truth about {keyword}"
      - "This {keyword} fact will blow your mind"
```

### Secrets Template (`config/secrets.yaml.example`)

```yaml
# API Keys and Credentials
# NEVER commit this file to version control!
# Copy to config/secrets.yaml and fill in your values

youtube:
  client_secrets_file: "config/client_secrets.json"
  oauth_token_file: "config/youtube_token.pickle"

openai:
  api_key: "sk-your-openai-key-here"  # Optional, for GPT-based generation

twitter:
  api_key: ""
  api_secret: ""
  access_token: ""
  access_token_secret: ""

reddit:
  client_id: ""
  client_secret: ""
  user_agent: "YouTubeShortsFactory/1.0"

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"
  recipient_email: "your-email@gmail.com"

webhook:
  discord_url: ""
  slack_url: ""
```

### Environment Variables (`.env.example`)

```bash
# Environment Configuration
# Copy to .env and customize

# Application
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Paths
CONFIG_PATH=./config/config.yaml
SECRETS_PATH=./config/secrets.yaml
ASSETS_DIR=./assets
DATA_DIR=./data

# YouTube
YOUTUBE_CLIENT_SECRETS=./config/client_secrets.json
YOUTUBE_OAUTH_TOKEN=./config/youtube_token.pickle

# AI Settings
USE_GPU=true
GPU_DEVICE=cuda:0
SD_MODEL_PATH=./models/stable-diffusion

# Optional: Override config values
# VIDEOS_PER_DAY=2
# TTS_ENGINE=coqui
# UPLOAD_TIME=14:00
```

---

## Docker Configuration [REF:DC-009]

### Production Dockerfile (`docker/Dockerfile`)

```dockerfile
FROM python:3.11-slim

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="YouTube Shorts Automation Factory"

# Set environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    APP_HOME=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    wget \
    curl \
    git \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.0

# Create app directory
WORKDIR $APP_HOME

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev packages)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY assets/ ./assets/
COPY scripts/ ./scripts/

# Create data directories
RUN mkdir -p /app/data/temp /app/data/cache /app/data/archives /app/logs

# Set permissions
RUN chmod +x /app/src/main.py

# Expose ports (if adding web dashboard in future)
# EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command (can be overridden)
CMD ["python", "-m", "src.main", "--daemon"]
```

### Docker Compose (`docker/docker-compose.yml`)

```yaml
version: '3.8'

services:
  yt-shorts-factory:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: yt-shorts-factory
    restart: unless-stopped
    
    environment:
      - APP_ENV=production
      - LOG_LEVEL=INFO
      - TZ=America/New_York
    
    volumes:
      # Config (read-only)
      - ../config:/app/config:ro
      
      # Data (persistent)
      - yt-shorts-data:/app/data
      - yt-shorts-logs:/app/logs
      
      # Assets (read-only)
      - ../assets:/app/assets:ro
      
      # Models (optional, for AI generation)
      - yt-shorts-models:/app/models
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
    
    # GPU support (uncomment if using)
    # runtime: nvidia
    # environment:
    #   - NVIDIA_VISIBLE_DEVICES=all
    
    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  # Optional: Redis for task queue (future scaling)
  # redis:
  #   image: redis:7-alpine
  #   container_name: yt-shorts-redis
  #   restart: unless-stopped
  #   volumes:
  #     - yt-shorts-redis:/data

volumes:
  yt-shorts-data:
  yt-shorts-logs:
  yt-shorts-models:
  # yt-shorts-redis:
```

---

## Testing Strategy [REF:TEST-010]

### Test Structure

```python
# tests/conftest.py
"""
Shared fixtures and configuration for pytest.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock
import tempfile

from src.core.config import Config


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Config(
        app_name="test-factory",
        niche="historical_mystery",
        videos_per_day=1,
        use_ai_images=False,  # Disable AI for faster tests
        log_level="DEBUG"
    )


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_youtube_api():
    """Mock YouTube API client."""
    mock = MagicMock()
    mock.videos().insert().execute.return_value = {
        "id": "test_video_123",
        "snippet": {"title": "Test Video"}
    }
    return mock


@pytest.fixture
def sample_script():
    """Sample script for testing."""
    from src.content_generation.script_generator import Script, ScriptScene
    
    return Script(
        title="Test Historical Mystery",
        hook="Did you know this ancient mystery?",
        body="This is a test script body.",
        call_to_action="Follow for more!",
        scenes=[
            ScriptScene(
                text="Scene 1 text",
                duration=5.0,
                image_prompt="ancient mystery scene",
                transition="fade"
            )
        ],
        total_duration=30.0,
        target_keywords=["mystery", "history"]
    )


# tests/unit/test_script_generator.py
"""
Unit tests for script generation.
"""

import pytest
from src.content_generation.script_generator import ScriptGenerator
from src.trend_analysis.analyzer import TrendData
from datetime import datetime


class TestScriptGenerator:
    
    @pytest.fixture
    def generator(self, test_config):
        return ScriptGenerator(test_config)
    
    @pytest.fixture
    def sample_trend(self):
        return TrendData(
            keyword="ancient Egypt",
            score=0.85,
            source="youtube",
            category="history",
            volume=50000,
            growth_rate=25.0,
            competition="low",
            timestamp=datetime.now(),
            related_keywords=["pyramids", "pharaohs", "hieroglyphics"]
        )
    
    @pytest.mark.asyncio
    async def test_generate_script(self, generator, sample_trend):
        """Test basic script generation."""
        script = await generator.generate(
            niche="historical_mystery",
            trend=sample_trend
        )
        
        assert script is not None
        assert script.title
        assert script.hook
        assert len(script.scenes) > 0
        assert 15 <= script.total_duration <= 60
        assert "ancient Egypt" in script.title.lower() or \
               "ancient Egypt" in script.body.lower()
    
    def test_generate_hook(self, generator, sample_trend):
        """Test hook generation."""
        hook = generator._generate_hook(sample_trend)
        
        assert hook
        assert len(hook) < 100  # Hooks should be concise
        assert "ancient Egypt" in hook.lower()
    
    def test_trim_to_duration(self, generator, sample_script):
        """Test duration trimming."""
        # Add scenes to exceed 60 seconds
        for i in range(10):
            sample_script.scenes.append(
                ScriptScene(
                    text=f"Extra scene {i}",
                    duration=8.0,
                    image_prompt="test prompt"
                )
            )
        
        trimmed = generator._trim_to_duration(sample_script.scenes, target=58)
        total_duration = sum(s.duration for s in trimmed)
        
        assert total_duration <= 60
        assert len(trimmed) >= 3  # Should keep minimum scenes


# tests/integration/test_pipeline_e2e.py
"""
End-to-end integration tests for full pipeline.
"""

import pytest
from unittest.mock import patch, AsyncMock
from src.core.pipeline import Pipeline


class TestPipelineE2E:
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_pipeline_without_upload(self, test_config, temp_dir):
        """Test full pipeline without actual YouTube upload."""
        
        # Override config to use temp directory
        test_config.temp_dir = temp_dir
        test_config.use_ai_images = False  # Use stock for speed
        
        pipeline = Pipeline(test_config)
        
        # Mock the YouTube upload
        with patch.object(
            pipeline.youtube_uploader, 
            'upload', 
            new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = MagicMock(
                success=True,
                video_id="test_123",
                error=None
            )
            
            result = await pipeline.run()
            
            assert result.success
            assert result.video_id == "test_123"
            assert result.video_path.exists()
            assert result.thumbnail_path.exists()
            assert 15 <= result.duration <= 60
```

### Test Coverage Goals

```yaml
Minimum Coverage: 80%

Priority Areas:
  - Core pipeline: 90%+
  - Script generation: 85%+
  - Video compilation: 80%+
  - YouTube upload: 85%+
  - Trend analysis: 75%+

Test Types:
  - Unit: 60% of tests
  - Integration: 30% of tests
  - E2E: 10% of tests
```

---

*This completes Part 2. Ready to create Part 3 with deployment guide, monitoring, and final implementation details?*
