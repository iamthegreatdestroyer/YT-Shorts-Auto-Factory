# GitHub Copilot Master Action Plan - Final Part
## Weeks 5-12: Video Compilation, Upload, Deployment & Launch

---

## 🎬 PHASE 3: Video Compilation (Weeks 5-6)

### Week 5: MoviePy Integration

#### Task 5.1: Video Compilation Models

**File**: `src/video_compilation/models.py`

```python
# COPILOT: Create video compilation data models
#
# Import pydantic, Path, List, Optional, datetime
#
# Create Enum TransitionType:
# - FADE = "fade"
# - DISSOLVE = "dissolve"
# - SLIDE = "slide"
# - ZOOM = "zoom"
# - NONE = "none"
#
# Create Pydantic model VideoClip:
# Fields:
# - image_path: Path
# - duration: float
# - transition: TransitionType = TransitionType.FADE
# - transition_duration: float = 0.5
# - zoom_effect: bool = False
# - pan_direction: Optional[str] = None  # 'left', 'right', 'up', 'down'
#
# Create Pydantic model AudioTrack:
# Fields:
# - voiceover_path: Path
# - background_music_path: Optional[Path] = None
# - music_volume: float = 0.1  # Background music volume (0-1)
# - voiceover_volume: float = 1.0
# - normalize_audio: bool = True
#
# Create Pydantic model CaptionStyle:
# Fields:
# - font_family: str = "Arial"
# - font_size: int = 60
# - font_color: str = "white"
# - stroke_color: str = "black"
# - stroke_width: int = 3
# - position: str = "bottom"  # 'top', 'center', 'bottom'
# - background_opacity: float = 0.5
# - animation: Optional[str] = None  # 'slide_in', 'fade_in'
#
# Create Pydantic model VideoCompilationRequest:
# Fields:
# - clips: List[VideoClip]
# - audio: AudioTrack
# - captions: Optional[str] = None  # SRT format text
# - caption_style: CaptionStyle = Field(default_factory=CaptionStyle)
# - output_path: Path
# - resolution: tuple[int, int] = (1080, 1920)  # Portrait 9:16
# - fps: int = 30
# - bitrate: str = "5000k"
#
# Create Pydantic model VideoCompilationResult:
# Fields:
# - video_path: Path
# - thumbnail_path: Path
# - duration: float
# - file_size: int  # bytes
# - resolution: tuple[int, int]
# - compilation_time: float  # seconds
# - success: bool
# - error: Optional[str] = None
#
# Add docstrings and validators
```

---

#### Task 5.2: Timeline Builder

**File**: `src/video_compilation/timeline_builder.py`

```python
# COPILOT: Create timeline builder for video scenes
#
# Import List, Path
# Import Script, ScriptScene, VideoClip, TransitionType
# Import logger
#
# Class TimelineBuilder:
# """
# Converts script scenes into video timeline with clips.
# Handles timing, transitions, and pacing.
# """
#
# def __init__(self, target_fps: int = 30):
# - Store target_fps
#
# def build_timeline(
#     self,
#     script: Script,
#     image_paths: List[Path],
#     audio_duration: float
# ) -> List[VideoClip]:
# - Validate inputs (len(image_paths) == len(script.scenes))
# - Create VideoClip for each scene:
#   * Match image to scene
#   * Set duration from scene.duration
#   * Select transition type
#   * Add zoom effect for visual interest
# - Adjust durations to match audio_duration
# - Log timeline creation
# - Return list of VideoClips
#
# def _select_transition(self, scene_index: int, total_scenes: int) -> TransitionType:
# - First scene: NONE
# - Last scene: FADE
# - Others: Alternate between FADE and DISSOLVE
# - Return TransitionType
#
# def _should_add_zoom(self, scene_index: int) -> bool:
# - Add zoom to 60% of clips for visual interest
# - Use random but deterministic selection
# - Return bool
#
# def _calculate_pan_direction(self, scene_index: int) -> Optional[str]:
# - Alternate pan directions for variety
# - Even indices: pan right
# - Odd indices: pan left
# - Every 4th: pan up or down
# - Return direction or None
#
# def adjust_clip_durations(
#     self,
#     clips: List[VideoClip],
#     target_duration: float
# ) -> List[VideoClip]:
# - Calculate current total
# - If too short: extend last clips proportionally
# - If too long: trim last clips
# - Maintain minimum 2s per clip
# - Return adjusted clips
#
# Add comprehensive logging
# Add docstrings
```

---

#### Task 5.3: Video Compiler Core

**File**: `src/video_compilation/compiler.py`

