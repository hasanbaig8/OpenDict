# Security Considerations

This document outlines the security considerations and design decisions for OpenDict.

## Security Scan Results

OpenDict uses `bandit` for security scanning. Below are explanations for the remaining security warnings:

### Pickle Usage (B301, B403)

**Files affected:** `transcribe.py`, `transcribe_server.py`
**Risk level:** Medium
**Justification:**

Pickle is used for caching the NVIDIA Parakeet ML model to improve performance. This is acceptable because:

1. **Local files only**: Pickle files are created and read locally on the user's machine
2. **No network deserialization**: We never deserialize pickle data received over the network
3. **Controlled environment**: The cache directory is user-specific (`~/.opendict_cache/`)
4. **Performance benefit**: Model loading time reduced from 30-60s to 2-5s

**Mitigation:** Consider migrating to safer serialization (like `joblib` or `torch.save`) in future versions.

### Subprocess Usage (B404, B603)

**Files affected:** `build.py`, `setup.py`
**Risk level:** Low
**Justification:**

Subprocess calls are used in build and setup scripts with controlled input:

1. **Build scripts only**: Not used in runtime application code
2. **Controlled input**: All subprocess arguments are hardcoded or validated
3. **No shell injection**: `shell=False` is used (default)
4. **Development tools**: Only used for development environment setup

### File Permissions (B103)

**Files affected:** `build.py`
**Risk level:** Medium
**Justification:**

Executable permissions (0o755) are set intentionally for:

1. **Application binaries**: Required for macOS app bundles
2. **Launch scripts**: Needed for proper application execution
3. **Standard practice**: Common pattern for macOS application distribution

## Runtime Security

### Network Security

- **Local only**: Server binds to localhost (127.0.0.1) by default
- **No authentication**: Intended for local-only use
- **Port isolation**: Uses non-standard port (8765) to avoid conflicts

### File System Security

- **Temp files**: Audio recordings stored in system temp directory with appropriate cleanup
- **Cache isolation**: Model cache stored in user-specific directory
- **No privilege escalation**: Application runs with user permissions only

### Privacy Considerations

- **Local processing**: All audio processing happens locally, no data sent to external servers
- **Temporary storage**: Audio files are automatically cleaned up after transcription
- **No logging**: Sensitive audio data is not logged

## Accessibility Security

The application requires accessibility permissions to insert text. This is necessary for the core functionality but should be noted:

- **Limited scope**: Only used for text insertion at cursor position
- **No data exfiltration**: No data is read from other applications
- **User controlled**: User can revoke permissions at any time

## Development Security

- **Pre-commit hooks**: Automated security scanning before commits
- **Dependency scanning**: Regular updates and vulnerability checks
- **CI/CD security**: Lightweight CI dependencies to minimize attack surface

## Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do not** open a public GitHub issue
2. Email security concerns to the maintainers
3. Provide detailed reproduction steps
4. Allow time for assessment and fixes before public disclosure

## Security Updates

This document is updated as part of the development process. Check the git history for changes to security posture.
