# 🎯 MediaForge: AI-Orchestrated Development Execution Guide

## Project Overview

**MediaForge** is your comprehensive personal media library application that will:
- Catalog all your media files (video, audio, images, documents)
- Extract rich metadata automatically
- Provide powerful search and organization
- Integrate with torrent clients (Phase 3)
- Support device import (Phase 3)
- Apply intelligent compression (Phase 3)

**Development Approach**: You're using GitHub Copilot as your development team, with Claude as your master architect, creating production-ready code through meticulously crafted prompts.

## 🚀 Your Next Steps

### Immediate Actions

1. **Review Your Repository**
   - Visit: https://github.com/iamthegreatdestroyer/MediaForge
   - Review the structure that's been created
   - Read the README.md for project overview

2. **Set Up Your Environment**
   ```bash
   # Clone your repository
   git clone https://github.com/iamthegreatdestroyer/MediaForge.git
   cd MediaForge
   
   # Create environment file
   cp .env.example .env
   
   # Build Docker containers
   docker-compose build
   
   # Start containers
   docker-compose up -d
   ```

3. **Open in VS Code**
   ```bash
   code .
   ```

4. **Start with Prompt 01**
   - Open: `prompts/01_database_schema.md`
   - Read the entire prompt
   - Copy everything after the metadata section
   - Open GitHub Copilot Chat (Ctrl+Shift+I)
   - Paste and let Copilot generate the code

## 📚 Complete Prompt Sequence

### Phase 1: Foundation (15-20 hours)

**Week 1-2:**

1. **Database Schema** (`prompts/01_database_schema.md`)
   - Time: 2-3 hours
   - Creates: `src/models/base.py`, `src/models/media.py`, `src/core/database.py`
   - Test: `pytest tests/unit/test_models.py`
   - ✅ Validates: Database structure, relationships, indexes

2. **Media Scanner** (`prompts/02_media_scanner.md`)
   - Time: 3-4 hours
   - Creates: `src/core/scanner.py`, `src/core/file_utils.py`, `src/core/hasher.py`
   - Test: `pytest tests/unit/test_scanner.py`
   - ✅ Validates: File discovery, hashing, duplicate detection

3. **Metadata Extraction** (`prompts/03_metadata_extraction.md`)
   - Time: 4-5 hours
   - Creates: `src/core/metadata_extractor.py`, `src/core/thumbnail_generator.py`
   - Test: `pytest tests/unit/test_metadata.py`
   - ✅ Validates: FFmpeg integration, EXIF reading, thumbnail generation

4. **CLI Interface** (`prompts/04_cli_interface.md`)
   - Time: 3-4 hours
   - Creates: `src/cli/main.py`, `src/cli/commands/`
   - Test: Manual CLI testing
   - ✅ Validates: All commands work, beautiful output

5. **Testing Framework** (`prompts/05_testing_framework.md`)
   - Time: 2-3 hours
   - Creates: Enhanced test infrastructure
   - Test: `pytest --cov=src`
   - ✅ Validates: 90%+ coverage, all fixtures work

## 👨‍💻 Working with GitHub Copilot

### The Process

1. **Open Prompt File**
   - Navigate to the specific prompt in `prompts/`
   - Read through to understand what you're building

2. **Copy the Prompt**
   - Select everything from "GITHUB COPILOT PROMPT" onward
   - Copy to clipboard

3. **Use Copilot Chat**
   - In VS Code, open Copilot Chat (Ctrl+Shift+I or Cmd+Shift+I)
   - Paste the prompt
   - Wait for Copilot to generate code

4. **Review Generated Code**
   - Check for completeness
   - Verify type hints
   - Ensure docstrings are present
   - Look for error handling

5. **Run Quality Checks**
   ```bash
   # Format code
   docker exec mediaforge-app black src/
   
   # Check linting
   docker exec mediaforge-app flake8 src/
   
   # Type checking
   docker exec mediaforge-app mypy src/
   ```

6. **Run Tests**
   ```bash
   # Run specific tests
   docker exec mediaforge-app pytest tests/unit/test_models.py -v
   
   # Or all tests
   docker exec mediaforge-app pytest
   ```

7. **Commit Your Work**
   ```bash
   git add .
   git commit -m "Implement database schema (Prompt 01)"
   git push origin main
   ```

8. **Mark Progress**
   - Update `prompts/README.md` checkboxes
   - Note any issues or customizations

### Tips for Success

**✅ Do:**
- Follow prompts in order (they build on each other)
- Review generated code carefully
- Run tests before committing
- Commit after each prompt completion
- Keep Docker containers running

**❌ Don't:**
- Skip prompts (dependencies matter)
- Commit without testing
- Ignore test failures
- Forget to format code
- Rush through reviews

