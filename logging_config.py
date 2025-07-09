"""
OpenDict Logging Configuration
Centralized logging setup with structured logging support
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_config


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured information."""
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if enabled
        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in {
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "message",
                    "asctime",
                }:
                    extra_fields[key] = value

            if extra_fields:
                log_data["extra"] = extra_fields

        # Format as structured log
        import json

        return json.dumps(log_data, ensure_ascii=False, default=str)


class OpenDictLogger:
    """OpenDict-specific logger with enhanced functionality."""

    def __init__(self, name: str = "opendict"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """Set up logger with configuration."""
        config = get_config()

        # Clear existing handlers
        self.logger.handlers.clear()

        # Set level
        level = getattr(logging, config.logging.level, logging.INFO)
        self.logger.setLevel(level)

        # Create formatters
        console_formatter = logging.Formatter(config.logging.format)
        structured_formatter = StructuredFormatter()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)

        # File handler (if configured)
        if config.logging.file:
            self._setup_file_handler(config, structured_formatter)

        # Prevent duplicate logs
        self.logger.propagate = False

    def _setup_file_handler(self, config, formatter):
        """Set up rotating file handler."""
        log_path = Path(config.logging.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=config.logging.max_file_size,
            backupCount=config.logging.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message with extra context."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with extra context."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with extra context."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with extra context."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with extra context."""
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)

    def log_request(self, client_addr: str, action: str, audio_file: str = None):
        """Log incoming request."""
        self.info(
            f"Request received: {action}",
            client_address=client_addr,
            action=action,
            audio_file=audio_file,
            request_type="transcription",
        )

    def log_response(
        self, client_addr: str, status: str, processing_time: float = None
    ):
        """Log response sent."""
        self.info(
            f"Response sent: {status}",
            client_address=client_addr,
            status=status,
            processing_time_ms=processing_time * 1000 if processing_time else None,
            response_type="transcription",
        )

    def log_model_loading(
        self, model_name: str, load_time: float = None, from_cache: bool = False
    ):
        """Log model loading event."""
        self.info(
            f"Model loaded: {model_name}",
            model_name=model_name,
            load_time_seconds=load_time,
            from_cache=from_cache,
            event_type="model_loading",
        )

    def log_transcription(
        self, audio_file: str, text_length: int, processing_time: float = None
    ):
        """Log transcription completion."""
        self.info(
            f"Transcription completed",
            audio_file=audio_file,
            text_length=text_length,
            processing_time_seconds=processing_time,
            event_type="transcription",
        )

    def log_error(
        self, error_type: str, error_message: str, context: Dict[str, Any] = None
    ):
        """Log error with context."""
        self.error(
            f"Error occurred: {error_type}",
            error_type=error_type,
            error_message=error_message,
            context=context or {},
            event_type="error",
        )


# Global logger instance
_logger = None


def get_logger(name: str = "opendict") -> OpenDictLogger:
    """Get global logger instance."""
    global _logger
    if _logger is None or _logger.name != name:
        _logger = OpenDictLogger(name)
    return _logger


def setup_logging(config_path: Optional[str] = None):
    """Set up logging configuration."""
    if config_path:
        # Update config path if provided
        from config import get_config_manager

        config_manager = get_config_manager()
        config_manager.config_path = config_path
        config_manager.config = config_manager._load_config()

    # Create new logger instance
    global _logger
    _logger = None
    return get_logger()


class LoggingContextManager:
    """Context manager for adding logging context."""

    def __init__(self, logger: OpenDictLogger, **context):
        self.logger = logger
        self.context = context
        self.old_context = {}

    def __enter__(self):
        # Store old context and set new context
        for key, value in self.context.items():
            if hasattr(self.logger.logger, key):
                self.old_context[key] = getattr(self.logger.logger, key)
            setattr(self.logger.logger, key, value)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        for key, value in self.old_context.items():
            setattr(self.logger.logger, key, value)

        # Remove new context keys
        for key in self.context:
            if key not in self.old_context:
                delattr(self.logger.logger, key)


def log_with_context(logger: OpenDictLogger, **context):
    """Create logging context manager."""
    return LoggingContextManager(logger, **context)


# Performance logging decorator
def log_performance(logger: OpenDictLogger = None, operation: str = None):
    """Decorator to log function performance."""
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger, operation
            if logger is None:
                logger = get_logger()
            if operation is None:
                operation = f"{func.__module__}.{func.__name__}"

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                processing_time = time.time() - start_time
                logger.debug(
                    f"Performance: {operation} completed",
                    operation=operation,
                    processing_time_seconds=processing_time,
                    success=True,
                )
                return result
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(
                    f"Performance: {operation} failed",
                    operation=operation,
                    processing_time_seconds=processing_time,
                    success=False,
                    error=str(e),
                )
                raise

        return wrapper

    return decorator


# Exception logging decorator
def log_exceptions(logger: OpenDictLogger = None, reraise: bool = True):
    """Decorator to log exceptions."""
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger()

            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception in {func.__name__}",
                    function=func.__name__,
                    module=func.__module__,
                    args=str(args),
                    kwargs=str(kwargs),
                )
                if reraise:
                    raise
                return None

        return wrapper

    return decorator


if __name__ == "__main__":
    # Example usage
    logger = get_logger()
    logger.info("Logger initialized")

    # Test structured logging
    logger.log_request("127.0.0.1", "transcribe", "test.wav")
    logger.log_response("127.0.0.1", "success", 2.5)

    # Test context manager
    with log_with_context(logger, client_id="test123", session_id="abc"):
        logger.info("Processing request")

    # Test performance decorator
    @log_performance(logger, "test_operation")
    def test_function():
        import time

        time.sleep(0.1)
        return "done"

    test_function()
