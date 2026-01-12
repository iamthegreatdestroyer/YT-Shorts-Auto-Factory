# GitHub Copilot Master Action Plan - Continuation
## Weeks 2-12: Full Implementation Guide

---

## 📊 PHASE 1 Week 2: Trend Analysis System

### Task 2.1: Trend Data Models

**File**: `src/trend_analysis/models.py`

```python
# COPILOT: Create data models for trend analysis
#
# Import pydantic, datetime, enum, List
#
# Create Enum TrendSource:
# - YOUTUBE = "youtube"
# - REDDIT = "reddit"
# - TWITTER = "twitter"
#
# Create Enum CompetitionLevel:
# - LOW = "low"
# - MEDIUM = "medium"
# - HIGH = "high"
#
# Create Pydantic model TrendData:
# Fields:
# - keyword: str (main trending keyword)
# - score: float = Field(ge=0.0, le=1.0) (relevance score 0-1)
# - source: TrendSource (where trend was found)
# - category: str (content category)
# - volume: int = Field(ge=0) (search volume or engagement)
# - growth_rate: float (percentage growth)
# - competition: CompetitionLevel (competition assessment)
# - timestamp: datetime (when trend was discovered)
# - related_keywords: List[str] = Field(default_factory=list)
# - url: Optional[str] = None (source URL)
# - metadata: Dict[str, Any] = Field(default_factory=dict)
#
# Methods:
# - def age_hours(self) -> float: Return hours since timestamp
# - def is_fresh(self, max_age_hours: int = 24) -> bool: Check if trend is recent
# - def __str__(self) -> str: Human-readable representation
#
# Create Pydantic model TrendCollection:
# Fields:
# - trends: List[TrendData]
# - fetched_at: datetime = Field(default_factory=datetime.now)
# - source_summary: Dict[str, int] = Field(default_factory=dict)
#
# Methods:
# - def sort_by_score(self) -> None: Sort trends by score descending
# - def filter_by_score(self, min_score: float) -> List[TrendData]
# - def filter_by_source(self, source: TrendSource) -> List[TrendData]
# - def get_top_n(self, n: int = 10) -> List[TrendData]
# - def __len__(self) -> int: Return trend count
```

---

### Task 2.2: Trend Cache System

**File**: `src/trend_analysis/cache.py`

```python
# COPILOT: Create trend caching system
#
# Import json, datetime, Path, List
# Import TrendData, TrendCollection from models
# Import logger
#
# Class TrendCache:
#
# __init__(self, cache_dir: Path):
# - Store cache_dir
# - Create directory if doesn't exist
# - Set cache_file = cache_dir / "trends_cache.json"
#
# def save_trends(self, trends: List[TrendData]):
# - Convert trends to dict using model_dump()
# - Add timestamp
# - Write to cache_file as JSON
# - Log cache save
#
# def get_trends(self, max_age_hours: int = 6) -> Optional[List[TrendData]]:
# - Check if cache_file exists
# - Load JSON
# - Check timestamp age
# - If too old, return None
# - Convert dict back to TrendData objects
# - Log cache hit/miss
# - Return trends or None
#
# def clear_cache(self):
# - Delete cache_file if exists
# - Log cache clear
#
# def get_cache_age(self) -> Optional[float]:
# - Return hours since cache was created
# - Return None if no cache
#
# Add error handling for JSON errors
# Add type hints and docstrings
```

---

### Task 2.3: YouTube Trends Scraper

**File**: `src/trend_analysis/sources/youtube_trends.py`

```python
# COPILOT: Create YouTube trends scraper
#
# Import requests, BeautifulSoup, re, datetime, asyncio, aiohttp
# Import TrendData, TrendSource, CompetitionLevel from models
# Import logger
#
# Class YouTubeTrendsScraper:
#
# __init__(self, region_code: str = "US", language: str = "en"):
# - Store region_code and language
# - Set base_url = "https://www.youtube.com/feed/trending"
# - Set headers with realistic User-Agent
#
# async def fetch_trends(self) -> List[TrendData]:
# - Build URL with region code
# - Use aiohttp to fetch page
# - Parse HTML with BeautifulSoup
# - Extract trending video data:
#   * Title
#   * View count
#   * Upload time
#   * Channel name
# - Calculate trend score based on:
#   * View count (logarithmic scale)
#   * Recency (newer = higher score)
#   * Engagement (if available)
# - Extract keywords from titles (remove common words)
# - Assess competition (views > 1M = high, > 100K = medium, else low)
# - Create TrendData objects
# - Return list of trends
# - Handle network errors gracefully
# - Log scraping progress
#
# def _extract_view_count(self, view_text: str) -> int:
# - Parse view count from text like "1.2M views"
# - Handle K (thousands), M (millions), B (billions)
# - Return integer
#
# def _calculate_score(self, views: int, hours_old: int) -> float:
# - Use formula: score = log10(views) / (1 + hours_old/24)
# - Normalize to 0-1 range
# - Return score
#
# def _extract_keywords(self, title: str) -> List[str]:
# - Remove common words (the, a, an, in, on, etc.)
# - Split into words
# - Return list of meaningful keywords
# - Limit to 5 keywords max
#
# Add retry logic with exponential backoff
# Add rate limiting to avoid being blocked
# Add comprehensive error handling
# Add docstrings
```

