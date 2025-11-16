# Getting Started with MediaForge Development

## 🚀 Quick Start Guide

This guide will help you start building MediaForge using GitHub Copilot and the provided prompts.

## Prerequisites

### Required Software
1. **Docker Desktop** - For containerized development
2. **VS Code** - Primary IDE
3. **GitHub Copilot** - AI-powered code generation
4. **Git** - Version control

### VS Code Extensions
- GitHub Copilot
- Python
- Docker
- GitLens (optional but recommended)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/iamthegreatdestroyer/MediaForge.git
cd MediaForge
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and customize settings if needed.

### 3. Build Docker Containers

```bash
docker-compose build
```

This will:
- Pull Python 3.11 base image
- Install FFmpeg and dependencies
- Install Python packages from requirements.txt
- Set up the development environment

### 4. Start Development Environment

```bash
docker-compose up -d
```

This starts the MediaForge container in detached mode.

### 5. Access the Container

```bash
# Open shell in container
docker exec -it mediaforge-app bash

# Or run commands directly
docker exec mediaforge-app python -m pytest
```

## Using GitHub Copilot Prompts

### Understanding the Prompt System

The `prompts/` directory contains meticulously crafted prompts that guide GitHub Copilot to generate production-ready code. Each prompt is a complete specification for a feature or module.

### Execution Workflow

1. **Open the Prompt File**
   - Navigate to `prompts/`
   - Start with `01_database_schema.md`

2. **Read the Context**
   - Each prompt has metadata and context
   - Understand dependencies
   - Review success criteria

3. **Copy the Prompt**
   - Copy everything after the metadata section
   - This is the actual prompt for Copilot

4. **Use Copilot Chat**
   - Open Copilot Chat in VS Code (Ctrl+Shift+I / Cmd+Shift+I)
   - Paste the entire prompt
   - Let Copilot generate the code

5. **Review Generated Code**
   - Check type hints
   - Verify docstrings
   - Ensure error handling
   - Run linters (Black, Flake8, Mypy)

6. **Run Tests**
   ```bash
   docker exec mediaforge-app pytest tests/unit/test_models.py -v
   ```

7. **Commit Changes**
   ```bash
   git add .
   git commit -m "Implement database schema (Prompt 01)"
   git push origin main
   ```

8. **Move to Next Prompt**
   - Mark the completed prompt in `prompts/README.md`
   - Proceed to the next prompt

## Development Workflow

### Phase 1: Foundation (Current)

Complete these prompts in order:

#### Week 1-2
1. ☐ **Prompt 01: Database Schema** (2-3 hours)
   - Files: `src/models/`, `src/core/database.py`
   - Test: `pytest tests/unit/test_models.py`

2. ☐ **Prompt 02: Media Scanner** (3-4 hours)
   - Files: `src/core/scanner.py`, `src/core/hasher.py`
   - Test: `pytest tests/unit/test_scanner.py`

3. ☐ **Prompt 03: Metadata Extraction** (4-5 hours)
   - Files: `src/core/metadata_extractor.py`
   - Test: `pytest tests/unit/test_metadata.py`

4. ☐ **Prompt 04: CLI Interface** (3-4 hours)
   - Files: `src/cli/main.py`, `src/cli/commands/`
   - Test: Manual CLI testing

5. ☐ **Prompt 05: Testing Framework** (2-3 hours)
   - Files: `tests/conftest.py`, test fixtures
   - Test: `pytest --cov=src`

### Testing Your Implementation

#### Run Specific Tests
```bash
# Unit tests only
docker exec mediaforge-app pytest tests/unit/ -v

# Integration tests
docker exec mediaforge-app pytest tests/integration/ -v

# With coverage
docker exec mediaforge-app pytest --cov=src --cov-report=html
```

#### Code Quality Checks
```bash
# Format code
docker exec mediaforge-app black src/ tests/

# Lint code
docker exec mediaforge-app flake8 src/ tests/

# Type checking
docker exec mediaforge-app mypy src/
```

### Using the CLI

Once you've implemented the CLI (Prompt 04):

```bash
# Scan a directory
docker exec mediaforge-app python -m src.cli.main scan /media_library

# View statistics
docker exec mediaforge-app python -m src.cli.main stats

# Search library
docker exec mediaforge-app python -m src.cli.main search "vacation"
```

## Troubleshooting

### Docker Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Permission issues:**
```bash
# Fix volume permissions
docker exec -u root mediaforge-app chown -R 1000:1000 /app
```

### Copilot Issues

**Copilot not responding:**
- Check Copilot status in VS Code
- Reload VS Code window
- Sign out and back into GitHub

**Generated code has errors:**
- Review the prompt for clarity
- Try breaking down into smaller chunks
- Manually fix obvious issues
- Re-run with clarified instructions

**Tests failing:**
- Check dependencies are installed
- Verify database is initialized
- Review fixture setup
- Check for async/await issues

### Python Issues

**Import errors:**
```bash
# Verify Python path
docker exec mediaforge-app python -c "import sys; print(sys.path)"

# Reinstall dependencies
docker exec mediaforge-app pip install -r requirements.txt
```

**Async errors:**
- Ensure using `async def` and `await`
- Check for missing `@pytest.mark.asyncio`
- Verify event loop handling

## Best Practices

### Code Quality
1. **Always use type hints**
2. **Write comprehensive docstrings**
3. **Handle errors gracefully**
4. **Use async/await correctly**
5. **Follow PEP 8 style guide**

### Testing
1. **Write tests as you go**
2. **Aim for 90%+ coverage**
3. **Test edge cases**
4. **Use fixtures for common setup**
5. **Keep tests fast and isolated**

### Git Workflow
1. **Commit after each prompt**
2. **Use descriptive commit messages**
3. **Reference prompt number in commits**
4. **Push regularly**
5. **Create branches for experiments**

## Next Steps

After completing Phase 1:

1. **Verify Everything Works**
   - All tests pass
   - CLI commands functional
   - Can scan and catalog media

2. **Create Test Data**
   - Add sample media files
   - Test scanning large directories
   - Verify metadata extraction

3. **Proceed to Phase 2**
   - Search engine implementation
   - Web API development
   - Advanced organization features

## Resources

### Documentation
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas

## FAQ

**Q: How long will Phase 1 take?**
A: Approximately 15-20 hours of active development if following the prompts systematically.

**Q: Can I modify the generated code?**
A: Absolutely! The prompts provide a foundation, but you should customize as needed.

**Q: What if Copilot generates incorrect code?**
A: Review carefully, run tests, and manually fix issues. Copilot is a tool, not a replacement for developer judgment.

**Q: Should I commit generated code immediately?**
A: No. Always review, test, and verify before committing.

**Q: Can I skip prompts?**
A: Not recommended. Prompts build on each other and dependencies matter.

---

**Ready to build? Start with Prompt 01!** 🚀