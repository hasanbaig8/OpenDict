"""
OpenDict Error Handling System
Comprehensive error handling with proper error types and recovery
"""

import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, Union

from logging_config import get_logger


class ErrorCode(Enum):
    """Error codes for different types of errors."""

    # Configuration errors
    CONFIG_INVALID = "CONFIG_INVALID"
    CONFIG_MISSING = "CONFIG_MISSING"

    # Network errors
    NETWORK_CONNECTION_FAILED = "NETWORK_CONNECTION_FAILED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_INVALID_RESPONSE = "NETWORK_INVALID_RESPONSE"

    # Model errors
    MODEL_LOADING_FAILED = "MODEL_LOADING_FAILED"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_INFERENCE_FAILED = "MODEL_INFERENCE_FAILED"

    # Audio processing errors
    AUDIO_FILE_NOT_FOUND = "AUDIO_FILE_NOT_FOUND"
    AUDIO_FORMAT_UNSUPPORTED = "AUDIO_FORMAT_UNSUPPORTED"
    AUDIO_PROCESSING_FAILED = "AUDIO_PROCESSING_FAILED"

    # Server errors
    SERVER_STARTUP_FAILED = "SERVER_STARTUP_FAILED"
    SERVER_PORT_UNAVAILABLE = "SERVER_PORT_UNAVAILABLE"
    SERVER_REQUEST_INVALID = "SERVER_REQUEST_INVALID"

    # Client errors
    CLIENT_CONNECTION_FAILED = "CLIENT_CONNECTION_FAILED"
    CLIENT_REQUEST_FAILED = "CLIENT_REQUEST_FAILED"
    CLIENT_RESPONSE_INVALID = "CLIENT_RESPONSE_INVALID"

    # Permission errors
    PERMISSION_DENIED = "PERMISSION_DENIED"
    ACCESSIBILITY_PERMISSION_REQUIRED = "ACCESSIBILITY_PERMISSION_REQUIRED"

    # Validation errors
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INPUT_INVALID = "INPUT_INVALID"

    # System errors
    SYSTEM_RESOURCE_UNAVAILABLE = "SYSTEM_RESOURCE_UNAVAILABLE"
    SYSTEM_PERMISSION_DENIED = "SYSTEM_PERMISSION_DENIED"

    # Generic errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    OPERATION_FAILED = "OPERATION_FAILED"


@dataclass
class ErrorContext:
    """Context information for errors."""

    operation: str
    component: str
    details: Dict[str, Any]
    timestamp: float

    @classmethod
    def create(cls, operation: str, component: str, **details) -> "ErrorContext":
        """Create error context with current timestamp."""
        import time

        return cls(
            operation=operation,
            component=component,
            details=details,
            timestamp=time.time(),
        )


class OpenDictError(Exception):
    """Base exception class for OpenDict errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        context: Optional[ErrorContext] = None,
        recoverable: bool = True,
        retry_count: int = 0,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context
        self.recoverable = recoverable
        self.retry_count = retry_count
        self.traceback = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "recoverable": self.recoverable,
            "retry_count": self.retry_count,
            "context": {
                "operation": self.context.operation if self.context else None,
                "component": self.context.component if self.context else None,
                "details": self.context.details if self.context else {},
                "timestamp": self.context.timestamp if self.context else None,
            },
            "traceback": self.traceback,
        }


class ConfigurationError(OpenDictError):
    """Configuration-related errors."""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(
            message,
            ErrorCode.CONFIG_INVALID,
            ErrorContext.create(
                "configuration", "config_manager", config_key=config_key
            ),
            recoverable=False,
            **kwargs,
        )


class NetworkError(OpenDictError):
    """Network-related errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        host: str = None,
        port: int = None,
        **kwargs,
    ):
        super().__init__(
            message,
            error_code,
            ErrorContext.create("network", "client", host=host, port=port),
            recoverable=True,
            **kwargs,
        )


class ModelError(OpenDictError):
    """Model-related errors."""

    def __init__(
        self, message: str, error_code: ErrorCode, model_name: str = None, **kwargs
    ):
        super().__init__(
            message,
            error_code,
            ErrorContext.create("model", "transcription_server", model_name=model_name),
            recoverable=error_code != ErrorCode.MODEL_NOT_FOUND,
            **kwargs,
        )


