# Contributing to Secure Container Base Image Recommender

Thank you for your interest in contributing to the Secure Container Base Image Recommender! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Architecture Overview](#architecture-overview)
- [Adding New Features](#adding-new-features)
- [Documentation](#documentation)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

## Getting Started

### Prerequisites

- **Docker**: Required for container image analysis
- **Python 3.12+**: Primary development language
- **Git**: Version control
- **VS Code** (recommended): For the best development experience with dev container support

### Quick Setup Options

**Option 1: Dev Container (Recommended)**
1. Install [VS Code](https://code.visualstudio.com/) and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Clone the repository: `git clone https://github.com/maniSbindra/secure-container-base-image-recommender.git`
3. Open in VS Code and select "Reopen in Container" when prompted
4. All dependencies (Docker, Syft, Trivy, Python packages) are automatically installed

**Option 2: Manual Setup**
1. Clone the repository
2. Install external dependencies:
   ```bash
   # Install Syft
   curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

   # Install Trivy
   brew install trivy  # or follow https://aquasecurity.github.io/trivy/latest/getting-started/installation/
   ```
3. Set up Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Development Setup

### Initial Setup

1. **Install pre-commit hooks** (automatically formats and checks code):
   ```bash
   pre-commit install
   ```

2. **Verify setup** by running tests:
   ```bash
   pytest
   ```

3. **Start the Web UI** for development:
   ```bash
   cd web_ui
   ./start.sh
   ```

### Project Structure

```
├── src/                     # Core application code
│   ├── cli.py              # Command-line interface
│   ├── database.py         # Database operations
│   ├── image_analyzer.py   # Container image analysis
│   ├── recommendation_engine.py  # Recommendation logic
│   └── registry_scanner.py # Registry scanning functionality
├── web_ui/                 # Flask web application
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── config/                # Configuration files
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

## Development Workflow

### Branch Strategy

1. **Fork** the repository (for external contributors)
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```
3. **Make your changes** with clear, focused commits
4. **Test thoroughly** (see [Testing](#testing) section)
5. **Submit a pull request** to the `main` branch

### Commit Messages

Use clear, descriptive commit messages:

```bash
# Good examples:
git commit -m "Add support for Python 3.13 base images"
git commit -m "Fix vulnerability scoring algorithm for CVSS v3"
git commit -m "Improve Web UI responsiveness on mobile devices"

# Include issue numbers when applicable:
git commit -m "Fix database connection timeout (#45)"
```

## Code Style and Standards

We use automated tools to maintain code quality. Pre-commit hooks will automatically format your code, but you can also run them manually:

### Code Formatting

```bash
# Format Python code with Black
black src/ web_ui/ tests/

# Sort imports with isort
isort src/ web_ui/ tests/

# Check code style with flake8
flake8 src/ web_ui/ tests/
```

### Code Quality Tools

- **Black**: Code formatting (line length: 88 characters)
- **isort**: Import sorting
- **flake8**: Style and complexity checking
- **bandit**: Security vulnerability scanning
- **mypy**: Type checking (optional but encouraged)

### Configuration

All tools are configured in:
- `pyproject.toml` - Black and isort settings
- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `.github/workflows/ci.yml` - CI/CD pipeline settings

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/          # End-to-end tests only

# Run tests matching a pattern
pytest -k "test_recommendation"

# Run tests in verbose mode
pytest -v
```

### Writing Tests

1. **Unit tests**: Test individual functions and classes in isolation
   ```python
   def test_vulnerability_scoring():
       # Test the scoring algorithm with known inputs
       pass
   ```

2. **Integration tests**: Test component interactions
   ```python
   def test_database_and_analyzer_integration():
       # Test that analyzer results are properly stored in database
       pass
   ```

3. **Mock external dependencies**: Use `pytest-mock` for Docker, Syft, Trivy calls
   ```python
   def test_image_analysis_with_mock(mocker):
       mock_docker = mocker.patch('docker.from_env')
       # Test logic without actually calling Docker
   ```

### Test Data

- Add test data to `tests/test_data/`
- Use small, representative samples
- Document any special test requirements

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass**:
   ```bash
   pytest
   pre-commit run --all-files
   ```

2. **Update documentation** if needed:
   - Update `README.md` for user-facing changes
   - Update docstrings for API changes
   - Add entries to `docs/` for significant features

3. **Write a clear PR description**:
   - Describe what the change does and why
   - Reference any related issues: "Fixes #123"
   - Include screenshots for UI changes
   - List any breaking changes

4. **Request review** from maintainers

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Fixes #(issue number)
```

## Issue Guidelines

### Reporting Bugs

Include:
- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected vs. actual behavior**
- **Environment details** (OS, Python version, Docker version)
- **Error messages** and stack traces
- **Sample images or commands** that trigger the issue

### Feature Requests

Include:
- **Use case description** - why is this needed?
- **Proposed solution** - how should it work?
- **Alternatives considered** - what other approaches did you think about?
- **Additional context** - mockups, examples, references

### Labels

We use these labels to categorize issues:
- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation needs
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `question` - Further information requested

## Architecture Overview

### Core Components

1. **CLI Interface** (`src/cli.py`): Command-line tool for scanning and recommendations
2. **Database Layer** (`src/database.py`): SQLite database operations
3. **Image Analyzer** (`src/image_analyzer.py`): Container image analysis using Syft and Trivy
4. **Registry Scanner** (`src/registry_scanner.py`): Automated registry scanning
5. **Recommendation Engine** (`src/recommendation_engine.py`): Matching and ranking algorithms
6. **Web UI** (`web_ui/`): Flask-based web interface

### Data Flow

```
Registry → Scanner → Analyzer → Database → Recommendation Engine → UI/CLI
```

### External Dependencies

- **Docker**: Container runtime for image analysis
- **Syft**: Software Bill of Materials generation
- **Trivy**: Vulnerability scanning
- **SQLite**: Database storage
- **Flask**: Web UI framework

## Adding New Features

### For Registry Support

1. **Extend `registry_scanner.py`**:
   - Add new registry authentication methods
   - Implement tag enumeration for the registry
   - Add registry-specific image reference parsing

2. **Update configuration**:
   - Extend `config/repositories.txt` format if needed
   - Add new configuration options

3. **Test thoroughly**:
   - Add unit tests for new registry code
   - Test with real registry if possible
   - Add integration tests

### For Analysis Tools

1. **Extend `image_analyzer.py`**:
   - Add new tool integration
   - Implement result parsing
   - Handle tool-specific errors

2. **Update database schema** if needed:
   - Add migration scripts in `src/database.py`
   - Update test data

3. **Update recommendation logic**:
   - Modify scoring algorithms in `recommendation_engine.py`
   - Update UI to display new data

### For Programming Languages

1. **Update language detection** in `image_analyzer.py`
2. **Add language-specific package managers** and detection logic
3. **Update recommendation algorithms** for new language patterns
4. **Add test cases** with sample images for the new language

## Documentation

### Code Documentation

- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Type hints**: Add type hints to function signatures
- **Comments**: Explain complex algorithms and business logic

Example:
```python
def calculate_vulnerability_score(cve_data: Dict[str, Any]) -> float:
    """Calculate a vulnerability score based on CVE data.

    Args:
        cve_data: Dictionary containing CVE information including
                 severity, CVSS score, and exploitability metrics.

    Returns:
        A float score between 0.0 and 10.0, where higher values
        indicate more severe vulnerabilities.

    Raises:
        ValueError: If CVE data is missing required fields.
    """
```

### User Documentation

- **README.md**: Keep the main README up-to-date
- **API documentation**: Document Web UI endpoints in `web_ui/README.md`
- **Architecture docs**: Update `docs/images/architecture.md` for structural changes

### Examples and Demos

- **Update demo GIF** if UI changes significantly
- **Add code examples** for new CLI commands or API endpoints
- **Update screenshots** in documentation

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: Maintainers will provide feedback on pull requests

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Special mentions for first-time contributors

Thank you for contributing to making container security more accessible! 🚀

---

For questions about contributing, please open an issue or start a discussion on GitHub.
