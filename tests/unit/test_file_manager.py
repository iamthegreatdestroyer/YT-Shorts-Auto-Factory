"""
Unit tests for file management utilities.
"""
from __future__ import annotations

import asyncio
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import StorageError


class TestEnsureDirectoryErrors:
    """Test ensure_directory error paths (success already in test_utils.py)."""

    def test_raises_storage_error_on_failure(self, tmp_path):
        from src.utils.file_manager import ensure_directory

        # Mock mkdir to raise OSError
        with patch.object(Path, "mkdir", side_effect=OSError("permission denied")):
            with pytest.raises(StorageError):
                ensure_directory(tmp_path / "new_dir")


class TestGetFileSizeHuman:
    """Test get_file_size_human function."""

    def test_bytes(self, tmp_path):
        from src.utils.file_manager import get_file_size_human
        f = tmp_path / "small.txt"
        f.write_bytes(b"x" * 500)
        result = get_file_size_human(f)
        assert "B" in result

    def test_kilobytes(self, tmp_path):
        from src.utils.file_manager import get_file_size_human
        f = tmp_path / "medium.txt"
        f.write_bytes(b"x" * 2048)
        result = get_file_size_human(f)
        assert "KB" in result or "B" in result

    def test_megabytes(self, tmp_path):
        from src.utils.file_manager import get_file_size_human
        f = tmp_path / "large.txt"
        f.write_bytes(b"x" * (2 * 1024 * 1024))
        result = get_file_size_human(f)
        assert "MB" in result

    def test_nonexistent_file(self, tmp_path):
        from src.utils.file_manager import get_file_size_human
        result = get_file_size_human(tmp_path / "missing.txt")
        assert result == "0.0 B"


class TestGetAvailableSpace:
    """Test get_available_space function."""

    def test_returns_positive_integer(self, tmp_path):
        from src.utils.file_manager import get_available_space
        space = get_available_space(tmp_path)
        assert isinstance(space, int)
        assert space > 0

    def test_nonexistent_path_uses_parent(self, tmp_path):
        from src.utils.file_manager import get_available_space
        # Path doesn't exist but parent does → should still work
        nonexistent = tmp_path / "new_subdir" / "nested"
        space = get_available_space(nonexistent)
        assert space > 0


class TestCleanupOldFiles:
    """Test cleanup_old_files function."""

    def test_missing_directory_returns_zero(self, tmp_path):
        from src.utils.file_manager import cleanup_old_files
        result = cleanup_old_files(tmp_path / "missing", max_age_days=1)
        assert result == 0

    def test_dry_run_does_not_delete(self, tmp_path):
        from src.utils.file_manager import cleanup_old_files
        f = tmp_path / "old.txt"
        f.write_text("content")
        # Backdate modified time
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(str(f), (old_time, old_time))

        count = cleanup_old_files(tmp_path, max_age_days=5, dry_run=True)
        assert count == 1
        assert f.exists()  # Not deleted

    def test_deletes_old_files(self, tmp_path):
        from src.utils.file_manager import cleanup_old_files
        f = tmp_path / "old.txt"
        f.write_text("content")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(str(f), (old_time, old_time))

        count = cleanup_old_files(tmp_path, max_age_days=5)
        assert count == 1
        assert not f.exists()

    def test_keeps_new_files(self, tmp_path):
        from src.utils.file_manager import cleanup_old_files
        new_file = tmp_path / "new.txt"
        new_file.write_text("content")

        count = cleanup_old_files(tmp_path, max_age_days=5)
        assert count == 0
        assert new_file.exists()

    def test_extension_filter(self, tmp_path):
        from src.utils.file_manager import cleanup_old_files
        mp4 = tmp_path / "old.mp4"
        txt = tmp_path / "old.txt"
        mp4.write_bytes(b"video")
        txt.write_text("text")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(str(mp4), (old_time, old_time))
        os.utime(str(txt), (old_time, old_time))

        count = cleanup_old_files(tmp_path, max_age_days=5, extensions=[".mp4"])
        assert count == 1
        assert not mp4.exists()
        assert txt.exists()

    def test_skips_directories(self, tmp_path):
        from src.utils.file_manager import cleanup_old_files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(str(subdir), (old_time, old_time))

        count = cleanup_old_files(tmp_path, max_age_days=5)
        assert count == 0


