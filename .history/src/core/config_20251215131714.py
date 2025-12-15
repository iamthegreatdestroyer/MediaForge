"""Configuration management for MediaForge"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
from typing import Optional
import os
import secrets


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
    secret_key: str = ""
    access_token_expire_minutes: int = 30
    
    # Compression
    compression_enabled: bool = True
    compression_level: int = 3
    compression_threads: int = 2
    
    # Pydantic v2-style settings configuration
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """
        Validate and secure the secret key.
        
        SECURITY CRITICAL: The secret key must be cryptographically secure.
        
        - PRODUCTION (debug=False): MUST load from MEDIAFORGE_SECRET_KEY environment variable.
          Fails immediately at startup if not provided.
        - DEVELOPMENT (debug=True): Falls back to generating a random secure key using
          secrets.token_urlsafe(32), suitable only for development/testing.
        
        The secret key is used for signing JWTs and session tokens. A weak or exposed
        secret key compromises the entire authentication system.
        
        Compliance:
        - OWASP A06:2021 Cryptographic Failures
        - NIST SP 800-63B: Secret Generation Requirements
        
        Args:
            v: Value passed to field (typically from .env file)
            info: Pydantic ValidationInfo containing context
            
        Returns:
            str: A secure secret key
            
        Raises:
            ValueError: If in production and MEDIAFORGE_SECRET_KEY is not set
        """
        # Get debug flag from context (defaults to True for safety)
        debug = info.data.get("debug", True)
        
        # Try to get from environment variable first
        env_secret = os.getenv("MEDIAFORGE_SECRET_KEY")
        
        if env_secret:
            # Validate minimum length (32 chars = 256 bits of entropy with base64)
            if len(env_secret) < 32:
                raise ValueError(
                    "secret_key from MEDIAFORGE_SECRET_KEY environment variable must be "
                    "at least 32 characters long for cryptographic security"
                )
            return env_secret
        
        # No environment variable found
        if not debug:
            # PRODUCTION: Fail immediately - secrets must be provisioned externally
            raise ValueError(
                "CRITICAL SECURITY ERROR: secret_key not configured for production.\n"
                "Set MEDIAFORGE_SECRET_KEY environment variable with a cryptographically "
                "secure random string (minimum 32 characters).\n\n"
                "Generate a secure key with: python -c \"import secrets; "
                "print(secrets.token_urlsafe(32))\""
            )
        
        # DEVELOPMENT: Generate random secure key as fallback
        generated_key = secrets.token_urlsafe(32)
        print(
            f"⚠️  WARNING: Using auto-generated secret key for development. "
            f"DO NOT use this in production.\n"
            f"Key: {generated_key}"
        )
        return generated_key


# Global settings instance
settings = Settings()
