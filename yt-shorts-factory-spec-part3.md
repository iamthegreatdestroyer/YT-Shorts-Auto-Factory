# YouTube Shorts Factory - Technical Spec (Part 3: Deployment & Operations)

## Deployment Guide [REF:DG-011]

### Prerequisites Checklist

```markdown
## System Requirements

### Hardware
- [ ] CPU: 4+ cores (Ryzen 5 or better recommended)
- [ ] RAM: 8GB minimum, 16GB recommended
- [ ] Storage: 50GB+ free space
- [ ] GPU: Optional (NVIDIA/AMD for AI generation)
- [ ] Internet: Stable connection with 10+ Mbps upload

### Software
- [ ] Operating System: Ubuntu 20.04+, Windows 10+, or macOS 12+
- [ ] Python 3.11 or higher
- [ ] Git
- [ ] FFmpeg 6.0+
- [ ] ImageMagick 7.1+
- [ ] Chrome/Chromium (for web scraping)

### Accounts & API Access
- [ ] YouTube account (eligible for Partner Program)
- [ ] Google Cloud Project with YouTube Data API v3 enabled
- [ ] OAuth 2.0 credentials configured
- [ ] Reddit account (optional, for trend scraping)
- [ ] Twitter/X API access (optional)
```

### Installation Steps

#### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
# Clone repository
git clone https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory.git
cd YT-Shorts-Auto-Factory

# Run automated setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Follow interactive prompts for:
# - System dependency installation
# - Python dependencies
# - Configuration setup
# - YouTube OAuth authentication
# - Model downloads (if using AI)
```

**Windows (PowerShell as Administrator):**
```powershell
# Clone repository
git clone https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory.git
cd YT-Shorts-Auto-Factory

# Run automated setup
Set-ExecutionPolicy Bypass -Scope Process -Force
.\scripts\setup.ps1

# Follow interactive prompts
```

#### Option 2: Manual Setup

**1. Install System Dependencies**

*Ubuntu/Debian:*
```bash
sudo apt update
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    imagemagick \
    git \
    chromium-browser \
    chromium-chromedriver
```

*macOS (Homebrew):*
```bash
brew install python@3.11 ffmpeg imagemagick git
brew install --cask google-chrome
```

*Windows (Chocolatey):*
```powershell
choco install python311 ffmpeg imagemagick git googlechrome -y
```

**2. Set Up Python Environment**

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Optional: Install AI generation extras
poetry install --extras ai
```

**3. Configure Application**

```bash
# Copy configuration templates
cp config/config.example.yaml config/config.yaml
cp config/secrets.yaml.example config/secrets.yaml
cp .env.example .env

# Edit config files
nano config/config.yaml
nano config/secrets.yaml
```

**4. YouTube OAuth Setup**

```bash
# Place your client_secrets.json in config/
# Run OAuth authentication
poetry run python scripts/authenticate_youtube.py

# This will:
# 1. Open browser for Google OAuth
# 2. Grant necessary permissions
# 3. Save token to config/youtube_token.pickle
```

**5. Download AI Models (Optional)**

```bash
# Download Stable Diffusion model
poetry run python scripts/download_models.py --model stable-diffusion

# This downloads ~4GB, stores in ./models/
```

**6. Test Installation**

```bash
# Run single test generation (no upload)
poetry run python -m src.main --test --no-upload

# Check logs
tail -f logs/yt-shorts-factory.log
```

### System Service Configuration

#### Linux (systemd)

Create service file: `/etc/systemd/system/yt-shorts-factory.service`

```ini
[Unit]
Description=YouTube Shorts Automation Factory
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/YT-Shorts-Auto-Factory
Environment="PATH=/path/to/YT-Shorts-Auto-Factory/.venv/bin:/usr/bin"
ExecStart=/path/to/YT-Shorts-Auto-Factory/.venv/bin/python -m src.main --daemon
Restart=on-failure
RestartSec=30
StandardOutput=append:/path/to/logs/yt-shorts-factory.log
StandardError=append:/path/to/logs/yt-shorts-factory.error.log

# Resource limits
MemoryMax=8G
CPUQuota=400%

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable yt-shorts-factory
sudo systemctl start yt-shorts-factory

# Check status
sudo systemctl status yt-shorts-factory

# View logs
sudo journalctl -u yt-shorts-factory -f
```

