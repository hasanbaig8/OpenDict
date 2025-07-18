"""Transcription server for OpenDict."""

import json
import os
import socket
import sys
import tempfile
import threading
import time
from typing import Any, Optional

import nemo.collections.asr as nemo_asr


class TranscriptionServer:
    """Server for handling transcription requests."""

    def __init__(self, port: int = 8765) -> None:
        """Initialize the transcription server."""
        self.port = port
        self.model: Optional[Any] = None
        self.server_socket: Optional[socket.socket] = None
        self.running = False

    def load_model(self) -> None:
        """Load model using NeMo's built-in caching."""
        print("Loading model (using built-in cache if available)...", file=sys.stderr)
        start_time = time.time()

        # NeMo automatically caches models in ~/.cache/huggingface/hub/
        # No need for custom pickle caching
        self.model = nemo_asr.models.ASRModel.from_pretrained(
            model_name="nvidia/parakeet-tdt-0.6b-v2"
        )

        load_time = time.time() - start_time
        print(f"Model loaded in {load_time:.2f} seconds", file=sys.stderr)

    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio file."""
        if not self.model:
            raise Exception("Model not loaded")

        output = self.model.transcribe([audio_file_path])
        return output[0].text

    def start_server(self) -> None:
        """Start the transcription server."""
        self.load_model()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("localhost", self.port))
        self.server_socket.listen(1)
        self.running = True

        print(f"Transcription server listening on port {self.port}", file=sys.stderr)

        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_client, args=(client_socket,)
                )
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}", file=sys.stderr)
                continue

    def handle_client(self, client_socket: socket.socket) -> None:
        """Handle client connection."""
        try:
            print("Client connected", file=sys.stderr)

            # Set socket timeout to prevent hanging
            client_socket.settimeout(60.0)

            # Receive request
            data = client_socket.recv(1024).decode("utf-8")
            if not data.strip():
                print("Received empty request, closing connection", file=sys.stderr)
                return

            print(f"Received request: {data}", file=sys.stderr)
            request = json.loads(data)

            if request["action"] == "transcribe":
                audio_file = request["audio_file"]

                # Transcribe audio
                try:
                    print(f"Transcribing audio file: {audio_file}", file=sys.stderr)
                    text = self.transcribe_audio(audio_file)
                    print(f"Transcription complete: {text[:50]}...", file=sys.stderr)

                    # Save result to temp file
                    temp_dir = tempfile.gettempdir()
                    output_path = os.path.join(temp_dir, "opendict_output.json")

                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump({"text": text}, f, ensure_ascii=False, indent=2)

                    response = {"status": "success", "text": text}
                    print("Sending success response", file=sys.stderr)
                except Exception as e:
                    print(f"Transcription error: {e}", file=sys.stderr)
                    response = {"status": "error", "error": str(e)}

            elif request["action"] == "shutdown":
                response = {"status": "shutdown"}
                self.running = False

            else:
                response = {"status": "error", "error": "Unknown action"}

            # Send response
            client_socket.send(json.dumps(response).encode("utf-8"))

        except Exception as e:
            print(f"Client handling error: {e}", file=sys.stderr)
        finally:
            client_socket.close()

    def stop_server(self) -> None:
        """Stop the server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


if __name__ == "__main__":
    server = TranscriptionServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("Server shutting down...", file=sys.stderr)
        server.stop_server()
