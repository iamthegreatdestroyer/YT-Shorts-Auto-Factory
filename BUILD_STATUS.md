# BUILD_STATUS — Sprint 1 Audit

**Date:** 2026-05-29  
**Python:** 3.14.3 (Pillow 10 incompatible → installed Pillow 12.2.0 pre-release)

## Dependency Install

| Package | Status | Notes |
|---------|--------|-------|
| moviepy 1.0.3 | ✅ | Installed |
| ffmpeg-python 0.2.0 | ✅ | Installed |
| Pillow 12.2.0 | ✅ | 10.x fails on Py 3.14; 12.x wheel works |
| google-api-python-client | ✅ | Installed |
| google-auth-oauthlib | ✅ | Installed |
| gtts 2.5.4 | ✅ | Installed |
| edge-tts 7.2.8 | ✅ | Added (free, no API key) |
| pydantic 2.x + pydantic-settings | ✅ | Installed |
| python-dotenv | ✅ | Installed |
| pyyaml | ✅ | Installed |
| apscheduler | ✅ | Installed |
| jinja2 | ✅ | Installed |
| loguru | ✅ | Installed |
| rich | ✅ | Installed |
| tenacity | ✅ | Installed |
| pytest + pytest-asyncio + pytest-mock + pytest-cov | ✅ | Installed |

**Note:** pyproject.toml uses Poetry backend. Install was done via `pip install` of individual packages (no `pip install -r requirements.txt` since project uses pyproject.toml with poetry backend, not compatible with pip editable on Python 3.14).

## Test Results

```
178 passed in 19.47s
```

All unit tests pass:
- test_config.py — 32 passed
- test_script_generator.py — 28 passed  
- test_trend_analyzer.py — 24 passed
- test_trend_models.py — 16 passed
- test_trend_scrapers.py — 25 passed
- test_utils.py — 53 passed

## Required API Keys (.env)

| Key | Required For | Status |
|-----|-------------|--------|
| `YOUTUBE_CLIENT_ID` | YouTube OAuth2 upload | **Must configure** |
| `YOUTUBE_CLIENT_SECRET` | YouTube OAuth2 upload | **Must configure** |
| `OPENAI_API_KEY` | Script generation (optional — template fallback active) | Optional |
| `ELEVENLABS_API_KEY` | Premium TTS (optional — edge-tts is free primary) | Optional |
| `PEXELS_API_KEY` | Stock video backgrounds (optional — solid color fallback active) | Optional |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Trend analysis (optional) | Optional |

**Minimum viable setup:** Only YouTube OAuth credentials required for upload. All other features have free/template fallbacks.

## Pipeline Status (pre-Sprint 2)

| Stage | Status |
|-------|--------|
| Trend Analysis | ⚠️ Placeholder (returns hardcoded topic) |
| Script Generation | ✅ Template engine implemented |
| TTS (voiceover) | ❌ Stub — no implementation |
| Video Compilation | ❌ Stub — no implementation |
| YouTube Upload | ❌ Stub — no implementation |
| Scheduler | ⚠️ APScheduler wired but not running |
