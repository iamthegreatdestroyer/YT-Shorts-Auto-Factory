"""
File management utilities for the YouTube Shorts Factory.

This module provides utilities for file operations including:
- Directory management
- File size and space checking
- Cleanup and archival operations
- Safe file operations
- Async file downloads

Example:
    >>> from src.utils.file_manager import ensure_directory, get_file_size
    >>> path = ensure_directory(Path("data/temp"))
    >>> size = get_file_size(Path("video.mp4"))
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiohttp

from src.core.exceptions import StorageError


def ensure_directory(path: Path) -> Path:
    """
    Create directory if it doesn't exist.

    Creates the directory and all parent directories as needed.
    Returns the path for method chaining.

    Args:
        path: Directory path to create.

    Returns:
        The same path after ensuring it exists.

    Raises:
        StorageError: If directory creation fails.

    Example:
        >>> ensure_directory(Path("data/cache/trends"))
        PosixPath('data/cache/trends')
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        raise StorageError(
            f"Failed to create directory: {path}",
            context={"path": str(path), "error": str(e)},
        ) from e


def get_file_size(path: Path) -> int:
    """
    Get file size in bytes.

    Args:
        path: Path to the file.

    Returns:
        File size in bytes, or 0 if file doesn't exist.

    Example:
        >>> get_file_size(Path("video.mp4"))
        1048576
    """
    try:
        return path.stat().st_size if path.exists() else 0
    except OSError:
        return 0


def get_file_size_human(path: Path) -> str:
    """
    Get file size in human-readable format.

    Args:
        path: Path to the file.

    Returns:
        Human-readable size string (e.g., "1.5 MB").
    """
    size = get_file_size(path)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def get_available_space(path: Path) -> int:
    """
    Get available disk space in bytes.

    Works cross-platform (Windows, Linux, macOS).

    Args:
        path: Path to check disk space for.

    Returns:
        Available space in bytes.

    Raises:
        StorageError: If unable to determine disk space.

    Example:
        >>> get_available_space(Path("."))
        107374182400  # ~100 GB
    """
    try:
        # Ensure path exists for stat
        check_path = path if path.exists() else path.parent
        while not check_path.exists() and check_path != check_path.parent:
            check_path = check_path.parent

        if os.name == "nt":  # Windows
            import ctypes

            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(str(check_path)),
                None,
                None,
                ctypes.pointer(free_bytes),
            )
            return free_bytes.value
        else:  # Unix-like
            stat = os.statvfs(check_path)
            return stat.f_bavail * stat.f_frsize
    except Exception as e:
        raise StorageError(
            f"Failed to get available disk space for: {path}",
            context={"path": str(path), "error": str(e)},
        ) from e


def cleanup_old_files(
    directory: Path,
    max_age_days: int,
    extensions: Optional[list[str]] = None,
    dry_run: bool = False,
) -> int:
    """
    Delete files older than max_age_days.

    Args:
        directory: Directory to clean up.
        max_age_days: Maximum age in days.
        extensions: Optional list of extensions to filter (e.g., [".mp4", ".tmp"]).
        dry_run: If True, only count files without deleting.

    Returns:
        Count of deleted (or would-be-deleted) files.

    Example:
        >>> cleanup_old_files(Path("data/temp"), max_age_days=7)
        15
    """
    if not directory.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=max_age_days)
    deleted_count = 0

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        # Filter by extension if specified
        if extensions and file_path.suffix.lower() not in extensions:
            continue

        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                if not dry_run:
                    file_path.unlink()
                deleted_count += 1
        except OSError:
            continue

    return deleted_count


def archive_file(
    source: Path,
    archive_dir: Path,
    add_timestamp: bool = True,
) -> Path:
    """
    Move file to archive directory with optional timestamp.

    Args:
        source: Source file path.
        archive_dir: Destination archive directory.
        add_timestamp: Whether to prefix filename with timestamp.

    Returns:
        New path in archive.

    Raises:
        StorageError: If archival fails.

    Example:
        >>> archive_file(Path("video.mp4"), Path("data/archives"))
        PosixPath('data/archives/20240115_120000_video.mp4')
    """
    if not source.exists():
        raise StorageError(
            f"Source file does not exist: {source}",
            context={"source": str(source)},
        )

    ensure_directory(archive_dir)

    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{timestamp}_{source.name}"
    else:
        new_name = source.name

    destination = archive_dir / new_name

    # Handle name collision
    counter = 1
    while destination.exists():
        stem = destination.stem
        destination = archive_dir / f"{stem}_{counter}{destination.suffix}"
        counter += 1

    try:
        shutil.move(str(source), str(destination))
        return destination
    except OSError as e:
        raise StorageError(
            f"Failed to archive file: {source}",
            context={"source": str(source), "destination": str(destination), "error": str(e)},
        ) from e


