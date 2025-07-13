"""
Pytest configuration and fixtures for OpenDict tests.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from config import AppConfig, ConfigManager


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def config_manager():
    """Create a test configuration manager."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "environment": "test",
            "debug": True,
            "server": {
                "host": "127.0.0.1",
                "port": 8766,  # Different port for testing
                "max_connections": 5,
            },
            "transcription": {
                "model_name": "test_model",
                "cache_dir": str(temp_dir / "test_cache"),
            },
        }
        import json

        json.dump(test_config, f)
        f.flush()

        config_manager = ConfigManager(f.name)
        yield config_manager

        # Cleanup
        os.unlink(f.name)


@pytest.fixture
def mock_audio_file(temp_dir):
    """Create a mock audio file for testing."""
    audio_path = Path(temp_dir) / "test_audio.wav"
    # Create a dummy WAV file (minimal WAV header)
    wav_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    audio_path.write_bytes(wav_header)
    return str(audio_path)


@pytest.fixture
def mock_nemo_model():
    """Mock NeMo ASR model."""
    mock_model = Mock()
    mock_model.transcribe.return_value = [Mock(text="Hello world")]
    return mock_model


@pytest.fixture
def mock_socket():
    """Mock socket for testing network communication."""
    with patch("socket.socket") as mock_sock:
        mock_instance = Mock()
        mock_sock.return_value = mock_instance
        mock_instance.connect.return_value = None
        mock_instance.send.return_value = 100
        mock_instance.recv.return_value = (
            b'{"status": "success", "text": "Hello world"}'
        )
        mock_instance.close.return_value = None
        yield mock_instance


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "OPENDICT_ENV": "test",
        "OPENDICT_DEBUG": "true",
        "OPENDICT_LOG_LEVEL": "DEBUG",
    }

    # Set environment variables
    for key, value in test_env.items():
        os.environ[key] = value

    yield

    # Cleanup environment variables
    for key in test_env:
        os.environ.pop(key, None)


@pytest.fixture
def sample_transcription_request():
    """Sample transcription request data."""
    return {"action": "transcribe", "audio_file": "/path/to/test.wav"}


@pytest.fixture
def sample_transcription_response():
    """Sample transcription response data."""
    return {"status": "success", "text": "This is a test transcription"}


@pytest.fixture
def sample_error_response():
    """Sample error response data."""
    return {"status": "error", "error": "Test error message"}


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
