# OpenDict API Documentation

This document provides comprehensive API documentation for OpenDict components.

## Table of Contents

- [Python Server API](#python-server-api)
- [Swift Client API](#swift-client-api)
- [Configuration API](#configuration-api)
- [Logging API](#logging-api)
- [Error Handling API](#error-handling-api)

## Python Server API

### TranscriptionServer Class

The main server class that handles transcription requests.

#### Constructor

```python
class TranscriptionServer:
    def __init__(self, port: int = 8765)
```

**Parameters:**
- `port` (int): TCP port number for the server (default: 8765)

#### Methods

##### `load_model()`

Loads the transcription model from cache or downloads it fresh.

```python
def load_model(self) -> None
```

**Raises:**
- `ModelError`: If model loading fails

##### `transcribe_audio(audio_file_path: str)`

Transcribes audio from the given file path.

```python
def transcribe_audio(self, audio_file_path: str) -> str
```

**Parameters:**
- `audio_file_path` (str): Path to the audio file

**Returns:**
- `str`: Transcribed text

**Raises:**
- `ModelError`: If model is not loaded
- `AudioProcessingError`: If audio processing fails

##### `start_server()`

Starts the TCP server and begins accepting connections.

```python
def start_server(self) -> None
```

**Raises:**
- `ServerError`: If server startup fails

##### `stop_server()`

Stops the server and closes all connections.

```python
def stop_server(self) -> None
```

### Network Protocol

#### Request Format

All requests must be JSON-encoded and sent over TCP.

```json
{
    "action": "transcribe",
    "audio_file": "/path/to/audio.wav"
}
```

**Fields:**
- `action` (str): Action type ("transcribe" or "shutdown")
- `audio_file` (str): Full path to audio file (required for transcribe)

#### Response Format

##### Success Response

```json
{
    "status": "success",
    "text": "Transcribed text here"
}
```

**Fields:**
- `status` (str): "success"
- `text` (str): Transcribed text

##### Error Response

```json
{
    "status": "error",
    "error_code": "ERROR_CODE",
    "message": "Error description",
    "recoverable": true,
    "retry_count": 0
}
```

**Fields:**
- `status` (str): "error"
- `error_code` (str): Error code from `ErrorCode` enum
- `message` (str): Human-readable error message
- `recoverable` (bool): Whether the error can be retried
- `retry_count` (int): Number of retry attempts

##### Shutdown Response

```json
{
    "status": "shutdown"
}
```

### Standalone Transcription API

#### `transcribe_audio(input_file_path: str)`

Transcribes audio from a file using the standalone function.

```python
def transcribe_audio(input_file_path: str) -> str
```

**Parameters:**
- `input_file_path` (str): Path to the audio file

**Returns:**
- `str`: Transcribed text

**Raises:**
- `ModelError`: If model loading fails
- `AudioProcessingError`: If audio processing fails

#### `load_or_cache_model()`

Loads the transcription model, using cache if available.

```python
def load_or_cache_model() -> ASRModel
```

**Returns:**
- `ASRModel`: Loaded NeMo ASR model

**Raises:**
- `ModelError`: If model loading fails

## Swift Client API

### AudioRecorder Class

Manages audio recording functionality.

#### Properties

```swift
@Published var isGlobalRecording: Bool
@Published var isTranscribing: Bool
```

#### Methods

##### `startGlobalRecording()`

Starts global audio recording.

```swift
func startGlobalRecording()
```

##### `stopGlobalRecording()`

Stops global audio recording and initiates transcription.

```swift
func stopGlobalRecording()
```

##### `cancelTranscription()`

Cancels ongoing transcription.

```swift
func cancelTranscription()
```

##### `shutdown()`

Shuts down the audio recorder and cleans up resources.

```swift
func shutdown()
```

### GlobalHotkeyManager Class

Manages global keyboard shortcuts.

#### Properties

```swift
@Published var isHotkeyPressed: Bool
```

#### Methods

##### `init()`

Initializes the hotkey manager and sets up global event monitoring.

```swift
init()
```

##### `deinit`

Cleans up event monitors and resources.

```swift
deinit
```

### AccessibilityManager Class

Handles accessibility permissions and text insertion.

#### Properties

```swift
@Published var hasAccessibilityPermissions: Bool
```

#### Methods

##### `checkAccessibilityPermissions()`

Checks current accessibility permission status.

```swift
func checkAccessibilityPermissions()
```

##### `requestAccessibilityPermissions()`

Requests accessibility permissions from the user.

```swift
func requestAccessibilityPermissions()
```

##### `insertTextAtCursor(_:)`

Inserts text at the current cursor position.

```swift
func insertTextAtCursor(_ text: String)
```

**Parameters:**
- `text` (String): Text to insert

### SimpleTranscriptionClient Class

Handles communication with the Python server.

#### Methods

##### `transcribeAudio(audioFilePath:completion:)`

Sends transcription request to the server.

```swift
func transcribeAudio(
    audioFilePath: String,
    completion: @escaping (Result<String, Error>) -> Void
)
```

**Parameters:**
- `audioFilePath` (String): Path to audio file
- `completion` (Function): Completion handler with result

##### `shutdown()`

Shuts down the client and closes connections.

```swift
func shutdown()
```

### Error Types

#### SimpleTranscriptionError

```swift
enum SimpleTranscriptionError: Error {
    case connectionFailed(String)
    case noResponse
    case serverError(String)
    case unknownResponse
    case invalidResponse
}
```

## Configuration API

### AppConfig Class

Main configuration container.

#### Properties

```python
@dataclass
class AppConfig:
    environment: str
    debug: bool
    server: ServerConfig
    transcription: TranscriptionConfig
    logging: LoggingConfig
    security: SecurityConfig
```

### ServerConfig Class

Server-specific configuration.

#### Properties

```python
@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    max_connections: int = 10
    connection_timeout: int = 30
    request_timeout: int = 120
```

### TranscriptionConfig Class

Transcription-specific configuration.

#### Properties

```python
@dataclass
class TranscriptionConfig:
    model_name: str = "nvidia/parakeet-tdt-0.6b-v2"
    cache_dir: str = "~/.opendict_cache"
    max_audio_duration: int = 60
    sample_rate: int = 16000
    channels: int = 1
    format: str = "wav"
```

### ConfigManager Class

Manages configuration loading and environment overrides.

#### Methods

##### `get_config()`

Gets the current configuration.

```python
def get_config(self) -> AppConfig
```

**Returns:**
- `AppConfig`: Current configuration

##### `save_config(path: Optional[str] = None)`

Saves configuration to file.

```python
def save_config(self, path: Optional[str] = None) -> None
```

**Parameters:**
- `path` (str, optional): Path to save configuration

##### `update_config(**kwargs)`

Updates configuration values.

```python
def update_config(self, **kwargs) -> None
```

**Parameters:**
- `**kwargs`: Configuration values to update

## Logging API

### OpenDictLogger Class

Enhanced logger with structured logging.

#### Methods

##### `debug(message: str, **kwargs)`

Logs debug message with context.

```python
def debug(self, message: str, **kwargs) -> None
```

**Parameters:**
- `message` (str): Log message
- `**kwargs`: Additional context

##### `info(message: str, **kwargs)`

Logs info message with context.

```python
def info(self, message: str, **kwargs) -> None
```

##### `warning(message: str, **kwargs)`

Logs warning message with context.

```python
def warning(self, message: str, **kwargs) -> None
```

##### `error(message: str, **kwargs)`

Logs error message with context.

```python
def error(self, message: str, **kwargs) -> None
```

##### `exception(message: str, **kwargs)`

Logs exception with traceback.

```python
def exception(self, message: str, **kwargs) -> None
```

#### Specialized Logging Methods

##### `log_request(client_addr: str, action: str, audio_file: str = None)`

Logs incoming request.

```python
def log_request(self, client_addr: str, action: str, audio_file: str = None) -> None
```

##### `log_response(client_addr: str, status: str, processing_time: float = None)`

Logs response sent.

```python
def log_response(self, client_addr: str, status: str, processing_time: float = None) -> None
```

##### `log_model_loading(model_name: str, load_time: float = None, from_cache: bool = False)`

Logs model loading event.

```python
def log_model_loading(self, model_name: str, load_time: float = None, from_cache: bool = False) -> None
```

### Decorators

#### `@log_performance`

Decorator to log function performance.

```python
@log_performance(logger=None, operation=None)
def my_function():
    pass
```

**Parameters:**
- `logger` (OpenDictLogger, optional): Logger instance
- `operation` (str, optional): Operation name

#### `@log_exceptions`

Decorator to log exceptions.

```python
@log_exceptions(logger=None, reraise=True)
def my_function():
    pass
```

**Parameters:**
- `logger` (OpenDictLogger, optional): Logger instance
- `reraise` (bool): Whether to reraise exceptions

## Error Handling API

### Error Classes

#### OpenDictError

Base error class for all OpenDict errors.

```python
class OpenDictError(Exception):
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        context: Optional[ErrorContext] = None,
        recoverable: bool = True,
        retry_count: int = 0
    )
```

#### Specific Error Classes

- `ConfigurationError`: Configuration-related errors
- `NetworkError`: Network-related errors
- `ModelError`: Model-related errors
- `AudioProcessingError`: Audio processing errors
- `ServerError`: Server-related errors
- `ClientError`: Client-related errors
- `PermissionError`: Permission-related errors
- `ValidationError`: Validation errors

### ErrorCode Enum

Defines error codes for different error types.

```python
class ErrorCode(Enum):
    # Configuration errors
    CONFIG_INVALID = "CONFIG_INVALID"
    CONFIG_MISSING = "CONFIG_MISSING"

    # Network errors
    NETWORK_CONNECTION_FAILED = "NETWORK_CONNECTION_FAILED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"

    # Model errors
    MODEL_LOADING_FAILED = "MODEL_LOADING_FAILED"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"

    # ... and more
```

### ErrorHandler Class

Handles errors with recovery strategies.

#### Methods

##### `handle_error(error: Exception, context: Dict[str, Any] = None)`

Handles error with appropriate strategy.

```python
def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Optional[Any]
```

**Parameters:**
- `error` (Exception): Error to handle
- `context` (dict, optional): Additional context

**Returns:**
- `Any`: Recovery result or None

##### `get_error_statistics()`

Gets error statistics for monitoring.

```python
def get_error_statistics(self) -> Dict[str, Any]
```

**Returns:**
- `dict`: Error statistics

### Utility Functions

#### `handle_error(error: Exception, context: Dict[str, Any] = None)`

Global error handling function.

```python
def handle_error(error: Exception, context: Dict[str, Any] = None) -> Optional[Any]
```

#### `create_error_response(error: OpenDictError)`

Creates standardized error response.

```python
def create_error_response(error: OpenDictError) -> Dict[str, Any]
```

**Parameters:**
- `error` (OpenDictError): Error to convert

**Returns:**
- `dict`: Standardized error response

### Decorators

#### `@handle_exceptions`

Decorator to handle exceptions with error handler.

```python
@handle_exceptions(error_handler=None, reraise=True)
def my_function():
    pass
```

**Parameters:**
- `error_handler` (ErrorHandler, optional): Error handler instance
- `reraise` (bool): Whether to reraise exceptions

## Usage Examples

### Python Server Usage

```python
from transcribe_server import TranscriptionServer
from logging_config import get_logger

# Create and start server
server = TranscriptionServer(port=8765)
logger = get_logger()

try:
    server.start_server()
except Exception as e:
    logger.exception("Server startup failed")
```

### Swift Client Usage

```swift
import SwiftUI

class ViewModel: ObservableObject {
    @Published var audioRecorder = AudioRecorder()
    @Published var accessibilityManager = AccessibilityManager()
    @Published var hotkeyManager = GlobalHotkeyManager()

    init() {
        audioRecorder.accessibilityManager = accessibilityManager
        hotkeyManager.audioRecorder = audioRecorder
    }
}
```

### Configuration Usage

```python
from config import get_config, get_config_manager

# Get configuration
config = get_config()
print(f"Server port: {config.server.port}")

# Update configuration
config_manager = get_config_manager()
config_manager.update_config(debug=True)
```

### Error Handling Usage

```python
from error_handling import handle_error, ModelError, ErrorCode

try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    # Handle error with recovery
    handle_error(e, {"operation": "risky_operation"})
```

For more examples and detailed usage, see the [Developer Guide](DEVELOPER_GUIDE.md).