---

### Task 2.4: Reddit Trends Scraper

**File**: `src/trend_analysis/sources/reddit_scraper.py`

```python
# COPILOT: Create Reddit trends scraper
#
# Import aiohttp, asyncio, re, datetime
# Import TrendData, TrendSource, CompetitionLevel
# Import logger
#
# Class RedditScraper:
#
# __init__(self, subreddits: List[str], min_score: int = 100):
# - Store subreddits list
# - Store min_score threshold
# - Set base_url = "https://www.reddit.com"
# - Set headers with User-Agent
#
# async def fetch_trends(self) -> List[TrendData]:
# - For each subreddit:
#   * Fetch top posts from last 24 hours
#   * Use endpoint: /r/{subreddit}/top/.json?t=day&limit=25
# - Parse JSON response
# - Extract:
#   * Post title
#   * Score (upvotes)
#   * Number of comments
#   * Subreddit
#   * Created timestamp
# - Filter posts with score >= min_score
# - Calculate trend score based on:
#   * Upvote count
#   * Comment count
#   * Recency
#   * Subreddit relevance to niche
# - Extract keywords from titles
# - Assess competition based on comment count
# - Create TrendData objects
# - Deduplicate similar trends
# - Return aggregated list
#
# def _calculate_reddit_score(self, upvotes: int, comments: int, hours_old: int) -> float:
# - Formula: score = (upvotes + comments*2) / (1 + hours_old)
# - Normalize to 0-1
# - Return score
#
# def _extract_topic(self, title: str) -> str:
# - Remove Reddit formatting ([OC], [Serious], etc.)
# - Extract main topic/keyword
# - Return cleaned topic
#
# async def _fetch_subreddit(self, subreddit: str) -> List[dict]:
# - Fetch posts for single subreddit
# - Handle rate limiting (Reddit allows 60 req/min)
# - Return list of post dicts
# - Handle errors per subreddit
#
# Add retry logic
# Add rate limiting (sleep between requests)
# Handle 429 (too many requests) gracefully
# Add docstrings and type hints
```

---

### Task 2.5: Trend Analyzer Core

**File**: `src/trend_analysis/analyzer.py`

```python
# COPILOT: Create main trend analyzer class
#
# Import asyncio, List, Optional, datetime
# Import all scrapers, TrendData, TrendCache, Config
# Import logger
#
# Class TrendAnalyzer:
#
# __init__(self, config: Config):
# - Store config
# - Initialize YouTubeTrendsScraper()
# - Initialize RedditScraper(config.trends.reddit_subreddits)
# - Initialize TrendCache(config.cache_dir)
# - Store niche_keywords from config
#
# async def get_trending_topics(self, force_refresh: bool = False) -> List[TrendData]:
# - If not force_refresh:
#   * Try to get from cache
#   * If cache valid, return cached trends
# - Log "Fetching fresh trend data"
# - Create tasks for all scrapers:
#   * youtube_task = self.youtube_scraper.fetch_trends()
#   * reddit_task = self.reddit_scraper.fetch_trends()
# - Use asyncio.gather() with return_exceptions=True
# - Handle errors from individual scrapers
# - Combine all trends into single list
# - Call self._score_trends() to calculate final scores
# - Sort by score descending
# - Save to cache
# - Return trends
#
# def _score_trends(self, trends: List[TrendData]) -> List[TrendData]:
# - For each trend:
#   * Calculate volume_score (normalize view/upvote count)
#   * Calculate growth_score (from growth_rate)
#   * Calculate niche_relevance (keyword matching)
#   * Calculate competition_score (inverse of competition level)
#   * Final score formula:
#     score = (volume * 0.3) + (growth * 0.3) + (niche * 0.25) + (competition * 0.15)
# - Update trend.score with final score
# - Return trends
#
# def _calculate_niche_relevance(self, keyword: str) -> float:
# - Compare keyword against config.niche_keywords
# - Count matches (case-insensitive)
# - Return match_count / len(niche_keywords)
# - Cap at 1.0
#
# def select_best_trend(self, trends: List[TrendData]) -> TrendData:
# - Filter out recently used trends (check video database)
# - Apply min_trend_score threshold from config
# - Filter by category if specified
# - Sort by score
# - Return top trend
# - If none qualify, return best available with warning
#
# def _get_recent_video_topics(self, days: int = 7) -> List[str]:
# - Query database/logs for recently used topics
# - Return list of keywords to avoid
# - For now, return empty list (TODO: implement after DB)
#
# def _deduplicate_trends(self, trends: List[TrendData]) -> List[TrendData]:
# - Group trends with similar keywords
# - Keep highest scoring trend from each group
# - Return deduplicated list
#
# Add comprehensive logging
# Add error handling
# Add docstrings with examples
```