def safe_delete(path: Path, ignore_missing: bool = True) -> bool:
    """
    Safely delete a file with error handling.

    Args:
        path: Path to delete.
        ignore_missing: If True, don't raise error if file doesn't exist.

    Returns:
        True if deleted, False if skipped.

    Example:
        >>> safe_delete(Path("temp_file.txt"))
        True
    """
    try:
        if path.is_file():
            path.unlink()
            return True
        elif path.is_dir():
            shutil.rmtree(path)
            return True
        elif not ignore_missing:
            raise StorageError(f"Path does not exist: {path}")
        return False
    except OSError as e:
        if not ignore_missing:
            raise StorageError(
                f"Failed to delete: {path}",
                context={"path": str(path), "error": str(e)},
            ) from e
        return False


def get_unique_filename(
    directory: Path,
    base_name: str,
    extension: str,
) -> Path:
    """
    Generate unique filename by adding counter if file exists.

    Args:
        directory: Target directory.
        base_name: Base filename without extension.
        extension: File extension (with or without dot).

    Returns:
        Unique file path.

    Example:
        >>> get_unique_filename(Path("."), "video", "mp4")
        PosixPath('./video.mp4')
        >>> # If video.mp4 exists:
        >>> get_unique_filename(Path("."), "video", "mp4")
        PosixPath('./video_001.mp4')
    """
    # Normalize extension
    if not extension.startswith("."):
        extension = f".{extension}"

    candidate = directory / f"{base_name}{extension}"

    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        candidate = directory / f"{base_name}_{counter:03d}{extension}"
        if not candidate.exists():
            return candidate
        counter += 1
        if counter > 9999:
            raise StorageError(
                f"Too many files with base name: {base_name}",
                context={"directory": str(directory), "base_name": base_name},
            )


def compute_file_hash(path: Path, algorithm: str = "md5") -> str:
    """
    Compute hash of file contents.

    Args:
        path: File path.
        algorithm: Hash algorithm (md5, sha1, sha256).

    Returns:
        Hex digest of file hash.

    Raises:
        StorageError: If file cannot be read.
    """
    hash_func = hashlib.new(algorithm)

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except OSError as e:
        raise StorageError(
            f"Failed to compute hash for: {path}",
            context={"path": str(path), "error": str(e)},
        ) from e


async def download_file(
    url: str,
    destination: Path,
    timeout: int = 30,
    chunk_size: int = 8192,
    progress_callback: Optional[callable] = None,
) -> Path:
    """
    Download file from URL using aiohttp.

    Args:
        url: URL to download from.
        destination: Local path to save file.
        timeout: Request timeout in seconds.
        chunk_size: Download chunk size in bytes.
        progress_callback: Optional callback(downloaded, total) for progress.

    Returns:
        Path to downloaded file.

    Raises:
        StorageError: If download fails.

    Example:
        >>> await download_file("https://example.com/file.mp4", Path("file.mp4"))
        PosixPath('file.mp4')
    """
    ensure_directory(destination.parent)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(destination, "wb") as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size:
                            progress_callback(downloaded, total_size)

        return destination

    except aiohttp.ClientError as e:
        # Clean up partial download
        safe_delete(destination)
        raise StorageError(
            f"Failed to download file from: {url}",
            context={"url": url, "destination": str(destination), "error": str(e)},
        ) from e
    except asyncio.TimeoutError as e:
        safe_delete(destination)
        raise StorageError(
            f"Download timeout for: {url}",
            context={"url": url, "timeout": timeout},
        ) from e


def copy_file(source: Path, destination: Path, overwrite: bool = False) -> Path:
    """
    Copy file to destination.

    Args:
        source: Source file path.
        destination: Destination path.
        overwrite: Whether to overwrite existing file.

    Returns:
        Destination path.

    Raises:
        StorageError: If copy fails.
    """
    if not source.exists():
        raise StorageError(f"Source file does not exist: {source}")

    if destination.exists() and not overwrite:
        raise StorageError(f"Destination already exists: {destination}")

    ensure_directory(destination.parent)

    try:
        shutil.copy2(str(source), str(destination))
        return destination
    except OSError as e:
        raise StorageError(
            f"Failed to copy file: {source} -> {destination}",
            context={"source": str(source), "destination": str(destination), "error": str(e)},
        ) from e


def get_directory_size(directory: Path) -> int:
    """
    Calculate total size of directory contents.

    Args:
        directory: Directory path.

    Returns:
        Total size in bytes.
    """
    if not directory.exists():
        return 0

    total = 0
    for path in directory.rglob("*"):
        if path.is_file():
            total += get_file_size(path)
    return total