```python
# COPILOT: Create main video compiler using MoviePy
#
# Import moviepy.editor as mpy
# Import Path, List, Optional
# Import Script, VideoCompilationRequest, VideoCompilationResult
# Import Config, logger
# Import time for performance tracking
#
# Class VideoCompiler:
# """
# Compiles images, audio, and captions into final video using MoviePy.
# """
#
# def __init__(self, config: Config):
# - Store config
# - Set temp_dir from config
# - Set output_dir from config
# - Ensure directories exist
#
# async def compile(
#     self,
#     script: Script,
#     audio_path: Path,
#     image_paths: List[Path]
# ) -> VideoCompilationResult:
# - Start timer
# - Log compilation start
# - Build timeline using TimelineBuilder
# - Create VideoCompilationRequest
# - Call _compile_video()
# - Generate thumbnail using _generate_thumbnail()
# - Calculate file size
# - Calculate compilation time
# - Log completion
# - Return VideoCompilationResult
#
# def _compile_video(self, request: VideoCompilationRequest) -> Path:
# - Load all image clips:
#   for clip_data in request.clips:
#     * img_clip = mpy.ImageClip(str(clip_data.image_path))
#     * Set duration
#     * Resize to resolution
#     * Add zoom effect if specified
#     * Add pan effect if specified
#     * Store in list
# - Concatenate clips with transitions:
#   video = mpy.concatenate_videoclips(
#     clips,
#     method="compose",
#     transition=self._create_transition
#   )
# - Load audio:
#   voiceover = mpy.AudioFileClip(str(request.audio.voiceover_path))
#   if background_music:
#     music = mpy.AudioFileClip(str(music_path))
#     music = music.volumex(request.audio.music_volume)
#     music = music.audio_loop(duration=video.duration)
#     audio = mpy.CompositeAudioClip([voiceover, music])
#   else:
#     audio = voiceover
# - Set video audio:
#   video = video.set_audio(audio)
# - Add captions if provided:
#   if request.captions:
#     video = self._add_captions(video, request.captions, request.caption_style)
# - Write final video:
#   video.write_videofile(
#     str(request.output_path),
#     fps=request.fps,
#     codec='libx264',
#     audio_codec='aac',
#     bitrate=request.bitrate,
#     preset='medium',
#     threads=4,
#     logger=None  # Suppress MoviePy logging
#   )
# - Close clips to free memory
# - Return output_path
#
# def _create_transition(
#     self,
#     clip1: mpy.VideoClip,
#     clip2: mpy.VideoClip,
#     transition_type: TransitionType
# ) -> mpy.VideoClip:
# - Create transition effect between clips
# - If FADE:
#   return mpy.CompositeVideoClip([
#     clip1.crossfadeout(0.5),
#     clip2.crossfadein(0.5).set_start(clip1.duration - 0.5)
#   ])
# - If DISSOLVE:
#   Similar to fade but different timing
# - Return transitioned clip
#
# def _add_zoom_effect(
#     self,
#     clip: mpy.ImageClip,
#     zoom_factor: float = 1.2
# ) -> mpy.VideoClip:
# - Create Ken Burns style zoom effect
# - Start at scale 1.0, end at zoom_factor
# - Use resize with time function:
#   clip.resize(lambda t: 1 + (zoom_factor - 1) * t / clip.duration)
# - Return zoomed clip
#
# def _add_pan_effect(
#     self,
#     clip: mpy.ImageClip,
#     direction: str
# ) -> mpy.VideoClip:
# - Create panning effect
# - Shift position over time
# - Use set_position with time function
# - Return panned clip
#
# def _add_captions(
#     self,
#     video: mpy.VideoClip,
#     srt_text: str,
#     style: CaptionStyle
# ) -> mpy.VideoClip:
# - Parse SRT text into list of (start, end, text) tuples
# - For each caption:
#   * Create TextClip with style
#   * Set start/end times
#   * Position on video
# - Composite all caption clips onto video
# - Return video with captions
#
# def _generate_thumbnail(
#     self,
#     video_path: Path,
#     output_path: Optional[Path] = None
# ) -> Path:
# - Extract frame from video (at 2 seconds in)
# - Add text overlay with title
# - Add branding/logo if configured
# - Make eye-catching (high contrast, bold text)
# - Save as PNG
# - Return thumbnail path
#
# def _parse_srt(self, srt_text: str) -> List[tuple[float, float, str]]:
# - Parse SRT format
# - Convert timestamps to seconds
# - Return list of (start, end, text)
#
# Add comprehensive error handling
# Add progress logging
# Add memory cleanup
# Add docstrings
```

