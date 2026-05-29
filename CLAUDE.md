# YT-Shorts-Auto-Factory — Autonomous Completion Brief

## Project Identity
- **Repo:** `iamthegreatdestroyer/YT-Shorts-Auto-Factory`
- **Local path:** `S:\YT-Shorts-Auto-Factory`
- **Language:** Python 3.11+
- **Castle Layer:** Layer 7 — Crown Services (Content Automation)
- **Current completion:** ~45%
- **Mission:** Fully autonomous YouTube Shorts generation + upload system — zero manual intervention after initial setup, AI-driven content creation in 15–60 second video format

## Sprint Plan

### Sprint 1 — Dependency & Config Audit (Day 1)
```
@APEX run: pip install -r requirements.txt (or pyproject.toml if present)
If it fails, fix dependency conflicts. Then: python -m pytest tests/ -x
Report what passes and what fails in BUILD_STATUS.md.

Check for required config files: .env.example, config.yaml, credentials/.
Create .env from .env.example, document which API keys are needed:
  - YOUTUBE_CLIENT_ID + YOUTUBE_CLIENT_SECRET (YouTube Data API v3)
  - OPENAI_API_KEY or similar for content generation
```

### Sprint 2 — Content Generation Pipeline (Days 1–2)
```
@APEX identify the main pipeline entry point (likely main.py or pipeline.py).
The pipeline must:
  1. Generate script (AI-driven: topic → 60-word script)
  2. Generate voiceover (TTS: elevenlabs, edge-tts, or gTTS)
  3. Combine with b-roll / background video (moviepy or ffmpeg)
  4. Add subtitles (auto-generated from script)
  5. Output: 1080x1920 MP4, <60s, <256MB

Test: python main.py --test --output ./test_output/
Verify a test video is created. Check video duration and resolution.
```

### Sprint 3 — YouTube Upload + Scheduler (Day 2–3)
```
@APEX implement or verify the YouTube upload module:
  - OAuth2 flow: open browser for auth if no token cached
  - Upload via YouTube Data API v3 with title, description, tags, category
  - Schedule: daily cron via APScheduler or system task scheduler
  
Test (dry run): python main.py --dry-run --upload
Should authenticate and show "Would upload: <title>" without actually uploading.

Create Windows Task Scheduler entry for daily 9AM run:
  schtasks /create /tn "YT-Shorts-Daily" /tr "python S:\YT-Shorts-Auto-Factory\main.py" /sc daily /st 09:00
```

### Sprint 4 — End-to-End Test + Tag (Day 3)
```
@APEX run a full end-to-end test:
  python main.py --topic "Python tip of the day" --publish-date tomorrow

Verify: video created, OAuth completes, upload queued.
Fix any failures.

Run: python -m pytest tests/ -v
git tag v1.0.0 && git push origin v1.0.0
```

## Done Criteria
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `pytest tests/` passes — no failures
- [ ] Test video generated: valid MP4, 1080x1920, <60s
- [ ] YouTube OAuth flow completes (token cached in credentials/)
- [ ] `--dry-run --upload` mode works without real upload
- [ ] Daily scheduler entry created (Windows Task Scheduler or APScheduler)
- [ ] `v1.0.0` tag pushed

## Completion Signal
```bash
git tag v1.0.0 && git push origin v1.0.0
```

## Critical Rules
1. **API keys never committed** — all credentials via .env only (covered by .gitignore)
2. **Always test in dry-run first** — `--dry-run` flag must be implemented before `--publish`
3. **Copyright compliance** — all music/video assets must be license-free; document sources
