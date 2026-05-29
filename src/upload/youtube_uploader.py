"""
YouTube uploader with OAuth2 and dry-run support.

OAuth flow:
  1. Check credentials/token.json for a cached token.
  2. If missing/expired, open browser for OAuth consent.
  3. Upload via YouTube Data API v3 resumable upload.
  4. With --dry-run: authenticate, then print plan without uploading.
"""

from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import Optional

from loguru import logger


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CREDENTIALS_DIR = Path("credentials")
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CLIENT_SECRETS_PATH = CREDENTIALS_DIR / "client_secrets.json"


def _load_credentials():
    """Load cached OAuth2 credentials or trigger browser flow."""
    from google.oauth2.credentials import Credentials  # type: ignore[import]
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import]
    from google.auth.transport.requests import Request  # type: ignore[import]

    creds = None

    if TOKEN_PATH.exists():
        try:
            with open(TOKEN_PATH) as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token: {e}")

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            creds = None

    if not creds or not creds.valid:
        if not CLIENT_SECRETS_PATH.exists():
            raise FileNotFoundError(
                f"YouTube client secrets not found at {CLIENT_SECRETS_PATH}. "
                "Download OAuth2 credentials from Google Cloud Console and save as "
                "credentials/client_secrets.json"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_PATH), SCOPES)
        creds = flow.run_local_server(port=8080)
        _save_token(creds)

    return creds


def _save_token(creds) -> None:
    """Persist OAuth token to disk."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    logger.debug(f"OAuth token saved → {TOKEN_PATH}")


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    category_id: str = "22",
    privacy_status: str = "private",
    dry_run: bool = False,
) -> Optional[str]:
    """
    Upload video to YouTube.

    Args:
        video_path: Path to the MP4 file.
        title: Video title.
        description: Video description.
        tags: List of tags.
        category_id: YouTube category (22 = People & Blogs).
        privacy_status: "private", "public", or "unlisted".
        dry_run: If True, authenticate but don't upload.

    Returns:
        YouTube video ID, or None on dry_run.
    """
    from googleapiclient.discovery import build  # type: ignore[import]
    from googleapiclient.http import MediaFileUpload  # type: ignore[import]

    creds = _load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    if dry_run:
        logger.info("Dry-run mode — skipping actual upload")
        print(f"\nWould upload: {title}")
        print(f"  File:        {video_path}")
        print(f"  Tags:        {', '.join(tags[:5])}")
        print(f"  Privacy:     {privacy_status}")
        print(f"  Category ID: {category_id}")
        return None

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.debug(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    logger.info(f"Uploaded → https://youtube.com/shorts/{video_id}")
    return video_id