---

#### Task 5.4: Effects Library

**File**: `src/video_compilation/effects.py`

```python
# COPILOT: Create video effects library
#
# Import moviepy.editor as mpy
# Import numpy as np
#
# Class VideoEffects:
# """
# Collection of video effects for engaging shorts.
# """
#
# @staticmethod
# def ken_burns(clip: mpy.VideoClip, zoom: float = 1.2) -> mpy.VideoClip:
# - Apply Ken Burns zoom effect
# - Smooth zoom from 1.0 to zoom factor
# - Return clip with effect
#
# @staticmethod
# def smooth_pan(
#     clip: mpy.VideoClip,
#     direction: str,
#     distance: int = 100
# ) -> mpy.VideoClip:
# - Apply smooth panning
# - Move clip position over duration
# - Use easing function (ease-in-out)
# - Return panned clip
#
# @staticmethod
# def vignette(clip: mpy.VideoClip, strength: float = 0.3) -> mpy.VideoClip:
# - Add vignette effect (darkened edges)
# - Create mask with gradient
# - Apply to clip
# - Return clip with vignette
#
# @staticmethod
# def color_grade(clip: mpy.VideoClip, preset: str = "cinematic") -> mpy.VideoClip:
# - Apply color grading preset
# - Presets: cinematic, warm, cool, vintage, vibrant
# - Adjust colors using moviepy filters
# - Return graded clip
#
# @staticmethod
# def motion_blur(clip: mpy.VideoClip, amount: int = 2) -> mpy.VideoClip:
# - Add subtle motion blur
# - Makes movement smoother
# - Return blurred clip
#
# @staticmethod
# def quick_zoom(clip: mpy.VideoClip, at_time: float) -> mpy.VideoClip:
# - Add quick zoom at specific moment
# - Useful for emphasis
# - Return clip with zoom
#
# Add docstrings with examples
```

---

### Week 5 Testing

**File**: `tests/unit/test_video_compilation.py`

```python
# COPILOT: Create tests for video compilation
#
# Import pytest, Path, asyncio
# Import VideoCompiler, TimelineBuilder
# Import sample fixtures
#
# Test VideoCompilationModels:
# - test_video_clip_creation
# - test_audio_track_validation
# - test_caption_style_defaults
# - test_compilation_request_validation
#
# Test TimelineBuilder:
# - test_build_timeline
# - test_select_transition
# - test_adjust_clip_durations
# - test_zoom_effect_selection
#
# Test VideoCompiler:
# - @pytest.mark.asyncio
#   @pytest.mark.slow
#   async def test_compile_simple_video
# - @pytest.mark.asyncio
#   async def test_generate_thumbnail
# - test_parse_srt
# - test_zoom_effect_application
# - test_pan_effect_application
#
# Test VideoEffects:
# - test_ken_burns_effect
# - test_smooth_pan_effect
# - test_vignette_effect
# - test_color_grading
#
# Use sample images/audio in fixtures
# Mark video compilation tests as slow
# Test with small test files for speed
# Aim for >75% coverage (video rendering is slow to test)
```

---

### Week 6: Rendering Optimization & Polish

#### Task 6.1: Rendering Optimizer

**File**: `src/video_compilation/rendering.py`

```python
# COPILOT: Create rendering optimization utilities
#
# Import multiprocessing, psutil, Path
# Import Config, logger
#
# Class RenderingOptimizer:
# """
# Optimizes video rendering for performance.
# """
#
# def __init__(self, config: Config):
# - Store config
# - Detect available CPU cores
# - Detect available RAM
# - Determine optimal thread count
#
# def get_optimal_settings(self) -> dict:
# - Return dict with optimal settings:
#   * threads: Based on CPU cores (leave 1-2 for system)
#   * preset: 'ultrafast' if testing, 'medium' for production
#   * bitrate: Based on resolution
#   * buffer_size: Based on available RAM
# - Log recommended settings
# - Return settings dict
#
# def estimate_render_time(
#     self,
#     duration: float,
#     resolution: tuple[int, int],
#     fps: int
# ) -> float:
# - Estimate rendering time in seconds
# - Based on empirical data
# - Factor in resolution, fps, duration
# - Return estimated seconds
#
# def check_disk_space(self, output_dir: Path, required_mb: int = 500) -> bool:
# - Check available disk space
# - Return True if enough space
# - Log warning if low
#
# def cleanup_temp_files(self, temp_dir: Path):
# - Remove temporary rendering files
# - Remove MoviePy cache files
# - Log cleanup
#
# Add docstrings
```

