"""Tests for configuration management."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from repox.core.config import RepoxConfig


def test_default_config():
    """Test default configuration values."""
    config = RepoxConfig()
    
    assert config.strong_model == "gpt-4"
    assert config.weak_model == "gpt-3.5-turbo"
    assert config.openai_base_url == "https://api.openai.com/v1"
    assert config.max_file_size == 100000
    assert config.max_context_size == 50000
    assert config.verbose is False
    assert len(config.exclude_patterns) > 0
    assert len(config.skip_large_dirs) > 0


def test_load_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.api.com/v1")
    monkeypatch.setenv("REPOX_STRONG_MODEL", "gpt-4-turbo")
    monkeypatch.setenv("REPOX_WEAK_MODEL", "gpt-3.5-turbo-16k")
    monkeypatch.setenv("REPOX_MAX_FILE_SIZE", "200000")
    monkeypatch.setenv("REPOX_VERBOSE", "true")
    
    config = RepoxConfig.load_from_env()
    
    assert config.openai_api_key == "test-key"
    assert config.openai_base_url == "https://custom.api.com/v1"
    assert config.strong_model == "gpt-4-turbo"
    assert config.weak_model == "gpt-3.5-turbo-16k"
    assert config.max_file_size == 200000
    assert config.verbose is True


def test_load_from_file():
    """Test loading configuration from file."""
    config_data = {
        "strong_model": "gpt-4-custom",
        "weak_model": "gpt-3.5-custom",
        "max_file_size": 150000,
        "exclude_patterns": ["*.test", "custom/**"]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = Path(f.name)
    
    try:
        config = RepoxConfig.load_from_file(config_path)
        
        assert config.strong_model == "gpt-4-custom"
        assert config.weak_model == "gpt-3.5-custom"
        assert config.max_file_size == 150000
        assert "*.test" in config.exclude_patterns
        assert "custom/**" in config.exclude_patterns
    
    finally:
        config_path.unlink()


def test_load_from_nonexistent_file():
    """Test loading from non-existent file returns default config."""
    config = RepoxConfig.load_from_file(Path("/nonexistent/config.json"))
    
    # Should return default config
    assert config.strong_model == "gpt-4"
    assert config.weak_model == "gpt-3.5-turbo"


def test_save_to_file():
    """Test saving configuration to file."""
    config = RepoxConfig()
    config.strong_model = "custom-model"
    config.max_file_size = 123456
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = Path(f.name)
    
    try:
        config.save_to_file(config_path)
        
        # Load and verify
        with open(config_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["strong_model"] == "custom-model"
        assert saved_data["max_file_size"] == 123456
        # API key should not be saved
        assert "openai_api_key" not in saved_data
    
    finally:
        config_path.unlink()


def test_get_effective_config(monkeypatch):
    """Test getting effective configuration with file and env override."""
    # Create config file
    config_data = {
        "strong_model": "file-model",
        "max_file_size": 100000
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = Path(f.name)
    
    # Set environment variables
    monkeypatch.setenv("REPOX_STRONG_MODEL", "env-model")
    monkeypatch.setenv("REPOX_WEAK_MODEL", "env-weak-model")
    
    try:
        # Change to directory with config file
        original_cwd = Path.cwd()
        config_dir = config_path.parent
        os.chdir(config_dir)
        config_path.rename(config_dir / ".repox.json")
        
        config = RepoxConfig().get_effective_config()
        
        # Environment should override file
        assert config.strong_model == "env-model"
        assert config.weak_model == "env-weak-model"
        # File values should be used when not overridden
        assert config.max_file_size == 100000
    
    finally:
        os.chdir(original_cwd)
        (config_dir / ".repox.json").unlink(missing_ok=True)