# YouTube Shorts Automation Factory 🎬🤖

> **Autonomous AI-powered YouTube Shorts generation and upload system**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Overview

Fully autonomous system that generates, compiles, and uploads YouTube Shorts (15-60s videos) daily with **zero manual intervention** after initial setup. Leverages AI for content generation, trend analysis, and optimization to create engaging educational content in under-utilized niches.

### Key Features

- ✅ **100% Autonomous**: Set it and forget it
- 📊 **Trend-Aware**: Auto-scrapes YouTube/Reddit for trending topics
- 🎨 **AI-Powered**: Optional Stable Diffusion for unique visuals
- 🎙️ **Multi-TTS**: gTTS, pyttsx3, or Coqui TTS support
- 🎬 **Professional Quality**: 1080x1920 Shorts with captions
- 📈 **SEO Optimized**: Auto-generates titles, descriptions, tags
- 🔄 **Scheduled**: Daily uploads at optimal times
- 💰 **Revenue-Focused**: Designed for YouTube Partner Program monetization

## 📁 Documentation

This repository contains the complete technical implementation specification across three documents:

1. **[Part 1: Architecture & Core Components](./yt-shorts-factory-spec.md)** [REF:ES-001 through REF:CC-005]
   - Executive Summary
   - System Architecture
   - Technology Stack
   - Project Structure
   - Core Component Implementation

2. **[Part 2: Build Systems & CI/CD](./yt-shorts-factory-spec-part2.md)** [REF:BS-006 through REF:TEST-010]
   - Build System (Poetry, Makefile)
   - CI/CD Pipelines (GitHub Actions)
   - Configuration Management
   - Docker Setup
   - Testing Strategy

3. **[Part 3: Deployment & Operations](./yt-shorts-factory-spec-part3.md)** [REF:DG-011 through REF:CONC-020]
   - Deployment Guide
   - Monitoring & Logging
   - Security Best Practices
   - Implementation Roadmap
   - Troubleshooting Guide

## ⚡ Quick Start

### Prerequisites

- **Hardware**: 4+ core CPU, 8GB+ RAM, 50GB storage
- **Software**: Python 3.11+, FFmpeg, Git
- **Accounts**: YouTube channel, Google Cloud Project with YouTube Data API v3

### Installation (5 minutes)

```bash
# Clone repository
git clone https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory.git
cd YT-Shorts-Auto-Factory

# Automated setup (Linux/Mac)
chmod +x scripts/setup.sh
./scripts/setup.sh

# Or Windows (PowerShell as Admin)
Set-ExecutionPolicy Bypass -Scope Process -Force
.\scripts\setup.ps1
```

### Configuration (10 minutes)

```bash
# Copy config templates
cp config/config.example.yaml config/config.yaml
cp config/secrets.yaml.example config/secrets.yaml

# Edit your settings
nano config/config.yaml

# Authenticate with YouTube
poetry run python scripts/authenticate_youtube.py
```

### First Run

```bash
# Test mode (no upload)
poetry run python -m src.main --test --no-upload

# Single production run
poetry run python -m src.main --once

# Start autonomous daemon
poetry run python -m src.main --daemon
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Daily Scheduler                         │
│           (3 AM generation, Noon upload)                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                Pipeline Orchestrator                     │
└─────────────────────────────────────────────────────────┘
    ↓           ↓           ↓           ↓           ↓
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ Trend  │→ │Script  │→ │ Media  │→ │ Video  │→ │YouTube │
│Analysis│  │ Gen    │  │Creation│  │Compiler│  │Upload  │
└────────┘  └────────┘  └────────┘  └────────┘  └────────┘
```

## 📊 Tech Stack

| Category | Technology |
|----------|-----------|
| **Language** | Python 3.11+ |
| **Package Manager** | Poetry |
| **Video Processing** | MoviePy, FFmpeg |
| **AI Generation** | Stable Diffusion (optional) |
| **TTS** | gTTS / pyttsx3 / Coqui |
| **Web Scraping** | BeautifulSoup, Selenium |
| **API Integration** | YouTube Data API v3 |
| **Scheduling** | APScheduler |
| **Testing** | pytest, pytest-cov |
| **CI/CD** | GitHub Actions |
| **Containerization** | Docker |

## 🗂️ Project Structure

