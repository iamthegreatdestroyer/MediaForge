"""Configuration management for MediaForge"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    mediaforge_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Database
    database_url: str = "sqlite:///data/mediaforge.db"
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
