"""
Tests for transcription server functionality.
"""

import json
import socket
import tempfile
import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from transcribe_server import TranscriptionServer


class TestTranscriptionServer:
    """Test TranscriptionServer class."""

    def test_server_initialization(self):
        """Test server initialization."""
        server = TranscriptionServer(port=8766)

        assert server.port == 8766
        assert server.model is None
        assert server.server_socket is None
        assert server.running is False

    def test_get_model_cache_path(self):
        """Test getting model cache path."""
        server = TranscriptionServer()
        cache_path = server.get_model_cache_path()

        assert cache_path.endswith("parakeet_model.pkl")
        assert ".opendict_cache" in cache_path

    @patch("transcribe_server.nemo_asr.models.ASRModel.from_pretrained")
    @patch("pickle.dump")
    @patch("pickle.load")
    @patch("os.path.exists")
    def test_load_model_from_cache(
        self, mock_exists, mock_load, mock_dump, mock_pretrained
    ):
        """Test loading model from cache."""
        mock_exists.return_value = True
        mock_model = Mock()
        mock_load.return_value = mock_model

        server = TranscriptionServer()
        server.load_model()

        assert server.model == mock_model
        mock_load.assert_called_once()
        mock_pretrained.assert_not_called()

    @patch("transcribe_server.nemo_asr.models.ASRModel.from_pretrained")
    @patch("pickle.dump")
    @patch("os.path.exists")
    def test_load_model_fresh(self, mock_exists, mock_dump, mock_pretrained):
        """Test loading fresh model."""
        mock_exists.return_value = False
        mock_model = Mock()
        mock_pretrained.return_value = mock_model

        server = TranscriptionServer()
        server.load_model()

        assert server.model == mock_model
        mock_pretrained.assert_called_once_with(
            model_name="nvidia/parakeet-tdt-0.6b-v2"
        )
        mock_dump.assert_called_once()

    @patch("transcribe_server.nemo_asr.models.ASRModel.from_pretrained")
    @patch("pickle.dump")
    @patch("pickle.load")
    @patch("os.path.exists")
    def test_load_model_cache_corruption(
        self, mock_exists, mock_load, mock_dump, mock_pretrained
    ):
        """Test handling corrupted cache."""
        mock_exists.return_value = True
        mock_load.side_effect = Exception("Cache corrupted")
        mock_model = Mock()
        mock_pretrained.return_value = mock_model

        server = TranscriptionServer()
        server.load_model()

        assert server.model == mock_model
        mock_pretrained.assert_called_once()

    def test_transcribe_audio_no_model(self):
        """Test transcribing audio without loaded model."""
        server = TranscriptionServer()

        with pytest.raises(Exception, match="Model not loaded"):
            server.transcribe_audio("test.wav")

    def test_transcribe_audio_success(self, mock_nemo_model):
        """Test successful audio transcription."""
        server = TranscriptionServer()
        server.model = mock_nemo_model

        result = server.transcribe_audio("test.wav")

        assert result == "Hello world"
        mock_nemo_model.transcribe.assert_called_once_with(["test.wav"])

    @patch("socket.socket")
    def test_start_server(self, mock_socket_class):
        """Test starting the server."""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        server = TranscriptionServer(port=8766)
        server.model = Mock()  # Mock loaded model

        # Mock accept to avoid blocking
        mock_socket.accept.side_effect = Exception("Stop server")

        with pytest.raises(Exception, match="Stop server"):
            server.start_server()

        mock_socket.setsockopt.assert_called_once()
        mock_socket.bind.assert_called_once_with(("localhost", 8766))
        mock_socket.listen.assert_called_once_with(1)

    @patch("tempfile.gettempdir")
    @patch("json.dump")
    @patch("builtins.open", new_callable=MagicMock)
    def test_handle_client_transcribe_success(
        self, mock_open, mock_json_dump, mock_tempdir
    ):
        """Test handling successful transcription request."""
        mock_tempdir.return_value = "/tmp"

        server = TranscriptionServer()
        server.model = Mock()
        server.model.transcribe.return_value = [Mock(text="Hello world")]

        mock_client = Mock()
        mock_client.recv.return_value = json.dumps(
            {"action": "transcribe", "audio_file": "test.wav"}
        ).encode("utf-8")

        server.handle_client(mock_client)

        mock_client.send.assert_called_once()
        sent_data = mock_client.send.call_args[0][0]
        response = json.loads(sent_data.decode("utf-8"))

        assert response["status"] == "success"
        assert response["text"] == "Hello world"

    def test_handle_client_transcribe_error(self):
        """Test handling transcription error."""
        server = TranscriptionServer()
        server.model = Mock()
        server.model.transcribe.side_effect = Exception("Transcription failed")

        mock_client = Mock()
        mock_client.recv.return_value = json.dumps(
            {"action": "transcribe", "audio_file": "test.wav"}
        ).encode("utf-8")

        server.handle_client(mock_client)

        mock_client.send.assert_called_once()
        sent_data = mock_client.send.call_args[0][0]
        response = json.loads(sent_data.decode("utf-8"))

        assert response["status"] == "error"
        assert "Transcription failed" in response["error"]

    def test_handle_client_shutdown(self):
        """Test handling shutdown request."""
        server = TranscriptionServer()

        mock_client = Mock()
        mock_client.recv.return_value = json.dumps({"action": "shutdown"}).encode(
            "utf-8"
        )

        server.handle_client(mock_client)

        assert server.running is False
        mock_client.send.assert_called_once()
        sent_data = mock_client.send.call_args[0][0]
        response = json.loads(sent_data.decode("utf-8"))

        assert response["status"] == "shutdown"

    def test_handle_client_unknown_action(self):
        """Test handling unknown action."""
        server = TranscriptionServer()

        mock_client = Mock()
        mock_client.recv.return_value = json.dumps({"action": "unknown"}).encode(
            "utf-8"
        )

        server.handle_client(mock_client)

        mock_client.send.assert_called_once()
        sent_data = mock_client.send.call_args[0][0]
        response = json.loads(sent_data.decode("utf-8"))

        assert response["status"] == "error"
        assert response["error"] == "Unknown action"

    def test_handle_client_invalid_json(self):
        """Test handling invalid JSON request."""
        server = TranscriptionServer()

        mock_client = Mock()
        mock_client.recv.return_value = b"invalid json"

        server.handle_client(mock_client)

        mock_client.close.assert_called_once()

    def test_stop_server(self):
        """Test stopping the server."""
        server = TranscriptionServer()
        server.running = True
        server.server_socket = Mock()

        server.stop_server()

        assert server.running is False
        server.server_socket.close.assert_called_once()