---

#### Task 6.2: Thumbnail Generator

**File**: `src/video_compilation/thumbnail_generator.py`

```python
# COPILOT: Create thumbnail generation system
#
# Import PIL (Pillow), Path, Optional
# Import moviepy for frame extraction
# Import Config, Script, logger
#
# Class ThumbnailGenerator:
# """
# Generates eye-catching thumbnails for videos.
# """
#
# def __init__(self, config: Config):
# - Store config
# - Load fonts from assets
# - Load logo/branding if configured
# - Set thumbnail size: 1280x720 (YouTube standard)
#
# def generate(
#     self,
#     video_path: Path,
#     script: Script,
#     output_path: Optional[Path] = None
# ) -> Path:
# - Extract frame from video (at exciting moment)
# - Add text overlay with title
# - Add visual elements:
#   * High contrast background
#   * Bold text
#   * Emoji if appropriate
#   * Branding
# - Apply thumbnail best practices:
#   * Large text (readable on mobile)
#   * High contrast
#   * Faces if available
#   * Bright colors
# - Save as PNG with high quality
# - Return thumbnail path
#
# def _extract_best_frame(self, video_path: Path) -> Image:
# - Load video with moviepy
# - Extract frame at 25% into video (usually good moment)
# - Convert to PIL Image
# - Return image
#
# def _add_text_overlay(
#     self,
#     image: Image,
#     title: str,
#     style: str = "bold"
# ) -> Image:
# - Create text overlay
# - Use PIL ImageDraw
# - Add text with stroke/shadow for readability
# - Position text appropriately
# - Return image with text
#
# def _add_branding(self, image: Image) -> Image:
# - Add logo/watermark if configured
# - Position in corner
# - Semi-transparent
# - Return branded image
#
# def _optimize_colors(self, image: Image) -> Image:
# - Increase contrast
# - Boost saturation slightly
# - Make more eye-catching
# - Return optimized image
#
# Add comprehensive docstrings
```

---

## 📤 PHASE 4: YouTube Integration (Week 7)

### Task 7.1: OAuth Manager

**File**: `src/upload/oauth_manager.py`

```python
# COPILOT: Create YouTube OAuth authentication manager
#
# Import google.auth, google_auth_oauthlib.flow
# Import google.auth.transport.requests
# Import pickle, Path, os
# Import Config, logger
#
# Class OAuthManager:
# """
# Manages YouTube API OAuth 2.0 authentication.
# """
#
# SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
#
# def __init__(self, config: Config):
# - Store config
# - Set client_secrets_file from config
# - Set token_file from config
# - Set credentials = None
#
# def get_credentials(self):
# - Check if token_file exists
# - If exists:
#   * Load credentials from pickle
#   * If credentials expired and has refresh token:
#     - Refresh credentials
#     - Save updated token
#   * Return credentials
# - If no token file:
#   * Run OAuth flow
#   * Save credentials
#   * Return credentials
#
# def run_oauth_flow(self):
# - Create flow from client_secrets_file
# - flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
# - Run local server flow:
#   flow.run_local_server(port=8080, prompt='consent')
# - Get credentials
# - Save to token_file
# - Return credentials
#
# def save_credentials(self, credentials):
# - Pickle credentials to token_file
# - Set file permissions (600 for security)
# - Log save
#
# def revoke_credentials(self):
# - Revoke current credentials
# - Delete token_file
# - Log revocation
#
# def is_authenticated(self) -> bool:
# - Check if valid credentials exist
# - Return bool
#
# Add error handling for auth failures
# Add comprehensive logging
# Add docstrings
```

---

### Task 7.2: YouTube Uploader

**File**: `src/upload/youtube_uploader.py`