class AudioProcessingError(OpenDictError):
    """Audio processing errors."""

    def __init__(
        self, message: str, error_code: ErrorCode, audio_file: str = None, **kwargs
    ):
        super().__init__(
            message,
            error_code,
            ErrorContext.create(
                "audio_processing", "transcription_server", audio_file=audio_file
            ),
            recoverable=error_code != ErrorCode.AUDIO_FILE_NOT_FOUND,
            **kwargs,
        )


class ServerError(OpenDictError):
    """Server-related errors."""

    def __init__(self, message: str, error_code: ErrorCode, port: int = None, **kwargs):
        super().__init__(
            message,
            error_code,
            ErrorContext.create("server", "transcription_server", port=port),
            recoverable=error_code != ErrorCode.SERVER_PORT_UNAVAILABLE,
            **kwargs,
        )


class ClientError(OpenDictError):
    """Client-related errors."""

    def __init__(self, message: str, error_code: ErrorCode, **kwargs):
        super().__init__(
            message,
            error_code,
            ErrorContext.create("client", "transcription_client"),
            recoverable=True,
            **kwargs,
        )


class PermissionError(OpenDictError):
    """Permission-related errors."""

    def __init__(
        self, message: str, error_code: ErrorCode, permission_type: str = None, **kwargs
    ):
        super().__init__(
            message,
            error_code,
            ErrorContext.create(
                "permission", "accessibility_manager", permission_type=permission_type
            ),
            recoverable=True,
            **kwargs,
        )


class ValidationError(OpenDictError):
    """Validation errors."""

    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        super().__init__(
            message,
            ErrorCode.VALIDATION_FAILED,
            ErrorContext.create(
                "validation", "validator", field=field, value=str(value)
            ),
            recoverable=False,
            **kwargs,
        )


