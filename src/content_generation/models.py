"""
Data models for video script generation.

Defines structures for scripts, scenes, hooks, and script metadata.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SceneTransition(str, Enum):
    """Transition types between scenes."""

    NONE = "none"
    FADE = "fade"
    DISSOLVE = "dissolve"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    CUT = "cut"


class SceneType(str, Enum):
    """Type of scene content."""

    HOOK = "hook"
    BODY = "body"
    TRANSITION = "transition"
    CALL_TO_ACTION = "call_to_action"
    OUTRO = "outro"


class VideoScene(BaseModel):
    """Represents a single scene in the video."""

    text: str = Field(..., description="Scene narration text")
    duration: float = Field(..., ge=0.5, le=30, description="Scene duration in seconds")
    image_prompt: str = Field(
        ..., description="Prompt for AI image generation or stock image search"
    )
    transition: SceneTransition = Field(
        default=SceneTransition.FADE, description="Transition to next scene"
    )
    scene_type: SceneType = Field(
        default=SceneType.BODY, description="Type of scene"
    )
    visual_style: Optional[str] = Field(
        default=None, description="Additional visual style instructions"
    )

    class Config:
        use_enum_values = False


class Hook(BaseModel):
    """Video hook (first 3 seconds - critical for retention)."""

    text: str = Field(..., min_length=10, max_length=200)
    pattern: str = Field(
        ..., description="Hook pattern used (e.g., 'question', 'shocking_statement')"
    )
    keyword: str = Field(..., description="Main keyword in hook")
    engagement_score: float = Field(
        default=0.5, ge=0, le=1, description="Predicted engagement 0-1"
    )


class Script(BaseModel):
    """Complete video script with metadata."""

    title: str = Field(..., min_length=5, max_length=100)
    hook: Hook = Field(..., description="Opening hook")
    scenes: list[VideoScene] = Field(..., min_items=3, description="Scene sequence")
    call_to_action: str = Field(..., min_length=10, max_length=200)
    
    # Metadata
    niche: str = Field(..., description="Content niche")
    trending_keyword: str = Field(..., description="Trending keyword incorporated")
    related_keywords: list[str] = Field(default_factory=list)
    
    # Generated metrics
    total_duration: float = Field(ge=15, le=60)
    word_count: int = Field(ge=50)
    scene_count: int
    
    # Generation metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(default="template_engine")
    quality_score: float = Field(default=0.5, ge=0, le=1)

    @property
    def full_text(self) -> str:
        """Return complete script as continuous text."""
        scene_texts = [self.hook.text] + [s.text for s in self.scenes]
        return " ".join(scene_texts) + " " + self.call_to_action

    @property
    def image_prompts(self) -> list[str]:
        """Extract all image generation prompts."""
        return [s.image_prompt for s in self.scenes]

    @property
    def scene_texts(self) -> list[str]:
        """Extract scene texts only."""
        return [s.text for s in self.scenes]

    def validate_duration(self) -> bool:
        """Check if script duration is within YouTube Shorts limits."""
        calculated = sum(s.duration for s in self.scenes)
        return 15 <= calculated <= 60 and abs(calculated - self.total_duration) < 0.1

    def to_srt(self) -> str:
        """Convert script to SRT subtitle format."""
        srt_lines = []
        current_time = 0

        scenes_with_timing = [(self.hook.text, 3.0)]
        for scene in self.scenes:
            scenes_with_timing.append((scene.text, scene.duration))

        for idx, (text, duration) in enumerate(scenes_with_timing, 1):
            start = self._format_timecode(current_time)
            end = self._format_timecode(current_time + duration)

            srt_lines.append(str(idx))
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text)
            srt_lines.append("")

            current_time += duration

        return "\n".join(srt_lines)

    @staticmethod
    def _format_timecode(seconds: float) -> str:
        """Format seconds to SRT timecode (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class ScriptGenerationRequest(BaseModel):
    """Request to generate a script."""

    niche: str = Field(..., description="Content niche")
    trending_keyword: str = Field(..., description="Trending keyword to incorporate")
    related_keywords: list[str] = Field(default_factory=list)
    target_duration: float = Field(default=45, ge=15, le=60)
    style: Optional[str] = Field(
        default=None, description="Optional generation style override"
    )


class ScriptGenerationResult(BaseModel):
    """Result of script generation."""

    success: bool
    script: Optional[Script] = None
    error: Optional[str] = None
    generation_time_ms: float = Field(default=0)
    model_used: str = Field(default="template_engine")