```python
# COPILOT: Create YouTube video uploader
#
# Import googleapiclient.discovery, googleapiclient.http
# Import google.auth.exceptions
# Import Path, Optional, Dict, Any
# Import OAuthManager, Config, logger
# Import time, random for retry logic
#
# Class YouTubeUploader:
# """
# Handles video uploads to YouTube via API v3.
# """
#
# def __init__(self, config: Config):
# - Store config
# - Initialize OAuthManager
# - Set youtube = None (will be initialized on first use)
#
# async def upload(
#     self,
#     video_path: Path,
#     metadata: Dict[str, Any]
# ) -> Dict[str, Any]:
# - Log upload start
# - Validate video file exists and size < 256GB
# - Get authenticated credentials
# - Initialize YouTube API client if not already
# - Prepare request body with metadata
# - Create MediaFileUpload object
# - Execute insert request with retry logic
# - Monitor upload progress
# - Handle quota errors
# - Log success/failure
# - Return upload response with video ID
#
# def _initialize_youtube_client(self):
# - Get credentials from OAuthManager
# - Build YouTube API client:
#   youtube = googleapiclient.discovery.build(
#     'youtube', 'v3', credentials=credentials
#   )
# - Store in self.youtube
#
# def _prepare_request_body(self, metadata: Dict[str, Any]) -> dict:
# - Create YouTube API request body:
#   {
#     'snippet': {
#       'title': metadata['title'],
#       'description': metadata['description'],
#       'tags': metadata['tags'],
#       'categoryId': metadata['category_id'],
#       'defaultLanguage': metadata['language']
#     },
#     'status': {
#       'privacyStatus': metadata['privacy_status'],
#       'selfDeclaredMadeForKids': False
#     }
#   }
# - Return body
#
# async def _upload_with_retry(
#     self,
#     request,
#     max_retries: int = 5
# ) -> dict:
# - Execute upload with exponential backoff
# - Handle:
#   * HttpError 500, 502, 503, 504 (retry)
#   * HttpError 403 quota (raise specific error)
#   * Network errors (retry)
# - Log each retry attempt
# - Return response or raise after max_retries
#
# def _monitor_upload_progress(self, request):
# - Show upload progress
# - Log percentage completed
# - Estimate time remaining
#
# async def set_thumbnail(self, video_id: str, thumbnail_path: Path):
# - Upload custom thumbnail
# - Use youtube.thumbnails().set()
# - Handle errors
# - Log result
#
# async def add_to_playlist(self, video_id: str, playlist_id: str):
# - Add video to playlist
# - Use youtube.playlistItems().insert()
# - Log result
#
# def check_quota(self) -> Dict[str, int]:
# - Query current quota usage
# - Return quota information
# - Log if approaching limit
#
# Add comprehensive error handling
# Add rate limiting
# Add logging
# Add docstrings with examples
```

---

### Task 7.3: Playlist Manager

**File**: `src/upload/playlist_manager.py`

```python
# COPILOT: Create YouTube playlist management
#
# Import googleapiclient, Path, List
# Import Config, logger
#
# Class PlaylistManager:
# """
# Manages YouTube playlists for organizing uploaded videos.
# """
#
# def __init__(self, youtube_client, config: Config):
# - Store youtube client
# - Store config
#
# def create_playlist(self, title: str, description: str) -> str:
# - Create new playlist
# - Use youtube.playlists().insert()
# - Return playlist ID
#
# def add_video(self, playlist_id: str, video_id: str):
# - Add video to playlist
# - Use youtube.playlistItems().insert()
# - Handle errors
#
# def get_playlist_videos(self, playlist_id: str) -> List[str]:
# - List videos in playlist
# - Return list of video IDs
#
# def create_dated_playlist(self, date_str: str = None) -> str:
# - Create playlist for specific month/year
# - Format: "YouTube Shorts - January 2026"
# - Return playlist ID
#
# Add docstrings
```

---

### Week 7 Testing

**File**: `tests/integration/test_youtube_upload.py`

```python
# COPILOT: Create integration tests for YouTube upload
# (These tests require valid OAuth credentials)
#
# Import pytest, Path
# Import YouTubeUploader, OAuthManager
#
# @pytest.mark.integration
# @pytest.mark.skipif(not os.getenv('YOUTUBE_CREDENTIALS'), reason="No credentials")
# class TestYouTubeUpload:
#
# def test_oauth_manager_get_credentials
# def test_oauth_manager_refresh_token
#
# @pytest.mark.asyncio
# async def test_upload_video:
# - Create small test video
# - Upload with test metadata
# - Verify video ID returned
# - Delete test video after
#
# @pytest.mark.asyncio
# async def test_set_thumbnail
#
# @pytest.mark.asyncio
# async def test_add_to_playlist
#
# def test_check_quota
#
# Use pytest.mark.skip for tests requiring credentials
# Add cleanup after tests
```

---

## 🔍 PHASE 5: SEO & Metadata (Week 8)

### Task 8.1: SEO Optimizer

**File**: `src/metadata/seo_optimizer.py`

