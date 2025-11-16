# Prompt 00: Docker Environment Setup & Verification

## Metadata
- **Phase**: Foundation (Prerequisites)
- **Priority**: Critical
- **Estimated Time**: 30 minutes
- **Dependencies**: None (This is the first step!)
- **Files to Verify**: All Docker and configuration files exist

---

# GITHUB COPILOT PROMPT: DOCKER ENVIRONMENT SETUP

## Context

You are setting up the complete Docker development environment for MediaForge, a comprehensive media library management system. The environment must be ready for Python development with all media processing dependencies, proper volume mounting for development, and verification that everything works correctly.

## Project Information

**Repository:** MediaForge  
**Language:** Python 3.11+  
**Framework:** FastAPI, SQLAlchemy, Typer  
**Media Processing:** FFmpeg, Pillow, Mutagen  
**Containerization:** Docker + Docker Compose  

## Your Tasks

### Task 1: Verify All Configuration Files Exist

Check that these files exist in the repository:
- ✅ `Dockerfile` or `docker/Dockerfile`
- ✅ `docker-compose.yml`
- ✅ `requirements.txt`
- ✅ `.env.example`
- ✅ `.gitignore`
- ✅ `pyproject.toml`

If any are missing, create them using the templates in the repository structure.

### Task 2: Create .env File from Template

```bash
# Copy the example environment file
cp .env.example .env
```

The `.env` file should contain:
```env
# MediaForge Environment Configuration

MEDIAFORGE_ENV=development
DEBUG=true
LOG_LEVEL=INFO

DATABASE_URL=sqlite:///data/mediaforge.db

MEDIA_ROOT=/media_library
CACHE_DIR=/app/cache
THUMBNAIL_DIR=/app/cache/thumbnails

MAX_WORKERS=4
CHUNK_SIZE=8192
THUMBNAIL_SIZE=300

API_HOST=0.0.0.0
API_PORT=8000

SECRET_KEY=development-secret-key-change-in-production

COMPRESSION_ENABLED=true
COMPRESSION_LEVEL=3
```

### Task 3: Build Docker Containers

```bash
# Build the Docker image
docker-compose build

# This will:
# - Pull Python 3.11 slim image
# - Install system dependencies (FFmpeg, libmagic, etc.)
# - Install Python packages from requirements.txt
# - Set up the working directory
# - Configure the container
```

**Expected Output:**
```
[+] Building 120.5s (12/12) FINISHED
 => [internal] load build definition
 => [internal] load .dockerignore
 => [internal] load metadata
 => [1/7] FROM docker.io/library/python:3.11-slim-bullseye
 => [2/7] RUN apt-get update && apt-get install -y ffmpeg...
 => [3/7] WORKDIR /app
 => [4/7] COPY requirements.txt .
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt
 => [6/7] COPY src/ ./src/
 => [7/7] RUN mkdir -p /app/data /app/cache /media_library
 => exporting to image
 => => naming to docker.io/library/mediaforge-app
```

### Task 4: Start the Containers

```bash
# Start containers in detached mode
docker-compose up -d

# Verify containers are running
docker-compose ps
```

**Expected Output:**
```
NAME                IMAGE               STATUS              PORTS
mediaforge-app      mediaforge-app      Up 5 seconds        0.0.0.0:8000->8000/tcp
```

### Task 5: Verify Python Environment

Run these commands to verify the environment is set up correctly:

```bash
# Check Python version
docker exec mediaforge-app python --version
# Expected: Python 3.11.x

# Verify key packages are installed
docker exec mediaforge-app python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
docker exec mediaforge-app python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
docker exec mediaforge-app python -c "import typer; print(f'Typer: {typer.__version__}')"
docker exec mediaforge-app python -c "import ffmpeg; print('FFmpeg-python: OK')"
docker exec mediaforge-app python -c "from PIL import Image; print('Pillow: OK')"

# Verify FFmpeg system binary
docker exec mediaforge-app ffmpeg -version
# Should show FFmpeg version info
```

### Task 6: Verify Directory Structure