---

### Week 2 Testing

**File**: `tests/unit/test_trend_analysis.py`

```python
# COPILOT: Create comprehensive tests for trend analysis
#
# Import pytest, asyncio, datetime, aiohttp
# Import TrendAnalyzer, TrendData, TrendCache
# Import all scraper classes
#
# Test TrendData model:
# - test_trend_data_creation
# - test_trend_data_validation
# - test_trend_age_calculation
# - test_trend_is_fresh
#
# Test TrendCache:
# - test_cache_save_and_load
# - test_cache_expiration
# - test_cache_clear
# - test_cache_invalid_json_handling
#
# Test YouTubeTrendsScraper:
# - @pytest.mark.asyncio
#   async def test_youtube_scraper_fetch(mocker):
#   * Mock aiohttp.ClientSession.get()
#   * Provide sample HTML response
#   * Call fetch_trends()
#   * Assert trends are returned
#   * Verify trend data structure
# - test_view_count_extraction
# - test_score_calculation
# - test_keyword_extraction
#
# Test RedditScraper:
# - @pytest.mark.asyncio
#   async def test_reddit_scraper_fetch(mocker):
#   * Mock API response
#   * Call fetch_trends()
#   * Verify trends
# - test_reddit_score_calculation
# - test_topic_extraction
#
# Test TrendAnalyzer:
# - @pytest.mark.asyncio
#   async def test_analyzer_get_trends_cached
# - @pytest.mark.asyncio
#   async def test_analyzer_get_trends_fresh
# - test_niche_relevance_calculation
# - test_select_best_trend
# - test_trend_deduplication
#
# Use pytest.mark.slow for integration tests that hit real APIs
# Use fixtures for sample trend data
# Mock external API calls in unit tests
# Aim for >85% coverage
```

---

### Week 2 Completion Checklist

```bash
# Run all tests
poetry run pytest tests/unit/test_trend_analysis.py -v --cov=src/trend_analysis

# Test scraping manually (requires internet)
poetry run python -c "
import asyncio
from src.trend_analysis.analyzer import TrendAnalyzer
from src.core.config import Config

async def test():
    config = Config.load()
    analyzer = TrendAnalyzer(config)
    trends = await analyzer.get_trending_topics(force_refresh=True)
    for t in trends[:5]:
        print(f'{t.keyword}: {t.score:.2f}')

asyncio.run(test())
"

# Verify cache works
ls -lh data/cache/trends/

# Check coverage
poetry run pytest --cov-report=html
open htmlcov/index.html  # View coverage report
```

---

## ✍️ PHASE 2: Content Generation (Weeks 3-4)

### Week 3: Script Generation System

#### Task 3.1: Script Data Models

**File**: `src/content_generation/models.py`