```python
# COPILOT: Create SEO optimization system
#
# Import re, List, Dict
# Import Script, TrendData, Config, logger
#
# Class SEOOptimizer:
# """
# Generates SEO-optimized titles, descriptions, and tags.
# """
#
# def __init__(self, config: Config):
# - Store config
# - Load SEO config
# - Load title templates
# - Load description templates
#
# def generate_metadata(
#     self,
#     script: Script,
#     trend: TrendData
# ) -> Dict[str, Any]:
# - Generate all metadata:
#   * title = self._generate_title(script, trend)
#   * description = self._generate_description(script, trend)
#   * tags = self._generate_tags(script, trend)
#   * hashtags = self._generate_hashtags(script, trend)
# - Return metadata dict
#
# def _generate_title(self, script: Script, trend: TrendData) -> str:
# - Use trend keyword prominently
# - Make it compelling (clickable but not clickbait)
# - Keep under 70 characters
# - Include power words:
#   * "Secret", "Truth", "Shocking", "Amazing", etc.
# - Templates:
#   * "The Truth About {keyword}"
#   * "{keyword} Explained in 60 Seconds"
#   * "Why {keyword} Is Trending"
# - Return title
#
# def _generate_description(self, script: Script, trend: TrendData) -> str:
# - Include:
#   * Hook from script
#   * Brief summary
#   * Timestamps for key moments
#   * Call to action
#   * Links (if any)
#   * Hashtags
# - Template from config
# - Keep under 5000 characters
# - Return description
#
# def _generate_tags(self, script: Script, trend: TrendData) -> List[str]:
# - Extract keywords from script
# - Include trend keyword and related
# - Add niche-specific tags
# - Add generic tags: "shorts", "trending", etc.
# - Limit to 500 total characters
# - Return list of tags
#
# def _generate_hashtags(self, script: Script, trend: TrendData) -> List[str]:
# - Select relevant hashtags
# - Include #Shorts (required)
# - Include trend-related hashtags
# - Limit to 15 total (YouTube limit)
# - Return list
#
# def _extract_keywords(self, text: str, count: int = 10) -> List[str]:
# - Use simple NLP to extract keywords
# - Remove stop words
# - Return top keywords by frequency
#
# Add comprehensive docstrings
```

---

### Task 8.2: Keyword Extractor

**File**: `src/metadata/keyword_extractor.py`

```python
# COPILOT: Create keyword extraction utility
#
# Import re, collections, List
#
# Class KeywordExtractor:
# """
# Extracts relevant keywords from text for SEO.
# """
#
# STOP_WORDS = {
#   'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of',
#   'and', 'or', 'but', 'is', 'are', 'was', 'were', 'been',
#   'this', 'that', 'these', 'those', 'will', 'would', 'could',
#   'should', 'can', 'may', 'might', 'must', 'shall'
# }
#
# @staticmethod
# def extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
# - Convert to lowercase
# - Remove punctuation
# - Split into words
# - Remove stop words
# - Count word frequency
# - Return top max_keywords
#
# @staticmethod
# def extract_noun_phrases(text: str) -> List[str]:
# - Use simple pattern matching
# - Find sequences like "ADJ NOUN" or "NOUN NOUN"
# - Return phrases
#
# @staticmethod
# def calculate_keyword_density(text: str, keyword: str) -> float:
# - Count occurrences of keyword
# - Calculate as percentage of total words
# - Return density
#
# Add docstrings
```

---

## ⏰ PHASE 6: Automation & Scheduling (Week 9)

### Task 9.1: Scheduler Setup

**File**: `src/core/scheduler.py`

```python
# COPILOT: Create scheduling system using APScheduler
#
# Import apscheduler, asyncio, datetime
# Import Config, Pipeline, logger
#
# Class VideoScheduler:
# """
# Manages scheduled video generation and upload.
# """
#
# def __init__(self, config: Config):
# - Store config
# - Initialize AsyncIOScheduler
# - Configure timezone
# - Set pipeline = Pipeline(config)
#
# async def start_daemon(self):
# - Parse generation_time from config
# - Schedule daily generation:
#   scheduler.add_job(
#     self._run_generation,
#     trigger='cron',
#     hour=hour, minute=minute,
#     timezone=config.schedule.timezone
#   )
# - Add health check job (every 5 minutes):
#   scheduler.add_job(
#     self._health_check,
#     trigger='interval',
#     minutes=5
#   )
# - Start scheduler
# - Log schedule
# - Wait forever (until interrupted)
#
# async def _run_generation(self):
# - Log scheduled run start
# - Try:
#   * result = await self.pipeline.run()
#   * Log result
#   * Send notifications if configured
# - Except:
#   * Log error
#   * Send error alert
#   * Retry if configured
#
# async def _health_check(self):
# - Check disk space
# - Check memory usage
# - Check API quotas
# - Log status
# - Alert if issues
#
# def get_next_run_time(self) -> datetime:
# - Return next scheduled run time
#
# def pause_scheduling(self):
# - Pause scheduler
# - Log pause
#
# def resume_scheduling(self):
# - Resume scheduler
# - Log resume
#
# Add error recovery
# Add graceful shutdown
# Add docstrings
```

