#!/usr/bin/env python3
"""
Container Image Analyzer for Azure Linux Base Images

This module analyzes container images to extract language runtimes, packages,
and capabilities using Syft and runtime verification.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ImageAnalyzer:
    """Analyzes container images to extract language and package information"""

    def __init__(self, image_name: str):
        self.image_name = image_name
        self.syft_data = None
        self.verified_runtimes = []

        # Language runtime patterns for detection - more specific patterns
        self.language_patterns = {
            "python": [r"^python3?$", r"^python3\.\d+$", r"^python3\.\d+-.*"],
            "node": [r"^nodejs?$", r"^node$"],
            "java": [r"^openjdk.*", r"^java$", r"^jre.*", r"^jdk.*"],
            "go": [r"^golang?$", r"^go$"],
            "ruby": [r"^ruby$", r"^ruby\d+.*"],
            "php": [r"^php$", r"^php\d+.*"],
            "dotnet": [
                r"^dotnet.*",
                r"^aspnetcore.*",
                r"^netstandard.*",
                r"^microsoft\.netcore\.app.*",
                r"^microsoft\.aspnetcore\.app.*",
            ],
            "rust": [r"^rust$", r"^cargo$"],
            "perl": [r"^perl$"],
            "lua": [r"^lua$", r"^lua\d+.*"],
        }

        # Packages to exclude when detecting languages (libraries, not runtimes)
        self.excluded_packages = {
            "python": [
                "python-wheel",
                "python-pip",
                "python-setuptools",
                "python-dev",
                "python-distutils",
                "python-pkg-resources",
                "python-six",
                "python-urllib3",
                "python-requests",
                "python-chardet",
                "python-certifi",
                "python-idna",
                "python-pysocks",
            ],
            "node": ["nodejs-dev", "nodejs-npm", "node-gyp"],
            "java": ["java-common"],
        }

        # Package manager mappings
        self.package_managers = {
            "pip": "python",
            "npm": "node",
            "yarn": "node",
            "composer": "php",
            "gem": "ruby",
            "cargo": "rust",
            "mvn": "java",
            "gradle": "java",
        }

        # Runtime verification commands
        self.runtime_commands = {
            "python": ["python3", "--version"],
            "python_alt": ["python", "--version"],
            "node": ["node", "--version"],
            "java": ["java", "-version"],
            "go": ["go", "version"],
            "ruby": ["ruby", "--version"],
            "php": ["php", "--version"],
            "dotnet": ["dotnet", "--info"],
            "perl": ["perl", "--version"],
            "lua": ["lua", "-v"],
        }

    def analyze(self) -> Dict:
        """Complete analysis of container image"""

        print(f"Analyzing {self.image_name} with Syft...")
        self.syft_data = self.run_syft()

        if not self.syft_data:
            print(
                "Warning: Syft analysis failed, proceeding with runtime verification only"
            )

        # Parse Syft output for languages
        syft_languages = self.extract_languages_from_syft()

        # Verify with runtime commands
        print("Verifying runtime versions...")
        self.verified_runtimes = self.verify_runtime_versions()

        # Combine and deduplicate results
        final_analysis = self.combine_results(syft_languages)

        return final_analysis

    def run_syft(self) -> Optional[Dict]:
        """Run Syft and return JSON output"""
        try:
            result = subprocess.run(
                ["syft", self.image_name, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"Syft failed: {result.stderr}")
                return None
        except FileNotFoundError:
            print("Error: Syft not found. Please install Syft first.")
            return None
        except subprocess.TimeoutExpired:
            print("Error: Syft analysis timed out")
            return None
        except Exception as e:
            print(f"Error running Syft: {e}")
            return None

    def extract_languages_from_syft(self) -> List[Dict]:
        """Extract language runtimes from Syft data"""
        if not self.syft_data or "artifacts" not in self.syft_data:
            return []

        languages = []
        found_languages = {}  # Track best match for each language

        print(
            f"  📦 Analyzing {len(self.syft_data['artifacts'])} packages for language runtimes..."
        )

        for artifact in self.syft_data["artifacts"]:
            package_name = artifact["name"].lower()
            original_name = artifact["name"]
            version = artifact["version"]
            package_type = artifact.get("type", "")

            # Check for language runtimes
            for lang, patterns in self.language_patterns.items():
                # Skip if this package is in the exclusion list
                if lang in self.excluded_packages:
                    if package_name in self.excluded_packages[lang]:
                        continue

                for pattern in patterns:
                    if re.match(pattern, package_name):
                        # Calculate priority (exact matches get higher priority)
                        priority = self.calculate_package_priority(
                            package_name, lang, package_type
                        )

                        # Only keep if this is a better match than what we already have
                        if (
                            lang not in found_languages
                            or priority > found_languages[lang]["priority"]
                        ):
                            print(
                                f"    🔍 Found {lang} runtime: {original_name} v{version} (priority: {priority})"
                            )

                            # Extract runtime info
                            runtime_info = {
                                "language": lang,
                                "version": version,
                                "package_name": original_name,
                                "package_type": package_type,
                                "architecture": None,
                                "vendor": None,
                                "source": "syft",
                                "priority": priority,
                            }

                            # Get additional metadata if available
                            if "metadata" in artifact:
                                metadata = artifact["metadata"]
                                if "architecture" in metadata:
                                    runtime_info["architecture"] = metadata[
                                        "architecture"
                                    ]
                                if "vendor" in metadata:
                                    runtime_info["vendor"] = metadata["vendor"]

                            # Special handling for Python versions
                            if lang == "python":
                                runtime_info["major_minor"] = (
                                    self.extract_python_version(package_name, version)
                                )
                                print(
                                    f"      🐍 Extracted Python major.minor: {runtime_info['major_minor']}"
                                )

                            # Special handling for Node.js versions
                            elif lang == "node":
                                runtime_info["major_minor"] = (
                                    self.extract_nodejs_version(package_name, version)
                                )
                                print(
                                    f"      🟢 Extracted Node.js major.minor: {runtime_info['major_minor']}"
                                )

                            # Special handling for .NET versions
                            elif lang == "dotnet":
                                runtime_info["major_minor"] = (
                                    self.extract_dotnet_version(package_name, version)
                                )
                                print(
                                    f"      🔷 Extracted .NET major.minor: {runtime_info['major_minor']}"
                                )

                            found_languages[lang] = runtime_info
                        break

        # Check for .NET based on image name patterns (fallback for Microsoft images)
        dotnet_from_image = self.detect_dotnet_from_image_name()
        if dotnet_from_image and "dotnet" not in found_languages:
            found_languages["dotnet"] = dotnet_from_image
            print(
                f"    🔍 Found .NET runtime from image name: {dotnet_from_image['version']} (priority: {dotnet_from_image['priority']})"
            )

        # Convert to list and remove priority field
        result_languages = []
        for lang_info in found_languages.values():
            del lang_info["priority"]  # Remove internal field
            result_languages.append(lang_info)

        print(f"  ✅ Detected {len(result_languages)} language runtimes from packages")
        return result_languages

    def extract_dotnet_version(self, package_name: str, full_version: str) -> str:
        """Extract major.minor version for .NET"""

        # Try to extract from the image tag if this is from a container image
        if hasattr(self, "image_name") and ":" in self.image_name:
            image_tag = self.image_name.split(":")[-1]
            # Look for version pattern in tag like "8.0" or "8.0.19"
            version_match = re.search(r"(\d+\.\d+)", image_tag)
            if version_match:
                return version_match.group(1)

        # Extract from version string like 8.0.19
        if full_version:
            match = re.search(r"^(\d+\.\d+)", full_version)
            if match:
                return match.group(1)

        # Fallback to full version
        return full_version

    def detect_dotnet_from_image_name(self) -> Optional[Dict]:
        """Detect .NET runtime from Microsoft image name patterns"""

        # Check if this is a Microsoft .NET image
        dotnet_image_patterns = [
            r"mcr\.microsoft\.com/dotnet/(?:aspnet|runtime):(\d+\.\d+)",
            r"mcr\.microsoft\.com/dotnet/(?:aspnet|runtime):(\d+\.\d+\.\d+)",
            r"microsoft/dotnet:(\d+\.\d+)-(?:aspnetcore-)?runtime",
            r"microsoft/aspnetcore:(\d+\.\d+)",
        ]

        for pattern in dotnet_image_patterns:
            match = re.search(pattern, self.image_name.lower())
            if match:
                version = match.group(1)
                # If we only have major.minor, assume latest patch version
                if version.count(".") == 1:
                    version += ".0"

                return {
                    "language": "dotnet",
                    "version": version,
                    "package_name": "Microsoft .NET Runtime",
                    "package_type": "container_runtime",
                    "architecture": None,
                    "vendor": "Microsoft",
                    "source": "image_name_detection",
                    "priority": 90,  # High priority for known Microsoft images
                    "major_minor": ".".join(version.split(".")[:2]),
                }

        return None

    def calculate_package_priority(
        self, package_name: str, language: str, package_type: str
    ) -> int:
        """Calculate priority for language package matching"""
        priority = 0

        # Exact language name match gets highest priority
        if package_name == language:
            priority += 100

        # Runtime packages get higher priority than dev packages
        if package_type in ["rpm", "deb", "apk"]:
            priority += 50

        # Specific version patterns get higher priority
        if language == "python":
            if re.match(r"^python3\.\d+$", package_name):
                priority += 80  # python3.12 gets high priority
            elif package_name == "python3":
                priority += 70  # python3 gets good priority
            elif package_name == "python":
                priority += 60  # python gets medium priority

        elif language == "node":
            if package_name == "nodejs":
                priority += 80
            elif package_name == "node":
                priority += 70

        elif language == "java":
            if "openjdk" in package_name:
                priority += 80
            elif package_name == "java":
                priority += 70

        # Penalize dev/lib packages
        if any(
            suffix in package_name for suffix in ["-dev", "-devel", "-lib", "-common"]
        ):
            priority -= 20

        return priority

    def extract_python_version(self, package_name: str, full_version: str) -> str:
        """Extract major.minor version for Python"""

        # First try to extract from package name (most reliable for runtime packages)
        if "python3." in package_name:
            # Extract from package name like python3.12
            match = re.search(r"python3\.(\d+)", package_name)
            if match:
                return f"3.{match.group(1)}"

        # Try to extract from the image tag if this is from a container image
        if hasattr(self, "image_name") and ":" in self.image_name:
            image_tag = self.image_name.split(":")[-1]
            # Look for version pattern in tag like "3.12" or "3.12.4"
            version_match = re.search(r"(\d+\.\d+)", image_tag)
            if version_match:
                return version_match.group(1)

        # Extract from version string like 3.12.4
        if full_version:
            match = re.search(r"^(\d+\.\d+)", full_version)
            if match:
                return match.group(1)

        # Fallback to full version
        return full_version

    def extract_nodejs_version(self, package_name: str, full_version: str) -> str:
        """Extract major.minor version for Node.js"""

        # Try to extract from the image tag if this is from a container image
        if hasattr(self, "image_name") and ":" in self.image_name:
            image_tag = self.image_name.split(":")[-1]
            # Look for version pattern in tag like "20" or "20.14" or "20.14.0"
            version_match = re.search(r"(\d+(?:\.\d+)?)", image_tag)
            if version_match:
                version_str = version_match.group(1)
                # If it's just a major version like "20", return "20.0"
                if "." not in version_str:
                    return f"{version_str}.0"
                return version_str

        # Extract from version string like 20.14.0
        if full_version:
            match = re.search(r"^(\d+\.\d+)", full_version)
            if match:
                return match.group(1)
            # Handle case where version is just major like "20"
            match = re.search(r"^(\d+)$", full_version)
            if match:
                return f"{match.group(1)}.0"

        # Fallback to full version
        return full_version

    def verify_runtime_versions(self) -> List[Dict]:
        """Verify language runtime versions by running the container"""

        verified_runtimes = []

        for runtime, cmd in self.runtime_commands.items():
            try:
                # Run command in container
                docker_cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "--entrypoint",
                    "",
                    self.image_name,
                ] + cmd

                result = subprocess.run(
                    docker_cmd, capture_output=True, text=True, timeout=30
                )

                if result.returncode == 0:
                    version = self.parse_version_output(
                        runtime, result.stdout, result.stderr
                    )
                    if version:
                        verified_runtimes.append(
                            {
                                "language": runtime.replace("_alt", ""),
                                "version": version,
                                "verified": True,
                                "source": "runtime_verification",
                            }
                        )

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                continue
            except Exception as e:
                print(f"Error verifying {runtime}: {e}")
                continue

        return verified_runtimes

    def parse_version_output(
        self, runtime: str, stdout: str, stderr: str
    ) -> Optional[str]:
        """Parse version from command output"""

        # Combine stdout and stderr (some tools output to stderr)
        output = (stdout + stderr).strip()

        version_patterns = {
            "python": r"Python (\d+\.\d+\.\d+)",
            "python_alt": r"Python (\d+\.\d+\.\d+)",
            "node": r"v(\d+\.\d+\.\d+)",
            "java": r'version "(\d+\.\d+\.\d+)',
            "go": r"go version go(\d+\.\d+\.\d+)",
            "ruby": r"ruby (\d+\.\d+\.\d+)",
            "php": r"PHP (\d+\.\d+\.\d+)",
            "dotnet": r"Version:\s*(\d+\.\d+\.\d+)",
            "perl": r"v(\d+\.\d+\.\d+)",
            "lua": r"Lua (\d+\.\d+\.\d+)",
        }

        if runtime in version_patterns:
            match = re.search(version_patterns[runtime], output)
            if match:
                return match.group(1)

        return None

    def extract_package_managers(self) -> List[Dict]:
        """Extract package managers from Syft data"""
        if not self.syft_data or "artifacts" not in self.syft_data:
            return []

        managers = []

        for artifact in self.syft_data["artifacts"]:
            package_name = artifact["name"].lower()

            if package_name in self.package_managers:
                managers.append(
                    {
                        "name": artifact["name"],
                        "version": artifact["version"],
                        "language": self.package_managers[package_name],
                        "type": artifact["type"],
                    }
                )

        return managers

    def extract_capabilities(self) -> List[str]:
        """Extract capabilities from system packages"""
        if not self.syft_data or "artifacts" not in self.syft_data:
            return []

        capabilities = set()

        for artifact in self.syft_data["artifacts"]:
            package_name = artifact["name"].lower()

            # Map packages to capabilities
            if "ssl" in package_name or "tls" in package_name:
                capabilities.add("ssl")
            if "curl" in package_name:
                capabilities.add("http_client")
            if "git" in package_name:
                capabilities.add("version_control")
            if "sqlite" in package_name:
                capabilities.add("database")
            if "postgres" in package_name or "mysql" in package_name:
                capabilities.add("database")
            if "zlib" in package_name or "gzip" in package_name:
                capabilities.add("compression")
            if "xml" in package_name:
                capabilities.add("xml_processing")
            if "json" in package_name:
                capabilities.add("json_processing")

        return list(capabilities)

    def combine_results(self, syft_languages: List[Dict]) -> Dict:
        """Combine Syft and verification results"""

        # Start with base analysis info
        final_result = {
            "image": self.image_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "base_os": {},
            "languages": [],
            "package_managers": [],
            "capabilities": [],
            "system_packages": [],
            "recommendations": {},
        }

        # Extract base OS info
        if self.syft_data and "distro" in self.syft_data:
            final_result["base_os"] = {
                "name": self.syft_data["distro"].get("name", "unknown"),
                "version": self.syft_data["distro"].get("version", "unknown"),
            }

        # Merge language information (prefer verified over syft)
        language_map = {}

        # Add Syft languages
        for lang in syft_languages:
            key = lang["language"]
            language_map[key] = lang

        # Override with verified versions (runtime verification is more accurate)
        for runtime in self.verified_runtimes:
            key = runtime["language"]
            if key in language_map:
                # Merge verified info with syft info, but use verified version
                syft_info = language_map[key].copy()
                syft_info.update(
                    {
                        "verified_version": runtime["version"],
                        "verified": True,
                        "version": runtime[
                            "version"
                        ],  # Use verified version as primary
                    }
                )

                # For Python, update major_minor based on verified version
                if key == "python":
                    version_match = re.search(r"^(\d+\.\d+)", runtime["version"])
                    if version_match:
                        syft_info["major_minor"] = version_match.group(1)

                # For Node.js, update major_minor based on verified version
                elif key == "node":
                    version_match = re.search(r"^(\d+\.\d+)", runtime["version"])
                    if version_match:
                        syft_info["major_minor"] = version_match.group(1)
                    else:
                        # Handle case where version is just major like "20"
                        version_match = re.search(r"^(\d+)", runtime["version"])
                        if version_match:
                            syft_info["major_minor"] = f"{version_match.group(1)}.0"

                # For .NET, update major_minor based on verified version
                elif key == "dotnet":
                    version_match = re.search(r"^(\d+\.\d+)", runtime["version"])
                    if version_match:
                        syft_info["major_minor"] = version_match.group(1)

                language_map[key] = syft_info
            else:
                # Add new verified runtime
                new_runtime = runtime.copy()
                new_runtime["verified"] = True

                # For Python, add major_minor
                if key == "python":
                    version_match = re.search(r"^(\d+\.\d+)", runtime["version"])
                    if version_match:
                        new_runtime["major_minor"] = version_match.group(1)

                # For Node.js, add major_minor
                elif key == "node":
                    version_match = re.search(r"^(\d+\.\d+)", runtime["version"])
                    if version_match:
                        new_runtime["major_minor"] = version_match.group(1)
                    else:
                        # Handle case where version is just major like "20"
                        version_match = re.search(r"^(\d+)", runtime["version"])
                        if version_match:
                            new_runtime["major_minor"] = f"{version_match.group(1)}.0"

                # For .NET, add major_minor
                elif key == "dotnet":
                    version_match = re.search(r"^(\d+\.\d+)", runtime["version"])
                    if version_match:
                        new_runtime["major_minor"] = version_match.group(1)

                language_map[key] = new_runtime

        final_result["languages"] = list(language_map.values())

        # Add package managers
        final_result["package_managers"] = self.extract_package_managers()

        # Add capabilities
        final_result["capabilities"] = self.extract_capabilities()

        # Add system packages summary
        if self.syft_data and "artifacts" in self.syft_data:
            system_packages = []
            for artifact in self.syft_data["artifacts"]:
                if artifact["type"] in ["rpm", "deb", "apk"]:
                    system_packages.append(
                        {
                            "name": artifact["name"],
                            "version": artifact["version"],
                            "type": artifact["type"],
                        }
                    )
            final_result["system_packages"] = system_packages

        # Generate recommendations
        final_result["recommendations"] = self.generate_recommendations(final_result)

        return final_result

    def generate_recommendations(self, analysis: Dict) -> Dict:
        """Generate usage recommendations based on analysis"""

        recommendations = {"best_for": [], "compatible_frameworks": [], "use_cases": []}

        # Generate recommendations based on detected languages
        for lang_info in analysis["languages"]:
            lang = lang_info["language"]
            version = lang_info.get("version", "unknown")

            if lang == "python":
                major_minor = lang_info.get("major_minor", version)
                recommendations["best_for"].extend(
                    [f"python-{major_minor}", "python-web-apps", "python-data-science"]
                )
                recommendations["compatible_frameworks"].extend(
                    ["flask", "django", "fastapi", "pandas", "numpy"]
                )
                recommendations["use_cases"].extend(
                    [
                        "Web applications",
                        "Data analysis",
                        "Machine learning",
                        "Automation scripts",
                    ]
                )

            elif lang == "node":
                recommendations["best_for"].extend(
                    [f"node-{version}", "javascript-apps", "node-web-services"]
                )
                recommendations["compatible_frameworks"].extend(
                    ["express", "nestjs", "react", "vue", "angular"]
                )
                recommendations["use_cases"].extend(
                    ["Web applications", "API services", "Real-time applications"]
                )

            elif lang == "java":
                recommendations["best_for"].extend(
                    [f"java-{version}", "enterprise-apps", "microservices"]
                )
                recommendations["compatible_frameworks"].extend(
                    ["spring", "spring-boot", "quarkus", "micronaut"]
                )
                recommendations["use_cases"].extend(
                    ["Enterprise applications", "Microservices", "Big data processing"]
                )

            elif lang == "dotnet":
                major_minor = lang_info.get("major_minor", version)
                recommendations["best_for"].extend(
                    [
                        f"dotnet-{major_minor}",
                        "aspnet-core",
                        "enterprise-apps",
                        "microservices",
                    ]
                )
                recommendations["compatible_frameworks"].extend(
                    ["ASP.NET Core", "Entity Framework", "Blazor", "Web API"]
                )
                recommendations["use_cases"].extend(
                    [
                        "Web applications",
                        "API services",
                        "Enterprise applications",
                        "Microservices",
                    ]
                )

        # Add capability-based recommendations
        if "ssl" in analysis["capabilities"]:
            recommendations["use_cases"].append("Secure communications")
        if "database" in analysis["capabilities"]:
            recommendations["use_cases"].append("Database applications")
        if "http_client" in analysis["capabilities"]:
            recommendations["use_cases"].append("API integrations")

        # Remove duplicates
        for key in recommendations:
            recommendations[key] = list(set(recommendations[key]))

        return recommendations


def main():
    """Main entry point for the image analyzer"""
    if len(sys.argv) != 2:
        print("Usage: python image_analyzer.py <image_name>")
        print(
            "Example: python image_analyzer.py mcr.microsoft.com/azurelinux/base/python:3.12"
        )
        sys.exit(1)

    image_name = sys.argv[1]
    analyzer = ImageAnalyzer(image_name)

    try:
        result = analyzer.analyze()
        print(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        print("\nAnalysis interrupted")
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
