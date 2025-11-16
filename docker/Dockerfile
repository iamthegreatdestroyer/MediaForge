# MediaForge Dockerfile
FROM python:3.11-slim-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    libmediainfo0v5 \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Create necessary directories
RUN mkdir -p /app/data /app/cache /media_library

# Set Python path
ENV PYTHONPATH=/app

# Expose ports
EXPOSE 8000 8001

# Default command (can be overridden)
CMD ["python", "-m", "src.cli.main"]