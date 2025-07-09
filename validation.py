"""
OpenDict Input Validation System
Comprehensive input validation for security and data integrity
"""

import hashlib
import json
import mimetypes
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config import get_config
from error_handling import ErrorCode, OpenDictError, ValidationError
from logging_config import get_logger


class ValidationSeverity(Enum):
    """Validation severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of validation operation."""

    is_valid: bool
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any]

    @classmethod
    def success(
        cls, message: str = "Validation passed", **details
    ) -> "ValidationResult":
        """Create successful validation result."""
        return cls(
            is_valid=True,
            severity=ValidationSeverity.INFO,
            message=message,
            details=details,
        )

    @classmethod
    def warning(cls, message: str, **details) -> "ValidationResult":
        """Create warning validation result."""
        return cls(
            is_valid=True,
            severity=ValidationSeverity.WARNING,
            message=message,
            details=details,
        )

    @classmethod
    def error(cls, message: str, **details) -> "ValidationResult":
        """Create error validation result."""
        return cls(
            is_valid=False,
            severity=ValidationSeverity.ERROR,
            message=message,
            details=details,
        )

    @classmethod
    def critical(cls, message: str, **details) -> "ValidationResult":
        """Create critical validation result."""
        return cls(
            is_valid=False,
            severity=ValidationSeverity.CRITICAL,
            message=message,
            details=details,
        )


class BaseValidator:
    """Base validator class."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.config = get_config()

    def validate(self, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate a value."""
        raise NotImplementedError("Subclasses must implement validate method")

    def _log_validation(self, result: ValidationResult, context: Dict[str, Any] = None):
        """Log validation result."""
        log_context = {
            "validator": self.__class__.__name__,
            "result": result.is_valid,
            "severity": result.severity.value,
            "message": result.message,
            "details": result.details,
        }
        if context:
            log_context.update(context)

        if result.severity == ValidationSeverity.CRITICAL:
            self.logger.critical("Validation failed", **log_context)
        elif result.severity == ValidationSeverity.ERROR:
            self.logger.error("Validation failed", **log_context)
        elif result.severity == ValidationSeverity.WARNING:
            self.logger.warning("Validation warning", **log_context)
        else:
            self.logger.debug("Validation passed", **log_context)


