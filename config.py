"""
OpenDict Configuration Management
Centralized configuration system with environment support
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Environment(Enum):
    """Environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ServerConfig:
    """Server configuration settings."""

    host: str = "127.0.0.1"
    port: int = 8765
    max_connections: int = 10
    connection_timeout: int = 30
    request_timeout: int = 120


@dataclass
class TranscriptionConfig:
    """Transcription model configuration."""

    model_name: str = "nvidia/parakeet-tdt-0.6b-v2"
    cache_dir: str = "~/.opendict_cache"
    max_audio_duration: int = 60
    sample_rate: int = 16000
    channels: int = 1
    format: str = "wav"


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class SecurityConfig:
    """Security configuration."""

    enable_input_validation: bool = True
    max_request_size: int = 104857600  # 100MB
    allowed_file_types: List[str] = field(
        default_factory=lambda: ["wav", "mp3", "flac", "m4a"]
    )

    def __post_init__(self) -> None:
        pass


@dataclass
class AppConfig:
    """Main application configuration."""

    environment: str = Environment.DEVELOPMENT.value
    debug: bool = False
    server: ServerConfig = field(default_factory=ServerConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    def __post_init__(self) -> None:
        pass


class ConfigManager:
    """Configuration manager with environment support."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self._apply_environment_overrides()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        env = os.getenv("OPENDICT_ENV", "development")
        return f"config/{env}.json"

    def _load_config(self) -> AppConfig:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config_data = json.load(f)
                return self._dict_to_config(config_data)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logging.warning(f"Could not load config from {self.config_path}: {e}")

        return AppConfig()

    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig object."""
        server_data = data.get("server", {})
        transcription_data = data.get("transcription", {})
        logging_data = data.get("logging", {})
        security_data = data.get("security", {})

        return AppConfig(
            environment=data.get("environment", Environment.DEVELOPMENT.value),
            debug=data.get("debug", False),
            server=ServerConfig(**server_data),
            transcription=TranscriptionConfig(**transcription_data),
            logging=LoggingConfig(**logging_data),
            security=SecurityConfig(**security_data),
        )

    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Environment
        if env := os.getenv("OPENDICT_ENV"):
            self.config.environment = env

        # Debug mode
        if debug := os.getenv("OPENDICT_DEBUG"):
            self.config.debug = debug.lower() in ("true", "1", "yes")

        # Server configuration
        if host := os.getenv("OPENDICT_HOST"):
            self.config.server.host = host

        if port := os.getenv("OPENDICT_PORT"):
            try:
                self.config.server.port = int(port)
            except ValueError:
                logging.warning(f"Invalid port value: {port}")

        # Transcription configuration
        if model := os.getenv("OPENDICT_MODEL"):
            self.config.transcription.model_name = model

        if cache_dir := os.getenv("OPENDICT_CACHE_DIR"):
            self.config.transcription.cache_dir = cache_dir

        # Logging configuration
        if log_level := os.getenv("OPENDICT_LOG_LEVEL"):
            self.config.logging.level = log_level.upper()

        if log_file := os.getenv("OPENDICT_LOG_FILE"):
            self.config.logging.file = log_file

    def save_config(self, path: Optional[str] = None) -> None:
        """Save configuration to file."""
        save_path = path or self.config_path

        # Create directory if it doesn't exist
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary
        config_dict = asdict(self.config)

        # Save to file
        with open(save_path, "w") as f:
            json.dump(config_dict, f, indent=2)

    def get_config(self) -> AppConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, **kwargs: Any) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.config.environment == Environment.PRODUCTION.value

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.config.environment == Environment.DEVELOPMENT.value


# Global configuration instance
_config_manager = None


def get_config() -> AppConfig:
    """Get global configuration instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_config() -> None:
    """Reload configuration from file."""
    global _config_manager
    _config_manager = ConfigManager()


if __name__ == "__main__":
    # Example usage
    config = get_config()
    print(f"Environment: {config.environment}")
    print(f"Server: {config.server.host}:{config.server.port}")
    print(f"Model: {config.transcription.model_name}")
    print(f"Debug: {config.debug}")
