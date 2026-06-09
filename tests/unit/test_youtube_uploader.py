"""Tests for src/upload/youtube_uploader.py."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


@pytest.fixture
def mock_credentials():
    """Returns a valid-looking MagicMock credentials object."""
    creds = MagicMock()
    creds.valid = True
    creds.expired = False
    creds.refresh_token = "refresh_token"
    creds.to_json = MagicMock(return_value='{"token": "test"}')
    return creds


def test_upload_video_dry_run_no_credentials(tmp_path, capsys):
    """dry_run=True with missing credentials still prints the plan (no error raised)."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")

    with patch("src.upload.youtube_uploader.TOKEN_PATH", tmp_path / "token.json"), \
         patch("src.upload.youtube_uploader.CLIENT_SECRETS_PATH", tmp_path / "secrets.json"):
        from src.upload.youtube_uploader import upload_video
        result = upload_video(
            video_path=video,
            title="Test Title",
            description="Test Desc",
            tags=["test"],
            dry_run=True,
        )

    assert result is None
    captured = capsys.readouterr()
    assert "Test Title" in captured.out


def test_upload_video_dry_run_with_cached_token(tmp_path, mock_credentials, capsys):
    """dry_run=True with a cached valid token loads credentials and prints plan."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")

    token_path = tmp_path / "token.json"
    token_path.write_text('{"token": "test", "scopes": []}')

    with patch("src.upload.youtube_uploader.TOKEN_PATH", token_path), \
         patch("src.upload.youtube_uploader.CLIENT_SECRETS_PATH", tmp_path / "secrets.json"), \
         patch("google.oauth2.credentials.Credentials.from_authorized_user_info",
               return_value=mock_credentials):
        from src.upload import youtube_uploader as mod
        import importlib; importlib.reload(mod)

        result = mod.upload_video(
            video_path=video,
            title="Dry Run Video",
            description="Desc",
            tags=["tag1", "tag2"],
            dry_run=True,
        )

    assert result is None


def test_upload_video_real_upload(tmp_path, mock_credentials):
    """Real upload path calls YouTube API and returns video_id."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")

    mock_youtube = MagicMock()
    mock_request = MagicMock()
    mock_request.next_chunk = MagicMock(return_value=(None, {"id": "abc123"}))
    mock_youtube.videos.return_value.insert.return_value = mock_request

    with patch("src.upload.youtube_uploader._load_credentials", return_value=mock_credentials), \
         patch("googleapiclient.discovery.build", return_value=mock_youtube), \
         patch("googleapiclient.http.MediaFileUpload"):
        from src.upload.youtube_uploader import upload_video
        result = upload_video(
            video_path=video,
            title="My Video",
            description="My Desc",
            tags=["a", "b"],
            dry_run=False,
        )

    assert result == "abc123"


def test_upload_video_truncates_long_title(tmp_path, mock_credentials):
    """Title is truncated to 100 chars as required by YouTube API."""
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")
    long_title = "X" * 200

    captured_body = {}

    mock_youtube = MagicMock()

    def _capture_insert(part, body, media_body):
        captured_body.update(body)
        req = MagicMock()
        req.next_chunk = MagicMock(return_value=(None, {"id": "vid999"}))
        return req

    mock_youtube.videos.return_value.insert = _capture_insert

    with patch("src.upload.youtube_uploader._load_credentials", return_value=mock_credentials), \
         patch("googleapiclient.discovery.build", return_value=mock_youtube), \
         patch("googleapiclient.http.MediaFileUpload"):
        from src.upload.youtube_uploader import upload_video
        upload_video(video, long_title, "desc", [], dry_run=False)

    assert len(captured_body["snippet"]["title"]) == 100


def test_save_token(tmp_path, mock_credentials):
    """_save_token writes credentials JSON to TOKEN_PATH."""
    token_path = tmp_path / "token.json"

    with patch("src.upload.youtube_uploader.TOKEN_PATH", token_path), \
         patch("src.upload.youtube_uploader.CREDENTIALS_DIR", tmp_path):
        from src.upload.youtube_uploader import _save_token
        _save_token(mock_credentials)

    assert token_path.exists()
    data = token_path.read_text()
    assert "token" in data


def test_load_credentials_missing_token_and_secrets(tmp_path):
    """Missing both token and secrets → FileNotFoundError."""
    with patch("src.upload.youtube_uploader.TOKEN_PATH", tmp_path / "no_token.json"), \
         patch("src.upload.youtube_uploader.CLIENT_SECRETS_PATH", tmp_path / "no_secrets.json"):
        from src.upload.youtube_uploader import _load_credentials
        with pytest.raises(FileNotFoundError):
            _load_credentials()


def test_load_credentials_expired_token_refresh(tmp_path, mock_credentials):
    """Expired token with refresh_token triggers a refresh call."""
    token_path = tmp_path / "token.json"
    token_path.write_text('{"token": "old"}')

    mock_credentials.valid = False
    mock_credentials.expired = True
    mock_credentials.refresh_token = "rt"

    # After refresh, mark as valid
    def _refresh(req):
        mock_credentials.valid = True

    mock_credentials.refresh = MagicMock(side_effect=_refresh)

    with patch("src.upload.youtube_uploader.TOKEN_PATH", token_path), \
         patch("src.upload.youtube_uploader.CLIENT_SECRETS_PATH", tmp_path / "no.json"), \
         patch("src.upload.youtube_uploader._save_token"), \
         patch("google.oauth2.credentials.Credentials.from_authorized_user_info",
               return_value=mock_credentials), \
         patch("google.auth.transport.requests.Request"):
        from src.upload import youtube_uploader as mod
        import importlib; importlib.reload(mod)
        result = mod._load_credentials()

    assert result is mock_credentials