```python
# COPILOT: Create script and content data models
#
# Import pydantic, List, Optional, datetime
#
# Create Enum NicheType:
# - HISTORICAL_MYSTERY = "historical_mystery"
# - PRODUCTIVITY_HACK = "productivity_hack"
# - OBSCURE_FACT = "obscure_fact"
#
# Create Pydantic model ScriptScene:
# Fields:
# - text: str (scene narration text)
# - duration: float = Field(gt=0) (seconds)
# - image_prompt: str (prompt for image generation)
# - transition: str = "fade" (transition effect)
# - voiceover_emphasis: Optional[str] = None (words to emphasize)
#
# Methods:
# - @property word_count(self) -> int: Return word count
# - def estimate_reading_time(self, wpm: int = 150) -> float: Calculate duration
#
# Create Pydantic model Script:
# Fields:
# - title: str
# - hook: str = Field(max_length=150) (first 3 seconds - critical!)
# - body: str (main content)
# - call_to_action: str (ending CTA)
# - scenes: List[ScriptScene]
# - total_duration: float
# - target_keywords: List[str]
# - niche: NicheType
# - metadata: Dict[str, Any] = Field(default_factory=dict)
# - created_at: datetime = Field(default_factory=datetime.now)
#
# Properties:
# - @property text(self) -> str: Return full script text
# - @property sentences(self) -> List[str]: Return all scene texts
# - @property image_prompts(self) -> List[str]: Return all prompts
# - @property word_count(self) -> int: Total word count
# - @property scene_count(self) -> int: Number of scenes
#
# Validators:
# - @validator('total_duration')
#   def validate_duration(cls, v):
#   * Check 15 <= v <= 60
#   * Raise ValueError if out of range
# - @validator('scenes')
#   def validate_scenes(cls, v):
#   * Check at least 3 scenes
#   * Check max 12 scenes
#
# Methods:
# - def to_srt(self) -> str: Convert to SRT subtitle format
# - def to_markdown(self) -> str: Convert to markdown for review
# - def trim_to_duration(self, target: float) -> "Script": Remove scenes to fit duration
#
# Add docstrings and examples
```

---

#### Task 3.2: Template System

**File**: `src/content_generation/templates/historical_mystery.jinja2`

```jinja2
{# COPILOT: Create Jinja2 template for historical mystery niche #}
{# 
Variables available:
- trend_keyword: Main trending keyword
- related_keywords: List of related keywords
- hook: Pre-generated hook

Template structure:
1. Hook (use {{ hook }})
2. Main mystery introduction
3. 3-5 key points about the mystery
4. Fascinating details
5. Current theories/research
6. Call to action

Guidelines:
- Use engaging, mysterious tone
- Include "Did you know" or similar phrases
- Reference {{ trend_keyword }} naturally
- Keep total around 40-50 seconds reading time
- End with question or cliffhanger
#}

{{ hook }}

The {{ trend_keyword }} has puzzled historians for {{ range(50, 200) | random }} years. 
What we know is fascinating, but what we don't know is even more intriguing.

{% for keyword in related_keywords[:3] %}
Ancient {{ keyword }} suggests something remarkable was happening. 
{% endfor %}

Recent archaeological discoveries have revealed {{ range(3, 7) | random }} surprising facts 
that challenge everything we thought we knew.

The mystery deepens when you consider the {{ related_keywords | random }} connection 
that researchers discovered just {{ range(1, 5) | random }} years ago.

Could this be evidence of {{ trend_keyword | title }} being far more {{ ['advanced', 'mysterious', 'significant', 'complex'] | random }} 
than we ever imagined?

What do you think happened? Drop your theory in the comments!
```

**File**: `src/content_generation/templates/productivity_hack.jinja2`

```jinja2
{# COPILOT: Create Jinja2 template for productivity hack niche #}
{#
Variables: trend_keyword, related_keywords, hook

Structure:
1. Hook with bold claim
2. Introduce the hack
3. Explain why it works
4. Quick implementation steps
5. Expected results
6. CTA to try it

Tone: Energetic, actionable, results-focused
#}

{{ hook }}

The {{ trend_keyword }} technique has been {{ ['transforming', 'revolutionizing', 'upgrading'] | random }} 
how {{ ['top performers', 'successful people', 'high achievers'] | random }} get things done.

Here's why it works: Your brain processes {{ related_keywords | random }} 
{{ range(30, 70) | random }} percent {{ ['faster', 'more efficiently', 'with better focus'] | random }} 
when you {{ ['align with this method', 'apply this principle', 'use this approach'] | random }}.

Step one: {{ ['Start your day', 'Begin each task', 'Set up your environment'] | random }} 
with {{ related_keywords[0] | lower }} in mind.

Step two: {{ ['Eliminate distractions', 'Focus intensely', 'Time-block your work'] | random }} 
for just {{ range(15, 90) | random }} minutes.

Step three: {{ ['Review and adjust', 'Track your progress', 'Measure results'] | random }}.

{% for keyword in related_keywords[1:3] %}
The {{ keyword }} component is crucial for {{ ['maintaining momentum', 'staying consistent', 'seeing results'] | random }}.
{% endfor %}

Within {{ range(1, 4) | random }} {{ ['days', 'weeks'] | random }}, you'll notice {{ ['significant improvements', 'major changes', 'impressive results'] | random }} 
in your {{ ['productivity', 'efficiency', 'output'] | random }}.

Try this today and watch your {{ trend_keyword }} {{ ['skyrocket', 'improve dramatically', 'reach new levels'] | random }}!
```

