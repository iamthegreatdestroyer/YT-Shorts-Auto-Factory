"""
Pipeline orchestration for video generation.

This module provides the main orchestration logic for generating
YouTube Shorts videos through a multi-stage pipeline.

Pipeline Stages:
    1. Trend Analysis - Identify trending topics
    2. Script Generation - Create video script
    3. TTS Generation - Convert script to audio
    4. Image Generation - Generate visual assets
    5. Video Compilation - Assemble final video
    6. Thumbnail Generation - Create video thumbnail
    7. Metadata Optimization - Optimize title, description, tags
    8. Upload - Upload to YouTube (optional)
    9. Cleanup - Remove temporary files

Example:
    >>> from src.core.pipeline import Pipeline
    >>> from src.core.config import get_settings
    >>>
    >>> settings = get_settings()
    >>> pipeline = Pipeline(settings)
    >>> result = await pipeline.run()
    >>> print(result['video_path'])
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Optional

from src.core.config import Settings
from src.core.constants import PipelineStage, PipelineStatus
from src.core.exceptions import PipelineError, StageError
from src.monitoring.logger import logger, log_separator, pipeline_context


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class StageResult:
    """Result from a pipeline stage execution."""

    stage: PipelineStage
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage": self.stage.value,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PipelineContext:
    """
    Context passed through pipeline stages.

    Contains accumulated data from all stages and shared resources.
    """

    run_id: str
    settings: Settings
    test_mode: bool = False
    no_upload: bool = False

    # Stage outputs
    trend_data: Optional[dict[str, Any]] = None
    script_data: Optional[dict[str, Any]] = None
    audio_path: Optional[Path] = None
    image_paths: list[Path] = field(default_factory=list)
    video_path: Optional[Path] = None
    thumbnail_path: Optional[Path] = None
    metadata: Optional[dict[str, Any]] = None
    video_id: Optional[str] = None

    # Temporary files to clean up
    temp_files: list[Path] = field(default_factory=list)

    # Stage results
    stage_results: list[StageResult] = field(default_factory=list)

    # Timing
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def add_temp_file(self, path: Path) -> None:
        """Register a temporary file for cleanup."""
        if path not in self.temp_files:
            self.temp_files.append(path)

    def get_duration(self) -> float:
        """Get total pipeline duration in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or perf_counter()
        return end - self.start_time

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for logging."""
        return {
            "run_id": self.run_id,
            "test_mode": self.test_mode,
            "no_upload": self.no_upload,
            "video_path": str(self.video_path) if self.video_path else None,
            "video_id": self.video_id,
            "duration": self.get_duration(),
            "stages_completed": len([r for r in self.stage_results if r.success]),
            "stages_failed": len([r for r in self.stage_results if not r.success]),
        }


@dataclass
class PipelineResult:
    """Final result from pipeline execution."""

    success: bool
    run_id: str
    video_path: Optional[Path] = None
    thumbnail_path: Optional[Path] = None
    video_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    duration: float = 0.0
    error: Optional[str] = None
    stage_results: list[StageResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "run_id": self.run_id,
            "video_path": str(self.video_path) if self.video_path else None,
            "thumbnail_path": str(self.thumbnail_path) if self.thumbnail_path else None,
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "duration": self.duration,
            "error": self.error,
            "stages": [r.to_dict() for r in self.stage_results],
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# Pipeline Class
# =============================================================================


class Pipeline:
    """
    Main pipeline orchestrator for video generation.

    Executes a series of stages to generate a complete YouTube Short,
    from trend analysis through to upload.
    """

    def __init__(
        self,
        settings: Settings,
        test_mode: bool = False,
        no_upload: bool = False,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            settings: Application settings.
            test_mode: If True, use mock services.
            no_upload: If True, skip YouTube upload.
        """
        self.settings = settings
        self.test_mode = test_mode
        self.no_upload = no_upload

        # Initialize components (will be implemented in later phases)
        self._init_components()

        logger.info(
            f"Pipeline initialized | test_mode={test_mode} | no_upload={no_upload}"
        )

    def _init_components(self) -> None:
        """Initialize pipeline components."""
        # TODO: Initialize actual components in later phases
        # self.trend_analyzer = TrendAnalyzer(self.settings)
        # self.script_generator = ScriptGenerator(self.settings)
        # self.tts_engine = get_tts_engine(self.settings)
        # self.image_generator = get_image_generator(self.settings)
        # self.video_compiler = VideoCompiler(self.settings)
        # self.seo_optimizer = SEOOptimizer(self.settings)
        # self.youtube_uploader = YouTubeUploader(self.settings)

        logger.debug("Pipeline components initialized (placeholder)")

    async def run(self) -> dict[str, Any]:
        """
        Execute the complete video generation pipeline.

        Returns:
            Dictionary with pipeline results.

        Raises:
            PipelineError: If pipeline execution fails.
        """
        # Create execution context
        run_id = str(uuid.uuid4())[:8]
        context = PipelineContext(
            run_id=run_id,
            settings=self.settings,
            test_mode=self.test_mode,
            no_upload=self.no_upload,
        )
        context.start_time = perf_counter()

        log_separator(f"Pipeline Run: {run_id}")

        try:
            # Execute stages in sequence
            stages = [
                (PipelineStage.TREND_ANALYSIS, self._analyze_trends),
                (PipelineStage.SCRIPT_GENERATION, self._generate_script),
                (PipelineStage.TTS_GENERATION, self._generate_audio),
                (PipelineStage.IMAGE_GENERATION, self._generate_images),
                (PipelineStage.VIDEO_COMPILATION, self._compile_video),
                (PipelineStage.THUMBNAIL_GENERATION, self._generate_thumbnail),
                (PipelineStage.METADATA_OPTIMIZATION, self._optimize_metadata),
            ]

            # Add upload stage if enabled
            if not self.no_upload:
                stages.append((PipelineStage.UPLOAD, self._upload_video))

            # Execute each stage
            for stage, handler in stages:
                await self._execute_stage(stage, handler, context)

            # Mark completion
            context.end_time = perf_counter()

            # Create result
            result = PipelineResult(
                success=True,
                run_id=run_id,
                video_path=context.video_path,
                thumbnail_path=context.thumbnail_path,
                video_id=context.video_id,
                title=context.metadata.get("title") if context.metadata else None,
                description=context.metadata.get("description") if context.metadata else None,
                tags=context.metadata.get("tags", []) if context.metadata else [],
                duration=context.get_duration(),
                stage_results=context.stage_results,
            )

            log_separator(f"Pipeline Complete: {run_id}", char="-")
            logger.info(
                f"Pipeline succeeded | run_id={run_id} | "
                f"duration={result.duration:.2f}s | "
                f"video_path={result.video_path}"
            )

            return result.to_dict()

        except StageError as e:
            context.end_time = perf_counter()
            logger.error(f"Pipeline stage failed | run_id={run_id} | error={e}")

            result = PipelineResult(
                success=False,
                run_id=run_id,
                error=str(e),
                duration=context.get_duration(),
                stage_results=context.stage_results,
            )
            return result.to_dict()

        except Exception as e:
            context.end_time = perf_counter()
            logger.exception(f"Pipeline failed unexpectedly | run_id={run_id}")

            raise PipelineError(
                f"Pipeline failed: {e}",
                pipeline_name="video_generation",
                run_id=run_id,
                original_error=e,
            ) from e

        finally:
            # Cleanup stage always runs
            await self._cleanup(context)

    async def _execute_stage(
        self,
        stage: PipelineStage,
        handler: Callable[[PipelineContext], Any],
        context: PipelineContext,
    ) -> StageResult:
        """
        Execute a single pipeline stage.

        Args:
            stage: The stage to execute.
            handler: The handler function for the stage.
            context: Pipeline context.

        Returns:
            StageResult with execution details.

        Raises:
            StageError: If stage execution fails.
        """
        stage_name = stage.value
        logger.info(f"🚀 Starting stage: {stage_name}")
        start_time = perf_counter()

        try:
            # Execute the handler
            await handler(context)

            # Record success
            duration = perf_counter() - start_time
            result = StageResult(
                stage=stage,
                success=True,
                duration=duration,
            )
            context.stage_results.append(result)

            logger.info(
                f"✅ Stage completed: {stage_name} | duration={duration:.2f}s"
            )

            return result

        except Exception as e:
            # Record failure
            duration = perf_counter() - start_time
            result = StageResult(
                stage=stage,
                success=False,
                error=str(e),
                duration=duration,
            )
            context.stage_results.append(result)

            logger.error(
                f"❌ Stage failed: {stage_name} | duration={duration:.2f}s | error={e}"
            )

            raise StageError(
                f"Stage '{stage_name}' failed: {e}",
                stage_name=stage_name,
                original_error=e,
            ) from e

    # =========================================================================
    # Stage Handlers (Placeholder implementations)
    # =========================================================================

    async def _analyze_trends(self, context: PipelineContext) -> None:
        """
        Analyze trends to find content topics.

        TODO: Implement actual trend analysis in Phase 2.
        """
        logger.debug("Analyzing trends...")

        if self.test_mode:
            # Return mock trend data
            context.trend_data = {
                "topic": "Amazing Technology Facts",
                "keywords": ["technology", "innovation", "future", "amazing"],
                "score": 0.85,
                "source": "mock",
            }
            logger.info(f"Mock trend selected: {context.trend_data['topic']}")
            return

        # TODO: Implement actual trend analysis
        # trend = await self.trend_analyzer.get_top_trend()
        # context.trend_data = trend.to_dict()

        # Placeholder
        await asyncio.sleep(0.1)  # Simulate work
        context.trend_data = {
            "topic": "5 Mind-Blowing Tech Facts You Didn't Know",
            "keywords": ["tech", "facts", "amazing", "innovation"],
            "score": 0.9,
            "source": "youtube_trending",
        }
        logger.info(f"Trend selected: {context.trend_data['topic']}")

    async def _generate_script(self, context: PipelineContext) -> None:
        """
        Generate video script from trend.

        TODO: Implement actual script generation in Phase 2.
        """
        logger.debug("Generating script...")

        if context.trend_data is None:
            raise StageError("No trend data available", stage_name="script_generation")

        topic = context.trend_data.get("topic", "Unknown Topic")

        if self.test_mode:
            context.script_data = {
                "title": topic,
                "hook": "Wait until you see number 3!",
                "segments": [
                    {"text": "Here's a mind-blowing fact...", "duration": 5},
                    {"text": "Scientists discovered that...", "duration": 10},
                    {"text": "The future is now!", "duration": 5},
                ],
                "outro": "Follow for more amazing facts!",
                "total_duration": 20,
            }
            return

        # TODO: Implement actual script generation
        # script = await self.script_generator.generate(context.trend_data)
        # context.script_data = script.to_dict()

        await asyncio.sleep(0.1)
        context.script_data = {
            "title": topic,
            "hook": "You won't believe what happens next!",
            "segments": [
                {
                    "text": "Did you know that the first computer bug was an actual bug?",
                    "duration": 8,
                },
                {
                    "text": "A moth was found in the Harvard Mark II computer in 1947.",
                    "duration": 7,
                },
                {
                    "text": "This is where the term 'debugging' comes from!",
                    "duration": 5,
                },
            ],
            "outro": "Follow for more tech history!",
            "total_duration": 25,
        }

    async def _generate_audio(self, context: PipelineContext) -> None:
        """
        Generate TTS audio from script.

        TODO: Implement actual TTS in Phase 3.
        """
        logger.debug("Generating audio...")

        if context.script_data is None:
            raise StageError("No script data available", stage_name="tts_generation")

        if self.test_mode:
            # Create mock audio file path
            context.audio_path = self.settings.storage.temp_path / f"audio_{context.run_id}.mp3"
            context.add_temp_file(context.audio_path)
            # Don't actually create the file in test mode
            return

        # TODO: Implement actual TTS
        # audio_path = await self.tts_engine.generate(context.script_data)
        # context.audio_path = audio_path
        # context.add_temp_file(audio_path)

        await asyncio.sleep(0.1)
        context.audio_path = self.settings.storage.temp_path / f"audio_{context.run_id}.mp3"
        context.add_temp_file(context.audio_path)
        logger.info(f"Audio generated: {context.audio_path}")

    async def _generate_images(self, context: PipelineContext) -> None:
        """
        Generate visual assets for video.

        TODO: Implement actual image generation in Phase 3.
        """
        logger.debug("Generating images...")

        if context.script_data is None:
            raise StageError("No script data available", stage_name="image_generation")

        segments = context.script_data.get("segments", [])
        image_paths = []

        for i, segment in enumerate(segments):
            if self.test_mode:
                path = self.settings.storage.temp_path / f"image_{context.run_id}_{i}.png"
            else:
                # TODO: Implement actual image generation
                # path = await self.image_generator.generate(segment['text'])
                await asyncio.sleep(0.05)
                path = self.settings.storage.temp_path / f"image_{context.run_id}_{i}.png"

            image_paths.append(path)
            context.add_temp_file(path)

        context.image_paths = image_paths
        logger.info(f"Generated {len(image_paths)} images")

    async def _compile_video(self, context: PipelineContext) -> None:
        """
        Compile final video from assets.

        TODO: Implement actual video compilation in Phase 4.
        """
        logger.debug("Compiling video...")

        if not context.audio_path or not context.image_paths:
            raise StageError(
                "Missing audio or images for compilation",
                stage_name="video_compilation",
            )

        output_path = (
            self.settings.storage.output_path
            / f"video_{context.run_id}.mp4"
        )

        if self.test_mode:
            context.video_path = output_path
            return

        # TODO: Implement actual video compilation
        # video_path = await self.video_compiler.compile(
        #     audio_path=context.audio_path,
        #     image_paths=context.image_paths,
        #     script=context.script_data,
        #     output_path=output_path,
        # )
        # context.video_path = video_path

        await asyncio.sleep(0.1)
        context.video_path = output_path
        logger.info(f"Video compiled: {context.video_path}")

    async def _generate_thumbnail(self, context: PipelineContext) -> None:
        """
        Generate video thumbnail.

        TODO: Implement actual thumbnail generation in Phase 4.
        """
        logger.debug("Generating thumbnail...")

        output_path = (
            self.settings.storage.output_path
            / f"thumbnail_{context.run_id}.jpg"
        )

        if self.test_mode:
            context.thumbnail_path = output_path
            return

        # TODO: Implement actual thumbnail generation
        # thumbnail_path = await self.thumbnail_generator.generate(
        #     title=context.script_data.get('title'),
        #     image=context.image_paths[0] if context.image_paths else None,
        # )
        # context.thumbnail_path = thumbnail_path

        await asyncio.sleep(0.05)
        context.thumbnail_path = output_path
        logger.info(f"Thumbnail generated: {context.thumbnail_path}")

    async def _optimize_metadata(self, context: PipelineContext) -> None:
        """
        Optimize video metadata for SEO.

        TODO: Implement actual SEO optimization in Phase 5.
        """
        logger.debug("Optimizing metadata...")

        if context.script_data is None or context.trend_data is None:
            raise StageError(
                "Missing script or trend data for metadata",
                stage_name="metadata_optimization",
            )

        if self.test_mode:
            context.metadata = {
                "title": context.script_data.get("title", "Amazing Video"),
                "description": "An amazing video about technology! #shorts",
                "tags": ["shorts", "viral", "technology"],
            }
            return

        # TODO: Implement actual SEO optimization
        # metadata = await self.seo_optimizer.optimize(
        #     script=context.script_data,
        #     trend=context.trend_data,
        # )
        # context.metadata = metadata

        await asyncio.sleep(0.05)
        title = context.script_data.get("title", "Amazing Video")
        context.metadata = {
            "title": f"{title} #shorts",
            "description": (
                f"{context.script_data.get('hook', '')}\n\n"
                f"{context.script_data.get('outro', '')}\n\n"
                "#shorts #viral #trending"
            ),
            "tags": context.trend_data.get("keywords", []) + ["shorts", "viral"],
        }
        logger.info(f"Metadata optimized: {context.metadata['title']}")

    async def _upload_video(self, context: PipelineContext) -> None:
        """
        Upload video to YouTube.

        TODO: Implement actual upload in Phase 6.
        """
        logger.debug("Uploading video...")

        if context.video_path is None or context.metadata is None:
            raise StageError(
                "Missing video or metadata for upload",
                stage_name="upload",
            )

        if self.test_mode:
            context.video_id = f"mock_{context.run_id}"
            logger.info(f"Mock upload complete: {context.video_id}")
            return

        if self.no_upload:
            logger.info("Upload skipped (no_upload=True)")
            return

        # TODO: Implement actual YouTube upload
        # video_id = await self.youtube_uploader.upload(
        #     video_path=context.video_path,
        #     title=context.metadata['title'],
        #     description=context.metadata['description'],
        #     tags=context.metadata['tags'],
        #     thumbnail_path=context.thumbnail_path,
        # )
        # context.video_id = video_id

        await asyncio.sleep(0.1)
        context.video_id = f"yt_{context.run_id}"
        logger.info(f"Video uploaded: https://youtube.com/shorts/{context.video_id}")

    async def _cleanup(self, context: PipelineContext) -> None:
        """Clean up temporary files."""
        logger.debug("Cleaning up temporary files...")

        if not context.temp_files:
            logger.debug("No temporary files to clean up")
            return

        cleaned = 0
        for path in context.temp_files:
            try:
                if path.exists():
                    path.unlink()
                    cleaned += 1
            except Exception as e:
                logger.warning(f"Failed to delete temp file {path}: {e}")

        logger.info(f"Cleaned up {cleaned}/{len(context.temp_files)} temporary files")


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "Pipeline",
    "PipelineContext",
    "PipelineResult",
    "StageResult",
]
