# Secure Container Base Image Recommender

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test the Repository

**Required External Tools Installation (ALWAYS install these first):**
```bash
# Install Syft for Software Bill of Materials generation
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sudo sh -s -- -b /usr/local/bin

# Install Grype for vulnerability scanning
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sudo sh -s -- -b /usr/local/bin

# Install Trivy for comprehensive security scanning
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh -s -- -b /usr/local/bin

# Verify installations
syft version && grype version && trivy --version && docker --version
```

**Python Dependencies Installation:**
```bash
# Install main dependencies (takes ~1-5 seconds)
pip install -r requirements.txt

# Install development dependencies (takes ~15 seconds)
pip install -r requirements-dev.txt

# Install web UI dependencies (takes ~3 seconds)
cd web_ui && pip install -r requirements.txt && cd ..
```

**Code Quality and Testing:**
```bash
# Install pre-commit hooks
pre-commit install

# Run all tests - NEVER CANCEL: Test suite takes ~6 seconds. Set timeout to 30+ seconds.
pytest tests/ --cov=src --cov-report=html --cov-report=term -v

# Code formatting (takes ~1 second)
black --check src/ web_ui/ tests/

# Import sorting (takes <1 second)
isort --check-only src/ web_ui/ tests/

# Linting (takes ~1 second)
flake8 src/ web_ui/ tests/ --max-line-length=88 --extend-ignore=F401,F841,F541,E402,D400,D202,D107,D104,D401,D205,E501,E231,E221,E722,E741,E713,F402,F811,B001,B017,D105,D200,D100

# Security scanning (takes ~1 second)
bandit -r src/ web_ui/ --skip B101,B603,B607,B404,B112,B105,B201,B104,B608,B110
```

### Running the Application

**Web UI (Recommended for development):**
```bash
cd web_ui
python app.py
# Access at http://localhost:8080
# Startup time: ~5 seconds
# Features: Dashboard, Image Search, Recommendations, Scanning, Comparison
```

**CLI Usage:**
```bash
# Get help
python src/cli.py --help

# Get recommendations (takes ~1-2 seconds)
python src/cli.py --recommend --language python --version 3.12 --limit 5

# Analyze a specific image - NEVER CANCEL: Takes ~12 seconds. Set timeout to 60+ seconds.
python src/cli.py --analyze mcr.microsoft.com/azurelinux/base/python:3.12

# Scan and add image to database - NEVER CANCEL: Takes ~13 seconds with --comprehensive. Set timeout to 60+ seconds.
python src/cli.py --scan-image mcr.microsoft.com/azurelinux/base/nodejs:20 --comprehensive

# Comprehensive repository scan - NEVER CANCEL: Can take 30+ minutes for full scans. Set timeout to 60+ minutes.
python src/cli.py --scan-repo mcr.microsoft.com/azurelinux/base/python --comprehensive --max-tags 5
```

## Validation

**ALWAYS manually validate changes through complete user scenarios:**

**CLI Validation Workflow:**
```bash
# 1. Test recommendation functionality
python src/cli.py --recommend --language python --version 3.12

# 2. Test image analysis
python src/cli.py --analyze mcr.microsoft.com/azurelinux/base/python:3.12

# 3. Test scanning functionality
python src/cli.py --scan-image mcr.microsoft.com/azurelinux/base/nodejs:20
```

**Web UI Validation Workflow:**
```bash
# 1. Start web server
cd web_ui && python app.py

# 2. Verify server responds
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/

# 3. Test in browser:
#    - Navigate to http://localhost:8080
#    - Access Dashboard (view statistics and database summary)
#    - Use Recommend page (select Python 3.12, get recommendations)
#    - Test MCR Scanner page (scan an image)
#    - Verify Compare functionality
```

**ALWAYS run these validation steps after making changes:**
```bash
# Quick validation suite (takes ~10 seconds total)
pytest tests/ -v
black --check src/ web_ui/ tests/
flake8 src/ web_ui/ tests/ --max-line-length=88 --extend-ignore=F401,F841,F541,E402,D400,D202,D107,D104,D401,D205,E501,E231,E221,E722,E741,E713,F402,F811,B001,B017,D105,D200,D100
```

## Common Tasks