**File**: `src/content_generation/templates/obscure_fact.jinja2`

```jinja2
{# COPILOT: Create Jinja2 template for obscure facts niche #}
{#
Variables: trend_keyword, related_keywords, hook

Structure:
1. Hook with surprising statement
2. Present the fact
3. Context and background
4. Why it's surprising/interesting
5. Related facts
6. CTA for engagement

Tone: Wonder, curiosity, "mind-blowing"
#}

{{ hook }}

{{ trend_keyword | title }} {{ ['contains', 'involves', 'demonstrates'] | random }} something 
{{ ['absolutely incredible', 'truly remarkable', 'completely unexpected'] | random }} 
that {{ ['most people', 'almost nobody', 'very few people'] | random }} know about.

Scientists {{ ['discovered', 'found', 'revealed'] | random }} that {{ related_keywords | random }} 
{{ ['can actually', 'is capable of', 'has the ability to'] | random }} 
{{ ['affect', 'influence', 'change'] | random }} {{ related_keywords[1] | lower }}.

This {{ ['happens', 'occurs', 'takes place'] | random }} because of 
{{ ['quantum mechanics', 'evolutionary biology', 'complex chemistry', 'natural physics'] | random }} 
that wasn't understood until {{ range(1990, 2020) | random }}.

But here's where it gets {{ ['even more interesting', 'truly fascinating', 'absolutely wild'] | random }}: 
{{ related_keywords[2] | lower }} also plays a role in this {{ ['phenomenon', 'process', 'mechanism'] | random }}.

{% if related_keywords | length > 3 %}
And when you factor in {{ related_keywords[3] | lower }}, 
the implications are {{ ['staggering', 'mind-blowing', 'extraordinary'] | random }}.
{% endif %}

Nature {{ ['never ceases', 'continues', 'keeps'] | random }} to {{ ['amaze us', 'surprise us', 'blow our minds'] | random }}!

What other {{ trend_keyword }} facts should we cover? Comment below!
```

---

#### Task 3.3: Script Generator Core

**File**: `src/content_generation/script_generator.py`

```python
# COPILOT: Create main script generation class
#
# Import jinja2, random, re, datetime, List, Optional
# Import Script, ScriptScene, NicheType, TrendData, Config
# Import logger
#
# Class ScriptGenerator:
#
# __init__(self, config: Config):
# - Store config
# - Initialize Jinja2 Environment:
#   * loader = FileSystemLoader(config.content.template_dir)
#   * trim_blocks = True, lstrip_blocks = True
# - Load hook patterns from config
# - Load niche configurations
#
# async def generate(self, niche: NicheType, trend: TrendData) -> Script:
# - Log start of generation
# - Select template file based on niche
# - Load template
# - Generate hook using _generate_hook()
# - Prepare template context:
#   * trend_keyword
#   * related_keywords
#   * hook
# - Render template
# - Parse rendered text into scenes using _parse_into_scenes()
# - Calculate duration for each scene
# - Calculate total duration
# - If duration > 60s, call _trim_to_duration()
# - Generate metadata:
#   * Title using _generate_title()
#   * Call to action using _generate_cta()
# - Create Script object
# - Log completion
# - Return script
#
# def _generate_hook(self, trend: TrendData) -> str:
# - Get hook patterns from config for current niche
# - Select random pattern
# - Format with trend.keyword
# - Ensure length < 150 characters
# - Make it attention-grabbing (use power words)
# - Examples:
#   * "This {keyword} mystery has baffled experts for decades"
#   * "You won't believe what {keyword} can actually do"
#   * "The truth about {keyword} will change everything"
# - Return formatted hook
#
# def _parse_into_scenes(self, text: str, trend: TrendData) -> List[ScriptScene]:
# - Split text into sentences
# - Group into scenes (1-2 sentences per scene)
# - For each scene:
#   * Calculate duration (word_count / 2.5 + 0.5 buffer)
#   * Generate image prompt using _generate_image_prompt()
#   * Set transition type
#   * Create ScriptScene object
# - Return list of scenes
#
# def _generate_image_prompt(self, text: str, trend: TrendData, index: int) -> str:
# - Extract key nouns from scene text
# - Use trend keyword as context
# - Add style descriptors:
#   * "cinematic lighting"
#   * "highly detailed"
#   * "4k quality"
#   * "dramatic atmosphere"
# - Format as Stable Diffusion prompt
# - Example: "ancient egyptian pyramid at sunset, cinematic lighting, highly detailed, 4k"
# - Return prompt
#
# def _trim_to_duration(self, scenes: List[ScriptScene], target: float = 58.0) -> List[ScriptScene]:
# - Calculate current total duration
# - If under target, return as-is
# - Remove scenes from end until within target
# - Keep minimum 3 scenes
# - Preserve hook scene (first)
# - Return trimmed scenes
#
# def _generate_title(self, trend: TrendData) -> str:
# - Use trend keyword
# - Make it SEO-optimized
# - Keep under 70 characters
# - Make it compelling
# - Templates:
#   * "The Truth About {keyword}"
#   * "{keyword}: What Nobody Tells You"
#   * "Why {keyword} Is Trending Right Now"
# - Return title
#
# def _generate_cta(self) -> str:
# - Select from pre-written CTAs
# - Options:
#   * "Follow for more mind-blowing facts!"
#   * "Like if you learned something new!"
#   * "Share this with someone who needs to know!"
#   * "What do you think? Comment below!"
# - Return CTA
#
# def _select_template(self, niche: NicheType) -> str:
# - Map niche to template file
# - Return template filename
#
# def _extract_keywords(self, text: str, count: int = 5) -> List[str]:
# - Remove common stop words
# - Extract nouns using simple NLP
# - Return top keywords by frequency
#
# Add comprehensive logging
# Add error handling for template errors
# Add docstrings with examples
```