class FileValidator(BaseValidator):
    """Validator for file-related inputs."""

    def __init__(self, logger=None):
        super().__init__(logger)
        self.allowed_extensions = self.config.security.allowed_file_types
        self.max_file_size = self.config.security.max_request_size

    def validate(
        self, file_path: str, context: Dict[str, Any] = None
    ) -> ValidationResult:
        """Validate file path and properties."""
        try:
            # Check if file path is provided
            if not file_path:
                return ValidationResult.error("File path is required")

            # Check path traversal attacks
            if self._has_path_traversal(file_path):
                return ValidationResult.critical(
                    "Path traversal attack detected",
                    file_path=file_path,
                    security_issue=True,
                )

            # Check if file exists
            if not os.path.exists(file_path):
                return ValidationResult.error(
                    "File does not exist", file_path=file_path
                )

            # Check if it's a file (not directory)
            if not os.path.isfile(file_path):
                return ValidationResult.error("Path is not a file", file_path=file_path)

            # Check file permissions
            if not os.access(file_path, os.R_OK):
                return ValidationResult.error(
                    "File is not readable", file_path=file_path
                )

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return ValidationResult.error(
                    "File too large",
                    file_path=file_path,
                    file_size=file_size,
                    max_size=self.max_file_size,
                )

            # Check file extension
            extension = Path(file_path).suffix.lower().lstrip(".")
            if extension not in self.allowed_extensions:
                return ValidationResult.error(
                    "File type not allowed",
                    file_path=file_path,
                    extension=extension,
                    allowed_extensions=self.allowed_extensions,
                )

            # Check MIME type
            mime_result = self._validate_mime_type(file_path, extension)
            if not mime_result.is_valid:
                return mime_result

            # Check for malicious content
            malware_result = self._check_malicious_content(file_path)
            if not malware_result.is_valid:
                return malware_result

            return ValidationResult.success(
                "File validation passed",
                file_path=file_path,
                file_size=file_size,
                extension=extension,
            )

        except Exception as e:
            return ValidationResult.critical(
                f"File validation failed: {str(e)}",
                file_path=file_path,
                exception=str(e),
            )

    def _has_path_traversal(self, file_path: str) -> bool:
        """Check for path traversal attacks."""
        # Normalize path
        normalized_path = os.path.normpath(file_path)

        # Check for suspicious patterns
        suspicious_patterns = [
            "..",
            "~",
            "/etc/",
            "/var/",
            "/usr/",
            "/bin/",
            "/sbin/",
            "/home/",
            "/root/",
            "\\\\",
            "%2e%2e",
            "%2f",
            "%5c",
        ]

        file_path_lower = file_path.lower()
        for pattern in suspicious_patterns:
            if pattern in file_path_lower:
                return True

        return False

    def _validate_mime_type(self, file_path: str, extension: str) -> ValidationResult:
        """Validate MIME type matches extension."""
        try:
            mime_type, _ = mimetypes.guess_type(file_path)

            # Expected MIME types for audio files
            expected_mimes = {
                "wav": ["audio/wav", "audio/x-wav", "audio/wave"],
                "mp3": ["audio/mpeg", "audio/mp3"],
                "flac": ["audio/flac", "audio/x-flac"],
                "m4a": ["audio/mp4", "audio/x-m4a"],
            }

            if extension in expected_mimes:
                expected = expected_mimes[extension]
                if mime_type not in expected:
                    return ValidationResult.warning(
                        "MIME type mismatch",
                        file_path=file_path,
                        detected_mime=mime_type,
                        expected_mimes=expected,
                    )

            return ValidationResult.success("MIME type validation passed")

        except Exception as e:
            return ValidationResult.warning(
                f"MIME type validation failed: {str(e)}", file_path=file_path
            )

    def _check_malicious_content(self, file_path: str) -> ValidationResult:
        """Basic check for malicious content."""
        try:
            # Check file signature (magic bytes)
            with open(file_path, "rb") as f:
                header = f.read(1024)

            # Check for executable signatures
            executable_signatures = [
                b"\x7fELF",  # ELF
                b"MZ",  # Windows PE
                b"\xca\xfe\xba\xbe",  # Mach-O
                b"\xfe\xed\xfa\xce",  # Mach-O
                b"\xfe\xed\xfa\xcf",  # Mach-O
                b"\xce\xfa\xed\xfe",  # Mach-O
                b"\xcf\xfa\xed\xfe",  # Mach-O
            ]

            for sig in executable_signatures:
                if header.startswith(sig):
                    return ValidationResult.critical(
                        "Executable file detected",
                        file_path=file_path,
                        security_issue=True,
                    )

            # Check for suspicious content
            suspicious_content = [
                b"<script",
                b"javascript:",
                b"eval(",
                b"exec(",
                b"system(",
                b"shell_exec(",
                b"passthru(",
                b"file_get_contents(",
                b"fopen(",
                b"curl_exec(",
            ]

            header_lower = header.lower()
            for content in suspicious_content:
                if content in header_lower:
                    return ValidationResult.critical(
                        "Suspicious content detected",
                        file_path=file_path,
                        security_issue=True,
                    )

            return ValidationResult.success("Malicious content check passed")

        except Exception as e:
            return ValidationResult.warning(
                f"Malicious content check failed: {str(e)}", file_path=file_path
            )


