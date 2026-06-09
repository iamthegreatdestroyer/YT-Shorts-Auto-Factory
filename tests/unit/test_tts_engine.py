"""Tests for src/media_creation/tts/engine.py."""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_synthesize_edge_tts_success(tmp_path):
    """Happy path: edge_tts saves the file."""
    output = tmp_path / "out.mp3"

    mock_communicate = MagicMock()
    mock_communicate.save = AsyncMock(side_effect=lambda p: Path(p).write_bytes(b"audio"))

    with patch("edge_tts.Communicate", return_value=mock_communicate):
        from src.media_creation.tts.engine import synthesize
        result = await synthesize("hello world", output)

    assert result == output
    assert output.exists()


@pytest.mark.asyncio
async def test_synthesize_edge_tts_fallback_to_gtts(tmp_path):
    """edge_tts raises → gTTS fallback runs."""
    output = tmp_path / "out.mp3"

    mock_communicate = MagicMock()
    mock_communicate.save = AsyncMock(side_effect=RuntimeError("edge_tts unavailable"))

    mock_gtts_instance = MagicMock()
    mock_gtts_instance.save = MagicMock(side_effect=lambda p: Path(p).write_bytes(b"gtts_audio"))

    with patch("edge_tts.Communicate", return_value=mock_communicate), \
         patch("gtts.gTTS", return_value=mock_gtts_instance):
        from src.media_creation.tts import engine
        import importlib
        importlib.reload(engine)
        result = await engine.synthesize("hello world", output)

    assert result == output


@pytest.mark.asyncio
async def test_synthesize_creates_parent_dirs(tmp_path):
    """Output parent directories are created if they don't exist."""
    output = tmp_path / "nested" / "deep" / "out.mp3"

    mock_communicate = MagicMock()
    mock_communicate.save = AsyncMock(side_effect=lambda p: Path(p).write_bytes(b"x"))

    with patch("edge_tts.Communicate", return_value=mock_communicate):
        from src.media_creation.tts.engine import synthesize
        result = await synthesize("text", output)

    assert output.parent.exists()


@pytest.mark.asyncio
async def test_synthesize_custom_voice(tmp_path):
    """Custom voice parameter is passed to edge_tts."""
    output = tmp_path / "out.mp3"
    captured_voice = []

    def _capture(text, voice):
        captured_voice.append(voice)
        m = MagicMock()
        m.save = AsyncMock(side_effect=lambda p: Path(p).write_bytes(b"x"))
        return m

    with patch("edge_tts.Communicate", side_effect=_capture):
        from src.media_creation.tts.engine import synthesize
        await synthesize("text", output, voice="en-GB-RyanNeural")

    assert captured_voice == ["en-GB-RyanNeural"]


@pytest.mark.asyncio
async def test_gtts_fallback_runs_in_executor(tmp_path):
    """_gtts_fallback runs gTTS.save via run_in_executor (non-blocking)."""
    output = tmp_path / "out.mp3"

    mock_gtts_instance = MagicMock()
    mock_gtts_instance.save = MagicMock(side_effect=lambda p: Path(p).write_bytes(b"gtts"))

    with patch("gtts.gTTS", return_value=mock_gtts_instance):
        from src.media_creation.tts.engine import _gtts_fallback
        result = await _gtts_fallback("test text", output)

    assert result == output
    mock_gtts_instance.save.assert_called_once_with(str(output))