---

#### Task 3.4: Script Validators

**File**: `src/content_generation/validators.py`

```python
# COPILOT: Create script validation utilities
#
# Import re, List from typing
# Import Script, ScriptScene
# Import logger
#
# Class ScriptValidator:
#
# @staticmethod
# def validate_script(script: Script) -> tuple[bool, List[str]]:
# - Run all validation checks
# - Collect errors in list
# - Return (is_valid, error_messages)
#
# @staticmethod
# def check_duration(script: Script) -> Optional[str]:
# - Check if 15 <= total_duration <= 60
# - Return error message or None
#
# @staticmethod
# def check_scene_count(script: Script) -> Optional[str]:
# - Check if 3 <= scene_count <= 12
# - Return error message or None
#
# @staticmethod
# def check_hook_quality(hook: str) -> Optional[str]:
# - Check length < 150 chars
# - Check for attention-grabbing words
# - Check for question marks or exclamations
# - Return error or None
#
# @staticmethod
# def check_keyword_usage(script: Script) -> Optional[str]:
# - Verify target_keywords appear in text
# - Check keyword density (not too high, not too low)
# - Return error or None
#
# @staticmethod
# def check_scene_duration(scenes: List[ScriptScene]) -> Optional[str]:
# - Check each scene is 2-10 seconds
# - Return error if any out of range
#
# @staticmethod
# def check_readability(text: str) -> Optional[str]:
# - Check for overly complex sentences
# - Prefer short, punchy sentences for shorts
# - Return warning if issues found
#
# @staticmethod
# def check_image_prompts(scenes: List[ScriptScene]) -> Optional[str]:
# - Verify all scenes have image prompts
# - Check prompts are descriptive enough
# - Return error if issues
#
# Add comprehensive docstrings
```

---

### Week 3 Testing

**File**: `tests/unit/test_script_generation.py`

```python
# COPILOT: Create tests for script generation
#
# Import pytest, Script, ScriptGenerator, TrendData
# Import jinja2
#
# Fixtures:
# - sample_trend: Return TrendData for testing
# - script_generator: Return ScriptGenerator instance
#
# Test Script model:
# - test_script_creation
# - test_script_validation_duration
# - test_script_to_srt
# - test_script_to_markdown
# - test_script_trim_to_duration
#
# Test ScriptScene model:
# - test_scene_creation
# - test_scene_word_count
# - test_scene_reading_time
#
# Test ScriptGenerator:
# - @pytest.mark.asyncio
#   async def test_generate_script_historical_mystery
# - @pytest.mark.asyncio
#   async def test_generate_script_productivity
# - @pytest.mark.asyncio
#   async def test_generate_script_obscure_fact
# - test_hook_generation
# - test_parse_into_scenes
# - test_image_prompt_generation
# - test_title_generation
# - test_cta_generation
# - test_trim_to_duration
#
# Test ScriptValidator:
# - test_validate_duration
# - test_validate_scene_count
# - test_validate_hook_quality
# - test_validate_keyword_usage
#
# Use parametrize for multiple niche types
# Mock Jinja2 templates for unit tests
# Test with real templates in integration tests
# Aim for >85% coverage
```