class RequestValidator(BaseValidator):
    """Validator for API requests."""

    def validate(
        self, request_data: Dict[str, Any], context: Dict[str, Any] = None
    ) -> ValidationResult:
        """Validate API request data."""
        try:
            # Check if request data is provided
            if not request_data:
                return ValidationResult.error("Request data is required")

            # Check if it's a dictionary
            if not isinstance(request_data, dict):
                return ValidationResult.error(
                    "Request data must be a dictionary",
                    data_type=type(request_data).__name__,
                )

            # Check for required fields
            required_fields = ["action"]
            for field in required_fields:
                if field not in request_data:
                    return ValidationResult.error(
                        f"Required field '{field}' is missing", missing_field=field
                    )

            # Validate action
            action = request_data.get("action")
            valid_actions = ["transcribe", "shutdown", "health_check"]
            if action not in valid_actions:
                return ValidationResult.error(
                    "Invalid action", action=action, valid_actions=valid_actions
                )

            # Validate transcribe action
            if action == "transcribe":
                if "audio_file" not in request_data:
                    return ValidationResult.error(
                        "audio_file is required for transcribe action"
                    )

                # Validate audio file
                file_validator = FileValidator(self.logger)
                file_result = file_validator.validate(request_data["audio_file"])
                if not file_result.is_valid:
                    return file_result

            # Check for SQL injection patterns
            sql_result = self._check_sql_injection(request_data)
            if not sql_result.is_valid:
                return sql_result

            # Check for XSS patterns
            xss_result = self._check_xss(request_data)
            if not xss_result.is_valid:
                return xss_result

            # Check request size
            request_size = len(json.dumps(request_data).encode("utf-8"))
            if request_size > self.config.security.max_request_size:
                return ValidationResult.error(
                    "Request too large",
                    request_size=request_size,
                    max_size=self.config.security.max_request_size,
                )

            return ValidationResult.success(
                "Request validation passed", action=action, request_size=request_size
            )

        except Exception as e:
            return ValidationResult.critical(
                f"Request validation failed: {str(e)}", exception=str(e)
            )

    def _check_sql_injection(self, data: Dict[str, Any]) -> ValidationResult:
        """Check for SQL injection patterns."""
        sql_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bselect\b.*\bfrom\b)",
            r"(\binsert\b.*\binto\b)",
            r"(\bupdate\b.*\bset\b)",
            r"(\bdelete\b.*\bfrom\b)",
            r"(\bdrop\b.*\btable\b)",
            r"(\bor\b.*\b=\b.*\bor\b)",
            r"(\band\b.*\b=\b.*\band\b)",
            r"(--\s*)",
            r"(;\s*--)",
            r"(\bexec\b.*\()",
            r"(\bsp_\w+)",
        ]

        for key, value in data.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in sql_patterns:
                    if re.search(pattern, value_lower, re.IGNORECASE):
                        return ValidationResult.critical(
                            "SQL injection pattern detected",
                            field=key,
                            pattern=pattern,
                            security_issue=True,
                        )

        return ValidationResult.success("SQL injection check passed")

    def _check_xss(self, data: Dict[str, Any]) -> ValidationResult:
        """Check for XSS patterns."""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"onfocus\s*=",
            r"onblur\s*=",
            r"onchange\s*=",
            r"onsubmit\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"eval\s*\(",
            r"document\.cookie",
            r"document\.write",
            r"window\.location",
        ]

        for key, value in data.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return ValidationResult.critical(
                            "XSS pattern detected",
                            field=key,
                            pattern=pattern,
                            security_issue=True,
                        )

        return ValidationResult.success("XSS check passed")


class NetworkValidator(BaseValidator):
    """Validator for network-related inputs."""

    def validate_client_address(self, client_address: str) -> ValidationResult:
        """Validate client address."""
        try:
            # Check if address is provided
            if not client_address:
                return ValidationResult.error("Client address is required")

            # Check for localhost/loopback
            allowed_addresses = ["127.0.0.1", "::1", "localhost"]

            if client_address not in allowed_addresses:
                return ValidationResult.warning(
                    "Non-localhost connection",
                    client_address=client_address,
                    security_note="External connections detected",
                )

            return ValidationResult.success(
                "Client address validation passed", client_address=client_address
            )

        except Exception as e:
            return ValidationResult.error(
                f"Client address validation failed: {str(e)}",
                client_address=client_address,
            )

    def validate_port(self, port: int) -> ValidationResult:
        """Validate port number."""
        try:
            # Check if port is in valid range
            if not (1 <= port <= 65535):
                return ValidationResult.error(
                    "Port out of valid range", port=port, valid_range="1-65535"
                )

            # Check for privileged ports
            if port < 1024:
                return ValidationResult.warning(
                    "Privileged port detected",
                    port=port,
                    security_note="Requires elevated privileges",
                )

            # Check for common service ports
            common_ports = {
                80: "HTTP",
                443: "HTTPS",
                22: "SSH",
                21: "FTP",
                23: "Telnet",
                25: "SMTP",
                53: "DNS",
                110: "POP3",
                143: "IMAP",
                993: "IMAPS",
                995: "POP3S",
            }

            if port in common_ports:
                return ValidationResult.warning(
                    "Common service port detected",
                    port=port,
                    service=common_ports[port],
                    security_note="May conflict with system services",
                )

            return ValidationResult.success("Port validation passed", port=port)

        except Exception as e:
            return ValidationResult.error(
                f"Port validation failed: {str(e)}", port=port
            )


