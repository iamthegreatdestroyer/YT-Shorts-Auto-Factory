# Implementation Starter Guide

This document provides **copy-paste ready code** to kickstart your development of Project Proposal 2: YouTube Shorts Automation Factory.

## Getting Started

### Step 1: Repository Setup

```bash
# Your repository is already created at:
# https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory.git

# Clone it locally
git clone https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory.git
cd YT-Shorts-Auto-Factory

# Initialize with this structure
mkdir -p src/{core,trend_analysis,content_generation,media_creation,video_compilation,metadata,upload,monitoring,utils}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p config assets/{templates,music,fonts,images} data/{cache,temp,archives} scripts docker docs

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;
```

### Step 2: Initialize Poetry

Create `pyproject.toml`:

```toml
[tool.poetry]
name = "yt-shorts-factory"
version = "0.1.0"
description = "Autonomous YouTube Shorts generation and upload system"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
repository = "https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory"

[tool.poetry.dependencies]
python = "^3.11"
moviepy = "^1.0.3"
google-api-python-client = "^2.108.0"
google-auth-oauthlib = "^1.1.0"
Pillow = "^10.1.0"
beautifulsoup4 = "^4.12.0"
selenium = "^4.15.0"
apscheduler = "^3.10.4"
pydantic = "^2.5.0"
loguru = "^0.7.2"
jinja2 = "^3.1.2"
pyyaml = "^6.0.1"
requests = "^2.31.0"
gTTS = "^2.4.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
black = "^23.12.0"
ruff = "^0.1.7"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Install dependencies:

```bash
# Install Poetry if needed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### Step 3: Core Configuration System

**File: `src/core/config.py`**

```python
"""
Configuration management using Pydantic for validation.
"""

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml


class AppConfig(BaseModel):
    """Application settings."""
    name: str = "YouTube Shorts Factory"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"


class ContentConfig(BaseModel):
    """Content generation settings."""
    niche: str = "historical_mystery"
    videos_per_day: int = 1
    min_duration: int = 15
    max_duration: int = 60
    target_duration: int = 45
    video_resolution: List[int] = [1080, 1920]
    video_fps: int = 30


class ScheduleConfig(BaseModel):
    """Scheduling settings."""
    generation_time: str = "03:00"
    upload_time: str = "12:00"
    timezone: str = "America/New_York"
    max_retries: int = 3
    retry_delay: int = 300


class YouTubeConfig(BaseModel):
    """YouTube upload settings."""
    channel_id: str = ""
    privacy_status: str = "public"
    category_id: str = "27"
    default_language: str = "en"


class Config(BaseSettings):
    """Main configuration class."""
    
    app: AppConfig = AppConfig()
    content: ContentConfig = ContentConfig()
    schedule: ScheduleConfig = ScheduleConfig()
    youtube: YouTubeConfig = YouTubeConfig()
    
    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    config_dir: Path = project_root / "config"
    assets_dir: Path = project_root / "assets"
    temp_dir: Path = project_root / "data" / "temp"
    cache_dir: Path = project_root / "data" / "cache"
    log_file: Path = project_root / "logs" / "yt-shorts-factory.log"
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)
                return cls(**data)
        
        return cls()
    
    def save(self, config_path: Optional[Path] = None):
        """Save configuration to YAML file."""
        if config_path is None:
            config_path = self.config_dir / "config.yaml"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
```

**File: `config/config.yaml`**

```yaml
app:
  name: "YouTube Shorts Factory"
  version: "0.1.0"
  environment: "development"
  debug: true
  log_level: "DEBUG"

content:
  niche: "historical_mystery"
  videos_per_day: 1
  min_duration: 15
  max_duration: 60
  target_duration: 45
  video_resolution: [1080, 1920]
  video_fps: 30

schedule:
  generation_time: "03:00"
  upload_time: "12:00"
  timezone: "America/New_York"
  max_retries: 3
  retry_delay: 300

youtube:
  channel_id: ""
  privacy_status: "public"
  category_id: "27"
  default_language: "en"
```