#### Windows (Task Scheduler)

**Create scheduled task via PowerShell:**

```powershell
$action = New-ScheduledTaskAction `
    -Execute "python.exe" `
    -Argument "-m src.main --daemon" `
    -WorkingDirectory "C:\Path\To\YT-Shorts-Auto-Factory"

$trigger = New-ScheduledTaskTrigger -AtStartup

$principal = New-ScheduledTaskPrincipal `
    -UserId "YOUR_USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName "YouTube Shorts Factory" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings
```

**Or use GUI:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start a program
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `-m src.main --daemon`
   - Start in: `C:\Path\To\YT-Shorts-Auto-Factory`
5. Set conditions: Run whether user is logged in or not

#### Docker Deployment

**Build and run:**
```bash
# Build image
docker build -t yt-shorts-factory:latest -f docker/Dockerfile .

# Run with docker-compose (recommended)
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**With GPU support (NVIDIA):**
```bash
# Install nvidia-docker2
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# Run with GPU
docker run -d \
    --name yt-shorts-factory \
    --gpus all \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    yt-shorts-factory:latest
```

---

## Monitoring & Logging [REF:ML-012]

### Structured Logging Setup

```python
# src/monitoring/logger.py
"""
Centralized logging configuration with structured output.
"""

import sys
from pathlib import Path
from loguru import logger
from src.core.config import Config


def setup_logging(config: Config):
    """
    Configure loguru with file rotation and structured format.
    """
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
               "<level>{message}</level>",
        level=config.log_level,
        colorize=True
    )
    
    # File handler with rotation
    log_path = Path(config.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_path,
        rotation=config.log_rotation,
        retention=config.log_retention,
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",  # Always log everything to file
        enqueue=True,  # Thread-safe
        serialize=True  # JSON format for parsing
    )
    
    # Error-only file
    logger.add(
        log_path.parent / "errors.log",
        rotation="100 MB",
        retention="60 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}\n{exception}",
        backtrace=True,
        diagnose=True
    )
    
    logger.info(f"Logging initialized: {log_path}")
    
    return logger


# Usage in pipeline
from src.monitoring.logger import setup_logging

logger = setup_logging(config)
logger.info("Pipeline started")
logger.debug("Trend analysis phase", trend_count=len(trends))
logger.error("Upload failed", error=str(e), video_path=video_path)
```

### Metrics Tracking

```python
# src/monitoring/metrics.py
"""
Performance and business metrics tracking.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class PipelineMetrics:
    """Metrics for a single pipeline execution."""
    timestamp: str
    video_id: str
    success: bool
    
    # Performance metrics
    total_duration: float  # seconds
    trend_analysis_time: float
    script_generation_time: float
    media_creation_time: float
    video_compilation_time: float
    upload_time: float
    
    # Content metrics
    video_duration: float
    scene_count: int
    word_count: int
    
    # Trend data
    trend_keyword: str
    trend_score: float
    
    # Upload results
    upload_success: bool
    upload_error: str = None


class MetricsCollector:
    """
    Collects and persists metrics for analysis.
    """
    
    def __init__(self, metrics_file: Path):
        self.metrics_file = metrics_file
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_metrics(self, metrics: PipelineMetrics):
        """Append metrics to JSON lines file."""
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(asdict(metrics)) + '\n')
    
    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Generate summary statistics for last N days."""
        if not self.metrics_file.exists():
            return {}
        
        metrics_list = []
        with open(self.metrics_file, 'r') as f:
            for line in f:
                metrics_list.append(json.loads(line))
        
        # Filter by date
        cutoff = datetime.now().timestamp() - (days * 86400)
        recent = [m for m in metrics_list if datetime.fromisoformat(m['timestamp']).timestamp() > cutoff]
        
        if not recent:
            return {}
        
        # Calculate statistics
        successful = [m for m in recent if m['success']]
        
        return {
            'total_runs': len(recent),
            'successful_runs': len(successful),
            'success_rate': len(successful) / len(recent),
            'avg_duration': sum(m['total_duration'] for m in recent) / len(recent),
            'avg_video_length': sum(m['video_duration'] for m in recent) / len(recent),
            'total_videos_uploaded': len([m for m in recent if m['upload_success']]),
            'common_errors': self._get_common_errors(recent)
        }
    
    def _get_common_errors(self, metrics: list) -> Dict[str, int]:
        """Count error frequencies."""
        errors = {}
        for m in metrics:
            if not m['success'] and m.get('upload_error'):
                error = m['upload_error']
                errors[error] = errors.get(error, 0) + 1
        return dict(sorted(errors.items(), key=lambda x: x[1], reverse=True)[:5])


