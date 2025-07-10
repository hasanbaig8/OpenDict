"""
OpenDict Security Module
Secure communication and authentication utilities
"""

import base64
import hashlib
import hmac
import json
import secrets
import socket
import ssl
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config import get_config
from error_handling import ErrorCode, OpenDictError
from logging_config import get_logger


class SecurityLevel(Enum):
    """Security level options."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class SecurityConfig:
    """Security configuration."""

    enable_encryption: bool = False
    enable_authentication: bool = True
    enable_rate_limiting: bool = True
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    max_requests_per_minute: int = 60
    session_timeout: int = 300  # 5 minutes
    token_expiry: int = 3600  # 1 hour


class RateLimiter:
    """Rate limiting for API requests."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}  # client_id -> list of timestamps
        self.logger = get_logger()

    def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make request."""
        now = time.time()

        # Initialize client if not exists
        if client_id not in self.requests:
            self.requests[client_id] = []

        # Clean old requests
        self.requests[client_id] = [
            req_time
            for req_time in self.requests[client_id]
            if now - req_time < self.window_seconds
        ]

        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            self.logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                request_count=len(self.requests[client_id]),
                max_requests=self.max_requests,
            )
            return False

        # Add current request
        self.requests[client_id].append(now)
        return True

    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get statistics for a client."""
        if client_id not in self.requests:
            return {"request_count": 0, "remaining": self.max_requests}

        current_count = len(self.requests[client_id])
        return {
            "request_count": current_count,
            "remaining": max(0, self.max_requests - current_count),
            "window_seconds": self.window_seconds,
        }


