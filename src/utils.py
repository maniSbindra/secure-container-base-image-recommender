"""
Utilities for Azure Linux Base Image Analysis

Common utility functions used across the project.
"""

import re
import subprocess
from typing import Dict, List, Optional, Tuple

from packaging import version


def parse_version(version_string: str) -> Tuple[int, int, int]:
    """Parse a version string into major, minor, patch components"""
    try:
        # Use packaging library for robust version parsing
        v = version.parse(version_string)
        if hasattr(v, "major"):
            return (v.major, getattr(v, "minor", 0), getattr(v, "micro", 0))
        else:
            # Fallback to regex parsing
            match = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", version_string)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2)) if match.group(2) else 0
                patch = int(match.group(3)) if match.group(3) else 0
                return (major, minor, patch)
    except Exception:
        pass

    # Fallback to 0.0.0 if parsing fails
    return (0, 0, 0)


def is_version_compatible(
    required: str, available: str, compatibility_mode: str = "minor"
) -> bool:
    """
    Check if available version is compatible with required version

    Args:
        required: Required version string
        available: Available version string
        compatibility_mode: "exact", "patch", "minor", or "major"
    """
    if not required or not available:
        return True

    req_parts = parse_version(required)
    avail_parts = parse_version(available)

    if compatibility_mode == "exact":
        return req_parts == avail_parts
    elif compatibility_mode == "patch":
        return req_parts[:2] == avail_parts[:2] and avail_parts[2] >= req_parts[2]
    elif compatibility_mode == "minor":
        return req_parts[0] == avail_parts[0] and avail_parts[1] >= req_parts[1]
    elif compatibility_mode == "major":
        return avail_parts[0] >= req_parts[0]

    return False


def normalize_package_name(package_name: str) -> str:
    """Normalize package name for comparison"""
    # Convert to lowercase and remove common variations
    normalized = package_name.lower().strip()

    # Handle common package name variations
    variations = {
        "nodejs": "node",
        "python3": "python",
        "openjdk": "java",
        "golang": "go",
    }

    for variant, canonical in variations.items():
        if normalized.startswith(variant):
            normalized = normalized.replace(variant, canonical, 1)

    return normalized


def extract_language_from_image_name(image_name: str) -> Optional[str]:
    """Extract language from image name patterns"""

    # Common patterns in Azure Linux image names
    patterns = [
        r"azurelinux/base/(\w+):",
        r"azurelinux/distroless/(\w+):",
        r"/(\w+):[\d\.]+",
    ]

    for pattern in patterns:
        match = re.search(pattern, image_name)
        if match:
            lang = match.group(1).lower()

            # Map common variations
            lang_map = {
                "nodejs": "node",
                "openjdk": "java",
                "golang": "go",
                "python3": "python",
            }

            return lang_map.get(lang, lang)

    return None


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable string"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def is_docker_available() -> bool:
    """Check if Docker is available and running"""
    try:
        result = subprocess.run(
            ["docker", "version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        subprocess.CalledProcessError,
    ):
        return False


def is_syft_available() -> bool:
    """Check if Syft is available"""
    try:
        result = subprocess.run(
            ["syft", "--version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        subprocess.CalledProcessError,
    ):
        return False


def validate_image_name(image_name: str) -> bool:
    """Validate container image name format"""
    # Basic validation for container image names
    pattern = r"^[a-z0-9]+([\.\-_][a-z0-9]+)*(/[a-z0-9]+([\.\-_][a-z0-9]+)*)*:[a-zA-Z0-9]+([\.\-_][a-zA-Z0-9]+)*$"
    return bool(re.match(pattern, image_name))


def extract_registry_info(image_name: str) -> Dict[str, str]:
    """Extract registry, repository, and tag from image name"""

    # Default values
    result = {"registry": "docker.io", "repository": "", "tag": "latest"}

    # Remove protocol if present
    image_name = re.sub(r"^https?://", "", image_name)

    # Split by slash to get parts
    parts = image_name.split("/")

    if len(parts) >= 3:
        # Full registry/namespace/repo:tag format
        result["registry"] = parts[0]

        # Check if last part has tag
        if ":" in parts[-1]:
            repo_tag = parts[-1].split(":")
            result["repository"] = "/".join(parts[1:-1]) + "/" + repo_tag[0]
            result["tag"] = repo_tag[1]
        else:
            result["repository"] = "/".join(parts[1:])

    elif len(parts) == 2:
        # namespace/repo:tag format (Docker Hub)
        if ":" in parts[1]:
            repo_tag = parts[1].split(":")
            result["repository"] = parts[0] + "/" + repo_tag[0]
            result["tag"] = repo_tag[1]
        else:
            result["repository"] = "/".join(parts)

    elif len(parts) == 1:
        # Just repo:tag format
        if ":" in parts[0]:
            repo_tag = parts[0].split(":")
            result["repository"] = repo_tag[0]
            result["tag"] = repo_tag[1]
        else:
            result["repository"] = parts[0]

    return result


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem operations"""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'

    for char in unsafe_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(" .")

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def merge_package_lists(list1: List[str], list2: List[str]) -> List[str]:
    """Merge two package lists, removing duplicates and normalizing names"""

    combined = set()

    for pkg_list in [list1, list2]:
        for pkg in pkg_list:
            normalized = normalize_package_name(pkg)
            combined.add(normalized)

    return sorted(list(combined))


def detect_package_manager_from_files(file_list: List[str]) -> List[str]:
    """Detect package managers based on configuration files"""

    managers = []

    file_patterns = {
        "npm": ["package.json", "package-lock.json"],
        "yarn": ["yarn.lock"],
        "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
        "maven": ["pom.xml"],
        "gradle": ["build.gradle", "build.gradle.kts"],
        "composer": ["composer.json"],
        "gem": ["Gemfile"],
        "cargo": ["Cargo.toml"],
        "go": ["go.mod"],
    }

    for manager, patterns in file_patterns.items():
        for pattern in patterns:
            if any(pattern in f for f in file_list):
                managers.append(manager)
                break

    return managers


class VersionRange:
    """Represents a version range for compatibility checking"""

    def __init__(self, min_version: str = None, max_version: str = None):
        self.min_version = min_version
        self.max_version = max_version

    def contains(self, version_str: str) -> bool:
        """Check if version falls within this range"""
        if not version_str:
            return False

        version_parts = parse_version(version_str)

        if self.min_version:
            min_parts = parse_version(self.min_version)
            if version_parts < min_parts:
                return False

        if self.max_version:
            max_parts = parse_version(self.max_version)
            if version_parts > max_parts:
                return False

        return True

    def __str__(self):
        if self.min_version and self.max_version:
            return f"{self.min_version} - {self.max_version}"
        elif self.min_version:
            return f">= {self.min_version}"
        elif self.max_version:
            return f"<= {self.max_version}"
        else:
            return "any"