---

## 🎤 Week 4: Media Creation Foundation

### Task 4.1: TTS Base Interface

**File**: `src/media_creation/tts/base.py`

```python
# COPILOT: Create abstract base class for TTS engines
#
# Import ABC, abstractmethod, Path, Optional
# Import Config
#
# Class TTSEngine(ABC):
#
# def __init__(self, config: Config):
# - Store config
# - Set output_dir from config
# - Ensure output_dir exists
#
# @abstractmethod
# async def generate(self, text: str, output_path: Optional[Path] = None) -> Path:
# - Generate speech from text
# - Save to output_path or auto-generate filename
# - Return path to generated audio file
# - Raise MediaCreationError on failure
#
# @abstractmethod
# def supports_language(self, language: str) -> bool:
# - Check if engine supports language
# - Return True/False
#
# @abstractmethod
# def get_available_voices(self) -> List[str]:
# - Return list of available voice IDs
#
# @property
# @abstractmethod
# def engine_name(self) -> str:
# - Return name of TTS engine
#
# def _generate_output_path(self) -> Path:
# - Generate unique filename
# - Use timestamp
# - Return path in output_dir
#
# Add comprehensive docstrings
```

---

### Task 4.2: gTTS Implementation

**File**: `src/media_creation/tts/gtts_engine.py`

```python
# COPILOT: Implement Google TTS (gTTS) engine
#
# Import gTTS, Path, asyncio
# Import TTSEngine base class
# Import Config, logger
#
# Class GTTSEngine(TTSEngine):
#
# def __init__(self, config: Config):
# - Call super().__init__(config)
# - Store language from config
# - Store speed (tld for accent: 'com', 'co.uk', 'com.au')
# - Store slow setting from config
#
# async def generate(self, text: str, output_path: Optional[Path] = None) -> Path:
# - If output_path None, generate using _generate_output_path()
# - Create gTTS object:
#   * text = text
#   * lang = self.language
#   * slow = self.slow
#   * tld = self._get_tld_for_accent()
# - Save to file using tts.save()
# - Run in thread pool (gTTS is synchronous):
#   await asyncio.to_thread(tts.save, str(output_path))
# - Verify file was created
# - Log success
# - Return output_path
# - Handle errors and raise MediaCreationError
#
# def supports_language(self, language: str) -> bool:
# - Check if language in gTTS.lang.tts_langs()
# - Return True/False
#
# def get_available_voices(self) -> List[str]:
# - Return list of supported languages
# - Use gTTS.lang.tts_langs()
#
# @property
# def engine_name(self) -> str:
# - Return "gTTS"
#
# def _get_tld_for_accent(self) -> str:
# - Map config accent to TLD
# - 'us' -> 'com', 'uk' -> 'co.uk', etc.
# - Return TLD string
#
# Add retry logic for network issues
# Add comprehensive logging
# Add docstrings
```

---

### Task 4.3: Factory Function for TTS

**File**: `src/media_creation/tts/__init__.py`

```python
# COPILOT: Create factory function to get TTS engine
#
# Import Config, TTSEngine
# Import all TTS implementations
# Import logger
#
# def get_tts_engine(config: Config) -> TTSEngine:
# - Read config.ai.tts_engine
# - Map to appropriate class:
#   * "gtts" -> GTTSEngine
#   * "pyttsx3" -> Pyttsx3Engine (implement later)
#   * "coqui" -> CoquiEngine (implement later)
# - Create instance with config
# - Log which engine was initialized
# - Return engine instance
# - Raise ValueError if engine not supported
#
# Add docstring explaining available engines
```

---

### Task 4.4: Image Generation Base

**File**: `src/media_creation/image_generation/base.py`

```python
# COPILOT: Create abstract base for image generation
#
# Import ABC, abstractmethod, Path, List, Optional
# Import Config
#
# Class ImageGenerator(ABC):
#
# def __init__(self, config: Config):
# - Store config
# - Set output_dir from config
# - Ensure output_dir exists
#
# @abstractmethod
# async def generate(self, prompt: str, output_path: Optional[Path] = None) -> Path:
# - Generate single image from prompt
# - Save to output_path or auto-generate
# - Return path to generated image
#
# @abstractmethod
# async def generate_batch(self, prompts: List[str]) -> List[Path]:
# - Generate multiple images efficiently
# - Return list of paths
#
# @property
# @abstractmethod
# def generator_name(self) -> str:
# - Return name of generator
#
# def _generate_output_path(self, index: int = 0) -> Path:
# - Generate unique filename
# - Include index for batches
# - Return path
#
# Add docstrings
```