```bash
# Check that all directories exist
docker exec mediaforge-app ls -la /app/

# Should see:
# drwxr-xr-x  src/
# drwxr-xr-x  tests/
# drwxr-xr-x  data/
# drwxr-xr-x  cache/
# -rw-r--r--  requirements.txt
```

### Task 7: Test Python Import Paths

```bash
# Verify Python can find the src module
docker exec mediaforge-app python -c "
import sys
print('Python path:')
for p in sys.path:
    print(f'  {p}')

print('\nTrying to import src modules...')
try:
    from src.core.config import settings
    print(f'✅ Config imported successfully')
    print(f'   Database URL: {settings.database_url}')
    print(f'   Media root: {settings.media_root}')
except ImportError as e:
    print(f'❌ Import failed: {e}')
"
```

**Expected Output:**
```
Python path:
  /app
  /usr/local/lib/python3.11/...

Trying to import src modules...
✅ Config imported successfully
   Database URL: sqlite:///data/mediaforge.db
   Media root: /media_library
```

### Task 8: Run Initial Tests

```bash
# Run pytest to verify test framework works
docker exec mediaforge-app pytest --version

# Run the basic configuration test
docker exec mediaforge-app pytest tests/ -v --tb=short 2>/dev/null || echo "Tests will be added in later prompts"
```

### Task 9: Create Helper Script (Optional but Recommended)

Create a file called `dev.sh` in the root directory:

```bash
#!/bin/bash
# MediaForge Development Helper Script

set -e

CONTAINER="mediaforge-app"

case "$1" in
    build)
        echo "🔨 Building Docker containers..."
        docker-compose build
        ;;
    start)
        echo "🚀 Starting MediaForge..."
        docker-compose up -d
        docker-compose ps
        ;;
    stop)
        echo "🛑 Stopping MediaForge..."
        docker-compose down
        ;;
    restart)
        echo "🔄 Restarting MediaForge..."
        docker-compose restart
        ;;
    logs)
        echo "📋 Showing logs..."
        docker-compose logs -f
        ;;
    shell)
        echo "🐚 Opening shell in container..."
        docker exec -it $CONTAINER bash
        ;;
    test)
        echo "🧪 Running tests..."
        docker exec $CONTAINER pytest "${@:2}"
        ;;
    format)
        echo "✨ Formatting code..."
        docker exec $CONTAINER black src/ tests/
        ;;
    lint)
        echo "🔍 Linting code..."
        docker exec $CONTAINER flake8 src/ tests/
        ;;
    types)
        echo "📝 Type checking..."
        docker exec $CONTAINER mypy src/
        ;;
    scan)
        echo "📁 Scanning media..."
        docker exec $CONTAINER python -m src.cli.main scan "${@:2}"
        ;;
    cli)
        echo "💻 Running CLI command..."
        docker exec $CONTAINER python -m src.cli.main "${@:2}"
        ;;
    clean)
        echo "🧹 Cleaning up..."
        docker-compose down -v
        docker system prune -f
        ;;
    status)
        echo "📊 MediaForge Status:"
        docker-compose ps
        echo ""
        echo "Container Stats:"
        docker stats $CONTAINER --no-stream
        ;;
    *)
        echo "MediaForge Development Helper"
        echo ""
        echo "Usage: ./dev.sh <command>"
        echo ""
        echo "Commands:"
        echo "  build     - Build Docker containers"
        echo "  start     - Start MediaForge services"
        echo "  stop      - Stop MediaForge services"
        echo "  restart   - Restart MediaForge services"
        echo "  logs      - Show container logs"
        echo "  shell     - Open bash shell in container"
        echo "  test      - Run tests (add pytest args after)"
        echo "  format    - Format code with Black"
        echo "  lint      - Lint code with Flake8"
        echo "  types     - Type check with Mypy"
        echo "  scan      - Scan media directory"
        echo "  cli       - Run MediaForge CLI"
        echo "  clean     - Clean up containers and volumes"
        echo "  status    - Show container status"
        echo ""
        echo "Examples:"
        echo "  ./dev.sh build"
        echo "  ./dev.sh start"
        echo "  ./dev.sh test -v"
        echo "  ./dev.sh scan /media_library"
        echo "  ./dev.sh cli stats"
        ;;
esac
```

