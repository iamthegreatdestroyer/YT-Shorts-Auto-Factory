"""
Video compiler: assembles audio + background + burnt-in subtitles → 1080x1920 MP4.

Uses moviepy. Background is a solid color frame if no image assets are available.
Subtitles are word-wrapped lines drawn with Pillow so no system fonts are required.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Optional

from loguru import logger


WIDTH = 1080
HEIGHT = 1920
FPS = 30
BACKGROUND_COLOR = (15, 15, 30)  # dark navy
TEXT_COLOR = (255, 255, 255)
FONT_SIZE = 60


def _make_text_frame(text: str, duration: float, width: int = WIDTH, height: int = HEIGHT):
    """Return a moviepy ImageClip with wrapped text centred on a solid background."""
    from PIL import Image, ImageDraw, ImageFont  # type: ignore[import]
    import numpy as np

    img = Image.new("RGB", (width, height), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    # Word-wrap to ~22 chars per line
    wrapped = "\n".join(textwrap.wrap(text, width=22))

    # Try a truetype font; fall back to default bitmap font
    try:
        font = ImageFont.truetype("arial.ttf", FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()

    # Centre the text block
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=12)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (width - text_w) // 2
    y = (height - text_h) // 2

    # Draw subtle shadow
    draw.multiline_text((x + 3, y + 3), wrapped, font=font, fill=(0, 0, 0), spacing=12, align="center")
    draw.multiline_text((x, y), wrapped, font=font, fill=TEXT_COLOR, spacing=12, align="center")

    frame = np.array(img)
    from moviepy.editor import ImageClip  # type: ignore[import]
    return ImageClip(frame).set_duration(duration)


async def compile_video(
    script_data: dict,
    audio_path: Path,
    output_path: Path,
    background_path: Optional[Path] = None,
) -> Path:
    """
    Compile final 1080x1920 MP4.

    Steps:
      1. Build one text-card ImageClip per scene.
      2. Concatenate clips.
      3. Overlay the TTS audio track.
      4. Export as H.264 MP4.
    """
    import asyncio
    from moviepy.editor import AudioFileClip, concatenate_videoclips  # type: ignore[import]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    hook_text = script_data.get("hook", "")
    segments = script_data.get("segments", [])
    outro_text = script_data.get("outro", "")

    clips = []

    # Hook card (3s)
    if hook_text:
        clips.append(_make_text_frame(hook_text, 3.0))

    # Body segments
    for seg in segments:
        text = seg.get("text", "")
        duration = float(seg.get("duration", 5))
        if text:
            clips.append(_make_text_frame(text, duration))

    # Outro card (3s)
    if outro_text:
        clips.append(_make_text_frame(outro_text, 3.0))

    if not clips:
        raise ValueError("No content clips to compile")

    video = concatenate_videoclips(clips, method="compose")

    # Attach audio — trim/pad to video length
    if audio_path.exists():
        audio = AudioFileClip(str(audio_path))
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        video = video.set_audio(audio)

    # Run blocking moviepy write in executor
    loop = asyncio.get_event_loop()

    def _write() -> None:
        video.write_videofile(
            str(output_path),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_path.parent / "temp_audio.aac"),
            remove_temp=True,
            logger=None,
            threads=4,
        )

    await loop.run_in_executor(None, _write)
    logger.info(f"Video compiled → {output_path}")
    return output_path