### Repository Structure
```
├── src/                     # Core application code
│   ├── cli.py              # Command-line interface (main entry point)
│   ├── database.py         # SQLite database operations
│   ├── image_analyzer.py   # Container image analysis (Syft, Trivy, Docker)
│   ├── recommendation_engine.py  # ML-style recommendation logic
│   └── registry_scanner.py # Registry scanning functionality
├── web_ui/                 # Flask web application
│   ├── app.py             # Web server entry point
│   ├── templates/         # HTML templates
│   └── requirements.txt   # Web UI dependencies
├── tests/                  # Test suite (unit, integration, e2e)
├── config/                # Configuration files
│   └── repositories.txt   # Registry scan configuration
├── scripts/               # Utility scripts
└── azure_linux_images.db # Pre-scanned SQLite database (Git LFS)
```

### Key Development Commands
```bash
# Generate nightly recommendations report (takes ~1 second)
python scripts/generate_nightly_recommendations_md.py

# Reset database (DESTRUCTIVE - use with caution)
python src/cli.py --reset-database

# View database statistics
sqlite3 azure_linux_images.db 'SELECT COUNT(*) FROM images;'
```

### Configuration Files
- **pyproject.toml**: Black and isort settings
- **.pre-commit-config.yaml**: Pre-commit hook configuration
- **.github/workflows/ci.yml**: CI/CD pipeline settings
- **config/repositories.txt**: Registry scan configuration

### External Dependencies
- **Docker**: Required for container analysis (version 28.0.4+)
- **Syft**: Software Bill of Materials generation (version 1.31.0+)
- **Trivy**: Vulnerability and security scanning (version 0.65.0+)
- **Grype**: Additional vulnerability scanning (version 0.98.0+)

### Database Operations
- **Pre-scanned database**: azure_linux_images.db (557KB, tracked with Git LFS)
- **Contains**: 33+ images with vulnerability data, language runtimes, packages
- **Statistics**: ~13 images with zero vulnerabilities, average 26.6 vulnerabilities per image
- **Languages supported**: Python, Node.js, Java, .NET, Perl, Go

### Timing Expectations

**CRITICAL - NEVER CANCEL OPERATIONS:**

| Operation | Time | Timeout Setting |
|-----------|------|----------------|
| Dependency installation | 15 seconds | 300 seconds |
| Test suite | 6 seconds | 30 seconds |
| Code quality tools | 1-3 seconds | 10 seconds |
| Web UI startup | 5 seconds | 15 seconds |
| CLI recommendations | 1-2 seconds | 10 seconds |
| Image analysis | 12 seconds | 60 seconds |
| Comprehensive image scan | 13 seconds | 60 seconds |
| Repository scan (5 tags) | 5-10 minutes | 20 minutes |
| Full repository scan (all tags) | 30+ minutes | 60+ minutes |
| Nightly workflow | 6 hours | 360 minutes |

**ALWAYS include "NEVER CANCEL" warnings for operations taking >10 seconds.**

### Security and Best Practices
- **Code scanning**: Bandit for security vulnerabilities (configured to skip common false positives)
- **Type checking**: MyPy available but optional
- **Container security**: Focus on images with zero critical/high vulnerabilities
- **Database constraints**: Name uniqueness enforced, composite uniqueness needs review
- **Pre-commit hooks**: Automated formatting and checks (may timeout in CI environments)

### CI/CD Integration
- **GitHub Actions**: Comprehensive CI pipeline with Python 3.12
- **Coverage**: Test coverage reporting via pytest-cov
- **Security scanning**: Trivy filesystem scanning
- **Nightly updates**: Automated database updates via GitHub Actions (runs at 02:00 UTC)

### Troubleshooting
- **Pre-commit timeout**: Run individual tools manually if pre-commit fails
- **Database issues**: Check azure_linux_images.db exists and is not a Git LFS pointer
- **Docker access**: Ensure Docker daemon is running and accessible
- **External tool failures**: Verify Syft, Trivy, Grype are in PATH and executable
- **Web UI port conflicts**: Default port 8080, check for conflicts
- **LFS issues**: Use `git lfs pull` to fetch actual database file if needed

Always run validation workflows end-to-end after making changes to ensure functionality remains intact.