class ErrorHandler:
    """Error handler with logging and recovery strategies."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.error_counts = {}
        self.recovery_strategies = self._setup_recovery_strategies()

    def _setup_recovery_strategies(self) -> Dict[ErrorCode, Callable]:
        """Set up recovery strategies for different error types."""
        return {
            ErrorCode.NETWORK_CONNECTION_FAILED: self._retry_with_backoff,
            ErrorCode.NETWORK_TIMEOUT: self._retry_with_backoff,
            ErrorCode.MODEL_LOADING_FAILED: self._retry_model_loading,
            ErrorCode.AUDIO_PROCESSING_FAILED: self._skip_and_continue,
            ErrorCode.SERVER_PORT_UNAVAILABLE: self._try_alternative_port,
            ErrorCode.CLIENT_CONNECTION_FAILED: self._retry_with_backoff,
        }

    def handle_error(
        self, error: Exception, context: Dict[str, Any] = None
    ) -> Optional[Any]:
        """Handle error with appropriate strategy."""
        # Convert to OpenDictError if needed
        if not isinstance(error, OpenDictError):
            error = self._convert_to_opendict_error(error, context)

        # Log error
        self._log_error(error)

        # Update error count
        self._update_error_count(error.error_code)

        # Try recovery if available and error is recoverable
        if error.recoverable and error.error_code in self.recovery_strategies:
            return self._attempt_recovery(error)

        # Re-raise if not recoverable
        raise error

    def _convert_to_opendict_error(
        self, error: Exception, context: Dict[str, Any] = None
    ) -> OpenDictError:
        """Convert generic exception to OpenDictError."""
        error_message = str(error)
        error_code = ErrorCode.UNKNOWN_ERROR

        # Try to determine error type based on exception type and message
        if isinstance(error, FileNotFoundError):
            error_code = ErrorCode.AUDIO_FILE_NOT_FOUND
        elif isinstance(error, ConnectionError):
            error_code = ErrorCode.NETWORK_CONNECTION_FAILED
        elif isinstance(error, TimeoutError):
            error_code = ErrorCode.NETWORK_TIMEOUT
        elif isinstance(error, PermissionError):
            error_code = ErrorCode.PERMISSION_DENIED
        elif isinstance(error, ValueError):
            error_code = ErrorCode.INPUT_INVALID

        return OpenDictError(
            error_message,
            error_code,
            ErrorContext.create(
                "unknown",
                "system",
                original_error=type(error).__name__,
                **context or {},
            ),
        )

    def _log_error(self, error: OpenDictError):
        """Log error with structured information."""
        self.logger.log_error(
            error.error_code.value,
            error.message,
            error.context.details if error.context else {},
        )

    def _update_error_count(self, error_code: ErrorCode):
        """Update error count for monitoring."""
        if error_code not in self.error_counts:
            self.error_counts[error_code] = 0
        self.error_counts[error_code] += 1

    def _attempt_recovery(self, error: OpenDictError) -> Optional[Any]:
        """Attempt recovery using appropriate strategy."""
        recovery_strategy = self.recovery_strategies[error.error_code]
        try:
            return recovery_strategy(error)
        except Exception as recovery_error:
            self.logger.error(
                f"Recovery failed for {error.error_code.value}",
                original_error=error.message,
                recovery_error=str(recovery_error),
            )
            raise error  # Re-raise original error

    def _retry_with_backoff(
        self, error: OpenDictError, max_retries: int = 3
    ) -> Optional[Any]:
        """Retry with exponential backoff."""
        if error.retry_count >= max_retries:
            raise error

        import time

        wait_time = 2**error.retry_count
        self.logger.info(
            f"Retrying after {wait_time} seconds (attempt {error.retry_count + 1}/{max_retries})"
        )
        time.sleep(wait_time)

        # Increment retry count
        error.retry_count += 1
        return None  # Indicate retry should be attempted

    def _retry_model_loading(self, error: OpenDictError) -> Optional[Any]:
        """Retry model loading with cache clearing."""
        if error.retry_count >= 2:
            raise error

        self.logger.info("Clearing model cache and retrying")
        # Clear cache logic would go here
        import os
        import shutil

        cache_dir = os.path.expanduser("~/.opendict_cache")
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)

        error.retry_count += 1
        return None

    def _skip_and_continue(self, error: OpenDictError) -> Optional[Any]:
        """Skip current operation and continue."""
        self.logger.warning(f"Skipping operation due to error: {error.message}")
        return None

    def _try_alternative_port(self, error: OpenDictError) -> Optional[Any]:
        """Try alternative port for server."""
        if error.retry_count >= 5:
            raise error

        if error.context is None:
            return False

        current_port = error.context.details.get("port", 8765)
        new_port = current_port + error.retry_count + 1

        self.logger.info(f"Trying alternative port: {new_port}")
        error.context.details["port"] = new_port
        error.retry_count += 1
        return new_port

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": {
                code.value: count for code, count in self.error_counts.items()
            },
            "most_common_error": (
                max(self.error_counts.items(), key=lambda x: x[1])[0].value
                if self.error_counts
                else None
            ),
        }


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: Exception, context: Dict[str, Any] = None) -> Optional[Any]:
    """Handle error using global error handler."""
    return get_error_handler().handle_error(error, context)


# Error handling decorators
def handle_exceptions(error_handler: ErrorHandler = None, reraise: bool = True):
    """Decorator to handle exceptions with error handler."""
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal error_handler
            if error_handler is None:
                error_handler = get_error_handler()

            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                }

                result = error_handler.handle_error(e, context)
                if result is None and reraise:
                    raise
                return result

        return wrapper

    return decorator


def create_error_response(error: OpenDictError) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "status": "error",
        "error_code": error.error_code.value,
        "message": error.message,
        "recoverable": error.recoverable,
        "retry_count": error.retry_count,
        "timestamp": error.context.timestamp if error.context else None,
    }


if __name__ == "__main__":
    # Example usage
    handler = ErrorHandler()

    # Test error handling
    try:
        raise FileNotFoundError("Audio file not found")
    except Exception as e:
        handler.handle_error(e, {"operation": "transcribe", "file": "test.wav"})

    # Test statistics
    print(handler.get_error_statistics())