---

### Task 9.2: Health Monitor

**File**: `src/monitoring/health.py`

```python
# COPILOT: Create health monitoring system
#
# Import psutil, Path
# Import Config, logger
#
# Class HealthMonitor:
# """
# Monitors system health and resources.
# """
#
# def __init__(self, config: Config):
# - Store config
# - Set thresholds from config
#
# def check_disk_space(self) -> Dict[str, Any]:
# - Get disk usage for output directory
# - Check if below threshold
# - Return status dict
#
# def check_memory(self) -> Dict[str, Any]:
# - Get memory usage
# - Check if below threshold
# - Return status dict
#
# def check_cpu(self) -> Dict[str, Any]:
# - Get CPU usage
# - Return status dict
#
# def check_api_quotas(self) -> Dict[str, Any]:
# - Check YouTube API quota
# - Warn if approaching limit
# - Return status dict
#
# def check_all(self) -> Dict[str, Any]:
# - Run all checks
# - Return comprehensive status
#
# def is_healthy(self) -> bool:
# - Run checks
# - Return True if all pass
#
# Add logging
# Add docstrings
```

---

## 🧪 PHASE 7: Testing & Refinement (Week 10)

### Task 10.1: End-to-End Tests

**File**: `tests/integration/test_full_pipeline.py`

```python
# COPILOT: Create comprehensive end-to-end tests
#
# Import pytest, asyncio, Path
# Import all major components
#
# @pytest.mark.e2e
# @pytest.mark.slow
# class TestFullPipeline:
#
# @pytest.mark.asyncio
# async def test_full_pipeline_no_upload:
# - Run complete pipeline
# - Mock YouTube upload
# - Verify video generated
# - Check all stages completed
# - Validate output quality
#
# @pytest.mark.asyncio
# async def test_error_recovery:
# - Simulate failures at each stage
# - Verify recovery mechanisms
# - Check cleanup on failure
#
# @pytest.mark.asyncio
# async def test_with_different_niches:
# - Test all niche types
# - Verify appropriate content generation
#
# Add comprehensive validation
# Test all edge cases
```

---

### Task 10.2: Load Testing

**File**: `tests/performance/test_load.py`

```python
# COPILOT: Create performance and load tests
#
# Import pytest, time, asyncio, statistics
# Import Pipeline, Config
#
# @pytest.mark.performance
# class TestPerformance:
#
# @pytest.mark.asyncio
# async def test_generation_speed:
# - Measure time for complete generation
# - Assert < 15 minutes
#
# @pytest.mark.asyncio
# async def test_memory_usage:
# - Monitor memory during generation
# - Assert < 8GB peak
#
# @pytest.mark.asyncio
# async def test_concurrent_generations:
# - Run multiple generations concurrently
# - Measure resource usage
#
# Collect metrics
# Generate performance report
```

---

## 🚀 PHASE 8: Deployment (Week 11)

### Task 11.1: Setup Scripts

**File**: `scripts/setup.sh`

```bash
#!/bin/bash
# COPILOT: Create automated setup script for Linux/macOS
#
# Steps:
# 1. Check Python version (>= 3.11)
# 2. Install system dependencies (ffmpeg, imagemagick)
# 3. Install Poetry if not present
# 4. Run poetry install
# 5. Create directories
# 6. Copy config templates
# 7. Run YouTube OAuth flow
# 8. Download models if AI enabled
# 9. Run test to verify installation
# 10. Print success message and next steps
#
# Add error handling
# Add progress indicators
# Add colored output
```

**File**: `scripts/setup.ps1`

```powershell
# COPILOT: Create automated setup script for Windows
#
# Same steps as setup.sh but for Windows
# Use Chocolatey for dependencies
# Handle Windows-specific paths
# Use PowerShell equivalents
```

---

### Task 11.2: Documentation

**File**: `docs/SETUP.md`

```markdown
# COPILOT: Create comprehensive setup documentation
#
# Include:
# - Prerequisites
# - Step-by-step installation
# - Configuration guide
# - YouTube API setup
# - OAuth configuration
# - First run instructions
# - Troubleshooting
# - FAQ
```

---

## 🎉 PHASE 9: Launch & Monitoring (Week 12)