## 🛠️ Development Environment

### Docker Commands

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose build --no-cache

# Access shell
docker exec -it mediaforge-app bash

# Run Python commands
docker exec mediaforge-app python -m src.cli.main --help
```

### Testing Commands

```bash
# Run all tests
docker exec mediaforge-app pytest

# Run with coverage
docker exec mediaforge-app pytest --cov=src --cov-report=html

# Run specific test file
docker exec mediaforge-app pytest tests/unit/test_models.py

# Run with verbose output
docker exec mediaforge-app pytest -v
```

### Code Quality Commands

```bash
# Format all code
docker exec mediaforge-app black src/ tests/

# Check code style
docker exec mediaforge-app flake8 src/ tests/

# Type checking
docker exec mediaforge-app mypy src/

# Sort imports
docker exec mediaforge-app isort src/ tests/
```

## 📝 Documentation

### Key Documents

- **README.md**: Project overview and quick start
- **docs/GETTING_STARTED.md**: Detailed setup guide
- **docs/ARCHITECTURE.md**: System architecture and design
- **prompts/README.md**: Prompt execution guide
- **EXECUTION_GUIDE.md** (this file): Your step-by-step guide

### Additional Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

## 🎯 Milestone Checklist

### Phase 1 Completion Criteria

Before moving to Phase 2, ensure:

- [ ] All 5 prompts completed
- [ ] All tests passing
- [ ] Code coverage >90%
- [ ] No linting errors
- [ ] No type checking errors
- [ ] CLI commands functional
- [ ] Can scan a directory successfully
- [ ] Metadata extraction works
- [ ] Thumbnails generate correctly
- [ ] Database queries are efficient

### Testing Your Implementation

```bash
# Create test media directory
mkdir -p ./test_media
# Add some sample files (videos, images, audio)

# Run a scan
docker exec mediaforge-app python -m src.cli.main scan ./test_media

# Check results
docker exec mediaforge-app python -m src.cli.main stats
```

## 🐛 Troubleshooting

### Common Issues

**Docker containers won't start:**
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Python import errors:**
```bash
docker exec mediaforge-app pip install -r requirements.txt
```

**Copilot generates incorrect code:**
- Review the prompt again
- Try breaking it into smaller sections
- Manually fix obvious issues
- Re-run with clarifications

**Tests failing:**
- Check fixtures are set up correctly
- Verify database initialization
- Look for async/await issues
- Check Docker containers are running

### Getting Help

If you encounter issues:

1. **Check the documentation** in `docs/`
2. **Review the prompts** for clarification
3. **Check Docker logs** for error messages
4. **Run tests with verbose output** for details
5. **Ask Claude** for specific guidance

## 🚀 What Happens Next

### After Phase 1

Once you complete Phase 1:

1. **Celebrate!** 🎉 You'll have:
   - Complete database schema
   - Working media scanner
   - Metadata extraction
   - Functional CLI
   - Comprehensive tests

2. **Test with Real Data**
   - Scan your actual media library
   - Verify performance
   - Check metadata accuracy
   - Generate thumbnails

3. **Plan Phase 2**
   - Search engine implementation
   - FastAPI web interface
   - Advanced filtering
   - Web UI foundation

### Future Phases

**Phase 2: Core Features** (Weeks 3-4)
- Full-text search
- REST API
- Web interface
- Advanced organization

**Phase 3: Advanced Features** (Weeks 5-8)
- Torrent integration (qBittorrent, Transmission, Deluge)
- Compression pipeline
- Device discovery and import
- Bulk operations

**Phase 4: Polish** (Weeks 9+)
- Performance optimization
- UI/UX refinement
- Documentation completion
- Distribution preparation

## 🌟 Success Metrics

You'll know Phase 1 is successful when:

- You can scan 10,000 files in under 1 minute
- Metadata extraction is accurate
- No memory leaks during long operations
- Tests run fast (<30 seconds for all unit tests)
- CLI is intuitive and responsive
- Code is well-documented and type-safe

## 💬 Final Notes

**Remember:**
- This is YOUR project - customize as needed
- The prompts are guidelines, not rigid requirements
- Code quality matters more than speed
- Testing prevents future headaches
- Documentation is for future you

**Most Importantly:**
- Have fun building!
- Learn from the AI-generated code
- Experiment and iterate
- Don't be afraid to ask questions

---

## 🏁 Ready to Start?

1. Set up your environment (see steps above)
2. Open `prompts/01_database_schema.md`
3. Copy the prompt to Copilot Chat
4. Start building MediaForge!

**Let's forge your perfect media collection!** 🔥

---

**Repository**: https://github.com/iamthegreatdestroyer/MediaForge
**Status**: Phase 1 Ready ✅
**Next Action**: Execute Prompt 01