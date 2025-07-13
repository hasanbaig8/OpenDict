# OpenDict 🎤

A voice-to-text dictation app for macOS that enables system-wide voice recording and transcription using AI-powered speech recognition.

## 📖 Table of Contents

- [Overview](#overview)
- [Demo](#demo)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Components](#components)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

OpenDict is a macOS menu bar application that provides seamless voice-to-text dictation capabilities. It uses a combination of Swift for the native macOS interface and Python for AI-powered speech recognition using NVIDIA's Parakeet model.

## 🎬 Demo

See OpenDict in action:

### Claude AI Demo
Watch OpenDict being used to dictate text directly into Claude AI:

https://github.com/user-attachments/assets/3c3eeb26-1a5d-4a65-8603-3a9f769756d9



### Notion Demo
Watch OpenDict being used to create content in Notion:

https://github.com/user-attachments/assets/15baca71-c7fe-4bc1-9fe1-b6657eb9bd39




## ✨ Key Features

- **Global Hotkey Support**: Press `Ctrl+Space` to start/stop recording from any application
- **Menu Bar Integration**: Clean, unobtrusive menu bar interface
- **AI-Powered Transcription**: Uses NVIDIA Parakeet TDT 0.6B model for accurate speech recognition
- **System-Wide Text Insertion**: Automatically inserts transcribed text at cursor position
- **Real-time Status Updates**: Visual feedback during recording and transcription
- **Accessibility Integration**: Uses macOS accessibility APIs for seamless text insertion

## 🔧 System Requirements

- macOS 13.0 or later
- Python 3.8+ with virtual environment support
- Accessibility permissions (for text insertion)
- Microphone access permissions

## 📦 Installation

### Quick Setup (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/opendict.git
   cd opendict
   ```

2. **Set up development environment**:
   ```bash
   make setup
   ```

3. **Install dependencies**:
   ```bash
   make install
   ```

4. **Build distribution package**:
   ```bash
   make dist
   ```
   This creates a DMG file in the `dist/` folder that you can install by dragging to Applications.

### Manual Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/opendict.git
   cd opendict
   ```

2. **Set up Python environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install nemo-toolkit[asr]
   ```

3. **Build the macOS app**:
   ```bash
   swift build
   ```

4. **Grant necessary permissions**:
   - Microphone access
   - Accessibility permissions (for text insertion)

## 🚀 Usage

### Starting the Application

1. Launch OpenDict from the applications folder or via command line
2. The app will appear in your menu bar with a microphone icon
3. Grant accessibility permissions when prompted

### Recording and Transcription

1. **Start Recording**: Press and hold `Ctrl+Space` from any application
2. **Stop Recording**: Release `Ctrl+Space`
3. **Transcription**: The app will automatically transcribe your speech and insert the text at your cursor position
4. **Cancel**: Press `Escape` to cancel ongoing transcription

### Status Indicators

- 🎤 **Normal**: Ready to record
- 🔴 **Recording**: Currently recording audio
- 🟠 **Transcribing**: Processing audio for transcription

## 🏗️ Architecture

OpenDict follows a client-server architecture:

<details>
<summary>Click to expand architecture details</summary>

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenDict macOS App                       │
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │   Menu Bar UI   │    │  Audio Recorder │               │
│  │  (Swift/SwiftUI)│    │    (AVFoundation)│               │
│  └─────────────────┘    └─────────────────┘               │
│           │                       │                        │
│  ┌─────────────────┐    ┌─────────────────┐               │
│  │  Hotkey Manager │    │ Accessibility   │               │
│  │    (Carbon)     │    │   Manager       │               │
│  └─────────────────┘    └─────────────────┘               │
│           │                       │                        │
│  ┌─────────────────────────────────────────────────────────┤
│  │           Transcription Client                          │
│  │              (Socket/Network)                           │
│  └─────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
                               │
                               │ TCP Socket (Port 8765)
                               │
┌─────────────────────────────────────────────────────────────┐
│                Python Transcription Server                  │
│  ┌─────────────────────────────────────────────────────────┤
│  │              NVIDIA Parakeet Model                      │
│  │                (NeMo Toolkit)                           │
│  └─────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **User Input**: User presses `Ctrl+Space` hotkey
2. **Recording**: Audio is captured and saved to temporary file
3. **Transcription Request**: Audio file path sent to Python server
4. **AI Processing**: Python server processes audio using Parakeet model
5. **Text Insertion**: Transcribed text is inserted at cursor position
6. **Cleanup**: Temporary files are cleaned up

</details>

## 🧩 Components

### Swift/macOS Components

<details>
<summary>Click to expand Swift components details</summary>

#### 1. **OpenDictApp.swift** (`OpenDictApp/OpenDictApp.swift`)
- **Purpose**: Main app delegate and entry point
- **Key Responsibilities**:
  - Manages app lifecycle and startup
  - Initializes Python transcription server
  - Coordinates all managers and components
  - Handles menu bar interface and status updates

#### 2. **AudioRecorder.swift** (`OpenDictApp/AudioRecorder.swift`)
- **Purpose**: Handles audio recording functionality
- **Key Features**:
  - Uses AVFoundation for audio capture
  - Manages recording state and timer (60-second limit)
  - Coordinates with transcription client
  - Publishes state changes for UI updates

#### 3. **GlobalHotkeyManager.swift** (`OpenDictApp/GlobalHotkeyManager.swift`)
- **Purpose**: Manages global keyboard shortcuts
- **Key Features**:
  - Monitors `Ctrl+Space` for recording trigger
  - Handles `Escape` for cancellation
  - Uses Carbon framework for low-level keyboard events
  - Coordinates with AudioRecorder for recording control

#### 4. **AccessibilityManager.swift** (`OpenDictApp/AccessibilityManager.swift`)
- **Purpose**: Handles accessibility permissions and text insertion
- **Key Features**:
  - Monitors accessibility permission status
  - Inserts transcribed text at cursor position
  - Uses pasteboard and keyboard events for text insertion
  - Preserves existing clipboard contents

#### 5. **ContentView.swift** (`OpenDictApp/ContentView.swift`)
- **Purpose**: SwiftUI interface for menu bar popover
- **Key Features**:
  - Displays app status and recording state
  - Shows accessibility permission warnings
  - Provides restart and quit functionality
  - Real-time status updates

#### 6. **SimpleTranscriptionClient.swift** (`OpenDictApp/SimpleTranscriptionClient.swift`)
- **Purpose**: Handles communication with Python transcription server
- **Key Features**:
  - Socket-based communication (TCP on port 8765)
  - Sends transcription requests with audio file paths
  - Handles server responses and error states
  - Supports graceful shutdown

#### 7. **TranscriptionClient.swift** (`OpenDictApp/TranscriptionClient.swift`)
- **Purpose**: Alternative Network framework-based transcription client
- **Key Features**:
  - Uses modern NWConnection for networking
  - Automatic reconnection handling
  - Asynchronous request/response handling
  - Connection state management

</details>

### Python Components

<details>
<summary>Click to expand Python components details</summary>

#### 1. **transcribe_server.py** (`transcribe_server.py`)
- **Purpose**: Main transcription server handling concurrent requests
- **Key Features**:
  - Multi-threaded TCP server (port 8765)
  - NVIDIA Parakeet TDT 0.6B model integration
  - Model caching for improved performance
  - JSON-based request/response protocol

**Server Protocol**:
```json
// Request
{
  "action": "transcribe",
  "audio_file": "/path/to/audio.wav"
}

// Response
{
  "status": "success",
  "text": "transcribed text here"
}
```

#### 2. **transcribe.py** (`transcribe.py`)
- **Purpose**: Standalone transcription script
- **Key Features**:
  - Command-line interface for direct transcription
  - Model caching system
  - Temporary file output
  - Error handling and logging

**Usage**:
```bash
python transcribe.py /path/to/audio.wav
```

#### 3. **Model Caching System**
Both Python components implement intelligent model caching:
- **Cache Location**: `~/.opendict_cache/parakeet_model.pkl`
- **Benefits**: Significantly reduces startup time after first use
- **Fallback**: Automatic fresh model loading if cache is corrupted

</details>

### Configuration Files

<details>
<summary>Click to expand configuration details</summary>

#### 1. **Package.swift** (`Package.swift`)
- **Purpose**: Swift Package Manager configuration
- **Key Settings**:
  - Minimum macOS version: 13.0
  - Target name: OpenDict
  - Source path: HelloWorldApp directory

#### 2. **Info.plist** (`OpenDictApp/Info.plist`)
- **Purpose**: macOS app configuration
- **Key Settings**:
  - Bundle identifier and version
  - Required permissions (microphone, accessibility)
  - Launch agent configuration

</details>

## 🔧 Development

### Quick Start

```bash
# Set up development environment
make dev-setup

# Run the transcription server
make run-server

# In another terminal, run the Swift app
make run-app

# Run tests
make test

# Check code quality
make quality-check
```

### Available Make Commands

OpenDict includes a comprehensive Makefile for development automation:

#### Setup and Installation
- `make setup` - Set up development environment
- `make install` - Install Python dependencies
- `make dev-setup` - Complete development setup with pre-commit hooks

#### Testing
- `make test` - Run all tests
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only
- `make test-coverage` - Run tests with coverage report

#### Code Quality
- `make lint` - Run linting checks
- `make format` - Format code (Python and Swift)
- `make type-check` - Run type checking
- `make security-check` - Run security checks
- `make quality-check` - Run all quality checks
- `make pre-commit` - Install pre-commit hooks

#### Build and Run
- `make build` - Build Swift application
- `make run-server` - Start Python transcription server
- `make run-app` - Run Swift application
- `make clean` - Clean build artifacts

#### Distribution
- `make dist` - Build release distribution packages
- `make dist-dev` - Build development distribution
- `make package` - Create installation packages (DMG, ZIP)

#### Documentation
- `make docs` - Generate documentation
- `make help` - Show all available commands

### Manual Development Setup

If you prefer manual setup:

1. **Install Xcode Command Line Tools**:
   ```bash
   xcode-select --install
   ```

2. **Set up Python Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. **Build Swift Application**:
   ```bash
   swift build -c release
   ```

4. **Run Development Server**:
   ```bash
   python transcribe_server.py
   ```

### Project Structure

```
opendict/
├── OpenDictApp/           # Swift source files
│   ├── OpenDictApp.swift  # Main app delegate
│   ├── AudioRecorder.swift  # Audio recording logic
│   ├── GlobalHotkeyManager.swift # Keyboard shortcuts
│   ├── AccessibilityManager.swift # Text insertion
│   ├── ContentView.swift    # SwiftUI interface
│   ├── SimpleTranscriptionClient.swift # Server communication
│   ├── TranscriptionClient.swift # Alternative client
│   └── Info.plist          # App configuration
├── transcribe_server.py    # Python transcription server
├── transcribe.py          # Standalone transcription script
├── Package.swift          # Swift package configuration
├── OpenDict.app/          # Built application bundle
├── venv/                  # Python virtual environment
└── README.md             # This file
```

### Key Dependencies

**Swift Dependencies**:
- AVFoundation (audio recording)
- SwiftUI (user interface)
- Carbon (keyboard events)
- ApplicationServices (accessibility)
- Network (modern networking)

**Python Dependencies**:
- nemo-toolkit[asr] (speech recognition)
- torch (deep learning backend)
- librosa (audio processing)
- pytest (testing framework)
- black (code formatting)
- flake8 (linting)
- mypy (type checking)
- bandit (security scanning)
- pre-commit (git hooks)

**Development Tools**:
- SwiftFormat (Swift code formatting)
- SwiftLint (Swift linting, optional)
- Sphinx (documentation generation)

## 🐛 Troubleshooting

### Common Issues

<details>
<summary>Click to expand troubleshooting guide</summary>

#### 1. **Accessibility Permission Issues**
**Problem**: Text not being inserted after transcription
**Solution**:
- Go to System Preferences > Security & Privacy > Privacy > Accessibility
- Add OpenDict to the list of allowed applications
- Restart the application

#### 2. **Python Server Not Starting**
**Problem**: Transcription fails with connection errors
**Solution**:
- Ensure Python virtual environment is activated
- Check if port 8765 is available: `lsof -i :8765`
- Verify NeMo toolkit installation: `pip list | grep nemo`
- Check server logs for detailed error messages

#### 3. **Recording Not Working**
**Problem**: No audio captured when pressing Ctrl+Space
**Solution**:
- Grant microphone permissions in System Preferences
- Check if another application is using the microphone
- Verify hotkey is not conflicting with other applications

#### 4. **Model Loading Issues**
**Problem**: First-time transcription takes very long or fails
**Solution**:
- Ensure stable internet connection for model download
- Check available disk space (model requires ~2GB)
- Clear model cache: `rm -rf ~/.opendict_cache/`

#### 5. **Menu Bar Icon Not Appearing**
**Problem**: App starts but no menu bar icon visible
**Solution**:
- Check if menu bar is full (remove other items)
- Restart the application
- Verify app is not running in background (check Activity Monitor)

</details>

### Debug Information

To enable verbose logging:
1. Run the Python server manually: `python transcribe_server.py`
2. Monitor server logs for transcription requests
3. Check Console.app for Swift application logs

### Performance Optimization

1. **Model Caching**: First transcription will be slow (~30-60 seconds) while downloading the model
2. **Subsequent Usage**: Cached model loads much faster (~2-5 seconds)
3. **Memory Usage**: Python server uses ~2-3GB RAM when loaded
4. **Recording Limit**: 60-second maximum recording time to prevent excessive memory usage

## 🤝 Contributing

We welcome contributions! Please see our [Developer Guide](docs/DEVELOPER_GUIDE.md) for detailed information.

### Quick Contributing Guide

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run quality checks: `make quality-check`
5. Run tests: `make test`
6. Commit your changes: `git commit -m "Add feature"`
7. Push to your fork: `git push origin feature-name`
8. Submit a pull request

### Development Workflow

```bash
# Set up your development environment
make dev-setup

# Make your changes, then run quality checks
make format
make quality-check
make test

# Build and test the application
make build
make run-server  # In one terminal
make run-app     # In another terminal
```

## 📄 Documentation

- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Comprehensive development documentation
- [API Documentation](docs/API.md) - Complete API reference
- [Troubleshooting](#troubleshooting) - Common issues and solutions

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For issues and questions, please:

1. Check the [troubleshooting section](#troubleshooting)
2. Search existing [GitHub issues](https://github.com/hasanbaig8/opendict/issues)
3. Open a new issue with detailed information

## 🌟 Acknowledgments

- Built with [NVIDIA NeMo](https://github.com/NVIDIA/NeMo) for state-of-the-art speech recognition
- Uses the Parakeet TDT 0.6B model for fast, accurate transcription
