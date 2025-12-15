# MediaForge 🔥

**Forge Your Perfect Media Collection**

MediaForge is a comprehensive personal digital media library application designed to handle all media formats with advanced features including torrent integration, device content extraction, and intelligent compression for storage optimization.

## 🎯 Project Vision

Create a downloadable, installable solution that can:
- Handle all media formats (video, audio, images, documents, streaming containers)
- Integrate with modern torrent clients (qBittorrent, Transmission, Deluge)
- Extract and organize content from connected devices
- Apply intelligent compression for storage optimization
- Provide powerful search and organization capabilities

## 🏗️ Architecture

- **Core Engine**: Python 3.11+ with async/await patterns
- **Database**: SQLite with SQLAlchemy ORM
- **Media Processing**: FFmpeg integration
- **Containerization**: Docker & Docker Compose
- **UI**: CLI + FastAPI Web Interface
- **Torrent**: libtorrent-python integration

## 📁 Project Structure

```
MediaForge/
├── src/
│   ├── core/              # Core engine modules
│   ├── api/               # FastAPI web interface
│   ├── cli/               # Command-line interface
│   └── models/            # Database models
├── docker/                # Docker configurations
├── tests/                 # Comprehensive test suite
├── docs/                  # Documentation
├── prompts/               # GitHub Copilot prompts
└── scripts/               # Utility scripts
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Git
- VS Code with GitHub Copilot

### Setup

```bash
# Clone the repository
git clone https://github.com/iamthegreatdestroyer/MediaForge.git
cd MediaForge

# Build and start containers
docker-compose up -d

# Access the application
# CLI: docker exec -it mediaforge-app bash
# Web UI: http://localhost:8000
```

## 📋 Development Phases

### Phase 1: Foundation ✅ (Current)
- [x] Project structure initialization
- [ ] Docker environment setup
- [ ] Database schema implementation
- [ ] Basic media scanner
- [ ] CLI interface foundation

### Phase 2: Core Features (Next)
- [ ] Metadata extraction engine
- [ ] Full-text search implementation
- [ ] Web UI foundation
- [ ] Basic media organization

### Phase 3: Advanced Features
- [ ] Compression pipeline
- [ ] Torrent integration
- [ ] Device discovery & import
- [ ] Advanced search & filtering

### Phase 4: Polish & Optimization
- [ ] Performance optimization
- [ ] UI/UX refinement
- [ ] Comprehensive testing
- [ ] Documentation completion

## 🤖 AI-Driven Development

This project leverages GitHub Copilot for autonomous code generation. The `prompts/` directory contains meticulously crafted prompts for each development phase.

## 📖 Documentation

Detailed documentation is available in the `docs/` directory:
- Architecture Overview
- API Documentation
- Database Schema
- Development Guide
- User Manual

## 🧪 Testing

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=src

# Run specific test suite
docker-compose exec app pytest tests/unit/
```

## 📄 License

Private project - All rights reserved

## 🙏 Acknowledgments

- FFmpeg for media processing
- SQLAlchemy for database ORM
- FastAPI for modern web framework
- libtorrent for torrent functionality

---

**Status**: 🚧 Active Development
**Version**: 0.1.0-alpha
**Last Updated**: November 2025