### Task 12.1: Pre-Launch Checklist

**File**: `scripts/pre_launch_checklist.py`

```python
# COPILOT: Create automated pre-launch validation
#
# Check:
# 1. All dependencies installed
# 2. Configuration valid
# 3. YouTube authentication works
# 4. Disk space sufficient
# 5. API quotas available
# 6. Test video generation succeeds
# 7. Test upload succeeds (to unlisted)
# 8. Monitoring configured
# 9. Backup strategy in place
# 10. Logging working
#
# Print checklist results
# Suggest fixes for failures
```

---

### Task 12.2: Monitoring Dashboard (Optional)

**File**: `src/monitoring/dashboard.py`

```python
# COPILOT: Create simple web dashboard with Flask
#
# Endpoints:
# - /: Main dashboard with stats
# - /api/status: JSON status
# - /api/metrics: JSON metrics
# - /api/logs: Recent logs
# - /api/videos: Uploaded videos list
#
# Display:
# - Success rate
# - Last run time
# - Next run time
# - Total videos uploaded
# - Storage usage
# - API quota remaining
# - Recent errors
#
# Simple HTML/CSS interface
# Real-time updates with JavaScript
```

---

## ✅ Final Completion Checklist

Run through this checklist before considering the project complete:

### Code Quality
```bash
- [ ] All code has type hints
- [ ] All functions have docstrings
- [ ] No linting errors (ruff, mypy)
- [ ] Code formatted with black
- [ ] No security vulnerabilities (bandit)
```

### Testing
```bash
- [ ] Unit test coverage >80%
- [ ] All integration tests passing
- [ ] E2E tests passing
- [ ] Performance tests within targets
```

### Documentation
```bash
- [ ] README.md complete
- [ ] SETUP.md detailed
- [ ] API documentation generated
- [ ] Configuration documented
- [ ] Troubleshooting guide complete
```

### Functionality
```bash
- [ ] Trend analysis working
- [ ] Script generation quality checked
- [ ] Video compilation tested
- [ ] YouTube upload working
- [ ] Scheduling operational
- [ ] Error handling robust
- [ ] Logging comprehensive
```

### Deployment
```bash
- [ ] Setup scripts tested
- [ ] CI/CD pipeline working
- [ ] Docker images building
- [ ] System service configured
- [ ] Monitoring active
- [ ] Backups configured
```

---

## 🎯 Quick Reference: Development Commands

```bash
# Development
poetry install              # Install dependencies
poetry run python -m src.main --test  # Test run
poetry run pytest -v       # Run tests
poetry run black src/      # Format code
poetry run ruff check src/ # Lint code
poetry run mypy src/       # Type check

# Testing
poetry run pytest tests/unit/ -v --cov=src
poetry run pytest tests/integration/ -v -s
poetry run pytest -m "not slow" -v
poetry run pytest --cov-report=html

# Production
poetry run python -m src.main --once    # Single run
poetry run python -m src.main --daemon  # Start daemon
systemctl start yt-shorts-factory       # System service
docker-compose up -d                     # Docker deployment

# Monitoring
tail -f logs/yt-shorts-factory.log     # View logs
python scripts/show_metrics.py         # Show metrics
curl localhost:8080/api/status         # Check status (if dashboard running)

# Maintenance
python scripts/cleanup_old_files.py    # Clean archives
python scripts/check_quotas.py         # Check API quotas
python scripts/backup_config.py        # Backup config
```

---

## 🏁 Project Complete!

**Congratulations!** You now have a complete, production-ready YouTube Shorts Automation Factory.

### What You've Built:
- ✅ Autonomous trend analysis
- ✅ AI-powered script generation
- ✅ Professional video compilation
- ✅ Automated YouTube uploads
- ✅ SEO optimization
- ✅ Scheduled daemon
- ✅ Comprehensive monitoring
- ✅ Production deployment

### Next Steps:
1. Let it run for 7 days to gather initial metrics
2. Review generated videos and adjust templates
3. Optimize based on performance data
4. Scale to multiple channels if successful
5. Implement advanced features from roadmap

### Expected Timeline to Monetization:
- **Month 1**: System refinement, first 10-20 videos
- **Month 2-3**: Consistent uploads, channel growth begins
- **Month 4-6**: Hit monetization threshold (1K subs, 4K watch hours)
- **Month 7-12**: Revenue scaling, $1K-$10K/month potential

---

**Remember**: This is a marathon, not a sprint. Focus on consistency and quality. The sub-linear scaling will compound over time!

Good luck! 🚀
