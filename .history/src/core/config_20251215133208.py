"""Configuration management for MediaForge"""
import os
import warnings
from pathlib import Path
from secrets import token_urlsafe
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_secret_key() -> str:
    """Get secret key from environment or generate one for development.
    
    SECURITY CRITICAL:
    - In production (MEDIAFORGE_ENV=production), MEDIAFORGE_SECRET_KEY MUST be set
    - Never rely on auto-generated keys in production environments
    - Generate a secure key with: python -c "from secrets import token_urlsafe; print(token_urlsafe(32))"
    
    Raises:
        ValueError: If MEDIAFORGE_ENV=production but secret key not provided
    """
    env_key = os.getenv("MEDIAFORGE_SECRET_KEY")
    if env_key:
        return env_key
    
    # Check environment mode
    env_mode = os.getenv("MEDIAFORGE_ENV", "development").lower()
    if env_mode in ("production", "prod"):
        raise ValueError(
            "SECURITY ERROR: MEDIAFORGE_SECRET_KEY environment variable is REQUIRED in production.\n"
            "Generate a secure key with:\n"
            '  python -c "from secrets import token_urlsafe; print(token_urlsafe(32))"\n'
            "Then set: export MEDIAFORGE_SECRET_KEY=<generated-key>"
        )
    
    # Development only: auto-generate and warn
    warnings.warn(
        "⚠️  Auto-generating secret key for development. "
        "DO NOT use this auto-generated key in production!",
        RuntimeWarning,
        stacklevel=2
    )
    return token_urlsafe(32)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    mediaforge_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///data/mediaforge.db"
    
    # Media Library
    media_root: Path = Path("/media_library")
    cache_dir: Path = Path("/app/cache")
    thumbnail_dir: Path = Path("/app/cache/thumbnails")
    
    # Processing
    max_workers: int = 4
    chunk_size: int = 8192
    thumbnail_size: int = 300
    
    # Web Interface
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    
    # Security
    secret_key: str = "change-this-to-a-random-secret-key"
    access_token_expire_minutes: int = 30
    
    # Compression
    compression_enabled: bool = True
    compression_level: int = 3
    compression_threads: int = 2
    
    # Pydantic v2-style settings configuration
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()