class TestArchiveFile:
    """Test archive_file function."""

    def test_basic_archive(self, tmp_path):
        from src.utils.file_manager import archive_file
        src = tmp_path / "video.mp4"
        src.write_bytes(b"video content")
        archive_dir = tmp_path / "archive"

        dest = archive_file(src, archive_dir)
        assert dest.exists()
        assert not src.exists()

    def test_timestamp_prefix(self, tmp_path):
        from src.utils.file_manager import archive_file
        src = tmp_path / "video.mp4"
        src.write_bytes(b"video content")
        archive_dir = tmp_path / "archive"

        dest = archive_file(src, archive_dir, add_timestamp=True)
        assert "_video.mp4" in dest.name

    def test_no_timestamp(self, tmp_path):
        from src.utils.file_manager import archive_file
        src = tmp_path / "video.mp4"
        src.write_bytes(b"video content")
        archive_dir = tmp_path / "archive"

        dest = archive_file(src, archive_dir, add_timestamp=False)
        assert dest.name == "video.mp4"

    def test_collision_handled(self, tmp_path):
        from src.utils.file_manager import archive_file
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        # Pre-create the destination
        existing = archive_dir / "video.mp4"
        existing.write_bytes(b"existing")

        src = tmp_path / "video.mp4"
        src.write_bytes(b"new content")

        dest = archive_file(src, archive_dir, add_timestamp=False)
        assert dest.exists()
        # Should have a counter suffix
        assert dest.name != "video.mp4"

    def test_missing_source_raises(self, tmp_path):
        from src.utils.file_manager import archive_file
        with pytest.raises(StorageError):
            archive_file(tmp_path / "missing.mp4", tmp_path / "archive")


class TestSafeDelete:
    """Test safe_delete function."""

    def test_deletes_file(self, tmp_path):
        from src.utils.file_manager import safe_delete
        f = tmp_path / "file.txt"
        f.write_text("content")
        result = safe_delete(f)
        assert result is True
        assert not f.exists()

    def test_deletes_directory(self, tmp_path):
        from src.utils.file_manager import safe_delete
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("x")
        result = safe_delete(subdir)
        assert result is True
        assert not subdir.exists()

    def test_missing_file_ignore(self, tmp_path):
        from src.utils.file_manager import safe_delete
        result = safe_delete(tmp_path / "missing.txt", ignore_missing=True)
        assert result is False

    def test_missing_file_raise(self, tmp_path):
        from src.utils.file_manager import safe_delete
        with pytest.raises(StorageError):
            safe_delete(tmp_path / "missing.txt", ignore_missing=False)


class TestGetUniqueFilename:
    """Test get_unique_filename function."""

    def test_no_conflict(self, tmp_path):
        from src.utils.file_manager import get_unique_filename
        result = get_unique_filename(tmp_path, "video", "mp4")
        assert result == tmp_path / "video.mp4"

    def test_conflict_adds_counter(self, tmp_path):
        from src.utils.file_manager import get_unique_filename
        existing = tmp_path / "video.mp4"
        existing.write_bytes(b"existing")
        result = get_unique_filename(tmp_path, "video", "mp4")
        assert result != existing
        assert "001" in result.name

    def test_multiple_conflicts(self, tmp_path):
        from src.utils.file_manager import get_unique_filename
        (tmp_path / "video.mp4").write_bytes(b"1")
        (tmp_path / "video_001.mp4").write_bytes(b"2")
        result = get_unique_filename(tmp_path, "video", "mp4")
        assert "002" in result.name

    def test_extension_without_dot(self, tmp_path):
        from src.utils.file_manager import get_unique_filename
        result = get_unique_filename(tmp_path, "video", "mp4")
        assert result.suffix == ".mp4"


class TestComputeFileHash:
    """Test compute_file_hash function."""

    def test_md5_hash(self, tmp_path):
        from src.utils.file_manager import compute_file_hash
        f = tmp_path / "file.txt"
        f.write_text("hello world")
        result = compute_file_hash(f, algorithm="md5")
        assert len(result) == 32  # MD5 hex digest length
        assert result == compute_file_hash(f, algorithm="md5")  # Deterministic

    def test_sha256_hash(self, tmp_path):
        from src.utils.file_manager import compute_file_hash
        f = tmp_path / "file.txt"
        f.write_text("hello world")
        result = compute_file_hash(f, algorithm="sha256")
        assert len(result) == 64

    def test_missing_file_raises(self, tmp_path):
        from src.utils.file_manager import compute_file_hash
        with pytest.raises(StorageError):
            compute_file_hash(tmp_path / "missing.txt")


