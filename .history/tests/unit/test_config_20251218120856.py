"""Tests for configuration management."""

import pytest
import os
from unittest.mock import patch
import warnings


class TestSettings:
    """Tests for Settings class."""
    
    def test_settings_defaults(self):
        """Test settings have sensible defaults."""
        with patch.dict(os.environ, {"MEDIAFORGE_SECRET_KEY": "test-key"}, clear=False):
            from src.core.config import Settings
            settings = Settings()
            
            assert settings.mediaforge_env == "development"
            assert settings.debug is True
            assert settings.log_level == "INFO"
            assert settings.max_workers == 4
            assert settings.chunk_size == 8192
            assert settings.thumbnail_size == 300
            assert settings.api_port == 8000
    
    def test_settings_from_environment(self):
        """Test settings can be overridden from environment."""
        env_vars = {
            "MEDIAFORGE_SECRET_KEY": "test-key",
            "MEDIAFORGE_ENV": "testing",
            "DEBUG": "false",
            "LOG_LEVEL": "DEBUG",
            "MAX_WORKERS": "8",
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from src.core.config import Settings
            settings = Settings()
            
            assert settings.mediaforge_env == "testing"
            assert settings.debug is False
            assert settings.log_level == "DEBUG"
            assert settings.max_workers == 8
    
    def test_database_url_default(self):
        """Test database URL default."""
        with patch.dict(os.environ, {"MEDIAFORGE_SECRET_KEY": "test-key"}, clear=False):
            from src.core.config import Settings
            settings = Settings()
            
            assert "sqlite" in settings.database_url
            assert "mediaforge.db" in settings.database_url


class TestGetSecretKey:
    """Tests for _get_secret_key function."""
    
    def test_get_secret_key_from_env(self):
        """Test secret key is read from environment."""
        with patch.dict(os.environ, {"MEDIAFORGE_SECRET_KEY": "my-secret-key"}, clear=False):
            from src.core.config import _get_secret_key
            assert _get_secret_key() == "my-secret-key"
    
    def test_get_secret_key_production_requires_key(self):
        """Test production mode requires secret key."""
        env_vars = {
            "MEDIAFORGE_ENV": "production",
        }
        # Remove secret key if present
        env_copy = {k: v for k, v in os.environ.items() if k != "MEDIAFORGE_SECRET_KEY"}
        env_copy.update(env_vars)
        
        with patch.dict(os.environ, env_copy, clear=True):
            from src.core.config import _get_secret_key
            with pytest.raises(ValueError, match="SECURITY ERROR"):
                _get_secret_key()
    
    def test_get_secret_key_development_auto_generates(self):
        """Test development mode auto-generates key with warning."""
        env_vars = {
            "MEDIAFORGE_ENV": "development",
        }
        # Remove secret key if present
        env_copy = {k: v for k, v in os.environ.items() if k != "MEDIAFORGE_SECRET_KEY"}
        env_copy.update(env_vars)
        
        with patch.dict(os.environ, env_copy, clear=True):
            from src.core.config import _get_secret_key
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                key = _get_secret_key()
                
                # Should generate a key
                assert len(key) > 0
                
                # Should warn
                assert len(w) >= 1
                assert "development" in str(w[0].message).lower() or "auto" in str(w[0].message).lower()