```
yt-shorts-factory/
├── src/
│   ├── core/              # Pipeline orchestration
│   ├── trend_analysis/    # YouTube/Reddit trend scraping
│   ├── content_generation/# Script & niche selection
│   ├── media_creation/    # TTS, images, captions
│   ├── video_compilation/ # MoviePy video assembly
│   ├── metadata/          # SEO optimization
│   ├── upload/            # YouTube API integration
│   └── monitoring/        # Logging, metrics, alerts
├── tests/                 # Comprehensive test suite
├── config/                # YAML configuration files
├── assets/                # Templates, music, fonts
├── data/                  # Cache, temp, archives
├── scripts/               # Setup & utility scripts
├── docker/                # Containerization files
└── docs/                  # Documentation
```

## 🎯 Supported Niches

Out-of-the-box templates for:

- **Historical Mystery**: Unsolved mysteries, ancient civilizations
- **Productivity Hack**: Time management, efficiency tips  
- **Obscure Facts**: Science trivia, nature wonders

**Easy to extend** with custom Jinja2 templates for any niche.

## 📈 Expected Performance

### Technical Metrics
- **Generation Time**: 5-15 minutes per video
- **Success Rate**: 95%+ uploads
- **Uptime**: 30+ days autonomous operation
- **CPU Usage**: 40-60% during generation

### Business Metrics
- **Monetization**: 3-6 months to YPP threshold
- **Revenue**: $1,000-$10,000+/month (12+ months)
- **Growth**: Sub-linear scaling (fixed effort, compound returns)

## 🛠️ Development Roadmap

### ✅ Phase 1: Foundation (Weeks 1-2)
- Project structure
- Configuration system
- Logging & monitoring
- Trend analysis

### 🔄 Phase 2: Content Generation (Weeks 3-4)
- Script generator
- Template system
- TTS integration
- Image generation

### 🔜 Phase 3: Video Compilation (Weeks 5-6)
- MoviePy integration
- Timeline builder
- Effects & transitions
- Thumbnail generation

### 🔜 Phase 4-9: Integration, Testing, Deployment (Weeks 7-12)
- YouTube API
- SEO optimization
- Scheduling automation
- Comprehensive testing
- CI/CD pipeline
- Production deployment

**Total Timeline**: ~12 weeks to production-ready system

## 🔒 Security

- ✅ OAuth 2.0 for YouTube authentication
- ✅ Secrets stored in `.gitignore`'d files
- ✅ Environment variable support
- ✅ Input validation and sanitization
- ✅ Rate limiting on API calls
- ✅ Regular dependency security audits

## 📊 Monitoring

Built-in monitoring includes:

- **Structured Logging**: JSON logs with Loguru
- **Metrics Tracking**: Success rates, durations, errors
- **Alerting**: Email/Discord/Slack notifications
- **Health Checks**: Automated system validation

```bash
# View real-time logs
tail -f logs/yt-shorts-factory.log

# Check metrics
poetry run python scripts/show_metrics.py

# Dashboard (optional web UI)
poetry run python -m src.monitoring.dashboard
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t yt-shorts-factory:latest -f docker/Dockerfile .

# Run with docker-compose
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🧪 Testing

```bash
# Run all tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# With coverage report
poetry run pytest --cov=src --cov-report=html
```

Current coverage target: **80%+**

## 📝 Configuration

### Key Settings (`config/config.yaml`)

```yaml
content:
  niche: "historical_mystery"
  videos_per_day: 1
  target_duration: 45  # seconds

schedule:
  generation_time: "03:00"  # 3 AM
  upload_time: "12:00"      # Noon

ai:
  tts_engine: "gtts"
  use_ai_images: true
  sd_model_id: "runwayml/stable-diffusion-v1-5"

youtube:
  privacy_status: "public"
  category_id: "27"  # Education
```

See [Configuration Guide](./docs/CONFIGURATION.md) for full options.

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guidelines](./CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- **MoviePy**: Video editing library
- **YouTube Data API**: Upload integration
- **Stable Diffusion**: AI image generation
- **BeautifulSoup**: Web scraping
- **Loguru**: Logging system

## 📞 Support

- 📖 **Documentation**: See `docs/` folder
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/iamthegreatdestroyer/YT-Shorts-Auto-Factory/discussions)
- 📧 **Email**: your-email@example.com

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

## 📊 Status

- **Current Version**: 0.1.0 (Pre-release)
- **Status**: Development
- **Last Updated**: January 2026
- **Maintainer**: [@iamthegreatdestroyer](https://github.com/iamthegreatdestroyer)

---

**Built with ❤️ for autonomous passive income generation**

*Leveraging AI and automation for sub-linear income scaling*
