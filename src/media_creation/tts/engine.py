"""
TTS engine using edge-tts (primary, free) with gTTS fallback.
Outputs MP3 to a given path.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from loguru import logger


async def synthesize(text: str, output_path: Path, voice: str = "en-US-JennyNeural") -> Path:
    """
    Convert text to speech, write MP3 to output_path.

    Tries edge-tts first; falls back to gTTS if edge-tts fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import edge_tts  # type: ignore[import]

        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(str(output_path))
        logger.info(f"TTS (edge-tts) → {output_path}")
        return output_path

    except Exception as e:
        logger.warning(f"edge-tts failed ({e}), falling back to gTTS")
        return await _gtts_fallback(text, output_path)


async def _gtts_fallback(text: str, output_path: Path) -> Path:
    """gTTS fallback — runs in thread executor to avoid blocking."""
    from gtts import gTTS  # type: ignore[import]

    def _run() -> None:
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(output_path))

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run)
    logger.info(f"TTS (gTTS fallback) → {output_path}")
    return output_path