# Usage
collector = MetricsCollector(Path('./logs/metrics.jsonl'))

# After pipeline execution
metrics = PipelineMetrics(
    timestamp=datetime.now().isoformat(),
    video_id=result.video_id,
    success=result.success,
    total_duration=execution_time,
    # ... other fields
)
collector.log_metrics(metrics)

# Get weekly summary
summary = collector.get_summary(days=7)
print(f"Success rate: {summary['success_rate']:.1%}")
```

### Alert System

```python
# src/monitoring/alerting.py
"""
Alert notifications for errors and important events.
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from loguru import logger

from src.core.config import Config


class AlertManager:
    """
    Manages alerts via email, Discord, Slack, etc.
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def send_error_alert(self, error: str, context: dict):
        """Send alert when pipeline fails."""
        subject = f"🚨 YouTube Shorts Factory: Pipeline Error"
        message = self._format_error_message(error, context)
        
        if self.config.email_alerts:
            self._send_email(subject, message)
        
        if self.config.webhook_url:
            self._send_webhook(message)
    
    def send_success_alert(self, video_id: str, title: str):
        """Send alert when video successfully uploaded."""
        if not self.config.email_on_success:
            return
        
        subject = f"✅ YouTube Shorts: Video Uploaded"
        message = f"""
        Video successfully uploaded!
        
        Title: {title}
        Video ID: {video_id}
        URL: https://youtube.com/shorts/{video_id}
        """
        
        if self.config.email_alerts:
            self._send_email(subject, message)
        
        if self.config.webhook_url and self.config.webhook_on_upload:
            self._send_webhook(message)
    
    def _send_email(self, subject: str, body: str):
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.email_sender
            msg['To'] = self.config.email_recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email_sender, self.config.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    def _send_webhook(self, message: str):
        """Send to Discord/Slack webhook."""
        try:
            # Discord format
            payload = {
                "content": message,
                "username": "YouTube Shorts Factory"
            }
            
            response = requests.post(self.config.webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info("Webhook notification sent")
            
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
    
    def _format_error_message(self, error: str, context: dict) -> str:
        """Format detailed error message."""
        return f"""
        Pipeline Execution Failed
        
        Error: {error}
        
        Context:
        - Timestamp: {context.get('timestamp')}
        - Stage: {context.get('stage')}
        - Trend: {context.get('trend_keyword')}
        
        Check logs for details: {self.config.log_file}
        """
```

### Dashboard (Optional Web UI)

```python
# src/monitoring/dashboard.py
"""
Simple web dashboard for monitoring (optional).
Future enhancement - displays metrics, recent videos, logs.
"""

from flask import Flask, render_template, jsonify
from src.monitoring.metrics import MetricsCollector

app = Flask(__name__)
collector = MetricsCollector(Path('./logs/metrics.jsonl'))

@app.route('/')
def index():
    summary = collector.get_summary(days=30)
    return render_template('dashboard.html', summary=summary)

@app.route('/api/metrics')
def api_metrics():
    return jsonify(collector.get_summary(days=7))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

---

## Security Considerations [REF:SEC-013]

### Secrets Management

**Best Practices:**

1. **Never commit secrets to Git**
   ```bash
   # .gitignore
   config/secrets.yaml
   config/*.json
   config/*.pickle
   .env
   *.key
   *.pem
   ```

2. **Use environment variables for CI/CD**
   ```yaml
   # GitHub Actions
   env:
     YOUTUBE_CLIENT_SECRETS: ${{ secrets.YOUTUBE_CLIENT_SECRETS }}
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
   ```

3. **Encrypt secrets at rest**
   ```python
   from cryptography.fernet import Fernet
   
   # Generate key once, store securely
   key = Fernet.generate_key()
   cipher = Fernet(key)
   
   # Encrypt sensitive data
   encrypted = cipher.encrypt(b"secret_data")
   
   # Decrypt when needed
   decrypted = cipher.decrypt(encrypted)
   ```

4. **Use OS keyring for local storage**
   ```python
   import keyring
   
   # Store
   keyring.set_password("yt-shorts-factory", "youtube_token", token)
   
   # Retrieve
   token = keyring.get_password("yt-shorts-factory", "youtube_token")
   ```

### API Security

```python
# src/utils/security.py
"""
Security utilities for API interactions.
"""

import hashlib
import hmac
from functools import wraps
from time import time
from loguru import logger


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period  # seconds
        self.calls = []
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time()
            
            # Remove old calls
            self.calls = [t for t in self.calls if now - t < self.period]
            
            if len(self.calls) >= self.max_calls:
                wait_time = self.period - (now - self.calls[0])
                logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                sleep(wait_time)
                self.calls = []
            
            self.calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper


@RateLimiter(max_calls=10, period=60)
def call_youtube_api():
    """Rate-limited YouTube API call."""
    pass


def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate webhook signature (e.g., for GitHub webhooks)."""
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

### Input Validation

```python
# src/utils/validators.py
"""
Input validation and sanitization.
"""

import re
from typing import Any
from pydantic import BaseModel, validator, Field


class VideoMetadata(BaseModel):
    """Validated video metadata."""
    
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=5000)
    tags: list[str] = Field(..., max_items=500)
    
    @validator('title')
    def sanitize_title(cls, v):
        # Remove potentially problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', v)
        return sanitized.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        # Remove empty tags, limit length
        return [tag[:30] for tag in v if tag.strip()]