Make it executable:
```bash
chmod +x dev.sh
```

### Task 10: Verify Complete Setup

Run this comprehensive verification:

```bash
# Create a test script
docker exec mediaforge-app python -c "
import sys
print('='*60)
print('MediaForge Environment Verification')
print('='*60)

# Check Python version
print(f'\n✅ Python Version: {sys.version.split()[0]}')

# Check imports
try:
    from src.core.config import settings
    print('✅ Config module: OK')
except Exception as e:
    print(f'❌ Config module: {e}')

try:
    import sqlalchemy
    print(f'✅ SQLAlchemy: {sqlalchemy.__version__}')
except Exception as e:
    print(f'❌ SQLAlchemy: {e}')

try:
    import fastapi
    print(f'✅ FastAPI: {fastapi.__version__}')
except Exception as e:
    print(f'❌ FastAPI: {e}')

try:
    import typer
    print(f'✅ Typer: {typer.__version__}')
except Exception as e:
    print(f'❌ Typer: {e}')

try:
    from rich import print as rprint
    print('✅ Rich: OK')
except Exception as e:
    print(f'❌ Rich: {e}')

try:
    import ffmpeg
    print('✅ ffmpeg-python: OK')
except Exception as e:
    print(f'❌ ffmpeg-python: {e}')

try:
    from PIL import Image
    print('✅ Pillow: OK')
except Exception as e:
    print(f'❌ Pillow: {e}')

try:
    import pytest
    print('✅ pytest: OK')
except Exception as e:
    print(f'❌ pytest: {e}')

print('\n' + '='*60)
print('Environment is ready for development! 🚀')
print('='*60)
"
```

**Expected Output:**
```
============================================================
MediaForge Environment Verification
============================================================

✅ Python Version: 3.11.x
✅ Config module: OK
✅ SQLAlchemy: 2.0.23
✅ FastAPI: 0.104.1
✅ Typer: 0.9.0
✅ Rich: OK
✅ ffmpeg-python: OK
✅ Pillow: OK
✅ pytest: OK

============================================================
Environment is ready for development! 🚀
============================================================
```

## Success Criteria

- [ ] Docker containers built successfully
- [ ] Containers are running (docker-compose ps shows "Up")
- [ ] Python 3.11+ is installed
- [ ] All required packages are installed
- [ ] FFmpeg is available
- [ ] Python can import src modules
- [ ] Config loads correctly from .env
- [ ] Directory structure is correct
- [ ] Helper script created (optional)
- [ ] Verification script passes all checks

## Common Issues & Solutions

### Issue: "docker: command not found"
**Solution:** Install Docker Desktop from https://www.docker.com/products/docker-desktop/

### Issue: "permission denied" on Linux
**Solution:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue: Port 8000 already in use
**Solution:** Edit docker-compose.yml to use different port:
```yaml
ports:
  - "8001:8000"  # Change 8001 to any available port
```

### Issue: Build fails on pip install
**Solution:** 
```bash
# Clear Docker cache and rebuild
docker-compose build --no-cache
```

### Issue: Cannot import src modules
**Solution:** Check PYTHONPATH in Dockerfile:
```dockerfile
ENV PYTHONPATH=/app
```

## Next Steps

Once verification passes:

1. ✅ **Environment is ready!**
2. 📝 **Proceed to Prompt 01: Database Schema**
3. 🚀 **Start building MediaForge!**

---

**EXECUTE ALL COMMANDS ABOVE IN SEQUENCE TO SET UP YOUR DOCKER ENVIRONMENT**

## Quick Command Reference

After setup, use these commands:

```bash
# Start development
./dev.sh start

# Run tests  
./dev.sh test

# Format code
./dev.sh format

# Open shell
./dev.sh shell

# Scan media
./dev.sh scan /path/to/media

# View logs
./dev.sh logs

# Stop everything
./dev.sh stop
```

Or without the helper script:

```bash
# Start
docker-compose up -d

# Run command
docker exec mediaforge-app <command>

# Stop
docker-compose down
```