class DataSanitizer:
    """Data sanitization utilities."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe usage."""
        # Remove path separators
        filename = os.path.basename(filename)

        # Replace dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, "_")

        # Remove control characters
        filename = "".join(char for char in filename if ord(char) >= 32)

        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[: max_length - len(ext)] + ext

        return filename

    def sanitize_string(self, text: str) -> str:
        """Sanitize string for safe usage."""
        # Remove null bytes
        text = text.replace("\x00", "")

        # Remove other control characters (except newline, tab, carriage return)
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t\r")

        # Limit length
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length]

        return text

    def sanitize_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize JSON data."""
        sanitized = {}

        for key, value in data.items():
            # Sanitize key
            clean_key = self.sanitize_string(str(key))

            # Sanitize value
            if isinstance(value, str):
                clean_value = self.sanitize_string(value)
            elif isinstance(value, dict):
                clean_value = self.sanitize_json(value)
            elif isinstance(value, list):
                clean_value = [self.sanitize_string(str(item)) for item in value]
            else:
                clean_value = value

            sanitized[clean_key] = clean_value

        return sanitized


class ValidationManager:
    """Main validation manager."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.config = get_config()
        self.file_validator = FileValidator(logger)
        self.request_validator = RequestValidator(logger)
        self.network_validator = NetworkValidator(logger)
        self.sanitizer = DataSanitizer(logger)
        self.validation_stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "security_issues": 0,
        }

    def validate_transcription_request(
        self, request_data: Dict[str, Any], client_address: str
    ) -> ValidationResult:
        """Validate complete transcription request."""
        try:
            self.validation_stats["total_validations"] += 1

            # Validate client address
            client_result = self.network_validator.validate_client_address(
                client_address
            )
            if not client_result.is_valid:
                self.validation_stats["failed_validations"] += 1
                if client_result.details.get("security_issue"):
                    self.validation_stats["security_issues"] += 1
                return client_result

            # Sanitize request data
            if self.config.security.enable_input_validation:
                request_data = self.sanitizer.sanitize_json(request_data)

            # Validate request
            request_result = self.request_validator.validate(request_data)
            if not request_result.is_valid:
                self.validation_stats["failed_validations"] += 1
                if request_result.details.get("security_issue"):
                    self.validation_stats["security_issues"] += 1
                return request_result

            self.validation_stats["passed_validations"] += 1
            return ValidationResult.success(
                "Transcription request validation passed",
                request_data=request_data,
                client_address=client_address,
            )

        except Exception as e:
            self.validation_stats["failed_validations"] += 1
            self.logger.exception("Validation manager error")
            return ValidationResult.critical(
                f"Validation manager error: {str(e)}", exception=str(e)
            )

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            **self.validation_stats,
            "success_rate": (
                self.validation_stats["passed_validations"]
                / max(self.validation_stats["total_validations"], 1)
            )
            * 100,
        }

    def reset_stats(self):
        """Reset validation statistics."""
        self.validation_stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "security_issues": 0,
        }


# Global validation manager instance
_validation_manager = None


def get_validation_manager() -> ValidationManager:
    """Get global validation manager instance."""
    global _validation_manager
    if _validation_manager is None:
        _validation_manager = ValidationManager()
    return _validation_manager


def validate_request(
    request_data: Dict[str, Any], client_address: str
) -> ValidationResult:
    """Validate request using global validation manager."""
    return get_validation_manager().validate_transcription_request(
        request_data, client_address
    )


if __name__ == "__main__":
    # Example usage
    manager = ValidationManager()

    # Test request validation
    request = {"action": "transcribe", "audio_file": "test.wav"}

    result = manager.validate_transcription_request(request, "127.0.0.1")
    print(f"Validation result: {result.is_valid}")
    print(f"Message: {result.message}")
    print(f"Stats: {manager.get_validation_stats()}")