class TokenManager:
    """Manage authentication tokens."""

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or self._generate_secret_key()
        self.tokens: Dict[
            str, Dict[str, Any]
        ] = {}  # token -> {client_id, created_at, expires_at}
        self.logger = get_logger()

    def _generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        return secrets.token_urlsafe(32)

    def generate_token(self, client_id: str, expiry_seconds: int = 3600) -> str:
        """Generate authentication token for client."""
        # Create token payload
        payload = {
            "client_id": client_id,
            "created_at": time.time(),
            "expires_at": time.time() + expiry_seconds,
            "nonce": secrets.token_urlsafe(16),
        }

        # Encode payload
        payload_json = json.dumps(payload, sort_keys=True)
        payload_encoded = base64.b64encode(payload_json.encode()).decode()

        # Create signature
        signature = hmac.new(
            self.secret_key.encode(), payload_encoded.encode(), hashlib.sha256
        ).hexdigest()

        # Combine payload and signature
        token = f"{payload_encoded}.{signature}"

        # Store token
        self.tokens[token] = {
            "client_id": client_id,
            "created_at": payload["created_at"],
            "expires_at": payload["expires_at"],
        }

        self.logger.info(
            "Token generated", client_id=client_id, expires_at=payload["expires_at"]
        )

        return token

    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Validate authentication token."""
        try:
            # Split token
            if "." not in token:
                return False, "Invalid token format"

            payload_encoded, signature = token.rsplit(".", 1)

            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(), payload_encoded.encode(), hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                self.logger.warning("Invalid token signature")
                return False, "Invalid token signature"

            # Decode payload
            payload_json = base64.b64decode(payload_encoded).decode()
            payload = json.loads(payload_json)

            # Check expiry
            if time.time() > payload["expires_at"]:
                self.logger.warning("Token expired", client_id=payload["client_id"])
                self._cleanup_token(token)
                return False, "Token expired"

            # Check if token exists in store
            if token not in self.tokens:
                self.logger.warning("Token not found in store")
                return False, "Token not found"

            return True, payload["client_id"]

        except Exception as e:
            self.logger.error("Token validation error", error=str(e))
            return False, f"Token validation error: {str(e)}"

    def revoke_token(self, token: str) -> bool:
        """Revoke authentication token."""
        if token in self.tokens:
            client_id = self.tokens[token]["client_id"]
            self._cleanup_token(token)
            self.logger.info("Token revoked", client_id=client_id)
            return True
        return False

    def _cleanup_token(self, token: str):
        """Remove token from store."""
        if token in self.tokens:
            del self.tokens[token]

    def cleanup_expired_tokens(self):
        """Remove expired tokens from store."""
        current_time = time.time()
        expired_tokens = [
            token
            for token, data in self.tokens.items()
            if current_time > data["expires_at"]
        ]

        for token in expired_tokens:
            self._cleanup_token(token)

        if expired_tokens:
            self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")


class SecureSocket:
    """Secure socket wrapper with optional TLS."""

    def __init__(
        self,
        use_tls: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
    ):
        self.use_tls = use_tls
        self.cert_file = cert_file
        self.key_file = key_file
        self.logger = get_logger()

    def create_server_socket(self, host: str, port: int) -> socket.socket:
        """Create secure server socket."""
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if self.use_tls:
            # Create SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            # Load certificate and key
            if self.cert_file and self.key_file:
                context.load_cert_chain(self.cert_file, self.key_file)
            else:
                self.logger.warning("TLS enabled but no certificate provided")

            # Wrap socket with SSL
            sock = context.wrap_socket(sock, server_side=True)

        # Bind and listen
        sock.bind((host, port))
        sock.listen(5)

        self.logger.info(
            "Secure server socket created",
            host=host,
            port=port,
            tls_enabled=self.use_tls,
        )

        return sock

    def create_client_socket(self, host: str, port: int) -> socket.socket:
        """Create secure client socket."""
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if self.use_tls:
            # Create SSL context
            context = ssl.create_default_context()

            # For self-signed certificates in development
            if get_config().environment == "development":
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            # Wrap socket with SSL
            sock = context.wrap_socket(sock, server_hostname=host)

        # Connect
        sock.connect((host, port))

        self.logger.info(
            "Secure client socket created",
            host=host,
            port=port,
            tls_enabled=self.use_tls,
        )

        return sock


class MessageEncryption:
    """Message encryption utilities."""

    def __init__(self, key: Optional[bytes] = None):
        self.key = key or self._generate_key()
        self.logger = get_logger()

    def _generate_key(self) -> bytes:
        """Generate encryption key."""
        return secrets.token_bytes(32)

    def encrypt_message(self, message: str) -> str:
        """Encrypt message using AES."""
        try:
            from cryptography.fernet import Fernet

            # Generate key for Fernet
            key = base64.urlsafe_b64encode(self.key)
            cipher = Fernet(key)

            # Encrypt message
            encrypted = cipher.encrypt(message.encode())

            # Encode as base64 for JSON serialization
            return base64.b64encode(encrypted).decode()

        except ImportError:
            self.logger.warning(
                "Cryptography library not available, using base64 encoding"
            )
            return base64.b64encode(message.encode()).decode()
        except Exception as e:
            self.logger.error("Encryption error", error=str(e))
            raise OpenDictError(
                f"Encryption failed: {str(e)}", ErrorCode.SYSTEM_RESOURCE_UNAVAILABLE
            )

    def decrypt_message(self, encrypted_message: str) -> str:
        """Decrypt message using AES."""
        try:
            from cryptography.fernet import Fernet

            # Generate key for Fernet
            key = base64.urlsafe_b64encode(self.key)
            cipher = Fernet(key)

            # Decode from base64
            encrypted = base64.b64decode(encrypted_message)

            # Decrypt message
            decrypted = cipher.decrypt(encrypted)

            return decrypted.decode()

        except ImportError:
            self.logger.warning(
                "Cryptography library not available, using base64 decoding"
            )
            return base64.b64decode(encrypted_message).decode()
        except Exception as e:
            self.logger.error("Decryption error", error=str(e))
            raise OpenDictError(
                f"Decryption failed: {str(e)}", ErrorCode.SYSTEM_RESOURCE_UNAVAILABLE
            )


class SecurityManager:
    """Main security manager."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.logger = get_logger()
        self.rate_limiter = RateLimiter(
            max_requests=self.config.max_requests_per_minute, window_seconds=60
        )
        self.token_manager = TokenManager()
        self.message_encryption = (
            MessageEncryption() if self.config.enable_encryption else None
        )
        self.secure_socket = SecureSocket(use_tls=self.config.enable_encryption)

        # Security statistics
        self.security_stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "authentication_failures": 0,
            "rate_limit_violations": 0,
        }

    def authenticate_client(
        self, client_id: str, token: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Authenticate client."""
        if not self.config.enable_authentication:
            return True, "Authentication disabled"

        if not token:
            # Generate new token for client
            new_token = self.token_manager.generate_token(client_id)
            return True, new_token

        # Validate existing token
        is_valid, result = self.token_manager.validate_token(token)
        if not is_valid:
            self.security_stats["authentication_failures"] += 1
            self.logger.warning(
                "Authentication failed", client_id=client_id, reason=result
            )

        return is_valid, result or "Unknown error"

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limits."""
        if not self.config.enable_rate_limiting:
            return True

        is_allowed = self.rate_limiter.is_allowed(client_id)
        if not is_allowed:
            self.security_stats["rate_limit_violations"] += 1
            self.security_stats["blocked_requests"] += 1

        return is_allowed

    def secure_message(self, message: str) -> str:
        """Secure message for transmission."""
        if not self.config.enable_encryption or not self.message_encryption:
            return message

        return self.message_encryption.encrypt_message(message)

    def unsecure_message(self, encrypted_message: str) -> str:
        """Unsecure message after transmission."""
        if not self.config.enable_encryption or not self.message_encryption:
            return encrypted_message

        return self.message_encryption.decrypt_message(encrypted_message)

    def create_secure_server(self, host: str, port: int) -> socket.socket:
        """Create secure server socket."""
        return self.secure_socket.create_server_socket(host, port)

    def create_secure_client(self, host: str, port: int) -> socket.socket:
        """Create secure client socket."""
        return self.secure_socket.create_client_socket(host, port)

    def process_request(
        self, client_id: str, request_data: Dict[str, Any], token: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Process request with security checks."""
        self.security_stats["total_requests"] += 1

        # Check rate limiting
        if not self.check_rate_limit(client_id):
            return False, "Rate limit exceeded", {}

        # Check authentication
        auth_valid, auth_result = self.authenticate_client(client_id, token)
        if not auth_valid:
            return False, f"Authentication failed: {auth_result}", {}

        # If authentication passed and no token was provided, auth_result is the new token
        response_data = {}
        if not token and self.config.enable_authentication:
            response_data["token"] = auth_result

        self.logger.info(
            "Request processed successfully",
            client_id=client_id,
            authenticated=auth_valid,
        )

        return True, "Request authorized", response_data

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        total_requests = max(self.security_stats["total_requests"], 1)
        return {
            **self.security_stats,
            "block_rate": (self.security_stats["blocked_requests"] / total_requests)
            * 100,
            "auth_failure_rate": (
                self.security_stats["authentication_failures"] / total_requests
            )
            * 100,
            "rate_limit_violation_rate": (
                self.security_stats["rate_limit_violations"] / total_requests
            )
            * 100,
        }

    def cleanup(self):
        """Clean up expired tokens and reset counters."""
        self.token_manager.cleanup_expired_tokens()

        # Reset counters periodically
        if self.security_stats["total_requests"] > 10000:
            self.security_stats = {
                "total_requests": 0,
                "blocked_requests": 0,
                "authentication_failures": 0,
                "rate_limit_violations": 0,
            }


# Global security manager instance
_security_manager = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def create_security_config(
    enable_encryption: bool = False,
    enable_authentication: bool = True,
    enable_rate_limiting: bool = True,
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
) -> SecurityConfig:
    """Create security configuration."""
    return SecurityConfig(
        enable_encryption=enable_encryption,
        enable_authentication=enable_authentication,
        enable_rate_limiting=enable_rate_limiting,
        security_level=security_level,
    )


if __name__ == "__main__":
    # Example usage
    security_config = create_security_config(
        enable_encryption=True, enable_authentication=True, enable_rate_limiting=True
    )

    manager = SecurityManager(security_config)

    # Test authentication
    client_id = "test_client"
    success, result, data = manager.process_request(client_id, {"action": "test"})
    print(f"Authentication result: {success}, {result}")

    # Test rate limiting
    for i in range(65):  # Exceed rate limit
        allowed = manager.check_rate_limit(client_id)
        if not allowed:
            print(f"Rate limit exceeded at request {i}")
            break

    # Test encryption
    if manager.message_encryption:
        original = "Hello, World!"
        encrypted = manager.secure_message(original)
        decrypted = manager.unsecure_message(encrypted)
        print(f"Encryption test: {original} -> {encrypted} -> {decrypted}")

    # Show statistics
    print(f"Security stats: {manager.get_security_stats()}")
