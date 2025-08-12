"""
Pytest configuration and shared fixtures for tests.
"""

import os

# Add src to Python path for imports
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import ImageDatabase
from recommendation_engine import RecommendationEngine, UserRequirement


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Create database
    db = ImageDatabase(db_path)
    yield db

    # Cleanup
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_image_data():
    """Sample image data for testing."""
    return {
        "image": "mcr.microsoft.com/azurelinux/base/python:3.12",
        "tag": "3.12",
        "languages": [
            {
                "language": "python",
                "version": "3.12.0",
                "major_minor": "3.12",
                "verified": True,
                "package_type": "deb",
                "package_name": "python3.12",
            }
        ],
        "package_managers": [{"name": "pip", "version": "23.0.1"}],
        "base_os": {"name": "Azure Linux", "version": "3.0"},
        "vulnerabilities": {
            "total": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "scanner": "grype",
            "scan_timestamp": "2024-01-01T00:00:00Z",
        },
        "manifest": {"size": 150000000, "layers": 5},
        "capabilities": ["python-runtime", "pip"],
        "recommendations": {
            "best_for": ["python-3.12", "python-web-apps"],
            "compatible_frameworks": ["flask", "django", "fastapi"],
            "use_cases": ["Web applications", "Data analysis"],
        },
    }


@pytest.fixture
def sample_syft_output():
    """Sample Syft output for testing."""
    return {
        "artifacts": [
            {
                "name": "python3.12",
                "version": "3.12.0-1",
                "type": "deb",
                "foundBy": "dpkgdb-cataloger",
                "locations": [{"path": "/var/lib/dpkg/status"}],
                "metadata": {
                    "package": "python3.12",
                    "source": "python3.12",
                    "version": "3.12.0-1",
                    "architecture": "amd64",
                },
            },
            {
                "name": "pip",
                "version": "23.0.1",
                "type": "python",
                "foundBy": "python-package-cataloger",
                "locations": [{"path": "/usr/lib/python3.12/site-packages"}],
            },
        ],
        "source": {
            "type": "image",
            "target": "mcr.microsoft.com/azurelinux/base/python:3.12",
        },
    }


@pytest.fixture
def user_requirement():
    """Sample user requirement for testing."""
    return UserRequirement(
        language="python",
        version="3.12",
        packages=["pip", "bash"],
        size_preference="balanced",
        security_level="high",
    )


@pytest.fixture
def mock_docker_commands():
    """Mock Docker commands."""
    with patch("subprocess.run") as mock_run:
        # Mock successful Docker commands
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"some": "json"}'
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_syft_commands():
    """Mock Syft commands."""

    def mock_syft_run(*args, **kwargs):
        if "syft" in args[0]:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '{"artifacts": []}'
            mock_result.stderr = ""
            return mock_result
        return Mock()

    with patch("subprocess.run", side_effect=mock_syft_run) as mock_run:
        yield mock_run


@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "test_data"
