# Contributing to OpenDict

Thank you for your interest in contributing to OpenDict! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Process](#development-process)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team. All complaints will be reviewed and investigated and will result in a response that is deemed necessary and appropriate to the circumstances.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- macOS 13.0 or later
- Xcode 15.0 or later
- Python 3.8 or later
- Git installed and configured

### Setting Up Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork locally**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/opendict.git
   cd opendict
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/opendict.git
   ```
4. **Set up development environment**:
   ```bash
   make dev-setup
   ```

### First Time Setup

1. **Install dependencies**:
   ```bash
   make install
   ```
2. **Run tests** to ensure everything works:
   ```bash
   make test
   ```
3. **Check code quality**:
   ```bash
   make quality-check
   ```

## How to Contribute

### Types of Contributions

We welcome several types of contributions:

1. **Bug Reports**: Help us identify issues
2. **Bug Fixes**: Solve reported problems
3. **Feature Requests**: Suggest new functionality
4. **Feature Implementation**: Add new features
5. **Documentation**: Improve or add documentation
6. **Code Quality**: Refactoring, performance improvements
7. **Tests**: Add or improve test coverage

### Areas That Need Help

- **Accessibility**: Improve accessibility features
- **Performance**: Optimize model loading and transcription
- **UI/UX**: Enhance user interface and experience
- **Testing**: Increase test coverage
- **Documentation**: Keep docs up-to-date
- **Platform Support**: Expand to other platforms

## Development Process

### Branching Strategy

We use a simplified Git flow:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches
- `hotfix/*`: Critical fixes for production

### Workflow

1. **Create a branch** from `develop`:
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   make dev-test
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

### Commit Message Format

Use conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(transcription): add support for MP3 files
fix(server): handle connection timeout properly
docs(api): update transcription endpoint documentation
test(audio): add unit tests for audio processing
```

## Code Style

### Python Code Style

We follow PEP 8 with some modifications:

- **Line Length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes preferred
- **Imports**: Sorted with isort
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public functions

#### Example:

```python
def transcribe_audio(
    audio_file: str,
    model_name: str = "nvidia/parakeet-tdt-0.6b-v2"
) -> str:
    """Transcribe audio file using the specified model.

    Args:
        audio_file: Path to the audio file to transcribe.
        model_name: Name of the model to use for transcription.

    Returns:
        The transcribed text.

    Raises:
        AudioProcessingError: If audio processing fails.
        ModelError: If model loading fails.
    """
    # Implementation here
    pass
```

### Swift Code Style

We follow Swift API Design Guidelines:

- **Indentation**: 4 spaces
- **Line Length**: 100 characters
- **Naming**: Use descriptive names
- **Documentation**: Use Swift documentation comments
- **Access Control**: Use appropriate access levels

#### Example:

```swift
/// Manages global keyboard shortcuts for the application.
class GlobalHotkeyManager: ObservableObject {
    /// Indicates whether the hotkey is currently pressed.
    @Published var isHotkeyPressed = false

    /// Initializes the hotkey manager and sets up global monitoring.
    init() {
        setupGlobalHotkey()
    }

    /// Sets up global hotkey monitoring.
    private func setupGlobalHotkey() {
        // Implementation here
    }
}
```

### Code Formatting

We use automatic formatters:

#### Python
```bash
# Format code
black .
isort .

# Check formatting
black --check .
isort --check-only .
```

#### Swift
```bash
# Format code
swiftformat OpenDictApp/

# Check formatting
swiftformat --lint HelloWorldApp/
```

### Static Analysis

We use static analysis tools:

#### Python
```bash
# Type checking
mypy .

# Linting
flake8 .

# Security scanning
bandit -r .
```

#### Swift
```bash
# Static analysis (if available)
swiftlint OpenDictApp/
```

## Testing

### Test Requirements

- **All new features** must include tests
- **Bug fixes** should include regression tests
- **Tests must pass** before merging
- **Aim for >80% coverage** on new code

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test fixtures
└── conftest.py     # Pytest configuration
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_config.py -v
```

### Writing Tests

#### Python Test Example

```python
def test_transcription_success(mock_audio_file, mock_nemo_model):
    """Test successful audio transcription."""
    # Arrange
    server = TranscriptionServer()
    server.model = mock_nemo_model

    # Act
    result = server.transcribe_audio(mock_audio_file)

    # Assert
    assert result == "Hello world"
    mock_nemo_model.transcribe.assert_called_once_with([mock_audio_file])
```

#### Swift Test Example

```swift
func testAudioRecordingStart() {
    // Arrange
    let recorder = AudioRecorder()

    // Act
    recorder.startGlobalRecording()

    // Assert
    XCTAssertTrue(recorder.isGlobalRecording)
}
```

## Documentation

### Documentation Requirements

- **All public APIs** must be documented
- **New features** need user documentation
- **Changes** should update existing docs
- **Examples** should be included where helpful

### Documentation Types

1. **API Documentation**: In-code documentation
2. **User Documentation**: README and guides
3. **Developer Documentation**: Contributing, architecture
4. **Examples**: Usage examples and tutorials

### Writing Documentation

#### Python Docstrings

Use Google style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: If param1 is invalid.
    """
```

#### Swift Documentation

Use Swift documentation comments:

```swift
/// Brief description of the function.
///
/// Longer description if needed.
///
/// - Parameters:
///   - param1: Description of param1
///   - param2: Description of param2
/// - Returns: Description of return value
/// - Throws: `ErrorType` if something goes wrong
func functionName(param1: String, param2: Int) throws -> Bool {
    // Implementation
}
```

### Building Documentation

```bash
# Generate documentation
make docs

# View documentation
open docs/_build/html/index.html
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   make test
   ```

2. **Run quality checks**:
   ```bash
   make quality-check
   ```

3. **Update documentation** if needed

4. **Rebase on latest develop**:
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout your-branch
   git rebase develop
   ```

### PR Guidelines

1. **Title**: Use clear, descriptive title
2. **Description**: Explain what and why
3. **Link Issues**: Reference related issues
4. **Small PRs**: Keep changes focused
5. **Tests**: Include relevant tests
6. **Documentation**: Update docs if needed

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated integration tests if needed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. **Automated Checks**: CI must pass
2. **Code Review**: At least one approval required
3. **Testing**: QA testing for significant changes
4. **Documentation**: Docs review for user-facing changes

### Merge Process

1. **Squash and Merge** for feature branches
2. **Update Changelog** if applicable
3. **Tag Release** for version updates
4. **Deploy** if needed

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- macOS version:
- Python version:
- Swift version:
- OpenDict version:

## Additional Context
Any other relevant information
```

### Feature Requests

Use the feature request template:

```markdown
## Feature Description
Brief description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other approaches you've considered

## Additional Context
Any other relevant information
```

### Security Issues

For security issues, please **DO NOT** create a public issue. Instead:

1. Email security@opendict.com
2. Include detailed description
3. Provide reproduction steps
4. Allow time for fixing before disclosure

## Getting Help

### Community

- **GitHub Discussions**: For questions and discussions
- **Issues**: For bug reports and feature requests
- **Discord**: For real-time chat (if available)

### Documentation

- **README**: Basic setup and usage
- **Developer Guide**: Detailed development info
- **API Documentation**: Complete API reference

### Contact

- **Maintainers**: Listed in MAINTAINERS.md
- **Email**: contribute@opendict.com
- **Discord**: #opendict-dev

## Recognition

### Contributors

All contributors are recognized in:
- **README**: Contributors section
- **CHANGELOG**: For each release
- **About**: In the application

### Maintainers

Current maintainers are listed in MAINTAINERS.md.

## License

By contributing to OpenDict, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to OpenDict! Your help makes this project better for everyone.
