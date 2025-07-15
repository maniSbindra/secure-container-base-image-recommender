"""
Recommendation Engine for Azure Linux Base Images

This module provides intelligent recommendations for secure base images
based on user requirements.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from database import ImageDatabase


@dataclass
class UserRequirement:
    """Represents user requirements for a base image"""
    language: str
    version: Optional[str] = None
    packages: List[str] = None
    capabilities: List[str] = None
    size_preference: str = "balanced"  # minimal, balanced, full
    security_level: str = "high"  # standard, high, maximum
    max_vulnerabilities: Optional[int] = None
    max_critical_vulnerabilities: int = 0
    max_high_vulnerabilities: int = 0


@dataclass
class ImageRecommendation:
    """Represents a recommended image with score and reasoning"""
    image_name: str
    score: float
    language_match: bool
    version_match: bool
    package_compatibility: float
    size_score: float
    security_score: float
    reasoning: List[str]
    analysis_data: Dict


class RecommendationEngine:
    """Recommends optimal Azure Linux base images based on requirements"""
    
    def __init__(self, database_path: str = "azure_linux_images.db"):
        self.database_path = database_path
        self.db = ImageDatabase(database_path)
        
        # Configure logging for this module
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            # Create console handler with formatting
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)  # Set to INFO to see package ecosystem logs
        
        # Version compatibility patterns
        self.version_patterns = {
            'python': r'(\d+)\.(\d+)(?:\.(\d+))?',
            'node': r'(\d+)\.(\d+)(?:\.(\d+))?',
            'java': r'(\d+)(?:\.(\d+))?(?:\.(\d+))?',
            'go': r'(\d+)\.(\d+)(?:\.(\d+))?',
            'dotnet': r'(\d+)\.(\d+)(?:\.(\d+))?'
        }
        
        # Package ecosystem mappings
        self.package_ecosystems = {
            'python': ['pip', 'conda', 'poetry'],
            'node': ['npm', 'yarn', 'pnpm'],
            'java': ['maven', 'gradle'],
            'go': ['go mod'],
            'dotnet': ['nuget'],
            'php': ['composer'],
            'ruby': ['gem', 'bundler']
        }
    
    def _filter_platform_specific_images(self, candidate_images: List[Dict]) -> List[Dict]:
        """Filter out platform-specific images (arm, amd, etc.) to avoid platform assumptions"""
        platform_keywords = [
            'arm', 'amd', 'x86', 'aarch64', 'arm64', 'armhf', 'armv7', 'armv6', 
            'i386', 'i686', 'x64', 'amd64', 'intel', 'apple', 'm1', 'm2', 'azl'
        ]
        
        filtered_images = []
        for image in candidate_images:
            image_name = image.get('name', '').lower()
            
            # Check if any platform keyword is present in the image name/tag
            # Look for keywords as separate words or with common separators
            has_platform_keyword = False
            for keyword in platform_keywords:
                # Check for the keyword as a separate word or with separators like -, _, :
                import re
                pattern = r'(?:^|[-_:/.])' + re.escape(keyword) + r'(?:[-_:/.@]|$)'
                if re.search(pattern, image_name):
                    has_platform_keyword = True
                    self.logger.debug(f"Found platform keyword '{keyword}' in image: {image.get('name', '')}")
                    break
            
            if not has_platform_keyword:
                filtered_images.append(image)
            else:
                self.logger.debug(f"Filtering out platform-specific image: {image.get('name', '')}")
        
        self.logger.info(f"Filtered {len(candidate_images) - len(filtered_images)} platform-specific images, {len(filtered_images)} remaining")
        return filtered_images

    def recommend(self, requirements: UserRequirement) -> List[ImageRecommendation]:
        """Get ranked recommendations based on requirements"""
        
        # Query database for images matching the language and security requirements
        candidate_images = self.db.query_images_by_language(
            language=requirements.language,
            version=requirements.version,
            max_vulnerabilities=requirements.max_vulnerabilities
        )
        
        # Additional security filtering
        if requirements.security_level == "maximum":
            candidate_images = [img for img in candidate_images 
                              if img['critical_vulnerabilities'] == 0 and img['high_vulnerabilities'] == 0]
        elif requirements.security_level == "high":
            candidate_images = [img for img in candidate_images 
                              if img['critical_vulnerabilities'] <= requirements.max_critical_vulnerabilities 
                              and img['high_vulnerabilities'] <= requirements.max_high_vulnerabilities]
        
        # Filter out platform-specific images
        candidate_images = self._filter_platform_specific_images(candidate_images)
        
        if not candidate_images:
            print("No images found matching security, language, and platform requirements")
            return []
        
        recommendations = []
        
        for image_data in candidate_images:
            # Convert database row to dict format expected by scoring
            analysis_data = self._convert_db_row_to_analysis(image_data)
            score, reasoning = self.score_image(analysis_data, requirements)
            
            if score > 0:  # Only include viable options
                recommendation = ImageRecommendation(
                    image_name=image_data['name'],
                    score=score,
                    language_match=True,  # Already filtered by language
                    version_match=self.check_version_match(analysis_data, requirements),
                    package_compatibility=self.calculate_package_compatibility(analysis_data, requirements),
                    size_score=self.calculate_size_score(analysis_data, requirements),
                    security_score=self.calculate_security_score(analysis_data, requirements),
                    reasoning=reasoning,
                    analysis_data=analysis_data
                )
                recommendations.append(recommendation)
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return recommendations
    
    def _convert_db_row_to_analysis(self, image_row: Dict) -> Dict:
        """Convert database row to analysis data format"""
        
        # Parse capabilities from concatenated string
        capabilities = []
        if image_row.get('capabilities'):
            capabilities = image_row['capabilities'].split(',')
        
        # Create mock analysis data structure
        analysis_data = {
            'image': image_row['name'],
            'languages': [{
                'language': image_row['language'],
                'version': image_row['lang_version'],
                'major_minor': image_row['major_minor']
            }] if image_row.get('language') else [],
            'capabilities': capabilities,
            'manifest': {
                'size': image_row.get('size_bytes', 0)
            },
            'vulnerabilities': {
                'total': image_row.get('total_vulnerabilities', 0),
                'critical': image_row.get('critical_vulnerabilities', 0),
                'high': image_row.get('high_vulnerabilities', 0),
                'medium': image_row.get('medium_vulnerabilities', 0),
                'low': image_row.get('low_vulnerabilities', 0)
            },
            'base_os': {
                'name': image_row.get('base_os_name', 'azurelinux')
            }
        }
        
        return analysis_data
    
    def score_image(self, image_data: Dict, requirements: UserRequirement) -> Tuple[float, List[str]]:
        """Score an image against requirements"""
        score = 0.0
        reasoning = []
        
        # Language match (40% of score)
        language_score = self.score_language_match(image_data, requirements)
        score += language_score * 0.4
        if language_score > 0.8:
            reasoning.append(f"Excellent {requirements.language} support")
        elif language_score > 0.5:
            reasoning.append(f"Good {requirements.language} support")
        
        # Version compatibility (25% of score)
        version_score = self.score_version_compatibility(image_data, requirements)
        score += version_score * 0.25
        if version_score > 0.9:
            reasoning.append("Perfect version match")
        elif version_score > 0.7:
            reasoning.append("Compatible version")
        
        # Package ecosystem (20% of score)
        package_score = self.score_package_ecosystem(image_data, requirements)
        score += package_score * 0.20
        if package_score >= 0.8:
            reasoning.append(self.get_package_reasoning(image_data, requirements))
        elif package_score > 0.6:
            reasoning.append("Good package manager support")
        
        # Size optimization (10% of score)
        size_score = self.score_size_preference(image_data, requirements)
        score += size_score * 0.10
        if size_score > 0.8:
            reasoning.append("Optimal size for requirements")
        
        # Security (5% of score)
        security_score = self.score_security(image_data, requirements)
        score += security_score * 0.05
        if security_score > 0.9:
            reasoning.append("Excellent security profile")
        
        return score, reasoning
    
    def score_language_match(self, image_data: Dict, requirements: UserRequirement) -> float:
        """Score language compatibility"""
        languages = image_data.get('languages', [])
        
        for lang_info in languages:
            if lang_info['language'].lower() == requirements.language.lower():
                # Perfect match
                if lang_info.get('verified', False):
                    return 1.0
                else:
                    return 0.9
        
        # Check if language could be installed
        base_os = image_data.get('base_os', {}).get('name', '') or ''  # Ensure it's never None
        if 'linux' in base_os.lower():
            return 0.3  # Could potentially install the language
        
        return 0.0
    
    def score_version_compatibility(self, image_data: Dict, requirements: UserRequirement) -> float:
        """Score version compatibility"""
        if not requirements.version:
            return 1.0  # No version requirement
        
        languages = image_data.get('languages', [])
        target_lang = requirements.language.lower()
        
        for lang_info in languages:
            if lang_info['language'].lower() == target_lang:
                image_version = lang_info.get('version', '')
                return self.compare_versions(requirements.version, image_version, target_lang)
        
        return 0.0
    
    def compare_versions(self, required: str, available: str, language: str) -> float:
        """Compare version compatibility"""
        if not required or not available:
            return 0.5
        
        # Get version pattern for language
        pattern = self.version_patterns.get(language, r'(\d+)\.(\d+)(?:\.(\d+))?')
        
        req_match = re.match(pattern, required)
        avail_match = re.match(pattern, available)
        
        if not req_match or not avail_match:
            # Fallback to string comparison
            return 1.0 if required == available else 0.5
        
        req_parts = [int(x) for x in req_match.groups() if x is not None]
        avail_parts = [int(x) for x in avail_match.groups() if x is not None]
        
        # Exact match
        if req_parts == avail_parts:
            return 1.0
        
        # Major version match
        if len(req_parts) >= 1 and len(avail_parts) >= 1:
            if req_parts[0] == avail_parts[0]:
                # Minor version compatibility
                if len(req_parts) >= 2 and len(avail_parts) >= 2:
                    if req_parts[1] == avail_parts[1]:
                        return 0.9  # Same major.minor
                    elif abs(req_parts[1] - avail_parts[1]) <= 1:
                        return 0.7  # Close minor version
                return 0.6  # Same major version
        
        return 0.2  # Different major version
    
    def score_package_ecosystem(self, image_data: Dict, requirements: UserRequirement) -> float:
        """Score package manager and ecosystem support"""
        # Use the class logger instead of creating a new one
        logger = self.logger
        
        # Log requirement parameters
        logger.info(f"Scoring package ecosystem for image: {image_data.get('image', 'unknown')}")
        logger.info(f"Required language: {requirements.language}")
        logger.info(f"Required packages: {requirements.packages}")
        
        if not requirements.packages:
            logger.info("No packages required - returning perfect score (1.0)")
            return 1.0
        
        total_required_packages = len(requirements.packages)
        logger.info(f"Total required packages: {total_required_packages}")
        
        # Get available data
        image_name = image_data.get('image', '')
        package_managers = image_data.get('package_managers', [])
        language = requirements.language.lower()
        
        # Get both system packages and package managers
        available_managers = self.get_installed_package_managers(image_name)
        installed_system_packages = self.get_installed_package_names(image_name)
        installed_packages_and_managers = self.get_system_packages_and_package_managers(image_name)
        
        logger.info(f"Available package managers in image: {list(available_managers)}")
        logger.info(f"Available system packages count: {len(installed_system_packages)}")
        logger.info(f"Total installed packages/managers: {len(installed_packages_and_managers)}")
        
        # Debug: Show some sample packages if any exist
        if installed_system_packages:
            sample_packages = list(installed_system_packages)[:5]  # Show first 5
            logger.debug(f"Sample system packages: {sample_packages}")
        
        # Check each package - either installed or available as package manager
        found_packages = 0
        found_package_details = []
        missing_packages = []
        
        for package in requirements.packages:
            package_lower = package.lower()
            
            # Check if it's an installed system package or package manager
            if package_lower in installed_packages_and_managers:
                found_packages += 1
                found_package_details.append(package)
                logger.debug(f"Package '{package}' found as installed package/manager")
                continue
            else:
                missing_packages.append(package)
                logger.debug(f"Package '{package}' not found in installed packages/managers")
        
        logger.info(f"Packages found: {found_packages}/{total_required_packages}")
        logger.info(f"Found packages: {found_package_details}")
        logger.info(f"Missing packages: {missing_packages}")
        
        # If all packages are found, perfect score
        if found_packages == len(requirements.packages):
            logger.info("All required packages found - returning perfect score (1.0)")
            return 1.0
        
        # If some packages found, partial score
        if found_packages > 0:
            base_score = found_packages / len(requirements.packages)
            logger.info(f"Partial package match - returning score: {base_score:.2f}")
            return base_score
        
        # Fallback to capabilities check
        capabilities = image_data.get('capabilities', [])
        logger.info(f"No packages found, checking capabilities: {capabilities}")
        
        if 'http_client' in capabilities:
            logger.info("HTTP client capability found - returning fallback score (0.4)")
            return 0.4  # Can download packages manually
        
        logger.info("No package support found - returning minimal score (0.1)")
        return 0.1  # Very limited package support
    
    def get_installed_package_managers(self, image_name: str) -> set:
        """Get set of installed package manager names for an image"""
        logger = self.logger
        logger.debug(f"Looking up package managers for image: {image_name}")
        
        # Get image ID from database
        cursor = self.db.conn.execute("SELECT id FROM images WHERE name = ?", (image_name,))
        image_row = cursor.fetchone()
        
        if not image_row:
            logger.debug(f"No image found with name: {image_name}")
            return set()
        
        image_id = image_row['id']
        logger.debug(f"Found image ID: {image_id}")
        
        # Get all installed package managers for this image
        cursor = self.db.conn.execute(
            "SELECT name FROM package_managers WHERE image_id = ?", (image_id,)
        )
        package_managers = {row['name'].lower() for row in cursor.fetchall()}
        logger.debug(f"Found {len(package_managers)} package managers: {list(package_managers)}")
        return package_managers
    
    def get_installed_package_names(self, image_name: str) -> set:
        """Get set of installed package names for an image"""
        logger = self.logger
        logger.debug(f"Looking up system packages for image: {image_name}")
        
        # Get image ID from database
        cursor = self.db.conn.execute("SELECT id FROM images WHERE name = ?", (image_name,))
        image_row = cursor.fetchone()
        
        if not image_row:
            logger.debug(f"No image found with name: {image_name}")
            return set()
        
        image_id = image_row['id']
        logger.debug(f"Found image ID: {image_id}")
        
        # Get all installed packages for this image
        cursor = self.db.conn.execute(
            "SELECT name FROM system_packages WHERE image_id = ?", (image_id,)
        )
        system_packages = {row['name'].lower() for row in cursor.fetchall()}
        logger.debug(f"Found {len(system_packages)} system packages")
        return system_packages
    
    def get_system_packages_and_package_managers(self, image_name: str) -> set:
        """Get set of installed system packages and package managers for an image"""
        # Get image ID from database
        cursor = self.db.conn.execute("SELECT id FROM images WHERE name = ?", (image_name,))
        image_row = cursor.fetchone()
        
        if not image_row:
            return set()
        
        image_id = image_row['id']
        
        # Get all installed system packages for this image
        cursor = self.db.conn.execute(
            "SELECT name FROM system_packages WHERE image_id = ?", (image_id,)
        )
        system_packages = {row['name'].lower() for row in cursor.fetchall()}
        
        # Get all installed package managers for this image
        cursor = self.db.conn.execute(
            "SELECT name FROM package_managers WHERE image_id = ?", (image_id,)
        )
        package_managers = {row['name'].lower() for row in cursor.fetchall()}
        return system_packages.union(package_managers)
    
    def check_installed_packages(self, image_name: str, required_packages: List[str]) -> float:
        """Check if required packages are already installed in the image"""
        if not required_packages:
            return 1.0
        
        # Get image ID from database
        cursor = self.db.conn.execute("SELECT id FROM images WHERE name = ?", (image_name,))
        image_row = cursor.fetchone()
        
        if not image_row:
            return 0.0
        
        image_id = image_row['id']
        
        # Get all installed packages for this image
        cursor = self.db.conn.execute(
            "SELECT name FROM system_packages WHERE image_id = ?", (image_id,)
        )
        installed_packages = {row['name'].lower() for row in cursor.fetchall()}
        
        # Check how many required packages are already installed
        required_lower = [pkg.lower() for pkg in required_packages]
        installed_count = sum(1 for pkg in required_lower if pkg in installed_packages)
        
        if installed_count == len(required_packages):
            return 1.0  # All packages installed - perfect score
        elif installed_count > 0:
            # Partial match - score based on percentage installed
            percentage = installed_count / len(required_packages)
            return 0.8 + (percentage * 0.2)  # Score between 0.8-1.0
        else:
            return 0.0  # No packages found
    
    def score_size_preference(self, image_data: Dict, requirements: UserRequirement) -> float:
        """Score based on size preference"""
        manifest = image_data.get('manifest', {})
        size = manifest.get('size', 0)
        
        if size == 0:
            return 0.5  # Unknown size
        
        # Size categories (in bytes)
        if requirements.size_preference == "minimal":
            if size < 50 * 1024 * 1024:  # < 50MB
                return 1.0
            elif size < 100 * 1024 * 1024:  # < 100MB
                return 0.7
            else:
                return 0.3
        
        elif requirements.size_preference == "balanced":
            if 50 * 1024 * 1024 < size < 200 * 1024 * 1024:  # 50-200MB
                return 1.0
            elif size < 300 * 1024 * 1024:  # < 300MB
                return 0.8
            else:
                return 0.5
        
        else:  # full
            return 1.0  # Size doesn't matter
    
    def score_security(self, image_data: Dict, requirements: UserRequirement) -> float:
        """Score security characteristics including vulnerability counts"""
        
        vulnerabilities = image_data.get('vulnerabilities', {})
        
        # Base score for Azure Linux (inherently secure)
        base_score = 1.0
        base_os = image_data.get('base_os', {}).get('name', '') or ''  # Ensure it's never None
        image_name = image_data.get('image', '')
        
        # Check if this is an Azure Linux image by OS name or image name
        is_azure_linux = (
            'azurelinux' in base_os.lower() or 
            'azurelinux' in image_name.lower() or
            'mcr.microsoft.com/azurelinux' in image_name.lower()
        )
        
        if not is_azure_linux:
            base_score = 0.8
        
        # Penalize based on vulnerability counts
        total_vulns = vulnerabilities.get('total', 0)
        critical_vulns = vulnerabilities.get('critical', 0)
        high_vulns = vulnerabilities.get('high', 0)
        
        # Heavy penalty for critical and high vulnerabilities
        if critical_vulns > 0:
            base_score -= 0.5  # Major penalty for critical vulns
        if high_vulns > 0:
            base_score -= 0.3  # Moderate penalty for high vulns
        
        # Light penalty for total vulnerability count
        if total_vulns > 10:
            base_score -= 0.1
        elif total_vulns > 5:
            base_score -= 0.05
        
        # Security level requirements
        if requirements.security_level == "maximum":
            if critical_vulns > 0 or high_vulns > 0:
                return 0.0  # Disqualify for maximum security
        elif requirements.security_level == "high":
            if critical_vulns > requirements.max_critical_vulnerabilities:
                return 0.0
            if high_vulns > requirements.max_high_vulnerabilities:
                return 0.0
        
        return max(0.0, base_score)
    
    def check_language_match(self, image_data: Dict, requirements: UserRequirement) -> bool:
        """Check if image supports the required language"""
        languages = image_data.get('languages', [])
        target_lang = requirements.language.lower()
        
        return any(lang['language'].lower() == target_lang for lang in languages)
    
    def check_version_match(self, image_data: Dict, requirements: UserRequirement) -> bool:
        """Check if image has compatible version"""
        if not requirements.version:
            return True
        
        score = self.score_version_compatibility(image_data, requirements)
        return score >= 0.7
    
    def calculate_package_compatibility(self, image_data: Dict, requirements: UserRequirement) -> float:
        """Calculate package compatibility score"""
        return self.score_package_ecosystem(image_data, requirements)
    
    def calculate_size_score(self, image_data: Dict, requirements: UserRequirement) -> float:
        """Calculate size optimization score"""
        return self.score_size_preference(image_data, requirements)
    
    def calculate_security_score(self, image_data: Dict, requirements: UserRequirement) -> float:
        """Calculate security score"""
        return self.score_security(image_data, requirements)
    
    def format_recommendations(self, recommendations: List[ImageRecommendation], limit: int = 5) -> str:
        """Format recommendations for display"""
        if not recommendations:
            return "No suitable images found for your requirements."
        
        output = []
        output.append("🔍 Recommended Azure Linux Base Images:\n")
        
        for i, rec in enumerate(recommendations[:limit], 1):
            output.append(f"{i}. {rec.image_name}")
            output.append(f"   Score: {rec.score:.2f}/1.00")
            output.append(f"   Reasons: {', '.join(rec.reasoning)}")
            
            # Show key details
            languages = rec.analysis_data.get('languages', [])
            if languages:
                lang_info = languages[0]  # Primary language
                version = lang_info.get('version', 'unknown')
                output.append(f"   Language: {lang_info['language']} {version}")
            
            # Show security info
            vulnerabilities = rec.analysis_data.get('vulnerabilities', {})
            total_vulns = vulnerabilities.get('total', 0)
            critical_vulns = vulnerabilities.get('critical', 0)
            high_vulns = vulnerabilities.get('high', 0)
            
            if total_vulns == 0:
                output.append(f"   Security: ✅ No vulnerabilities found")
            else:
                security_status = f"   Security: {total_vulns} total"
                if critical_vulns > 0:
                    security_status += f", {critical_vulns} critical ⚠️"
                if high_vulns > 0:
                    security_status += f", {high_vulns} high ⚠️"
                output.append(security_status)
            
            manifest = rec.analysis_data.get('manifest', {})
            if manifest.get('size'):
                size_mb = manifest['size'] / (1024 * 1024)
                output.append(f"   Size: {size_mb:.1f} MB")
            
            output.append("")
        
        return "\n".join(output)
    
    def get_package_reasoning(self, image_data: Dict, requirements: UserRequirement) -> str:
        """Get detailed reasoning about package availability"""
        if not requirements.packages:
            return "Rich package ecosystem"
        
        # Get available data
        image_name = image_data.get('image', '')
        package_managers = image_data.get('package_managers', [])
        available_managers = [pm['name'].lower() for pm in package_managers]
        
        # Get installed system packages
        installed_system_packages = set()
        if image_name:
            installed_system_packages = self.get_installed_package_names(image_name)
        
        found_system = []
        found_managers = []
        not_found = []
        
        # Check each package
        for package in requirements.packages:
            package_lower = package.lower()
            
            if package_lower in installed_system_packages:
                found_system.append(package)
            elif package_lower in available_managers:
                found_managers.append(package)
            else:
                not_found.append(package)
        
        # Build reasoning message
        total_found = len(found_system) + len(found_managers)
        total_packages = len(requirements.packages)
        
        if total_found == total_packages:
            parts = []
            if found_system:
                parts.append(f"{len(found_system)} pre-installed")
            if found_managers:
                parts.append(f"{len(found_managers)} package managers available")
            return f"All packages available ({', '.join(parts)})"
        elif total_found > 0:
            parts = []
            if found_system:
                parts.append(f"{len(found_system)} pre-installed")
            if found_managers:
                parts.append(f"{len(found_managers)} available as managers")
            return f"{', '.join(parts)} ({len(not_found)} missing)"
        else:
            # Check if we have appropriate package managers for installation
            language = requirements.language.lower()
            expected_managers = self.package_ecosystems.get(language, [])
            can_install = any(expected in available_managers for expected in expected_managers)
            if can_install:
                return "Can install packages via package managers"
            else:
                return "Limited package support"
    
    def get_image_from_database(self, image_name: str) -> Optional[Dict]:
        """Check if an image exists in the database and return its analysis data"""
        
        self.logger.debug(f"Searching for image in database: {image_name}")
        
        # Add default tag if not specified
        if ':' not in image_name:
            image_name += ':latest'
            self.logger.debug(f"Added default tag, searching for: {image_name}")
        
        # Query database for the image
        cursor = self.db.conn.execute("SELECT * FROM images WHERE name = ?", (image_name,))
        image_row = cursor.fetchone()
        
        if not image_row:
            self.logger.debug(f"Image not found in database: {image_name}")
            return None
        
        self.logger.debug(f"Found image in database with ID: {image_row['id']}")
        
        # Convert to dict and get additional data
        image_dict = dict(image_row)
        
        # Get system packages
        image_id = image_dict['id']
        cursor = self.db.conn.execute(
            "SELECT name, version FROM system_packages WHERE image_id = ?", (image_id,)
        )
        system_packages = [row['name'] for row in cursor.fetchall()]
        self.logger.debug(f"Found {len(system_packages)} system packages")
        
        # Get package managers
        cursor = self.db.conn.execute(
            "SELECT name, version FROM package_managers WHERE image_id = ?", (image_id,)
        )
        package_managers = [row['name'] for row in cursor.fetchall()]
        self.logger.debug(f"Found {len(package_managers)} package managers")
        
        # Get languages from the proper languages table
        cursor = self.db.conn.execute(
            "SELECT language, version, major_minor, verified FROM languages WHERE image_id = ?", (image_id,)
        )
        languages = []
        for row in cursor.fetchall():
            languages.append({
                'language': row['language'],
                'version': row['version'] or '',
                'major_minor': row['major_minor'] or '',
                'verified': bool(row['verified'])
            })
        
        self.logger.debug(f"Found {len(languages)} languages in languages table: {[l['language'] for l in languages]}")
        
        # Fallback to main table if no languages found in languages table (for backward compatibility)
        if not languages and image_dict.get('language'):
            self.logger.debug(f"No languages in languages table, using main table fallback: {image_dict.get('language')}")
            languages = [{
                'language': image_dict['language'],
                'version': image_dict['lang_version'] or '',
                'major_minor': image_dict['major_minor'] or '',
                'verified': False
            }]
        
        # Create analysis data structure similar to what ImageAnalyzer would return
        analysis_data = {
            'image': image_name,
            'languages': languages,
            'system_packages': system_packages,
            'package_managers': package_managers,
            'total_packages': len(system_packages) + len(package_managers),
            'manifest': {
                'size': image_dict.get('size_bytes', 0)
            },
            'vulnerabilities': {
                'total': image_dict.get('total_vulnerabilities', 0),
                'critical': image_dict.get('critical_vulnerabilities', 0),
                'high': image_dict.get('high_vulnerabilities', 0),
                'medium': image_dict.get('medium_vulnerabilities', 0),
                'low': image_dict.get('low_vulnerabilities', 0)
            },
            'base_os': {
                'name': image_dict.get('base_os_name', 'azurelinux')
            }
        }
        
        return analysis_data
    
    def recommend_from_existing_image(self, image_name: str, requirements: UserRequirement) -> Tuple[Optional[Dict], List[ImageRecommendation], UserRequirement]:
        """Get recommendations based on an existing image in the database"""
        
        self.logger.info(f"=== Starting recommendation analysis for existing image: {image_name} ===")
        self.logger.info(f"Input requirements - Size: {requirements.size_preference}, Security: {requirements.security_level}")
        self.logger.info(f"Vulnerability limits - Max total: {requirements.max_vulnerabilities}, Critical: {requirements.max_critical_vulnerabilities}, High: {requirements.max_high_vulnerabilities}")
        
        # Check if image exists in database
        self.logger.info(f"Step 1: Searching for image in database...")
        analysis_data = self.get_image_from_database(image_name)
        
        if not analysis_data:
            self.logger.warning(f"❌ Image not found in database: {image_name}")
            self.logger.info("Recommendation: Use the scan feature to add this image to the database first")
            return None, [], requirements
        
        self.logger.info(f"✅ Found image in database: {image_name}")
        self.logger.info(f"Image size: {analysis_data.get('manifest', {}).get('size', 0)} bytes")
        
        # Extract information from the existing image analysis
        self.logger.info(f"Step 2: Extracting image analysis data...")
        detected_languages = analysis_data.get('languages', [])
        system_packages = analysis_data.get('system_packages', [])
        package_managers = analysis_data.get('package_managers', [])
        vulnerabilities = analysis_data.get('vulnerabilities', {})
        
        language_descriptions = [f"{l.get('language')} {l.get('version', 'no-version')}" for l in detected_languages]
        self.logger.info(f"Detected {len(detected_languages)} languages: {language_descriptions}")
        self.logger.info(f"Found {len(system_packages)} system packages and {len(package_managers)} package managers")
        self.logger.info(f"Vulnerability summary - Total: {vulnerabilities.get('total', 0)}, Critical: {vulnerabilities.get('critical', 0)}, High: {vulnerabilities.get('high', 0)}")
        
        if not detected_languages:
            self.logger.error("❌ No programming language runtimes detected in the stored image analysis")
            self.logger.info("This could indicate:")
            self.logger.info("  - The image only contains system libraries")
            self.logger.info("  - The analysis needs to be updated")
            self.logger.info("  - The image is a minimal base OS without runtime")
            return analysis_data, [], requirements
        
        # Get all packages (system + package managers)
        self.logger.info(f"Step 3: Processing packages...")
        all_packages = list(set(system_packages + package_managers))
        self.logger.info(f"Combined unique packages: {len(all_packages)} total")
        if len(all_packages) > 0:
            sample_packages = all_packages[:10]  # Show first 10 as sample
            self.logger.info(f"Sample packages: {sample_packages}")
            if len(all_packages) > 10:
                self.logger.info(f"... and {len(all_packages) - 10} more")
        
        # Select the most appropriate primary language for recommendations
        self.logger.info(f"Step 4: Selecting primary language...")
        # Priority: 1) Verified languages, 2) Languages with versions, 3) First language
        primary_language = detected_languages[0]  # Default to first
        self.logger.info(f"Default primary language: {primary_language.get('language')} {primary_language.get('version', 'no-version')}")
        
        # Try to find a verified language first
        for lang in detected_languages:
            if lang.get('verified', False):
                primary_language = lang
                self.logger.info(f"Found verified language, switching to: {primary_language.get('language')} {primary_language.get('version', 'no-version')}")
                break
        
        # If no verified language, try to find one with a version
        if not primary_language.get('verified', False):
            for lang in detected_languages:
                if lang.get('version'):
                    primary_language = lang
                    self.logger.info(f"Found language with version, switching to: {primary_language.get('language')} {primary_language.get('version', 'no-version')}")
                    break
        
        language = primary_language.get('language', '')
        version = primary_language.get('version', '')
        
        self.logger.info(f"✅ Final primary language selected: {language} {version}")
        self.logger.info(f"Language verification status: {'verified' if primary_language.get('verified', False) else 'unverified'}")
        
        # Update requirements with detected information
        self.logger.info(f"Step 5: Creating updated requirements...")
        package_limit = 20
        limited_packages = all_packages[:package_limit]
        self.logger.info(f"Using first {len(limited_packages)} packages (limit: {package_limit}) for recommendations")
        
        updated_requirements = UserRequirement(
            language=language,
            version=version,
            packages=limited_packages,
            size_preference=requirements.size_preference,
            security_level=requirements.security_level,
            max_vulnerabilities=requirements.max_vulnerabilities,
            max_critical_vulnerabilities=requirements.max_critical_vulnerabilities,
            max_high_vulnerabilities=requirements.max_high_vulnerabilities
        )
        
        self.logger.info(f"Updated requirements created:")
        self.logger.info(f"  Language: {updated_requirements.language}")
        self.logger.info(f"  Version: {updated_requirements.version}")
        self.logger.info(f"  Packages: {len(updated_requirements.packages)} items")
        self.logger.info(f"  Size preference: {updated_requirements.size_preference}")
        self.logger.info(f"  Security level: {updated_requirements.security_level}")
        
        # Get recommendations using the existing recommendation engine
        self.logger.info(f"Step 6: Running recommendation engine with primary criteria...")
        recommendations = self.recommend(updated_requirements)
        self.logger.info(f"Primary search result: {len(recommendations)} recommendations found")
        
        # If no recommendations found with specific version, try with major.minor only
        if not recommendations and version:
            self.logger.info(f"Step 7: No results with specific version, trying fallback strategies...")
            import re
            version_match = re.match(r'(\d+)\.(\d+)', version)
            if version_match:
                major_minor = f"{version_match.group(1)}.{version_match.group(2)}"
                self.logger.info(f"Fallback 1: Trying with major.minor version only: {version} -> {major_minor}")
                
                fallback_requirements = UserRequirement(
                    language=language,
                    version=major_minor,
                    packages=limited_packages,
                    size_preference=requirements.size_preference,
                    security_level=requirements.security_level,
                    max_vulnerabilities=requirements.max_vulnerabilities,
                    max_critical_vulnerabilities=requirements.max_critical_vulnerabilities,
                    max_high_vulnerabilities=requirements.max_high_vulnerabilities
                )
                
                recommendations = self.recommend(fallback_requirements)
                self.logger.info(f"Fallback 1 result: {len(recommendations)} recommendations found")
                if recommendations:
                    updated_requirements = fallback_requirements  # Use the fallback requirements for response
                    self.logger.info(f"✅ Using fallback requirements with major.minor version")
        
        # If still no recommendations, try without version constraint
        if not recommendations:
            self.logger.info(f"Fallback 2: No results with version constraint, trying without version")
            
            no_version_requirements = UserRequirement(
                language=language,
                version=None,
                packages=limited_packages,
                size_preference=requirements.size_preference,
                security_level=requirements.security_level,
                max_vulnerabilities=requirements.max_vulnerabilities,
                max_critical_vulnerabilities=requirements.max_critical_vulnerabilities,
                max_high_vulnerabilities=requirements.max_high_vulnerabilities
            )
            
            recommendations = self.recommend(no_version_requirements)
            self.logger.info(f"Fallback 2 result: {len(recommendations)} recommendations found")
            if recommendations:
                updated_requirements = no_version_requirements  # Use the no-version requirements for response
                self.logger.info(f"✅ Using fallback requirements without version constraint")
        
        # Final logging
        self.logger.info(f"Step 8: Finalizing results...")
        self.logger.info(f"Final recommendations count: {len(recommendations)}")
        if recommendations:
            top_scores = [f"{rec.image_name} ({rec.score:.3f})" for rec in recommendations[:3]]
            self.logger.info(f"Top 3 recommendations by score: {top_scores}")
        else:
            self.logger.warning(f"⚠️ No recommendations found even with fallback strategies")
            self.logger.info(f"Consider:")
            self.logger.info(f"  - Relaxing security requirements")
            self.logger.info(f"  - Changing size preference")
            self.logger.info(f"  - Using a different base language")
        
        self.logger.info(f"=== Recommendation analysis complete for {image_name} ===")
        
        return analysis_data, recommendations, updated_requirements

    def enable_debug_logging(self):
        """Enable debug level logging to see detailed package analysis"""
        self.logger.setLevel(logging.DEBUG)
        
    def disable_debug_logging(self):
        """Disable debug level logging (back to INFO level)"""
        self.logger.setLevel(logging.INFO)


def main():
    """Demo the recommendation engine"""
    # Configure root logger to see all messages
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    engine = RecommendationEngine()
    
    # Enable debug logging to see detailed package analysis
    engine.enable_debug_logging()
    
    # Example requirements with security constraints
    requirements = UserRequirement(
        language="python",
        version="3.12",
        packages=["pip", "bash"],
        size_preference="balanced",
        security_level="high",
        max_critical_vulnerabilities=0,
        max_high_vulnerabilities=2
    )
    
    print("Finding secure recommendations for Python 3.12 with pip and bash...")
    
    recommendations = engine.recommend(requirements)
    result = engine.format_recommendations(recommendations)
    
    print(result)
    
    # Close database connection
    engine.db.close()


if __name__ == "__main__":
    main()
