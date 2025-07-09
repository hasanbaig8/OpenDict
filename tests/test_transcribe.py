"""
Tests for standalone transcription functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from transcribe import get_model_cache_path, load_or_cache_model, transcribe_audio


class TestTranscribeFunctions:
    """Test standalone transcription functions."""

    def test_get_model_cache_path(self):
        """Test getting model cache path."""
        cache_path = get_model_cache_path()

        assert cache_path.endswith("parakeet_model.pkl")
        assert ".opendict_cache" in cache_path

    @patch("transcribe.nemo_asr.models.ASRModel.from_pretrained")
    @patch("pickle.dump")
    @patch("pickle.load")
    @patch("os.path.exists")
    def test_load_or_cache_model_from_cache(
        self, mock_exists, mock_load, mock_dump, mock_pretrained
    ):
        """Test loading model from cache."""
        mock_exists.return_value = True
        mock_model = Mock()
        mock_load.return_value = mock_model

        result = load_or_cache_model()

        assert result == mock_model
        mock_load.assert_called_once()
        mock_pretrained.assert_not_called()

    @patch("transcribe.nemo_asr.models.ASRModel.from_pretrained")
    @patch("pickle.dump")
    @patch("os.path.exists")
    def test_load_or_cache_model_fresh(self, mock_exists, mock_dump, mock_pretrained):
        """Test loading fresh model."""
        mock_exists.return_value = False
        mock_model = Mock()
        mock_pretrained.return_value = mock_model

        result = load_or_cache_model()

        assert result == mock_model
        mock_pretrained.assert_called_once_with(
            model_name="nvidia/parakeet-tdt-0.6b-v2"
        )
        mock_dump.assert_called_once()

    @patch("transcribe.nemo_asr.models.ASRModel.from_pretrained")
    @patch("pickle.dump")
    @patch("pickle.load")
    @patch("os.path.exists")
    def test_load_or_cache_model_cache_corruption(
        self, mock_exists, mock_load, mock_dump, mock_pretrained
    ):
        """Test handling corrupted cache."""
        mock_exists.return_value = True
        mock_load.side_effect = Exception("Cache corrupted")
        mock_model = Mock()
        mock_pretrained.return_value = mock_model

        result = load_or_cache_model()

        assert result == mock_model
        mock_pretrained.assert_called_once()

    @patch("transcribe.load_or_cache_model")
    def test_transcribe_audio_success(self, mock_load_model):
        """Test successful audio transcription."""
        mock_model = Mock()
        mock_model.transcribe.return_value = [Mock(text="Hello world")]
        mock_load_model.return_value = mock_model

        result = transcribe_audio("test.wav")

        assert result == "Hello world"
        mock_model.transcribe.assert_called_once_with(["test.wav"])

    @patch("transcribe.load_or_cache_model")
    def test_transcribe_audio_model_error(self, mock_load_model):
        """Test transcription with model error."""
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Model error")
        mock_load_model.return_value = mock_model

        with pytest.raises(Exception, match="Model error"):
            transcribe_audio("test.wav")


class TestTranscribeMainFunction:
    """Test the main function of transcribe.py."""

    @patch("transcribe.transcribe_audio")
    @patch("tempfile.gettempdir")
    @patch("json.dump")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("sys.argv", ["transcribe.py", "test.wav"])
    def test_main_function_success(
        self, mock_open, mock_json_dump, mock_tempdir, mock_transcribe
    ):
        """Test successful main function execution."""
        mock_tempdir.return_value = "/tmp"
        mock_transcribe.return_value = "Hello world"

        # Import and run main
        import transcribe

        # Mock stdout to capture output
        with patch("builtins.print") as mock_print:
            transcribe.main()

            # Check that the result was printed
            mock_print.assert_called_once_with(json.dumps({"text": "Hello world"}))

        # Check that transcription was called
        mock_transcribe.assert_called_once_with("test.wav")

        # Check that output file was written
        mock_json_dump.assert_called_once()

    @patch("transcribe.transcribe_audio")
    @patch("sys.argv", ["transcribe.py", "test.wav"])
    def test_main_function_error(self, mock_transcribe):
        """Test main function with transcription error."""
        mock_transcribe.side_effect = Exception("Transcription failed")

        # Import and run main
        import transcribe

        # Mock stdout to capture output
        with patch("builtins.print") as mock_print:
            transcribe.main()

            # Check that error was printed
            mock_print.assert_called_once_with(
                json.dumps({"error": "Transcription failed"})
            )

    @patch("sys.argv", ["transcribe.py"])
    @patch("sys.exit")
    def test_main_function_no_args(self, mock_exit):
        """Test main function without arguments."""
        import transcribe

        # Mock stdout to capture output
        with patch("builtins.print") as mock_print:
            transcribe.main()

            # Check that usage error was printed
            mock_print.assert_called_once_with(
                json.dumps({"error": "Usage: python transcribe.py <input_file_path>"})
            )

        # Check that script exited with error code
        mock_exit.assert_called_once_with(1)

    @patch("sys.argv", ["transcribe.py", "file1.wav", "file2.wav"])
    @patch("sys.exit")
    def test_main_function_too_many_args(self, mock_exit):
        """Test main function with too many arguments."""
        import transcribe

        # Mock stdout to capture output
        with patch("builtins.print") as mock_print:
            transcribe.main()

            # Check that usage error was printed
            mock_print.assert_called_once_with(
                json.dumps({"error": "Usage: python transcribe.py <input_file_path>"})
            )

        # Check that script exited with error code
        mock_exit.assert_called_once_with(1)


class TestTranscribeIntegration:
    """Integration tests for transcribe.py."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_transcribe_with_mock_model(self, mock_audio_file):
        """Test transcription with mock model."""
        with patch("transcribe.load_or_cache_model") as mock_load_model:
            mock_model = Mock()
            mock_model.transcribe.return_value = [Mock(text="Integration test")]
            mock_load_model.return_value = mock_model

            result = transcribe_audio(mock_audio_file)

            assert result == "Integration test"
            mock_model.transcribe.assert_called_once_with([mock_audio_file])

    @pytest.mark.integration
    def test_output_file_creation(self, mock_audio_file, temp_dir):
        """Test that output file is created correctly."""
        with patch("transcribe.load_or_cache_model") as mock_load_model:
            mock_model = Mock()
            mock_model.transcribe.return_value = [Mock(text="File test")]
            mock_load_model.return_value = mock_model

            with patch("tempfile.gettempdir", return_value=temp_dir):
                import transcribe

                with patch("sys.argv", ["transcribe.py", mock_audio_file]):
                    with patch("builtins.print"):
                        transcribe.main()

                # Check that output file was created
                output_path = Path(temp_dir) / "opendict_output.json"
                assert output_path.exists()

                # Check output content
                with open(output_path) as f:
                    output_data = json.load(f)

                assert output_data["text"] == "File test"