def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from filenames."""
    # Remove path traversal attempts
    filename = filename.replace('..', '')
    
    # Allow only safe characters
    safe_chars = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    return safe_chars[:255]  # Max filename length
```

### Dependency Security

```bash
# Regular security audits
poetry audit

# Update dependencies
poetry update

# Check for CVEs
pip-audit
```

---

## Implementation Roadmap [REF:IR-014]

### Phase 1: Foundation (Weeks 1-2)

**Week 1: Core Infrastructure**
- [x] Set up project structure
- [ ] Implement configuration system
- [ ] Set up logging and monitoring
- [ ] Create pipeline orchestrator skeleton
- [ ] Write initial tests

**Week 2: Trend Analysis**
- [ ] Implement YouTube trends scraper
- [ ] Implement Reddit scraper
- [ ] Create trend scoring algorithm
- [ ] Add trend caching mechanism
- [ ] Test trend analysis pipeline

### Phase 2: Content Generation (Weeks 3-4)

**Week 3: Script & Template System**
- [ ] Create Jinja2 template system
- [ ] Implement script generator
- [ ] Add niche selectors
- [ ] Create hook generation logic
- [ ] Build script validators

**Week 4: Media Creation**
- [ ] Integrate TTS engines (gTTS, pyttsx3)
- [ ] Set up image generation (stock assets)
- [ ] Optional: Stable Diffusion integration
- [ ] Create caption generator
- [ ] Add background music mixer

### Phase 3: Video Compilation (Weeks 5-6)

**Week 5: MoviePy Integration**
- [ ] Implement timeline builder
- [ ] Create video compiler
- [ ] Add transitions and effects
- [ ] Build thumbnail generator
- [ ] Optimize rendering settings

**Week 6: Polish & Testing**
- [ ] Add video quality checks
- [ ] Implement multiple resolution support
- [ ] Create rendering presets
- [ ] Comprehensive video generation tests
- [ ] Performance optimization

### Phase 4: YouTube Integration (Week 7)

- [ ] Set up YouTube Data API v3
- [ ] Implement OAuth flow
- [ ] Create upload manager
- [ ] Add retry logic
- [ ] Build playlist manager
- [ ] Implement scheduling

### Phase 5: SEO & Metadata (Week 8)

- [ ] Create SEO optimizer
- [ ] Build keyword extractor
- [ ] Implement hashtag generator
- [ ] Add title/description templates
- [ ] Test metadata generation

### Phase 6: Automation & Scheduling (Week 9)

- [ ] Integrate APScheduler
- [ ] Create daemon mode
- [ ] Build cleanup utilities
- [ ] Add error recovery
- [ ] Implement health checks

### Phase 7: Testing & Refinement (Week 10)

- [ ] Complete unit test suite
- [ ] End-to-end integration tests
- [ ] Load/stress testing
- [ ] Bug fixes
- [ ] Documentation

### Phase 8: Deployment & Monitoring (Week 11)

- [ ] Create Docker images
- [ ] Write deployment scripts
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring
- [ ] Create user documentation

### Phase 9: Launch & Iteration (Week 12+)

- [ ] Deploy to production
- [ ] Monitor first videos
- [ ] Gather metrics
- [ ] Iterate based on performance
- [ ] Plan v2 features

---

## Future Enhancements [REF:FE-015]

### Short-Term (3-6 months)

1. **Multi-Channel Support**
   - Manage multiple YouTube channels
   - Channel-specific niches
   - Separate scheduling per channel

2. **Advanced AI Integration**
   - GPT-4 for dynamic script generation
   - DALL-E 3 for higher quality images
   - Voice cloning for consistent narrator

3. **Analytics Dashboard**
   - Web UI for monitoring
   - Performance metrics visualization
   - A/B testing for thumbnails/titles

4. **Content Variations**
   - Multiple video formats (Shorts, regular videos)
   - Series and episodic content
   - Playlist organization

### Mid-Term (6-12 months)

5. **Machine Learning Optimization**
   - Learn from successful videos
   - Predict viral potential
   - Auto-optimize based on analytics

6. **Community Features**
   - Auto-respond to comments
   - Community polls integration
   - Viewer suggestion incorporation

7. **Monetization Enhancement**
   - Affiliate link integration
   - Sponsored content automation
   - Merchandise promotion

8. **Cross-Platform Distribution**
   - TikTok upload support
   - Instagram Reels
   - Facebook Reels

### Long-Term (12+ months)

9. **Enterprise Features**
   - Multi-user support
   - Team collaboration
   - White-label options

10. **Advanced Analytics**
    - Competitor analysis
    - Market trend prediction
    - Revenue forecasting

11. **Content Marketplace**
    - Sell/buy templates
    - Share successful strategies
    - Community asset library

---

## Quick Start Commands [REF:QS-016]

```bash
# Installation
git clone https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory.git
cd YT-Shorts-Auto-Factory
./scripts/setup.sh

# Configuration
cp config/config.example.yaml config/config.yaml
nano config/config.yaml

# YouTube Authentication
poetry run python scripts/authenticate_youtube.py

# Test Run (no upload)
poetry run python -m src.main --test --no-upload

# Single Production Run
poetry run python -m src.main --once

# Start Daemon
poetry run python -m src.main --daemon

# View Logs
tail -f logs/yt-shorts-factory.log

# Check Metrics
poetry run python scripts/show_metrics.py

# Stop Daemon
pkill -f "python -m src.main"
```

---

## Troubleshooting Guide [REF:TG-017]

### Common Issues

**1. YouTube Authentication Fails**
```
Error: invalid_grant
```
**Solution:**
- Delete `config/youtube_token.pickle`
- Re-run `python scripts/authenticate_youtube.py`
- Ensure OAuth consent screen is configured
- Check API quotas not exceeded

**2. FFmpeg Not Found**
```
FileNotFoundError: ffmpeg
```
**Solution:**
```bash
# Ubuntu
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

**3. Out of Memory During Rendering**
```
MemoryError: Unable to allocate array
```
**Solution:**
- Reduce `video_resolution` in config
- Lower `max_concurrent_tasks`
- Increase system swap space
- Use GPU rendering if available

**4. Trend Scraping Returns Empty**
```
TrendAnalyzer: No trends found
```
**Solution:**
- Check internet connection
- Verify Reddit credentials
- Try different subreddits
- Use cached trends temporarily

**5. Upload Quota Exceeded**
```
HttpError 403: quotaExceeded
```
**Solution:**
- YouTube API has daily quota limits (10,000 units)
- Each upload costs ~1,600 units (6 uploads/day max)
- Wait for quota reset (midnight Pacific Time)
- Request quota increase from Google

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
poetry run python -m src.main --once

# Test individual components
poetry run python -c "
from src.trend_analysis.analyzer import TrendAnalyzer
from src.core.config import Config

config = Config.load('config/config.yaml')
analyzer = TrendAnalyzer(config)
trends = analyzer.get_trending_topics()
print(f'Found {len(trends)} trends')
"
```

---

## Resource Estimates [REF:RE-018]

### Development Time

| Phase | Task | Hours | Days |
|-------|------|-------|------|
| 1 | Foundation | 40 | 5 |
| 2 | Content Generation | 48 | 6 |
| 3 | Video Compilation | 48 | 6 |
| 4 | YouTube Integration | 24 | 3 |
| 5 | SEO & Metadata | 16 | 2 |
| 6 | Automation | 24 | 3 |
| 7 | Testing | 32 | 4 |
| 8 | Deployment | 16 | 2 |
| 9 | Documentation | 16 | 2 |
| **Total** | | **264** | **33** |

*With GitHub Copilot: Estimated 40-50% faster = ~20-25 days*

### Operating Costs

| Item | Cost (Monthly) |
|------|----------------|
| YouTube API (free tier) | $0 |
| Hosting (if cloud) | $5-20 |
| Additional API quotas | $0-50 |
| AI API calls (optional) | $0-100 |
| Domain (optional) | $1 |
| **Total** | **$6-171** |

*Local deployment = $0-50/month (only optional AI APIs)*

### Hardware Utilization

**During Video Generation (30-60 min/video):**
- CPU: 40-60% average
- RAM: 4-6 GB
- Storage: ~500 MB per video (before cleanup)
- Network: Minimal except during upload

**Idle (Daemon Mode):**
- CPU: <5%
- RAM: ~500 MB
- Storage: Growing slowly (logs, cache)

---

## License & Attribution [REF:LA-019]

```
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Third-Party Assets

**Required Attributions:**
- Background music: Must use royalty-free or Creative Commons
  - Recommended: YouTube Audio Library, Incompetech
- Stock images: Use free sources (Unsplash, Pexels) with attribution
- Fonts: SIL Open Font License compatible

---

## Conclusion [REF:CONC-020]

This technical specification provides a **production-ready blueprint** for building the YouTube Shorts Automation Factory. The architecture is designed for:

✅ **Autonomy**: Fully hands-off after initial setup
✅ **Scalability**: Easy to extend with new features
✅ **Maintainability**: Clean code structure with comprehensive tests
✅ **Reliability**: Error handling, monitoring, and recovery
✅ **Performance**: Optimized for consumer hardware (Ryzen laptop)

### Success Criteria

1. **Technical**: 
   - Pipeline completes in < 1 hour per video
   - 95%+ upload success rate
   - Zero manual intervention for 30 days

2. **Business**:
   - Reach monetization threshold (1K subs, 4K watch hours) in 3-6 months
   - Generate $1K+/month passive income by month 12
   - Sub-linear scaling: fixed effort, growing revenue

### Next Steps

1. ✅ Review this specification
2. 🔄 Set up development environment
3. 🔜 Begin Phase 1 implementation
4. 🔜 Iterate based on real-world testing

**Ready to begin development?** Start with Phase 1, Week 1 tasks and leverage GitHub Copilot for accelerated coding. The foundation is designed to get you to a working prototype in 2-3 weeks.

---

## Appendix: Reference Codes Summary

| Code | Section | Description |
|------|---------|-------------|
| REF:ES-001 | Executive Summary | Project goals and metrics |
| REF:SA-002 | System Architecture | High-level design and components |
| REF:TS-003 | Technology Stack | Languages, frameworks, tools |
| REF:PS-004 | Project Structure | File organization |
| REF:CC-005 | Core Components | Key implementation details |
| REF:BS-006 | Build System | Poetry, Makefile setup |
| REF:CICD-007 | CI/CD Pipeline | GitHub Actions workflows |
| REF:CM-008 | Configuration | YAML configs and secrets |
| REF:DC-009 | Docker | Containerization setup |
| REF:TEST-010 | Testing | Test strategy and examples |
| REF:DG-011 | Deployment | Installation and setup |
| REF:ML-012 | Monitoring | Logging and metrics |
| REF:SEC-013 | Security | Security best practices |
| REF:IR-014 | Roadmap | Implementation phases |
| REF:FE-015 | Future | Enhancement ideas |
| REF:QS-016 | Quick Start | Common commands |
| REF:TG-017 | Troubleshooting | Common issues |
| REF:RE-018 | Resources | Time and cost estimates |
| REF:LA-019 | License | Legal information |
| REF:CONC-020 | Conclusion | Summary and next steps |

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Total Pages**: 75+  
**Status**: Ready for Implementation ✅
