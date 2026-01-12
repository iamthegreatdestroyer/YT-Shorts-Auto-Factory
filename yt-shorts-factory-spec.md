# YouTube Shorts Automation Factory - Technical Implementation Specification

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Core Components](#core-components)
6. [Data Flow](#data-flow)
7. [Configuration Management](#configuration-management)
8. [Build System](#build-system)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Guide](#deployment-guide)
12. [Monitoring & Logging](#monitoring--logging)
13. [Security Considerations](#security-considerations)
14. [Scalability & Future Enhancements](#scalability--future-enhancements)

---

## Executive Summary [REF:ES-001]

### Project Goals
- Autonomous generation and upload of YouTube Shorts (15-60s)
- Zero manual intervention after initial setup
- Cross-platform support (Windows/Linux)
- Local processing (no cloud costs)
- Trend-aware content generation
- Sub-linear income scaling through algorithmic growth

### Key Metrics
- **Target Output**: 1-3 shorts per day
- **Processing Time**: ~5-15 minutes per short
- **Storage Requirements**: ~50GB for assets and temp files
- **CPU Utilization**: 40-60% during generation
- **Memory**: 4-8GB during video compilation

### Revenue Model
- YouTube Partner Program (YPP) monetization
- Target: $1,000-$10,000/month after channel growth
- Timeline: 3-6 months to monetization threshold

---

## System Architecture [REF:SA-002]

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Scheduler Layer                          │
│  (APScheduler / Cron) - Triggers daily generation pipeline   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Orchestration Layer                         │
│           (Main Pipeline Controller)                         │
└─────────────────────────────────────────────────────────────┘
       ↓              ↓              ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Trend   │  │  Script  │  │  Media   │  │ YouTube  │
│ Analysis │→ │Generator │→ │Compiler  │→ │ Uploader │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
       ↓              ↓              ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│Web Scrape│  │   TTS    │  │  Image   │  │  OAuth   │
│  Engine  │  │ Service  │  │Generator │  │  Manager │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
                              ↓
                      ┌──────────────┐
                      │Stable Diffusion│
                      │   (Optional)   │
                      └──────────────┘

                    ┌─────────────────┐
                    │  Storage Layer  │
                    │ • Assets        │
                    │ • Temp Files    │
                    │ • Logs          │
                    │ • Cache         │
                    └─────────────────┘
```

### Component Interactions

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Execution Flow                   │
└─────────────────────────────────────────────────────────────┘

1. TRIGGER (Daily Schedule)
   ↓
2. TREND ANALYSIS
   • Scrape YouTube Trends
   • Analyze Reddit/X mentions
   • Extract trending keywords
   • Store in trend_cache.json
   ↓
3. CONTENT GENERATION
   • Select niche + trend combination
   • Generate script via templates or LLM
   • Validate script length/quality
   ↓
4. MEDIA CREATION
   ├─→ AUDIO: TTS generation (gTTS/Coqui)
   ├─→ VISUALS: AI images (SD) or stock assets
   └─→ CAPTIONS: SRT generation for accessibility
   ↓
5. VIDEO COMPILATION
   • Assemble timeline (moviepy)
   • Add background music
   • Render captions/text overlays
   • Generate thumbnail
   • Export MP4 (H.264, 1080x1920)
   ↓
6. METADATA OPTIMIZATION
   • Generate SEO-optimized title
   • Write description with timestamps
   • Extract tags from script
   • Add hashtags
   ↓
7. UPLOAD TO YOUTUBE
   • OAuth authentication
   • Upload via YouTube Data API v3
   • Set visibility (public/scheduled)
   • Add to playlist
   ↓
8. LOGGING & CLEANUP
   • Log success/failure
   • Archive assets
   • Clean temp files
   • Update analytics dashboard
```

---

## Technology Stack [REF:TS-003]

### Core Languages & Frameworks
```yaml
Runtime:
  - Python: 3.11+
  - Poetry: Dependency management
  
Core Libraries:
  - moviepy: 1.0.3+ (video editing)
  - google-api-python-client: 2.108.0+ (YouTube upload)
  - google-auth-oauthlib: 1.1.0+ (OAuth)
  - Pillow: 10.1.0+ (image processing)
  - beautifulsoup4: 4.12.0+ (web scraping)
  - selenium: 4.15.0+ (dynamic content scraping)
  - apscheduler: 3.10.4+ (scheduling)
  - pydantic: 2.5.0+ (config validation)
  - loguru: 0.7.2+ (structured logging)
  
TTS Options:
  - gTTS: 2.4.0+ (simple, cloud-based)
  - pyttsx3: 2.90+ (offline, multi-platform)
  - Coqui TTS: 0.22.0+ (high-quality, local)
  
AI Generation (Optional):
  - diffusers: 0.25.0+ (Stable Diffusion pipeline)
  - transformers: 4.36.0+ (model loading)
  - torch: 2.1.0+ (AMD ROCm support)
  
Testing:
  - pytest: 7.4.0+
  - pytest-cov: 4.1.0+
  - pytest-asyncio: 0.21.0+
  - pytest-mock: 3.12.0+
  
CI/CD:
  - GitHub Actions
  - Docker: 24.0+
  - docker-compose: 2.23.0+
```

### External Tools
```yaml
System Dependencies:
  - ffmpeg: 6.0+ (video/audio processing)
  - ImageMagick: 7.1.0+ (image manipulation)
  - Chrome/Chromium: Latest (for Selenium)
  - chromedriver: Matching Chrome version

Optional:
  - CUDA/ROCm: For GPU-accelerated AI generation
  - Redis: For distributed task queue (future scaling)
```

---

## Project Structure [REF:PS-004]

```
yt-shorts-factory/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Main CI pipeline
│   │   ├── release.yml               # Release automation
│   │   └── security-scan.yml         # Security scanning
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
│
├── src/
│   ├── __init__.py
│   ├── main.py                       # Entry point & orchestrator
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pipeline.py               # Main pipeline orchestration
│   │   ├── config.py                 # Configuration loader (Pydantic)
│   │   ├── exceptions.py             # Custom exceptions
│   │   └── constants.py              # Global constants
│   │
│   ├── trend_analysis/
│   │   ├── __init__.py
│   │   ├── scraper.py                # Web scraping (YouTube/Reddit/X)
│   │   ├── analyzer.py               # Trend scoring & filtering
│   │   ├── cache.py                  # Trend caching mechanism
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── youtube_trends.py
│   │       ├── reddit_scraper.py
│   │       └── twitter_api.py        # X API integration
│   │
│   ├── content_generation/
│   │   ├── __init__.py
│   │   ├── script_generator.py       # Template-based or LLM script gen
│   │   ├── niche_selector.py         # Niche + trend combination logic
│   │   ├── templates/
│   │   │   ├── historical_mystery.jinja2
│   │   │   ├── productivity_hack.jinja2
│   │   │   └── obscure_fact.jinja2
│   │   └── validators.py             # Script quality checks
│   │
│   ├── media_creation/
│   │   ├── __init__.py
│   │   ├── tts/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # TTS interface
│   │   │   ├── gtts_engine.py
│   │   │   ├── pyttsx3_engine.py
│   │   │   └── coqui_engine.py
│   │   ├── image_generation/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Image generator interface
│   │   │   ├── stable_diffusion.py
│   │   │   ├── stock_assets.py       # Pre-made asset pool
│   │   │   └── compositor.py         # Image composition logic
│   │   ├── caption_generator.py      # SRT/subtitle generation
│   │   └── audio_mixer.py            # Background music integration
│   │
│   ├── video_compilation/
│   │   ├── __init__.py
│   │   ├── compiler.py               # Main video assembly (moviepy)
│   │   ├── timeline_builder.py       # Scene/clip ordering
│   │   ├── effects.py                # Transitions, zooms, etc.
│   │   ├── thumbnail_generator.py    # Auto-thumbnail creation
│   │   └── rendering.py              # Export settings & optimization
│   │
│   ├── metadata/
│   │   ├── __init__.py
│   │   ├── seo_optimizer.py          # Title/description/tag generation
│   │   ├── keyword_extractor.py      # NLP keyword extraction
│   │   └── hashtag_generator.py      # Trending hashtag selection
│   │
│   ├── upload/
│   │   ├── __init__.py
│   │   ├── youtube_uploader.py       # YouTube Data API integration
│   │   ├── oauth_manager.py          # OAuth token management
│   │   ├── retry_handler.py          # Upload retry logic
│   │   └── playlist_manager.py       # Auto-playlist organization
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── logger.py                 # Structured logging setup
│   │   ├── metrics.py                # Performance tracking
│   │   └── alerting.py               # Error notification system
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_manager.py           # Asset storage/cleanup
│       ├── network.py                # HTTP utilities
│       ├── validators.py             # General validation
│       └── decorators.py             # Retry, cache decorators
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── unit/
│   │   ├── test_trend_analysis.py
│   │   ├── test_script_generator.py
│   │   ├── test_tts.py
│   │   ├── test_video_compiler.py
│   │   └── test_youtube_uploader.py
│   ├── integration/
│   │   ├── test_pipeline_e2e.py
│   │   └── test_upload_workflow.py
│   └── fixtures/
│       ├── sample_scripts.json
│       ├── mock_trends.json
│       └── test_video.mp4
│
├── assets/
│   ├── templates/                    # Video templates
│   ├── music/                        # Royalty-free background music
│   ├── fonts/                        # Fonts for captions
│   ├── images/                       # Stock images/overlays
│   └── logos/                        # Channel branding
│
├── data/
│   ├── cache/
│   │   ├── trends/                   # Cached trend data
│   │   └── generated/                # Generated content cache
│   ├── archives/                     # Archived videos
│   └── temp/                         # Temporary processing files
│
├── config/
│   ├── config.yaml                   # Main configuration
│   ├── config.example.yaml           # Template for users
│   ├── niches.yaml                   # Niche definitions
│   ├── prompts.yaml                  # AI generation prompts
│   └── secrets.yaml.example          # API keys template (gitignored)
│
├── scripts/
│   ├── setup.sh                      # Linux setup script
│   ├── setup.ps1                     # Windows setup script
│   ├── install_dependencies.py       # Dependency installer
│   ├── download_models.py            # Download AI models
│   └── test_pipeline.py              # Manual pipeline test
│
├── docker/
│   ├── Dockerfile                    # Production container
│   ├── Dockerfile.dev                # Development container
│   └── docker-compose.yml            # Multi-service orchestration
│
├── docs/
│   ├── SETUP.md                      # Setup guide
│   ├── CONFIGURATION.md              # Configuration reference
│   ├── API.md                        # API documentation
│   ├── TROUBLESHOOTING.md            # Common issues
│   └── ARCHITECTURE.md               # System architecture details
│
├── .env.example                      # Environment variables template
├── .gitignore
├── .dockerignore
├── pyproject.toml                    # Poetry config & dependencies
├── poetry.lock                       # Locked dependencies
├── pytest.ini                        # Pytest configuration
├── setup.py                          # Package setup (if needed)
├── README.md                         # Project overview
├── LICENSE                           # MIT License
└── CHANGELOG.md                      # Version history
```

---

## Core Components [REF:CC-005]

### 1. Pipeline Orchestrator (`src/core/pipeline.py`)

```python
"""
Main pipeline orchestration logic.
Coordinates all stages of video generation and upload.
"""

from typing import Dict, Any, Optional
from loguru import logger
from pydantic import BaseModel

from src.trend_analysis.analyzer import TrendAnalyzer
from src.content_generation.script_generator import ScriptGenerator
from src.media_creation.tts.gtts_engine import GTTSEngine
from src.media_creation.image_generation.stable_diffusion import SDImageGenerator
from src.video_compilation.compiler import VideoCompiler
from src.metadata.seo_optimizer import SEOOptimizer
from src.upload.youtube_uploader import YouTubeUploader
from src.core.config import Config
from src.core.exceptions import PipelineError


class VideoGenerationResult(BaseModel):
    """Result of video generation pipeline."""
    video_id: Optional[str] = None
    video_path: str
    thumbnail_path: str
    title: str
    description: str
    tags: list[str]
    duration: float
    success: bool
    error: Optional[str] = None


class Pipeline:
    """
    Main pipeline for autonomous video generation.
    
    Orchestrates:
    1. Trend analysis
    2. Script generation
    3. Media creation (TTS, images)
    4. Video compilation
    5. Metadata optimization
    6. YouTube upload
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.trend_analyzer = TrendAnalyzer(config)
        self.script_generator = ScriptGenerator(config)
        self.tts_engine = GTTSEngine(config)
        self.image_generator = SDImageGenerator(config) if config.use_ai_images else None
        self.video_compiler = VideoCompiler(config)
        self.seo_optimizer = SEOOptimizer(config)
        self.youtube_uploader = YouTubeUploader(config)
        
    async def run(self) -> VideoGenerationResult:
        """
        Execute full pipeline from trend analysis to upload.
        
        Returns:
            VideoGenerationResult with success status and metadata
        """
        try:
            logger.info("🚀 Starting video generation pipeline")
            
            # Stage 1: Trend Analysis
            logger.info("📊 Stage 1: Analyzing trends")
            trends = await self.trend_analyzer.get_trending_topics()
            selected_trend = self.trend_analyzer.select_best_trend(trends)
            logger.info(f"Selected trend: {selected_trend.keyword}")
            
            # Stage 2: Script Generation
            logger.info("✍️ Stage 2: Generating script")
            script = await self.script_generator.generate(
                niche=self.config.niche,
                trend=selected_trend
            )
            logger.info(f"Generated script ({len(script.sentences)} sentences)")
            
            # Stage 3: Media Creation
            logger.info("🎤 Stage 3: Creating media assets")
            
            # TTS Generation
            audio_path = await self.tts_engine.generate(script.text)
            
            # Image Generation
            if self.image_generator:
                images = await self.image_generator.generate_sequence(
                    prompts=script.image_prompts,
                    count=len(script.scenes)
                )
            else:
                images = self._get_stock_images(script.scenes)
            
            logger.info(f"Generated {len(images)} images and audio track")
            
            # Stage 4: Video Compilation
            logger.info("🎬 Stage 4: Compiling video")
            video_result = await self.video_compiler.compile(
                script=script,
                audio_path=audio_path,
                images=images
            )
            logger.info(f"Compiled video: {video_result.path}")
            
            # Stage 5: Metadata Optimization
            logger.info("🔍 Stage 5: Optimizing metadata")
            metadata = await self.seo_optimizer.generate_metadata(
                script=script,
                trend=selected_trend
            )
            logger.info(f"Generated metadata: '{metadata.title}'")
            
            # Stage 6: YouTube Upload
            logger.info("📤 Stage 6: Uploading to YouTube")
            upload_result = await self.youtube_uploader.upload(
                video_path=video_result.path,
                thumbnail_path=video_result.thumbnail_path,
                metadata=metadata
            )
            
            if upload_result.success:
                logger.success(f"✅ Video uploaded successfully: {upload_result.video_id}")
            else:
                logger.error(f"❌ Upload failed: {upload_result.error}")
            
            # Cleanup
            await self._cleanup_temp_files(video_result)
            
            return VideoGenerationResult(
                video_id=upload_result.video_id,
                video_path=video_result.path,
                thumbnail_path=video_result.thumbnail_path,
                title=metadata.title,
                description=metadata.description,
                tags=metadata.tags,
                duration=video_result.duration,
                success=upload_result.success,
                error=upload_result.error
            )
            
        except Exception as e:
            logger.exception("Pipeline execution failed")
            raise PipelineError(f"Pipeline failed: {str(e)}") from e
    
    def _get_stock_images(self, scenes: list) -> list:
        """Fallback to stock images if AI generation disabled."""
        # Implementation for stock image selection
        pass
    
    async def _cleanup_temp_files(self, video_result):
        """Clean up temporary files after successful upload."""
        # Implementation for cleanup
        pass
```

### 2. Trend Analyzer (`src/trend_analysis/analyzer.py`)

```python
"""
Trend analysis and scoring system.
Aggregates data from multiple sources to identify optimal content topics.
"""

from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel
from loguru import logger

from src.trend_analysis.sources.youtube_trends import YouTubeTrendsScraper
from src.trend_analysis.sources.reddit_scraper import RedditScraper
from src.trend_analysis.cache import TrendCache
from src.core.config import Config


class TrendData(BaseModel):
    """Represents a trending topic with metadata."""
    keyword: str
    score: float
    source: str
    category: str
    volume: int
    growth_rate: float
    competition: str  # 'low', 'medium', 'high'
    timestamp: datetime
    related_keywords: List[str] = []


class TrendAnalyzer:
    """
    Analyzes trends from multiple sources and scores them.
    
    Scoring factors:
    - Search volume
    - Growth rate
    - Competition level
    - Relevance to configured niche
    - Recency
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.youtube_scraper = YouTubeTrendsScraper()
        self.reddit_scraper = RedditScraper(config.reddit_subreddits)
        self.cache = TrendCache(config.cache_dir)
        
    async def get_trending_topics(self, force_refresh: bool = False) -> List[TrendData]:
        """
        Fetch and aggregate trending topics from all sources.
        
        Args:
            force_refresh: Bypass cache and fetch fresh data
            
        Returns:
            List of TrendData sorted by score (highest first)
        """
        # Check cache first
        if not force_refresh:
            cached = self.cache.get_trends(max_age_hours=6)
            if cached:
                logger.info(f"Using {len(cached)} cached trends")
                return cached
        
        logger.info("Fetching fresh trend data from all sources")
        
        # Fetch from all sources concurrently
        youtube_task = self.youtube_scraper.fetch_trends()
        reddit_task = self.reddit_scraper.fetch_trends()
        
        youtube_trends, reddit_trends = await asyncio.gather(
            youtube_task, reddit_task, return_exceptions=True
        )
        
        # Handle errors gracefully
        all_trends = []
        if isinstance(youtube_trends, list):
            all_trends.extend(youtube_trends)
        else:
            logger.warning(f"YouTube trends fetch failed: {youtube_trends}")
        
        if isinstance(reddit_trends, list):
            all_trends.extend(reddit_trends)
        else:
            logger.warning(f"Reddit trends fetch failed: {reddit_trends}")
        
        # Score and sort
        scored_trends = self._score_trends(all_trends)
        scored_trends.sort(key=lambda t: t.score, reverse=True)
        
        # Cache results
        self.cache.save_trends(scored_trends)
        
        logger.info(f"Found {len(scored_trends)} total trends")
        return scored_trends
    
    def _score_trends(self, trends: List[TrendData]) -> List[TrendData]:
        """
        Apply scoring algorithm to rank trends.
        
        Scoring formula:
        score = (volume_score * 0.3) + 
                (growth_score * 0.3) + 
                (niche_relevance * 0.25) + 
                (competition_score * 0.15)
        """
        for trend in trends:
            # Normalize volume (log scale)
            volume_score = min(trend.volume / 10000, 1.0)
            
            # Growth rate score
            growth_score = min(trend.growth_rate / 100, 1.0)
            
            # Niche relevance (keyword matching)
            niche_relevance = self._calculate_niche_relevance(trend.keyword)
            
            # Competition score (inverse)
            competition_map = {'low': 1.0, 'medium': 0.6, 'high': 0.3}
            competition_score = competition_map.get(trend.competition, 0.5)
            
            # Final score
            trend.score = (
                volume_score * 0.3 +
                growth_score * 0.3 +
                niche_relevance * 0.25 +
                competition_score * 0.15
            )
        
        return trends
    
    def _calculate_niche_relevance(self, keyword: str) -> float:
        """Calculate how relevant a keyword is to configured niche."""
        niche_keywords = self.config.niche_keywords
        keyword_lower = keyword.lower()
        
        matches = sum(1 for nk in niche_keywords if nk.lower() in keyword_lower)
        return min(matches / len(niche_keywords), 1.0)
    
    def select_best_trend(self, trends: List[TrendData]) -> TrendData:
        """
        Select the best trend for video creation.
        
        Applies additional filters:
        - Not used in recent videos
        - Minimum score threshold
        - Category diversity
        """
        # Filter out recently used trends
        recent_videos = self._get_recent_video_topics(days=7)
        available_trends = [
            t for t in trends 
            if t.keyword not in recent_videos
        ]
        
        if not available_trends:
            logger.warning("All top trends recently used, expanding search")
            available_trends = trends
        
        # Apply minimum score threshold
        min_score = self.config.min_trend_score
        qualified_trends = [t for t in available_trends if t.score >= min_score]
        
        if not qualified_trends:
            logger.warning(f"No trends meet minimum score {min_score}, using best available")
            return available_trends[0]
        
        # Return top trend
        return qualified_trends[0]
    
    def _get_recent_video_topics(self, days: int = 7) -> List[str]:
        """Get topics used in recent videos to avoid repetition."""
        # Query video database/logs for recent topics
        # Implementation depends on how you track uploaded videos
        return []
```

### 3. Script Generator (`src/content_generation/script_generator.py`)

```python
"""
Script generation using templates or LLM.
Creates engaging short-form content optimized for YouTube Shorts.
"""

from typing import List, Optional
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
import random

from src.core.config import Config
from src.trend_analysis.analyzer import TrendData


class ScriptScene(BaseModel):
    """Represents a single scene in the video."""
    text: str
    duration: float  # seconds
    image_prompt: str
    transition: str = "fade"


class Script(BaseModel):
    """Complete video script with metadata."""
    title: str
    hook: str  # First 3 seconds - critical for retention
    body: str
    call_to_action: str
    scenes: List[ScriptScene]
    total_duration: float
    target_keywords: List[str]
    
    @property
    def text(self) -> str:
        """Full script text."""
        return f"{self.hook} {self.body} {self.call_to_action}"
    
    @property
    def sentences(self) -> List[str]:
        """Script split into sentences."""
        return [s.text for s in self.scenes]
    
    @property
    def image_prompts(self) -> List[str]:
        """All image generation prompts."""
        return [s.image_prompt for s in self.scenes]


class ScriptGenerator:
    """
    Generates video scripts using template system.
    
    Templates are Jinja2 files with niche-specific structures.
    Future: Can integrate LLM for more dynamic generation.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(config.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.hooks_library = self._load_hooks()
        
    async def generate(self, niche: str, trend: TrendData) -> Script:
        """
        Generate a complete script for a video.
        
        Args:
            niche: Content niche (e.g., 'historical_mystery')
            trend: Trending topic to incorporate
            
        Returns:
            Complete Script object ready for production
        """
        # Select template
        template_name = self._select_template(niche)
        template = self.env.get_template(template_name)
        
        # Generate hook (first 3 seconds - critical!)
        hook = self._generate_hook(trend)
        
        # Render template with trend data
        rendered = template.render(
            trend_keyword=trend.keyword,
            related_keywords=trend.related_keywords,
            hook=hook
        )
        
        # Parse into scenes
        scenes = self._parse_into_scenes(rendered, trend)
        
        # Calculate timing
        total_duration = sum(s.duration for s in scenes)
        
        # Ensure duration is within Shorts limits (15-60s)
        if total_duration > 60:
            scenes = self._trim_to_duration(scenes, target=58)
            total_duration = sum(s.duration for s in scenes)
        
        return Script(
            title=self._generate_title(trend),
            hook=hook,
            body=rendered,
            call_to_action=self._generate_cta(),
            scenes=scenes,
            total_duration=total_duration,
            target_keywords=[trend.keyword] + trend.related_keywords[:5]
        )
    
    def _generate_hook(self, trend: TrendData) -> str:
        """
        Generate attention-grabbing hook.
        
        Hook patterns:
        - Question: "Did you know that [fact]?"
        - Shocking statement: "This [topic] will blow your mind"
        - Challenge: "Can you guess what [mystery]?"
        - Number: "3 things you didn't know about [topic]"
        """
        patterns = self.config.hook_patterns
        selected_pattern = random.choice(patterns)
        
        return selected_pattern.format(keyword=trend.keyword)
    
    def _parse_into_scenes(self, text: str, trend: TrendData) -> List[ScriptScene]:
        """
        Break script into scenes with timing and image prompts.
        
        Each scene = 1-2 sentences, 3-8 seconds
        """
        sentences = text.split('. ')
        scenes = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            # Estimate duration (reading speed ~150 words/min = 2.5 words/sec)
            word_count = len(sentence.split())
            duration = (word_count / 2.5) + 0.5  # Add buffer
            
            # Generate image prompt
            image_prompt = self._generate_image_prompt(sentence, trend, i)
            
            scenes.append(ScriptScene(
                text=sentence,
                duration=duration,
                image_prompt=image_prompt,
                transition="fade" if i > 0 else "none"
            ))
        
        return scenes
    
    def _generate_image_prompt(self, text: str, trend: TrendData, index: int) -> str:
        """
        Generate Stable Diffusion prompt for scene.
        
        Style: Cinematic, dramatic, high-quality
        """
        # Extract key nouns from text
        # Simple approach: use trend keyword + scene index variation
        
        base_style = "cinematic lighting, highly detailed, 4k, dramatic"
        scene_descriptor = self._extract_scene_subject(text)
        
        return f"{scene_descriptor} related to {trend.keyword}, {base_style}"
    
    def _extract_scene_subject(self, text: str) -> str:
        """Extract main subject from scene text."""
        # Simplified extraction - could use NLP for better results
        words = text.lower().split()
        # Remove common words
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        keywords = [w for w in words if w not in stop_words]
        return ' '.join(keywords[:3]) if keywords else "abstract concept"
    
    def _select_template(self, niche: str) -> str:
        """Select appropriate template file for niche."""
        template_map = {
            'historical_mystery': 'historical_mystery.jinja2',
            'productivity_hack': 'productivity_hack.jinja2',
            'obscure_fact': 'obscure_fact.jinja2'
        }
        return template_map.get(niche, 'default.jinja2')
    
    def _generate_title(self, trend: TrendData) -> str:
        """Generate SEO-optimized title."""
        title_templates = [
            f"The Truth About {trend.keyword}",
            f"{trend.keyword}: What Nobody Tells You",
            f"Why {trend.keyword} Is Trending Right Now"
        ]
        return random.choice(title_templates)
    
    def _generate_cta(self) -> str:
        """Generate call-to-action for end of video."""
        ctas = [
            "Follow for more mind-blowing facts!",
            "Like if you learned something new!",
            "Share this with someone who needs to know!"
        ]
        return random.choice(ctas)
    
    def _trim_to_duration(self, scenes: List[ScriptScene], target: float) -> List[ScriptScene]:
        """Trim scenes to fit target duration."""
        current_duration = sum(s.duration for s in scenes)
        
        if current_duration <= target:
            return scenes
        
        # Remove scenes from end until within target
        while current_duration > target and len(scenes) > 3:
            removed = scenes.pop()
            current_duration -= removed.duration
        
        return scenes
    
    def _load_hooks(self) -> List[str]:
        """Load hook templates from config."""
        return self.config.hook_patterns
```

---

*Continuing with remaining core components...*