class TestTranscriptionServerIntegration:
    """Integration tests for TranscriptionServer."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_server_client_communication(self):
        """Test actual server-client communication."""
        server = TranscriptionServer(port=8767)
        server.model = Mock()
        server.model.transcribe.return_value = [Mock(text="Test transcription")]

        # Start server in a separate thread
        server_thread = threading.Thread(target=server.start_server)
        server_thread.daemon = True
        server_thread.start()

        # Give server time to start
        time.sleep(0.1)

        try:
            # Create client connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("localhost", 8767))

            # Send request
            request = {"action": "transcribe", "audio_file": "test.wav"}
            client_socket.send(json.dumps(request).encode("utf-8"))

            # Receive response
            response_data = client_socket.recv(1024).decode("utf-8")
            response = json.loads(response_data)

            assert response["status"] == "success"
            assert response["text"] == "Test transcription"

            client_socket.close()

        finally:
            server.stop_server()

    @pytest.mark.integration
    def test_server_shutdown_request(self):
        """Test server shutdown via request."""
        server = TranscriptionServer(port=8768)
        server.model = Mock()

        # Start server in a separate thread
        server_thread = threading.Thread(target=server.start_server)
        server_thread.daemon = True
        server_thread.start()

        # Give server time to start
        time.sleep(0.1)

        try:
            # Create client connection
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("localhost", 8768))

            # Send shutdown request
            request = {"action": "shutdown"}
            client_socket.send(json.dumps(request).encode("utf-8"))

            # Receive response
            response_data = client_socket.recv(1024).decode("utf-8")
            response = json.loads(response_data)

            assert response["status"] == "shutdown"

            client_socket.close()

            # Server should have stopped
            server_thread.join(timeout=1)
            assert not server.running

        except Exception:
            server.stop_server()
