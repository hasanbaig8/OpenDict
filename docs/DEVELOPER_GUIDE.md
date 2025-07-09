# OpenDict Developer Guide

This guide provides comprehensive information for developers working on OpenDict.

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Code Structure](#code-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Contributing](#contributing)

## Getting Started

### Prerequisites

- macOS 13.0 or later
- Xcode 15.0 or later (or Swift 5.9+ command line tools)
- Python 3.8 or later
- Git

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd opendict
   ```

2. **Set up development environment**:
   ```bash
   make dev-setup
   ```

3. **Run tests**:
   ```bash
   make test
   ```

4. **Start development server**:
   ```bash
   make run-server
   ```

## Architecture Overview

OpenDict follows a client-server architecture with the following components:

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  OpenDict macOS App (Swift)                 │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   UI Layer      │  │  Business Logic │  │  Data Layer │ │
│  │                 │  │                 │  │             │ │
│  │ • MenuBar UI    │  │ • AudioRecorder │  │ • Config    │ │
│  │ • Popover       │  │ • Hotkey Mgr    │  │ • Cache     │ │
│  │ • Status Icons  │  │ • Access Mgr    │  │ • Logs      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                │                            │
│                                │ IPC (TCP Socket)           │
└────────────────────────────────┼────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────┐
│                                │                            │
│               Python Transcription Server                  │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Network Layer  │  │  AI/ML Layer    │  │ Utils Layer │ │
│  │                 │  │                 │  │             │ │
│  │ • TCP Server    │  │ • NeMo Model    │  │ • Logging   │ │
│  │ • Request Mgr   │  │ • Transcription │  │ • Config    │ │
│  │ • Response Mgr  │  │ • Model Cache   │  │ • Error Hdl │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Swift Components

1. **App Delegate** (`HelloWorldApp.swift`):
   - Application lifecycle management
   - Component initialization and coordination
   - Menu bar and status item management

2. **Audio Recorder** (`AudioRecorder.swift`):
   - Audio capture using AVFoundation
   - Recording state management
   - Integration with transcription client

3. **Global Hotkey Manager** (`GlobalHotkeyManager.swift`):
   - System-wide keyboard event monitoring
   - Hotkey registration and handling
   - Event coordination with audio recorder

4. **Accessibility Manager** (`AccessibilityManager.swift`):
   - macOS accessibility permission handling
   - Text insertion at cursor position
   - Clipboard management

5. **Transcription Client** (`SimpleTranscriptionClient.swift`):
   - Communication with Python server
   - Request/response handling
   - Error management

6. **UI Components** (`ContentView.swift`):
   - SwiftUI interface for menu bar popover
   - Status display and user controls
   - Real-time state updates

#### Python Components

1. **Transcription Server** (`transcribe_server.py`):
   - TCP server for handling requests
   - Multi-threaded client handling
   - Model management and caching

2. **Configuration System** (`config.py`):
   - Centralized configuration management
   - Environment-based settings
   - Runtime configuration updates

3. **Logging System** (`logging_config.py`):
   - Structured logging with JSON format
   - Performance monitoring
   - Error tracking

4. **Error Handling** (`error_handling.py`):
   - Comprehensive error classification
   - Recovery strategies
   - Error statistics and monitoring

## Development Setup

### Environment Setup

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Configuration

#### Environment Variables

- `OPENDICT_ENV`: Environment (development/staging/production)
- `OPENDICT_DEBUG`: Enable debug mode (true/false)
- `OPENDICT_LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `OPENDICT_HOST`: Server host (default: 127.0.0.1)
- `OPENDICT_PORT`: Server port (default: 8765)
- `OPENDICT_MODEL`: Model name (default: nvidia/parakeet-tdt-0.6b-v2)
- `OPENDICT_CACHE_DIR`: Model cache directory (default: ~/.opendict_cache)

#### Configuration Files

- `config/development.json`: Development configuration
- `config/production.json`: Production configuration
- `.env`: Environment variables (create from `.env.example`)

### Development Workflow

1. **Start development server**:
   ```bash
   make run-server
   ```

2. **Run Swift app**:
   ```bash
   make run-app
   ```

3. **Run tests**:
   ```bash
   make test
   ```

4. **Code formatting**:
   ```bash
   make format
   ```

5. **Quality checks**:
   ```bash
   make quality-check
   ```

## Code Structure

### Project Layout

```
opendict/
├── HelloWorldApp/              # Swift source code
│   ├── HelloWorldApp.swift     # Main app delegate
│   ├── AudioRecorder.swift     # Audio recording logic
│   ├── GlobalHotkeyManager.swift # Hotkey handling
│   ├── AccessibilityManager.swift # Accessibility integration
│   ├── ContentView.swift       # SwiftUI interface
│   ├── SimpleTranscriptionClient.swift # Server communication
│   ├── TranscriptionClient.swift # Alternative client
│   └── Info.plist             # App configuration
├── config/                     # Configuration files
│   ├── development.json        # Development config
│   └── production.json         # Production config
├── docs/                       # Documentation
│   ├── API.md                 # API documentation
│   ├── DEVELOPER_GUIDE.md     # This file
│   └── CONTRIBUTING.md        # Contributing guidelines
├── tests/                      # Test files
│   ├── conftest.py            # Test fixtures
│   ├── test_config.py         # Configuration tests
│   ├── test_transcription_server.py # Server tests
│   └── test_transcribe.py     # Transcription tests
├── .github/                    # GitHub Actions
│   └── workflows/
│       ├── ci.yml             # Continuous integration
│       └── release.yml        # Release automation
├── transcribe_server.py        # Python transcription server
├── transcribe.py              # Standalone transcription
├── config.py                  # Configuration management
├── logging_config.py          # Logging system
├── error_handling.py          # Error handling
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Python project configuration
├── Makefile                  # Build automation
├── Package.swift             # Swift package configuration
└── README.md                 # Project documentation
```

### Coding Standards

#### Swift Code Style

- Use 4 spaces for indentation
- Follow Swift API Design Guidelines
- Use SwiftFormat for automatic formatting
- Maximum line length: 100 characters
- Use descriptive variable and function names
- Add documentation comments for public APIs

#### Python Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting
- Use type hints for all functions
- Maximum line length: 88 characters
- Use isort for import sorting
- Add docstrings for all functions and classes

#### General Guidelines

- Write self-documenting code
- Use meaningful commit messages
- Include tests for new features
- Update documentation when making changes
- Follow the principle of least surprise

## API Documentation

### Python Server API

#### Base URL
```
tcp://localhost:8765
```

#### Request Format
```json
{
    "action": "transcribe",
    "audio_file": "/path/to/audio.wav"
}
```

#### Response Format
```json
{
    "status": "success",
    "text": "Transcribed text here"
}
```

#### Error Response Format
```json
{
    "status": "error",
    "error_code": "ERROR_CODE",
    "message": "Error description",
    "recoverable": true,
    "retry_count": 0
}
```

### Swift Client API

#### AudioRecorder

```swift
class AudioRecorder: ObservableObject {
    @Published var isGlobalRecording: Bool
    @Published var isTranscribing: Bool

    func startGlobalRecording()
    func stopGlobalRecording()
    func cancelTranscription()
}
```

#### GlobalHotkeyManager

```swift
class GlobalHotkeyManager: ObservableObject {
    @Published var isHotkeyPressed: Bool

    init()
    deinit
}
```

#### AccessibilityManager

```swift
class AccessibilityManager: ObservableObject {
    @Published var hasAccessibilityPermissions: Bool

    func checkAccessibilityPermissions()
    func requestAccessibilityPermissions()
    func insertTextAtCursor(_ text: String)
}
```

## Testing

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run tests with coverage
make test-coverage
```

### Test Categories

#### Python Tests

1. **Configuration Tests** (`test_config.py`):
   - Configuration loading and validation
   - Environment variable handling
   - Default value handling

2. **Server Tests** (`test_transcription_server.py`):
   - Server startup and shutdown
   - Request handling
   - Model loading and caching
   - Error handling

3. **Transcription Tests** (`test_transcribe.py`):
   - Standalone transcription functionality
   - Model loading and caching
   - Error handling

#### Swift Tests

1. **Audio Tests**:
   - Audio recording functionality
   - Format validation
   - Error handling

2. **Network Tests**:
   - Client-server communication
   - Request/response handling
   - Connection management

3. **UI Tests**:
   - User interface components
   - State management
   - User interactions

### Test Fixtures

Common test fixtures are defined in `tests/conftest.py`:

- `temp_dir`: Temporary directory for test files
- `config_manager`: Test configuration manager
- `mock_audio_file`: Mock audio file for testing
- `mock_nemo_model`: Mock NeMo model for testing
- `mock_socket`: Mock socket for network tests

## Code Quality

### Linting and Formatting

#### Python
```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .

# Security scanning
bandit -r .
```

#### Swift
```bash
# Format code
swiftformat HelloWorldApp/

# Lint code (requires SwiftLint)
swiftlint HelloWorldApp/
```

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks:

```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Quality Metrics

- **Code Coverage**: Aim for >80% test coverage
- **Type Coverage**: Use type hints for all Python functions
- **Documentation Coverage**: Document all public APIs
- **Security**: No security vulnerabilities in dependencies

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run quality checks
6. Submit a pull request

### Pull Request Process

1. **Pre-submission**:
   - Run `make dev-test` to ensure all checks pass
   - Update documentation if needed
   - Add tests for new features

2. **Review Process**:
   - All tests must pass
   - Code must pass quality checks
   - Documentation must be updated
   - At least one reviewer approval required

3. **Merge Process**:
   - Squash and merge for feature branches
   - Update changelog
   - Tag releases following semantic versioning

### Development Tips

1. **Use the Makefile**: All common tasks are automated
2. **Follow TDD**: Write tests before implementing features
3. **Keep PRs small**: Easier to review and merge
4. **Update documentation**: Keep docs in sync with code
5. **Test on real hardware**: Especially for audio and accessibility features

### Common Issues

1. **Model Loading**: First run takes time to download model
2. **Accessibility Permissions**: Must be granted manually
3. **Port Conflicts**: Change port if 8765 is in use
4. **Python Dependencies**: Use virtual environment

For more detailed information, see:
- [API Documentation](API.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Troubleshooting Guide](../README.md#troubleshooting)
