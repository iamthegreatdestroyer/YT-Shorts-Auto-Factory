"""
Pytest configuration and shared fixtures.

This module provides:
- Common test fixtures (config, temp directories, sample files)
- Mock objects for external services
- Test utilities and helpers
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# Async Event Loop
# =============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def test_config():
    """
    Create minimal test configuration.

    Uses temporary directories and test-safe settings.
    """
    from src.core.config import Settings

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a test settings instance with minimal config
        settings = Settings(
            app_name="YT Shorts Factory Test",
            environment="testing",
            debug=True,
            log_level="DEBUG",
            # Use temp directories
            data_dir=temp_path / "data",
            assets_dir=temp_path / "assets",
            logs_dir=temp_path / "logs",
            # Disable actual uploads
            youtube_enabled=False,
        )

        # Create required directories
        (temp_path / "data").mkdir(parents=True, exist_ok=True)
        (temp_path / "assets").mkdir(parents=True, exist_ok=True)
        (temp_path / "logs").mkdir(parents=True, exist_ok=True)

        yield settings


@pytest.fixture
def minimal_config():
    """Create absolute minimal config for unit tests."""
    return {
        "app_name": "Test",
        "environment": "testing",
        "debug": True,
    }


# =============================================================================
# Temporary Directory Fixtures
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test files.

    Directory is automatically cleaned up after test.
    """
    with tempfile.TemporaryDirectory(prefix="yt_shorts_test_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("test content")
    yield file_path


# =============================================================================
# Sample Media Files
# =============================================================================


@pytest.fixture
def sample_video_path(temp_dir: Path) -> Path:
    """
    Create a minimal valid video file for testing.

    Note: This creates a dummy file, not a real video.
    For actual video testing, use proper test fixtures.
    """
    video_path = temp_dir / "test_video.mp4"
    # Create minimal MP4 file signature
    video_path.write_bytes(
        b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00"
        + b"isomiso2mp41" + b"\x00" * 1000
    )
    return video_path


@pytest.fixture
def sample_audio_path(temp_dir: Path) -> Path:
    """Create a minimal audio file for testing."""
    audio_path = temp_dir / "test_audio.mp3"
    # Create minimal MP3 file signature
    audio_path.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1000)
    return audio_path


@pytest.fixture
def sample_image_path(temp_dir: Path) -> Path:
    """Create a minimal PNG image for testing."""
    image_path = temp_dir / "test_image.png"
    # Minimal PNG signature
    png_signature = (
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        b"\x00\x00\x00\rIHDR"  # IHDR chunk
        b"\x00\x00\x00\x01"  # Width: 1
        b"\x00\x00\x00\x01"  # Height: 1
        b"\x08\x02"  # Bit depth: 8, Color type: RGB
        b"\x00\x00\x00"  # Compression, Filter, Interlace
        b"\x90wS\xde"  # CRC
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01"  # IDAT
        b"\x00\x18\xdd\x8d\xb4"  # CRC
        b"\x00\x00\x00\x00IEND\xaeB`\x82"  # IEND
    )
    image_path.write_bytes(png_signature)
    return image_path


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_youtube_client():
    """
    Create mock YouTube API client.

    Returns a MagicMock with expected methods pre-configured.
    """
    client = MagicMock()

    # Mock videos().insert()
    insert_response = {
        "id": "test_video_id",
        "snippet": {
            "title": "Test Video",
            "description": "Test Description",
        },
        "status": {
            "uploadStatus": "processed",
            "privacyStatus": "private",
        },
    }
    client.videos.return_value.insert.return_value.execute.return_value = (
        insert_response
    )

    # Mock videos().list()
    list_response = {
        "items": [insert_response],
    }
    client.videos.return_value.list.return_value.execute.return_value = (
        list_response
    )

    return client


@pytest.fixture
def mock_tts_engine():
    """Create mock TTS engine."""
    engine = MagicMock()
    engine.synthesize = AsyncMock(return_value=b"audio_data")
    engine.get_duration = MagicMock(return_value=30.0)
    return engine


@pytest.fixture
def mock_image_generator():
    """Create mock image generator."""
    generator = MagicMock()
    generator.generate = AsyncMock(return_value=b"image_data")
    return generator


# =============================================================================
# Logging Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """
    Set up minimal logging for tests.

    Captures logs for assertion.
    """
    import logging

    logging.getLogger("src").setLevel(logging.DEBUG)
    yield


@pytest.fixture
def capture_logs(caplog):
    """Fixture to capture and return log records."""
    caplog.set_level("DEBUG")
    yield caplog


# =============================================================================
# Data Fixtures
# =============================================================================


@pytest.fixture
def sample_trend_data():
    """Sample trend data for testing."""
    return {
        "topic": "Test Topic",
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "score": 85.5,
        "source": "youtube",
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_script_data():
    """Sample script data for testing."""
    return {
        "title": "Test Video Title",
        "hook": "This is an attention-grabbing hook!",
        "sections": [
            {"text": "Section 1 content", "duration": 10.0},
            {"text": "Section 2 content", "duration": 15.0},
            {"text": "Section 3 content", "duration": 10.0},
        ],
        "call_to_action": "Like and subscribe!",
        "total_duration": 35.0,
    }


@pytest.fixture
def sample_metadata():
    """Sample video metadata for testing."""
    return {
        "title": "Test Video | Amazing Content #shorts",
        "description": "This is a test video description.\n\n#shorts #test",
        "tags": ["shorts", "test", "youtube"],
        "category_id": "22",
        "privacy_status": "private",
    }


# =============================================================================
# Pipeline Fixtures
# =============================================================================


@pytest.fixture
def mock_pipeline_stages():
    """Create mocks for all pipeline stages."""
    return {
        "trend_analyzer": AsyncMock(),
        "script_generator": AsyncMock(),
        "tts_engine": AsyncMock(),
        "image_generator": AsyncMock(),
        "video_compiler": AsyncMock(),
        "metadata_optimizer": AsyncMock(),
        "uploader": AsyncMock(),
    }


# =============================================================================
# Network Fixtures
# =============================================================================


@pytest.fixture
def mock_aiohttp_session():
    """Create mock aiohttp session for network tests."""
    session = MagicMock()
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"status": "ok"})
    response.text = AsyncMock(return_value="OK")
    response.read = AsyncMock(return_value=b"content")

    session.get = AsyncMock(return_value=response)
    session.post = AsyncMock(return_value=response)

    return session


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def clean_env():
    """
    Fixture that cleans environment variables before and after test.

    Use this when testing environment-dependent code.
    """
    # Store original env
    original_env = os.environ.copy()

    # Clear YT Shorts related env vars
    yt_vars = [k for k in os.environ if k.startswith("YT_SHORTS_")]
    for var in yt_vars:
        del os.environ[var]

    yield

    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


# =============================================================================
# Markers
# =============================================================================


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "network: marks tests requiring network")
    config.addinivalue_line("markers", "youtube: marks tests requiring YouTube API")