---

### Task 4.5: Stock Images Implementation

**File**: `src/media_creation/image_generation/stock_assets.py`

```python
# COPILOT: Implement stock image selector
#
# Import Path, List, random, shutil
# Import ImageGenerator base
# Import Config, logger
#
# Class StockImageGenerator(ImageGenerator):
# """
# Selects appropriate stock images from assets directory.
# Fast and no API costs, but less unique than AI generation.
# """
#
# def __init__(self, config: Config):
# - Call super().__init__(config)
# - Set stock_dir = config.assets_dir / "images"
# - Scan and index available stock images
# - Create category mappings
#
# async def generate(self, prompt: str, output_path: Optional[Path] = None) -> Path:
# - Parse prompt to extract subject/category
# - Find relevant stock images using _find_matching_images()
# - Select best match or random from matches
# - Copy to output_path
# - Return path
#
# async def generate_batch(self, prompts: List[str]) -> List[Path]:
# - Process each prompt
# - Try to avoid duplicates
# - Return list of paths
#
# @property
# def generator_name(self) -> str:
# - Return "StockImages"
#
# def _find_matching_images(self, keywords: List[str]) -> List[Path]:
# - Search stock images by filename/category
# - Return matching paths
#
# def _index_stock_images(self):
# - Scan stock_dir
# - Create dict of {category: [paths]}
# - Store in self.image_index
#
# def _extract_keywords(self, prompt: str) -> List[str]:
# - Parse prompt for nouns
# - Remove style descriptors
# - Return content keywords
#
# Add logging
# Add error handling for missing stock images
# Add docstrings
```

---

### Week 4 Testing

**File**: `tests/unit/test_media_creation.py`

```python
# COPILOT: Create tests for media creation
#
# Import pytest, asyncio, Path
# Import TTS and Image generators
#
# Test GTTSEngine:
# - @pytest.mark.asyncio
#   async def test_gtts_generate_audio
# - test_gtts_supports_language
# - test_gtts_get_available_voices
# - @pytest.mark.asyncio
#   async def test_gtts_generate_error_handling
#
# Test get_tts_engine factory:
# - test_factory_returns_gtts
# - test_factory_invalid_engine_raises
#
# Test StockImageGenerator:
# - @pytest.mark.asyncio
#   async def test_stock_select_image
# - @pytest.mark.asyncio
#   async def test_stock_generate_batch
# - test_stock_find_matching_images
# - test_stock_keyword_extraction
#
# Use temporary directories for output
# Mock network calls for gTTS
# Use sample stock images in fixtures
# Aim for >80% coverage
```

---

## Week 4 Completion

```bash
# Test TTS generation
poetry run python -c "
import asyncio
from src.media_creation.tts import get_tts_engine
from src.core.config import Config

async def test():
    config = Config.load()
    tts = get_tts_engine(config)
    path = await tts.generate('This is a test of the TTS system.')
    print(f'Audio generated: {path}')

asyncio.run(test())
"

# Test image selection
poetry run python -c "
import asyncio
from src.media_creation.image_generation.stock_assets import StockImageGenerator
from src.core.config import Config

async def test():
    config = Config.load()
    gen = StockImageGenerator(config)
    paths = await gen.generate_batch([
        'ancient pyramid cinematic',
        'productive workspace minimal',
        'ocean wildlife documentary'
    ])
    print(f'Images selected: {len(paths)}')

asyncio.run(test())
"
```

---

## 📝 Status Check

**✅ Completed:**
- Phase 1 Week 1: Foundation (Config, Logging, Pipeline skeleton)
- Phase 1 Week 2: Trend Analysis (Scrapers, Cache, Scoring)
- Phase 2 Week 3: Script Generation (Templates, Models, Validator)
- Phase 2 Week 4: Media Creation (TTS, Images foundation)

**🔄 Next: Phase 3 - Video Compilation (Weeks 5-6)**

Would you like me to continue with Weeks 5-12 instructions? The next sections will cover:
- Week 5-6: Video compilation with MoviePy
- Week 7: YouTube integration
- Week 8: SEO & Metadata
- Week 9: Automation & Scheduling
- Week 10: Testing & Refinement
- Week 11: Deployment
- Week 12: Launch & Monitoring