### Step 4: Logging Setup

**File: `src/monitoring/logger.py`**

```python
"""
Centralized logging configuration.
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: Path = None):
    """Configure loguru logger."""
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            rotation="10 MB",
            retention="30 days",
            compression="gz",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG"
        )
    
    return logger


# Usage
# from src.monitoring.logger import setup_logging
# logger = setup_logging(log_level="DEBUG", log_file=Path("logs/app.log"))
```

### Step 5: Main Entry Point

**File: `src/main.py`**

```python
"""
Main entry point for YouTube Shorts Factory.
"""

import asyncio
import argparse
from pathlib import Path

from src.core.config import Config
from src.core.pipeline import Pipeline
from src.monitoring.logger import setup_logging


async def run_once(config: Config):
    """Run pipeline once and exit."""
    logger = setup_logging(config.app.log_level, config.log_file)
    logger.info("Starting single pipeline execution")
    
    pipeline = Pipeline(config)
    result = await pipeline.run()
    
    if result.success:
        logger.success(f"Pipeline completed successfully: {result.video_id}")
    else:
        logger.error(f"Pipeline failed: {result.error}")
    
    return result


async def run_daemon(config: Config):
    """Run as daemon with scheduling."""
    logger = setup_logging(config.app.log_level, config.log_file)
    logger.info("Starting daemon mode")
    
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    
    scheduler = AsyncIOScheduler()
    
    # Schedule daily generation
    hour, minute = map(int, config.schedule.generation_time.split(':'))
    scheduler.add_job(
        run_once,
        'cron',
        hour=hour,
        minute=minute,
        args=[config],
        timezone=config.schedule.timezone
    )
    
    scheduler.start()
    logger.info(f"Scheduled daily generation at {config.schedule.generation_time}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down daemon")
        scheduler.shutdown()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="YouTube Shorts Automation Factory")
    parser.add_argument("--config", type=Path, help="Path to config file")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--test", action="store_true", help="Test mode (no upload)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config.load(args.config)
    
    # Run appropriate mode
    if args.once or args.test:
        asyncio.run(run_once(config))
    elif args.daemon:
        asyncio.run(run_daemon(config))
    else:
        print("Please specify --once or --daemon mode")
        parser.print_help()


if __name__ == "__main__":
    main()
```

### Step 6: Pipeline Skeleton

**File: `src/core/pipeline.py`**

```python
"""
Main pipeline orchestration.
"""

from typing import Optional
from dataclasses import dataclass
from loguru import logger

from src.core.config import Config


@dataclass
class VideoResult:
    """Result of video generation."""
    success: bool
    video_id: Optional[str] = None
    video_path: Optional[str] = None
    error: Optional[str] = None


class Pipeline:
    """
    Main video generation pipeline.
    
    Orchestrates all stages from trend analysis to upload.
    """
    
    def __init__(self, config: Config):
        self.config = config
        logger.info("Pipeline initialized")
    
    async def run(self) -> VideoResult:
        """
        Execute full pipeline.
        
        Returns:
            VideoResult with success status and details
        """
        try:
            logger.info("🚀 Starting pipeline execution")
            
            # Stage 1: Trend Analysis (TODO)
            logger.info("📊 Stage 1: Analyzing trends")
            trend = await self._analyze_trends()
            
            # Stage 2: Script Generation (TODO)
            logger.info("✍️ Stage 2: Generating script")
            script = await self._generate_script(trend)
            
            # Stage 3: Media Creation (TODO)
            logger.info("🎤 Stage 3: Creating media")
            media = await self._create_media(script)
            
            # Stage 4: Video Compilation (TODO)
            logger.info("🎬 Stage 4: Compiling video")
            video_path = await self._compile_video(media)
            
            # Stage 5: Upload (TODO)
            logger.info("📤 Stage 5: Uploading to YouTube")
            video_id = await self._upload_video(video_path)
            
            logger.success(f"✅ Pipeline completed: {video_id}")
            
            return VideoResult(
                success=True,
                video_id=video_id,
                video_path=video_path
            )
            
        except Exception as e:
            logger.exception("Pipeline execution failed")
            return VideoResult(
                success=False,
                error=str(e)
            )
    
    async def _analyze_trends(self):
        """Placeholder for trend analysis."""
        logger.debug("Trend analysis not yet implemented")
        return {"keyword": "ancient egypt", "score": 0.85}
    
    async def _generate_script(self, trend):
        """Placeholder for script generation."""
        logger.debug("Script generation not yet implemented")
        return {"text": "Test script", "scenes": []}
    
    async def _create_media(self, script):
        """Placeholder for media creation."""
        logger.debug("Media creation not yet implemented")
        return {"audio": None, "images": []}
    
    async def _compile_video(self, media):
        """Placeholder for video compilation."""
        logger.debug("Video compilation not yet implemented")
        return "test_video.mp4"
    
    async def _upload_video(self, video_path):
        """Placeholder for YouTube upload."""
        logger.debug("Upload not yet implemented")
        return "test_video_123"
```

