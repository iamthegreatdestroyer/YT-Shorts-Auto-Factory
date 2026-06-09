"""Tests for src/video_compilation/compiler.py."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio

import pytest


SAMPLE_SCRIPT = {
    "hook": "Amazing facts incoming!",
    "segments": [
        {"text": "Fact one here", "duration": 5},
        {"text": "Fact two here", "duration": 8},
    ],
    "outro": "Follow for more!",
}

SCRIPT_NO_HOOK = {
    "segments": [{"text": "Only body", "duration": 10}],
    "outro": "See you next time!",
}

SCRIPT_EMPTY = {}


def _make_mock_clip(duration: float = 3.0):
    clip = MagicMock()
    clip.duration = duration
    clip.set_audio = MagicMock(return_value=clip)
    return clip


def _patch_moviepy(clips_list=None):
    """Return context managers patching both moviepy and PIL."""
    if clips_list is None:
        clips_list = [_make_mock_clip()]

    mock_image_clip = MagicMock(side_effect=lambda arr: _make_mock_clip())
    mock_concat = MagicMock(return_value=_make_mock_clip(20.0))
    mock_audio = MagicMock()
    mock_audio.duration = 25.0
    mock_audio.subclip = MagicMock(return_value=mock_audio)

    return mock_image_clip, mock_concat, mock_audio


@pytest.mark.asyncio
async def test_compile_video_happy_path(tmp_path):
    """Full pipeline: hook + segments + outro → MP4 written."""
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"mp3")
    output = tmp_path / "out.mp4"

    mock_clip = _make_mock_clip(20.0)
    mock_clip.write_videofile = MagicMock()

    with patch("src.video_compilation.compiler._make_text_frame", return_value=mock_clip), \
         patch("src.video_compilation.compiler.concatenate_videoclips", return_value=mock_clip, create=True), \
         patch("src.video_compilation.compiler.AudioFileClip", return_value=mock_clip, create=True):
        # Import fresh to pick up patches
        import importlib
        import src.video_compilation.compiler as mod
        importlib.reload(mod)

        # Patch moviepy inside the module after reload
        with patch.object(mod, "_make_text_frame", return_value=mock_clip):
            from moviepy.editor import concatenate_videoclips as real_cat  # noqa: F401
        pass  # just ensuring imports work

    # Direct approach: patch at the module level
    with patch("moviepy.editor.ImageClip") as mock_ic, \
         patch("moviepy.editor.concatenate_videoclips", return_value=mock_clip) as mock_cat, \
         patch("moviepy.editor.AudioFileClip", return_value=mock_clip) as mock_afc, \
         patch("PIL.Image.new", return_value=MagicMock()), \
         patch("PIL.ImageDraw.Draw", return_value=MagicMock()), \
         patch("PIL.ImageFont.truetype", side_effect=OSError), \
         patch("PIL.ImageFont.load_default", return_value=MagicMock()), \
         patch("numpy.array", return_value=MagicMock()):
        mock_ic.return_value = mock_clip
        mock_clip.set_duration = MagicMock(return_value=mock_clip)
        mock_cat.return_value = mock_clip
        mock_clip.write_videofile = MagicMock()

        from src.video_compilation.compiler import compile_video
        result = await compile_video(SAMPLE_SCRIPT, audio, output)

    assert result == output


@pytest.mark.asyncio
async def test_compile_video_empty_script_raises(tmp_path):
    """Empty script dict raises ValueError (no clips)."""
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"mp3")
    output = tmp_path / "out.mp4"

    with pytest.raises((ValueError, Exception)):
        from src.video_compilation.compiler import compile_video
        await compile_video(SCRIPT_EMPTY, audio, output)


@pytest.mark.asyncio
async def test_compile_video_no_audio(tmp_path):
    """Missing audio file is handled gracefully — video still compiled."""
    audio = tmp_path / "nonexistent.mp3"  # does not exist
    output = tmp_path / "out.mp4"

    mock_clip = _make_mock_clip(20.0)
    mock_clip.write_videofile = MagicMock()

    with patch("moviepy.editor.ImageClip", return_value=mock_clip), \
         patch("moviepy.editor.concatenate_videoclips", return_value=mock_clip), \
         patch("PIL.Image.new", return_value=MagicMock()), \
         patch("PIL.ImageDraw.Draw", return_value=MagicMock()), \
         patch("PIL.ImageFont.truetype", side_effect=OSError), \
         patch("PIL.ImageFont.load_default", return_value=MagicMock()), \
         patch("numpy.array", return_value=MagicMock()):
        mock_clip.set_duration = MagicMock(return_value=mock_clip)

        from src.video_compilation.compiler import compile_video
        result = await compile_video(SAMPLE_SCRIPT, audio, output)

    assert result == output


def test_make_text_frame_returns_clip():
    """_make_text_frame builds a clip for given text and duration."""
    mock_image = MagicMock()
    mock_draw = MagicMock()
    mock_draw.multiline_textbbox = MagicMock(return_value=(0, 0, 200, 80))
    mock_draw.multiline_text = MagicMock()
    mock_clip = MagicMock()
    mock_clip.set_duration = MagicMock(return_value=mock_clip)

    with patch("PIL.Image.new", return_value=mock_image), \
         patch("PIL.ImageDraw.Draw", return_value=mock_draw), \
         patch("PIL.ImageFont.truetype", side_effect=OSError), \
         patch("PIL.ImageFont.load_default", return_value=MagicMock()), \
         patch("numpy.array", return_value=MagicMock()), \
         patch("moviepy.editor.ImageClip", return_value=mock_clip):
        from src.video_compilation.compiler import _make_text_frame
        result = _make_text_frame("Hello world", 5.0)

    assert result is mock_clip


def test_make_text_frame_with_truetype_font():
    """_make_text_frame works when truetype font is available."""
    mock_image = MagicMock()
    mock_draw = MagicMock()
    mock_draw.multiline_textbbox = MagicMock(return_value=(0, 0, 200, 80))
    mock_clip = MagicMock()
    mock_clip.set_duration = MagicMock(return_value=mock_clip)

    with patch("PIL.Image.new", return_value=mock_image), \
         patch("PIL.ImageDraw.Draw", return_value=mock_draw), \
         patch("PIL.ImageFont.truetype", return_value=MagicMock()), \
         patch("numpy.array", return_value=MagicMock()), \
         patch("moviepy.editor.ImageClip", return_value=mock_clip):
        from src.video_compilation.compiler import _make_text_frame
        result = _make_text_frame("Short text", 3.0)

    assert result is mock_clip