class TestDownloadFile:
    """Test download_file async function."""

    @pytest.mark.asyncio
    async def test_successful_download(self, tmp_path):
        from src.utils.file_manager import download_file

        mock_response = AsyncMock()
        mock_response.headers = {"content-length": "11"}
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        async def mock_iter_chunked(chunk_size):
            yield b"hello world"

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=mock_response)

        dest = tmp_path / "downloaded.txt"
        with patch("src.utils.file_manager.aiohttp.ClientSession", return_value=mock_session):
            result = await download_file("https://example.com/file.txt", dest)
        assert result == dest

    @pytest.mark.asyncio
    async def test_download_with_progress_callback(self, tmp_path):
        from src.utils.file_manager import download_file

        progress_calls = []

        def progress_cb(downloaded, total):
            progress_calls.append((downloaded, total))

        mock_response = AsyncMock()
        mock_response.headers = {"content-length": "5"}
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        async def mock_iter_chunked(chunk_size):
            yield b"hello"

        mock_response.content.iter_chunked = mock_iter_chunked

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=mock_response)

        dest = tmp_path / "downloaded.txt"
        with patch("src.utils.file_manager.aiohttp.ClientSession", return_value=mock_session):
            await download_file(
                "https://example.com/file.txt",
                dest,
                progress_callback=progress_cb,
            )
        assert len(progress_calls) > 0

    @pytest.mark.asyncio
    async def test_download_client_error(self, tmp_path):
        from src.utils.file_manager import download_file
        import aiohttp as aiohttp_mod

        # session.get() is sync, returning async ctx mgr that raises on __aenter__
        error_ctx = MagicMock()
        error_ctx.__aenter__ = AsyncMock(side_effect=aiohttp_mod.ClientConnectionError("refused"))
        error_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=error_ctx)

        dest = tmp_path / "failed.txt"
        with patch("src.utils.file_manager.aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(StorageError):
                await download_file("https://example.com/file.txt", dest)

    @pytest.mark.asyncio
    async def test_download_timeout(self, tmp_path):
        from src.utils.file_manager import download_file

        error_ctx = MagicMock()
        error_ctx.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        error_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=error_ctx)

        dest = tmp_path / "timeout.txt"
        with patch("src.utils.file_manager.aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(StorageError):
                await download_file("https://example.com/file.txt", dest)


class TestCopyFile:
    """Test copy_file function."""

    def test_basic_copy(self, tmp_path):
        from src.utils.file_manager import copy_file
        src = tmp_path / "source.txt"
        src.write_text("content")
        dest = tmp_path / "dest.txt"

        result = copy_file(src, dest)
        assert result == dest
        assert dest.exists()
        assert dest.read_text() == "content"

    def test_overwrite_true(self, tmp_path):
        from src.utils.file_manager import copy_file
        src = tmp_path / "source.txt"
        src.write_text("new content")
        dest = tmp_path / "dest.txt"
        dest.write_text("old content")

        copy_file(src, dest, overwrite=True)
        assert dest.read_text() == "new content"

    def test_overwrite_false_raises(self, tmp_path):
        from src.utils.file_manager import copy_file
        src = tmp_path / "source.txt"
        src.write_text("content")
        dest = tmp_path / "dest.txt"
        dest.write_text("existing")

        with pytest.raises(StorageError):
            copy_file(src, dest, overwrite=False)

    def test_missing_source_raises(self, tmp_path):
        from src.utils.file_manager import copy_file
        with pytest.raises(StorageError):
            copy_file(tmp_path / "missing.txt", tmp_path / "dest.txt")

    def test_creates_parent_dir(self, tmp_path):
        from src.utils.file_manager import copy_file
        src = tmp_path / "source.txt"
        src.write_text("content")
        dest = tmp_path / "nested" / "dest.txt"

        copy_file(src, dest)
        assert dest.exists()


class TestGetDirectorySize:
    """Test get_directory_size function."""

    def test_empty_directory(self, tmp_path):
        from src.utils.file_manager import get_directory_size
        assert get_directory_size(tmp_path) == 0

    def test_with_files(self, tmp_path):
        from src.utils.file_manager import get_directory_size
        (tmp_path / "a.txt").write_bytes(b"x" * 100)
        (tmp_path / "b.txt").write_bytes(b"y" * 200)
        size = get_directory_size(tmp_path)
        assert size == 300

    def test_nested_files(self, tmp_path):
        from src.utils.file_manager import get_directory_size
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "file.txt").write_bytes(b"z" * 50)
        size = get_directory_size(tmp_path)
        assert size == 50

    def test_nonexistent_directory(self, tmp_path):
        from src.utils.file_manager import get_directory_size
        assert get_directory_size(tmp_path / "missing") == 0
