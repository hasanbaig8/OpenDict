"""
Tests for configuration management.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from config import (
    AppConfig,
    ConfigManager,
    Environment,
    LoggingConfig,
    SecurityConfig,
    ServerConfig,
    TranscriptionConfig,
)


class TestAppConfig:
    """Test AppConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AppConfig()

        assert config.environment == Environment.DEVELOPMENT.value
        assert config.debug is False
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.transcription, TranscriptionConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.security, SecurityConfig)

    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        server = ServerConfig(host="0.0.0.0", port=9999)
        config = AppConfig(
            environment=Environment.PRODUCTION.value, debug=True, server=server
        )

        assert config.environment == Environment.PRODUCTION.value
        assert config.debug is True
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 9999


class TestServerConfig:
    """Test ServerConfig dataclass."""

    def test_default_server_config(self):
        """Test default server configuration."""
        config = ServerConfig()

        assert config.host == "127.0.0.1"
        assert config.port == 8765
        assert config.max_connections == 10
        assert config.connection_timeout == 30
        assert config.request_timeout == 120

    def test_custom_server_config(self):
        """Test custom server configuration."""
        config = ServerConfig(host="0.0.0.0", port=9000, max_connections=5)

        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.max_connections == 5


class TestTranscriptionConfig:
    """Test TranscriptionConfig dataclass."""

    def test_default_transcription_config(self):
        """Test default transcription configuration."""
        config = TranscriptionConfig()

        assert config.model_name == "nvidia/parakeet-tdt-0.6b-v2"
        assert config.cache_dir == "~/.opendict_cache"
        assert config.max_audio_duration == 60
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.format == "wav"


class TestSecurityConfig:
    """Test SecurityConfig dataclass."""

    def test_default_security_config(self):
        """Test default security configuration."""
        config = SecurityConfig()

        assert config.enable_input_validation is True
        assert config.max_request_size == 104857600  # 100MB
        assert config.allowed_file_types == ["wav", "mp3", "flac", "m4a"]

    def test_custom_allowed_file_types(self):
        """Test custom allowed file types."""
        config = SecurityConfig(allowed_file_types=["wav", "mp3"])

        assert config.allowed_file_types == ["wav", "mp3"]


class TestConfigManager:
    """Test ConfigManager class."""

    def test_default_config_manager(self):
        """Test default configuration manager."""
        manager = ConfigManager()
        config = manager.get_config()

        assert isinstance(config, AppConfig)
        assert config.environment == Environment.DEVELOPMENT.value

    def test_config_manager_with_file(self, config_manager):
        """Test configuration manager with config file."""
        config = config_manager.get_config()

        assert config.environment == "test"
        assert config.debug is True
        assert config.server.port == 8766
        assert config.transcription.model_name == "test_model"

    def test_environment_overrides(self, config_manager):
        """Test environment variable overrides."""
        os.environ["OPENDICT_PORT"] = "9999"
        os.environ["OPENDICT_HOST"] = "0.0.0.0"
        os.environ["OPENDICT_DEBUG"] = "false"

        manager = ConfigManager(config_manager.config_path)
        config = manager.get_config()

        assert config.server.port == 9999
        assert config.server.host == "0.0.0.0"
        assert config.debug is False

        # Cleanup
        del os.environ["OPENDICT_PORT"]
        del os.environ["OPENDICT_HOST"]
        del os.environ["OPENDICT_DEBUG"]

    def test_invalid_port_environment(self, config_manager):
        """Test invalid port environment variable."""
        os.environ["OPENDICT_PORT"] = "invalid"

        manager = ConfigManager(config_manager.config_path)
        config = manager.get_config()

        # Should use default port when invalid
        assert config.server.port == 8766  # From test config

        # Cleanup
        del os.environ["OPENDICT_PORT"]

    def test_save_config(self, config_manager, temp_dir):
        """Test saving configuration to file."""
        save_path = Path(temp_dir) / "test_config.json"
        config_manager.save_config(str(save_path))

        assert save_path.exists()

        # Verify saved content
        with open(save_path) as f:
            saved_config = json.load(f)

        assert saved_config["environment"] == "test"
        assert saved_config["debug"] is True
        assert saved_config["server"]["port"] == 8766

    def test_update_config(self, config_manager):
        """Test updating configuration values."""
        original_debug = config_manager.get_config().debug
        config_manager.update_config(debug=not original_debug)

        assert config_manager.get_config().debug == (not original_debug)

    def test_is_production(self, config_manager):
        """Test production environment check."""
        assert not config_manager.is_production()

        config_manager.update_config(environment=Environment.PRODUCTION.value)
        assert config_manager.is_production()

    def test_is_development(self, config_manager):
        """Test development environment check."""
        config_manager.update_config(environment=Environment.DEVELOPMENT.value)
        assert config_manager.is_development()

    def test_nonexistent_config_file(self):
        """Test loading non-existent config file."""
        manager = ConfigManager("/nonexistent/config.json")
        config = manager.get_config()

        # Should use default configuration
        assert config.environment == Environment.DEVELOPMENT.value

    def test_invalid_json_config(self, temp_dir):
        """Test loading invalid JSON config file."""
        invalid_config_path = Path(temp_dir) / "invalid.json"
        invalid_config_path.write_text("invalid json content")

        manager = ConfigManager(str(invalid_config_path))
        config = manager.get_config()

        # Should use default configuration
        assert config.environment == Environment.DEVELOPMENT.value


class TestGlobalConfig:
    """Test global configuration functions."""

    def test_get_config(self):
        """Test getting global configuration."""
        from config import get_config

        config = get_config()
        assert isinstance(config, AppConfig)

    def test_get_config_manager(self):
        """Test getting global configuration manager."""
        from config import get_config_manager

        manager = get_config_manager()
        assert isinstance(manager, ConfigManager)

    def test_reload_config(self):
        """Test reloading configuration."""
        from config import get_config, reload_config

        config1 = get_config()
        reload_config()
        config2 = get_config()

        # Should be different instances
        assert config1 is not config2