### Step 7: First Test

**File: `tests/unit/test_pipeline.py`**

```python
"""
Test pipeline orchestration.
"""

import pytest
from src.core.config import Config
from src.core.pipeline import Pipeline


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Config()


@pytest.mark.asyncio
async def test_pipeline_initialization(test_config):
    """Test pipeline can be initialized."""
    pipeline = Pipeline(test_config)
    assert pipeline is not None
    assert pipeline.config == test_config


@pytest.mark.asyncio
async def test_pipeline_run(test_config):
    """Test pipeline execution (placeholder stages)."""
    pipeline = Pipeline(test_config)
    result = await pipeline.run()
    
    # With placeholder implementations, should complete
    assert result.success is True
    assert result.video_id is not None
```

Run the test:

```bash
poetry run pytest tests/unit/test_pipeline.py -v
```

## Next Steps

You now have a **working skeleton** with:

✅ Configuration system  
✅ Logging setup  
✅ Main entry point  
✅ Pipeline structure  
✅ Initial tests  

### Recommended Development Order:

1. **Week 1**: Complete `src/trend_analysis/`
   - Implement YouTube trends scraper
   - Implement Reddit scraper
   - Create trend scoring algorithm

2. **Week 2**: Complete `src/content_generation/`
   - Build template system
   - Implement script generator
   - Add validation logic

3. **Week 3**: Complete `src/media_creation/`
   - Integrate TTS engine
   - Set up image generation or stock assets
   - Create caption generator

4. **Week 4**: Complete `src/video_compilation/`
   - Implement MoviePy video compiler
   - Add effects and transitions
   - Create thumbnail generator

5. **Week 5**: Complete `src/upload/`
   - YouTube API integration
   - OAuth authentication
   - Upload with retry logic

## Using GitHub Copilot

With this structure in place, GitHub Copilot will be **highly effective** at:

- Completing function implementations
- Writing tests based on docstrings
- Generating boilerplate code
- Suggesting error handling

**Example Copilot prompts:**

```python
# In src/trend_analysis/scraper.py

# TODO: Implement YouTube trends scraper using BeautifulSoup
# Should scrape trending videos from youtube.com/feed/trending
# Extract: title, views, upload time, channel
# Return list of TrendData objects

# Copilot will suggest complete implementation
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/trend-analysis

# Make changes
git add src/trend_analysis/
git commit -m "feat: implement YouTube trends scraper"

# Push and create PR
git push origin feature/trend-analysis
```

## Ready to Code!

You have everything you need to start development. The specification provides detailed implementation guidance for each component.

**Start with Phase 1, Week 1 tasks** and build incrementally. Each component is designed to work independently, allowing parallel development if working with a team.

Good luck! 🚀
