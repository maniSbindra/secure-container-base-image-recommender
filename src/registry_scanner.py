"""
Registry Scanner for Azure Linux Base Images

This module scans the Microsoft Container Registry for available
Azure Linux base images and builds a database of their capabilities.
"""

import requests
import json
import time
import subprocess
import logging
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from image_analyzer import ImageAnalyzer
from database import ImageDatabase


class MCRRegistryScanner:
    """Scans Microsoft Container Registry for Azure Linux base images"""
    
    def __init__(self, db_path: str = "azure_linux_images.db", comprehensive_scan: bool = False, cleanup_images: bool = True, update_existing: bool = False, max_tags_per_repo: int = 0):
        self.base_url = "https://mcr.microsoft.com/v2"
        self.registry_prefix = "azurelinux"
        self.session = requests.Session()
        self.db = ImageDatabase(db_path)
        self.comprehensive_scan = comprehensive_scan  # Enable Trivy comprehensive scanning
        self.cleanup_images = cleanup_images  # Enable Docker image cleanup
        self.update_existing = update_existing  # Whether to update existing database entries
        self.max_tags_per_repo = max_tags_per_repo  # Maximum tags to scan per repository (0 = all)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            # Create console handler with formatting
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)
        
        # Common Azure Linux image patterns to scan
        self.image_patterns = [
            # "azurelinux/base/core",
            "azurelinux/base/python",
            "azurelinux/base/nodejs",
            # "mcr.microsoft.com/openjdk/jdk",
            # "mcr.microsoft.com/azurelinux/distroless/base",
            # "mcr.microsoft.com/dotnet/runtime",
            "azurelinux/distroless/base",
            "azurelinux/distroless/python",
            "azurelinux/distroless/node",
            "azurelinux/distroless/java"
        ]
            # "azurelinux/base/php",
            # "azurelinux/base/ruby",
    
    def get_image_tags(self, repository: str) -> List[str]:
        """Get all available tags for a repository"""
        try:
            url = f"{self.base_url}/{repository}/tags/list"
            self.logger.debug(f"Fetching tags from URL: {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                tags = data.get('tags', [])
                self.logger.debug(f"Successfully fetched {len(tags)} tags for {repository}")
                return tags
            else:
                self.logger.error(f"Failed to get tags for {repository}: HTTP {response.status_code}")
                print(f"Failed to get tags for {repository}: {response.status_code}")
                return []
        
        except Exception as e:
            self.logger.error(f"Error fetching tags for {repository}: {e}")
            print(f"Error fetching tags for {repository}: {e}")
            return []
    
    def get_image_manifest(self, repository: str, tag: str) -> Optional[Dict]:
        """Get image manifest for a specific tag"""
        try:
            url = f"{self.base_url}/{repository}/manifests/{tag}"
            headers = {
                'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
            }
            
            self.logger.debug(f"Fetching manifest from URL: {url}")
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                manifest = response.json()
                self.logger.debug(f"Successfully fetched manifest for {repository}:{tag}")
                return manifest
            else:
                self.logger.error(f"Failed to get manifest for {repository}:{tag}: HTTP {response.status_code}")
                print(f"Failed to get manifest for {repository}:{tag}: {response.status_code}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error fetching manifest for {repository}:{tag}: {e}")
            print(f"Error fetching manifest for {repository}:{tag}: {e}")
            return None
    
    def scan_image(self, image_name: str) -> List[Dict]:
        """Scan a specific image by full image name (e.g., 'python:3.12', 'mcr.microsoft.com/azurelinux/base/python:3.12')"""
        self.logger.info(f"=== Starting scan for image: {image_name} ===")
        print(f"Scanning image: {image_name}")
        
        # Parse the image name to extract repository and tag
        try:
            # Use the image name as provided (don't force MCR registry)
            full_image_name = image_name
            
            # Extract tag from image name
            if ':' in image_name:
                image_without_tag, tag = image_name.rsplit(':', 1)
            else:
                # Default to 'latest' if no tag specified
                image_without_tag = image_name
                tag = 'latest'
                full_image_name = f"{image_name}:latest"
            
            self.logger.info(f"Parsed image: {full_image_name}, tag: {tag}")
            
            # Note: Manifest fetching is only supported for MCR images via scan_repository()
            # For generic image scanning, we skip manifest data and rely on image analysis tools
                
        except Exception as e:
            self.logger.error(f"Error parsing image name '{image_name}': {e}")
            print(f"  ❌ Error parsing image name '{image_name}': {e}")
            return []
        
        # Check if image already exists in database
        full_image_name = full_image_name
        
        if not self.update_existing and self.db.image_exists(full_image_name):
            scan_info = self.db.get_image_scan_info(full_image_name)
            self.logger.info(f"Image {full_image_name} already exists in database, skipping")
            print(f"  ⏭️  Skipping - already in database (scanned: {scan_info.get('scan_timestamp', 'unknown')})")
            print(f"      Use --update-existing to rescan existing images")
            return []
        
        try:
            # Skip manifest fetching for generic image scanning
            # Manifest data is only available via scan_repository() for MCR images
            manifest = None
            self.logger.debug(f"Generic image scan - skipping manifest fetch for {full_image_name}")
            print(f"  ℹ️  Generic image scan - skipping manifest fetch (use scan_repository for MCR manifest data)")
            
            # Step 1: Image Analysis
            self.logger.info(f"Step 1: Starting image analysis for {full_image_name}")
            try:
                analyzer = ImageAnalyzer(full_image_name)
                analysis = analyzer.analyze()
                self.logger.info(f"Image analysis completed successfully")
                self.logger.debug(f"Found {len(analysis.get('languages', []))} languages, {len(analysis.get('package_managers', []))} package managers")
            except Exception as e:
                self.logger.warning(f"Image analysis failed: {e}")
                print(f"  ⚠️  Analysis failed: {e}")
                # Create minimal analysis with just image name
                analysis = {
                    'image': full_image_name,
                    'languages': [],
                    'capabilities': [],
                    'package_managers': [],
                    'analysis_timestamp': datetime.now().isoformat()
                }
            
            # Step 2: Manifest Data Collection
            self.logger.info(f"Step 2: Getting accurate image manifest data for {full_image_name}")
            print(f"  📊 Getting accurate image manifest data...")
            accurate_manifest_data = self.get_docker_manifest_data(full_image_name)
            if accurate_manifest_data:
                analysis['manifest'] = accurate_manifest_data
                self.logger.info(f"Accurate manifest data obtained: size={accurate_manifest_data['size']} bytes, layers={accurate_manifest_data['layers']}")
                print(f"  🔍 Accurate manifest data created: size={accurate_manifest_data['size']}, layers={accurate_manifest_data['layers']}")
            else:
                # If docker-based manifest data failed, try to get size from docker images directly
                self.logger.warning(f"Docker manifest data extraction failed, attempting direct docker images size lookup")
                print(f"  ⚠️  Docker manifest extraction failed, trying direct size lookup...")
                
                try:
                    # Try to get size directly from docker images (without full manifest processing)
                    fallback_size = 0
                    
                    # Try different image name variations to handle Docker Hub naming
                    image_name_variations = [full_image_name]
                    
                    # For Docker Hub images, also try the short name without registry prefix
                    if full_image_name.startswith('docker.io/library/'):
                        short_name = full_image_name.replace('docker.io/library/', '')
                        image_name_variations.append(short_name)
                    elif full_image_name.startswith('docker.io/'):
                        short_name = full_image_name.replace('docker.io/', '')
                        image_name_variations.append(short_name)
                    
                    for variant in image_name_variations:
                        images_result = subprocess.run([
                            'docker', 'images', variant, '--format', '{{.Size}}'
                        ], capture_output=True, text=True, timeout=30)
                        
                        if images_result.returncode == 0 and images_result.stdout.strip():
                            size_str = images_result.stdout.strip()
                            self.logger.info(f"Direct docker images lookup successful: '{size_str}' (using name: {variant})")
                            try:
                                # Convert human-readable size to bytes
                                if size_str.endswith('MB'):
                                    fallback_size = int(float(size_str[:-2]) * 1024 * 1024)
                                elif size_str.endswith('GB'):
                                    fallback_size = int(float(size_str[:-2]) * 1024 * 1024 * 1024)
                                elif size_str.endswith('KB'):
                                    fallback_size = int(float(size_str[:-2]) * 1024)
                                elif size_str.endswith('B'):
                                    fallback_size = int(size_str[:-1])
                                else:
                                    fallback_size = int(float(size_str))
                                
                                self.logger.info(f"Successfully parsed direct size: {fallback_size} bytes ({fallback_size / (1024*1024):.1f} MB)")
                                print(f"  ✅ Direct size lookup: {fallback_size / (1024*1024):.1f} MB from docker images (using name: {variant})")
                                break  # Success, stop trying other variations
                            except (ValueError, IndexError) as e:
                                self.logger.warning(f"Could not parse direct size '{size_str}' from {variant}: {e}")
                                print(f"  ⚠️  Could not parse size '{size_str}' from {variant}")
                                continue  # Try next variation
                    
                    if fallback_size == 0:
                        # No fallback - set size to 0
                        self.logger.warning(f"Docker images command failed for all variations of {full_image_name}, setting size to 0")
                        print(f"  ⚠️  Docker images failed for all name variations, setting size to 0")
                    
                    if fallback_size > 0:
                        # Create minimal manifest data with direct size
                        manifest_data = {
                            'size': fallback_size,
                            'layers': len(manifest.get('layers', [])) if manifest else 0,
                            'created': manifest.get('history', [{}])[0].get('created', '') if manifest else ''
                        }
                        analysis['manifest'] = manifest_data
                        print(f"  🔍 Fallback manifest created: size={manifest_data['size'] / (1024*1024):.1f} MB, layers={manifest_data['layers']}")
                    else:
                        # Set size to 0 if all docker images methods failed
                        manifest_data = {
                            'size': 0,
                            'layers': len(manifest.get('layers', [])) if manifest else 0,
                            'created': manifest.get('history', [{}])[0].get('created', '') if manifest else ''
                        }
                        analysis['manifest'] = manifest_data
                        self.logger.warning(f"No docker images size available for {full_image_name}, setting to 0")
                        print(f"  ⚠️  No docker images size available, setting to 0")
                        
                except Exception as e:
                    self.logger.error(f"Direct size lookup failed: {e}")
                    print(f"  ❌ Direct size lookup failed: {e}")
                    # No fallback - set size to 0
                    manifest_data = {
                        'size': 0,
                        'layers': len(manifest.get('layers', [])) if manifest else 0,
                        'created': manifest.get('history', [{}])[0].get('created', '') if manifest else ''
                    }
                    analysis['manifest'] = manifest_data
                    self.logger.warning(f"All size calculation failed for {full_image_name}, setting to 0")
                    print(f"  ⚠️  All size calculation failed, setting to 0")
            
            # Data validation
            existing_manifest = analysis.get('manifest', {})
            if existing_manifest:
                layers_val = existing_manifest.get('layers')
                if isinstance(layers_val, list):
                    self.logger.warning(f"Found layers as list instead of count: {layers_val}")
                    print(f"  ⚠️  WARNING: Existing analysis has layers as list: {layers_val}")
                    existing_manifest['layers'] = len(layers_val)  # Fix it
                    print(f"  ✅ Fixed layers to: {existing_manifest['layers']}")
            
            # Debug: Check all data types in analysis before database insertion
            manifest_check = analysis.get('manifest', {})
            if manifest_check:
                for key, value in manifest_check.items():
                    if isinstance(value, list):
                        self.logger.warning(f"manifest['{key}'] is unexpectedly a list: {value}")
                        print(f"  🐛 WARNING: manifest['{key}'] is a list: {value}")
            
            # Step 3: Vulnerability Scanning
            self.logger.info(f"Step 3: Starting vulnerability scan for {full_image_name}")
            try:
                vulnerability_data = self.scan_vulnerabilities(full_image_name, self.comprehensive_scan)
                analysis.update(vulnerability_data)
                total_vulns = vulnerability_data.get('vulnerabilities', {}).get('total', 0)
                self.logger.info(f"Vulnerability scan completed: {total_vulns} vulnerabilities found")
            except Exception as e:
                self.logger.error(f"Vulnerability scan failed: {e}")
                print(f"  ⚠️  Vulnerability scan failed: {e}")
                # Add default vulnerability data
                analysis.update(self.get_default_vulnerability_data())
            
            # Step 4: Database Storage
            self.logger.info(f"Step 4: Saving analysis to database")
            try:
                force_update = getattr(self, 'update_existing', False)
                image_id = self.db.insert_image_analysis(analysis, force_update=force_update)
                analysis['database_id'] = image_id
                self.logger.info(f"Successfully saved to database with ID: {image_id}")
                print(f"  ✅ Saved to database with ID: {image_id}")
            except Exception as e:
                self.logger.error(f"Database save failed: {e}")
                print(f"  ❌ Database error: {e}")
                return []
            
            # Step 5: Cleanup
            if self.cleanup_images:
                self.logger.info(f"Step 5: Cleaning up Docker image {full_image_name}")
                self.cleanup_docker_images([full_image_name])
            else:
                self.logger.info(f"Step 5: Skipping cleanup (disabled)")
            
            self.logger.info(f"=== Successfully completed scan for {full_image_name} ===")
            print(f"  ✅ Successfully analyzed {full_image_name}")
            return [analysis]
            
        except Exception as e:
            self.logger.error(f"Critical error during scan of {full_image_name}: {e}")
            print(f"  ❌ Error analyzing {full_image_name}: {e}")
            return []

    def scan_repository(self, repository: str) -> List[Dict]:
        """Scan a repository and analyze all its tags"""
        self.logger.info(f"=== Starting repository scan: {repository} ===")
        print(f"Scanning repository: {repository}")
        
        # Normalize repository path (handle both full MCR URLs and repository paths)
        normalized_repo = self._normalize_repository_path(repository)
        if normalized_repo != repository:
            self.logger.info(f"Normalized repository path: {repository} -> {normalized_repo}")
            print(f"  📋 Normalized repository path: {normalized_repo}")
        
        # Step 1: Get available tags
        self.logger.info(f"Step 1: Fetching tags for repository {normalized_repo}")
        tags = self.get_image_tags(normalized_repo)
        if not tags:
            self.logger.warning(f"No tags found for repository {normalized_repo}")
            return []
        
        self.logger.info(f"Found {len(tags)} total tags for {normalized_repo}")
        
        # Step 2: Filter tags
        self.logger.info(f"Step 2: Filtering tags")
        filtered_tags = self.filter_tags(tags)
        self.logger.info(f"After filtering: {len(filtered_tags)} tags remaining")
        
        if self.max_tags_per_repo > 0 and len(filtered_tags) > self.max_tags_per_repo:
            self.logger.info(f"Limiting to {self.max_tags_per_repo} most recent tags (from {len(filtered_tags)})")
            print(f"  Found {len(filtered_tags)} tags, limiting to {self.max_tags_per_repo} most recent")
            filtered_tags = filtered_tags[:self.max_tags_per_repo]
        else:
            print(f"  Found {len(filtered_tags)} tags to scan")
        
        results = []
        processed_images = []  # Track images for cleanup
        skipped_count = 0  # Track skipped images
        
        # Step 3: Process each tag
        self.logger.info(f"Step 3: Processing {len(filtered_tags)} tags")
        for i, tag in enumerate(filtered_tags, 1):
            self.logger.info(f"Processing tag {i}/{len(filtered_tags)}: {normalized_repo}:{tag}")
            print(f"  Analyzing {normalized_repo}:{tag}")
            
            # Check if image already exists in database
            full_image_name = f"mcr.microsoft.com/{normalized_repo}:{tag}"
            
            if not self.update_existing and self.db.image_exists(full_image_name):
                scan_info = self.db.get_image_scan_info(full_image_name)
                self.logger.info(f"Skipping {full_image_name} - already in database")
                print(f"    ⏭️  Skipping - already in database (scanned: {scan_info.get('scan_timestamp', 'unknown')})")
                print(f"        Use --update-existing to rescan existing images")
                skipped_count += 1
                continue
            
            try:
                # Get manifest info
                self.logger.debug(f"Fetching manifest for {normalized_repo}:{tag}")
                manifest = self.get_image_manifest(normalized_repo, tag)
                
                # Track image for cleanup
                processed_images.append(full_image_name)
                
                # Image analysis
                self.logger.info(f"Starting image analysis for {full_image_name}")
                try:
                    analyzer = ImageAnalyzer(full_image_name)
                    analysis = analyzer.analyze()
                    self.logger.debug(f"Image analysis completed for {full_image_name}")
                except Exception as e:
                    self.logger.warning(f"Image analysis failed for {full_image_name}: {e}")
                    print(f"    ⚠️  Analysis failed: {e}")
                    # Create minimal analysis with just image name
                    analysis = {
                        'image': full_image_name,
                        'languages': [],
                        'capabilities': [],
                        'package_managers': [],
                        'analysis_timestamp': datetime.now().isoformat()
                    }
                
                # Manifest data collection
                self.logger.info(f"Getting accurate manifest data for {full_image_name}")
                print(f"    📊 Getting accurate image manifest data...")
                accurate_manifest_data = self.get_docker_manifest_data(full_image_name)
                if accurate_manifest_data:
                    analysis['manifest'] = accurate_manifest_data
                    self.logger.info(f"Manifest data: size={accurate_manifest_data['size']} bytes, layers={accurate_manifest_data['layers']}, digest={accurate_manifest_data.get('digest', 'none')[:12]}...")
                    print(f"    🔍 Accurate manifest data created: size={accurate_manifest_data['size']}, layers={accurate_manifest_data['layers']}")
                else:
                    # If docker-based manifest data failed, try to get size from docker images directly
                    self.logger.warning(f"Docker manifest data extraction failed for {full_image_name}, attempting direct docker images size lookup")
                    print(f"    ⚠️  Docker manifest extraction failed, trying direct size lookup...")
                    
                    try:
                        # Try to get size directly from docker images (without full manifest processing)
                        fallback_size = 0
                        
                        # Try different image name variations to handle Docker Hub naming
                        image_name_variations = [full_image_name]
                        
                        # For Docker Hub images, also try the short name without registry prefix
                        if full_image_name.startswith('docker.io/library/'):
                            short_name = full_image_name.replace('docker.io/library/', '')
                            image_name_variations.append(short_name)
                        elif full_image_name.startswith('docker.io/'):
                            short_name = full_image_name.replace('docker.io/', '')
                            image_name_variations.append(short_name)
                        
                        for variant in image_name_variations:
                            images_result = subprocess.run([
                                'docker', 'images', variant, '--format', '{{.Size}}'
                            ], capture_output=True, text=True, timeout=30)
                            
                            if images_result.returncode == 0 and images_result.stdout.strip():
                                size_str = images_result.stdout.strip()
                                self.logger.info(f"Direct docker images lookup successful for {variant}: '{size_str}'")
                                try:
                                    # Convert human-readable size to bytes
                                    if size_str.endswith('MB'):
                                        fallback_size = int(float(size_str[:-2]) * 1024 * 1024)
                                    elif size_str.endswith('GB'):
                                        fallback_size = int(float(size_str[:-2]) * 1024 * 1024 * 1024)
                                    elif size_str.endswith('KB'):
                                        fallback_size = int(float(size_str[:-2]) * 1024)
                                    elif size_str.endswith('B'):
                                        fallback_size = int(size_str[:-1])
                                    else:
                                        fallback_size = int(float(size_str))
                                    
                                    self.logger.info(f"Successfully parsed direct size for {variant}: {fallback_size} bytes ({fallback_size / (1024*1024):.1f} MB)")
                                    print(f"    ✅ Direct size lookup: {fallback_size / (1024*1024):.1f} MB from docker images (using name: {variant})")
                                    break  # Success, stop trying other variations
                                except (ValueError, IndexError) as e:
                                    self.logger.warning(f"Could not parse direct size '{size_str}' for {variant}: {e}")
                                    print(f"    ⚠️  Could not parse size '{size_str}' from {variant}")
                                    continue  # Try next variation
                        
                        if fallback_size == 0:
                            # No fallback - set size to 0
                            self.logger.warning(f"Docker images command failed for all variations of {full_image_name}, setting size to 0")
                            fallback_size = 0
                            print(f"    ⚠️  Docker images failed for all name variations, setting size to 0")
                        
                        if fallback_size > 0:
                            # Create minimal manifest data with direct size
                            manifest_data = {
                                'size': fallback_size,
                                'layers': len(manifest.get('layers', [])) if manifest else 0,
                                'created': manifest.get('history', [{}])[0].get('created', '') if manifest else ''
                            }
                            analysis['manifest'] = manifest_data
                            print(f"    🔍 Fallback manifest created: size={manifest_data['size'] / (1024*1024):.1f} MB, layers={manifest_data['layers']}")
                        else:
                            # Set size to 0 if all docker images methods failed
                            manifest_data = {
                                'size': 0,
                                'layers': len(manifest.get('layers', [])) if manifest else 0,
                                'created': manifest.get('history', [{}])[0].get('created', '') if manifest else ''
                            }
                            analysis['manifest'] = manifest_data
                            self.logger.warning(f"No docker images size available for {full_image_name}, setting to 0")
                            print(f"    ⚠️  No docker images size available, setting to 0")
                            
                    except Exception as e:
                        self.logger.error(f"Direct size lookup failed for {full_image_name}: {e}")
                        print(f"    ❌ Direct size lookup failed: {e}")
                        # No fallback - set size to 0
                        manifest_data = {
                            'size': 0,
                            'layers': len(manifest.get('layers', [])) if manifest else 0,
                            'created': manifest.get('history', [{}])[0].get('created', '') if manifest else ''
                        }
                        analysis['manifest'] = manifest_data
                        self.logger.warning(f"All size calculation failed for {full_image_name}, setting to 0")
                        print(f"    ⚠️  All size calculation failed, setting to 0")
                
                # Data validation
                existing_manifest = analysis.get('manifest', {})
                if existing_manifest:
                    layers_val = existing_manifest.get('layers')
                    if isinstance(layers_val, list):
                        self.logger.warning(f"Fixed layers field from list to count for {full_image_name}")
                        print(f"    ⚠️  WARNING: Existing analysis has layers as list: {layers_val}")
                        existing_manifest['layers'] = len(layers_val)  # Fix it
                        print(f"    ✅ Fixed layers to: {existing_manifest['layers']}")
                
                # Debug: Check all data types in analysis before database insertion
                manifest_check = analysis.get('manifest', {})
                if manifest_check:
                    for key, value in manifest_check.items():
                        if isinstance(value, list):
                            self.logger.warning(f"manifest['{key}'] is unexpectedly a list for {full_image_name}: {value}")
                            print(f"    🐛 WARNING: manifest['{key}'] is a list: {value}")
                
                # Vulnerability scanning
                self.logger.info(f"Starting vulnerability scan for {full_image_name}")
                try:
                    vulnerability_data = self.scan_vulnerabilities(full_image_name, self.comprehensive_scan)
                    analysis.update(vulnerability_data)
                    total_vulns = vulnerability_data.get('vulnerabilities', {}).get('total', 0)
                    self.logger.info(f"Vulnerability scan completed for {full_image_name}: {total_vulns} vulnerabilities")
                except Exception as e:
                    self.logger.error(f"Vulnerability scan failed for {full_image_name}: {e}")
                    print(f"    ⚠️  Vulnerability scan failed: {e}")
                    # Add default vulnerability data
                    analysis.update(self.get_default_vulnerability_data())
                
                # Database storage
                self.logger.info(f"Saving {full_image_name} to database")
                try:
                    force_update = getattr(self, 'update_existing', False)
                    image_id = self.db.insert_image_analysis(analysis, force_update=force_update)
                    analysis['database_id'] = image_id
                    self.logger.info(f"Successfully saved {full_image_name} with database ID: {image_id}")
                    print(f"    ✅ Saved to database with ID: {image_id}")
                except Exception as e:
                    self.logger.error(f"Database save failed for {full_image_name}: {e}")
                    print(f"    ❌ Database error: {e}")
                    continue  # Skip this image if database save fails
                
                results.append(analysis)
                
                # Rate limiting
                self.logger.debug(f"Rate limiting: sleeping for 2 seconds")
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Critical error analyzing {normalized_repo}:{tag}: {e}")
                print(f"    Error analyzing {normalized_repo}:{tag}: {e}")
                continue
        
        # Cleanup
        if processed_images and self.cleanup_images:
            self.logger.info(f"Cleaning up {len(processed_images)} Docker images")
            self.cleanup_docker_images(processed_images)
        else:
            self.logger.info(f"Skipping cleanup for {len(processed_images)} images")
        
        # Summary
        total_processed = len(results)
        self.logger.info(f"Repository scan completed: {total_processed} analyzed, {skipped_count} skipped")
        if skipped_count > 0:
            print(f"  📊 Repository summary: {len(results)} analyzed, {skipped_count} skipped")
        
        self.logger.info(f"=== Completed repository scan: {normalized_repo} ===")
        return results
    
    def filter_tags(self, tags: List[str]) -> List[str]:
        """Filter tags to keep only meaningful versions"""
        filtered = []
        
        # Skip common non-version tags
        skip_tags = {'latest', 'dev', 'nightly', 'edge', 'rc', 'beta', 'alpha'}
        
        for tag in tags:
            # Skip if it's in skip list
            if tag.lower() in skip_tags:
                continue
            
            # Skip if it contains unwanted keywords
            if any(keyword in tag.lower() for keyword in ['debug', 'test', 'experimental', 'arm', 'amd', 'azl']):
                continue
            
            # Keep version-like tags
            if any(char.isdigit() for char in tag):
                filtered.append(tag)
        
        # Sort by version (simple string sort for now)
        return sorted(filtered, reverse=True)
    
    def calculate_image_size(self, manifest: Dict) -> int:
        """Calculate total image size from manifest (DEPRECATED - NO LONGER USED)
        
        This method is deprecated and should not be used. Size calculation now only
        uses 'docker images' command. This method is kept for reference only.
        """
        self.logger.warning("calculate_image_size() called - this method is deprecated and should not be used")
        return 0

    def get_docker_manifest_data(self, image_name: str) -> Optional[Dict]:
        """Get Docker image manifest data with simplified size calculation
        
        Uses only docker images command for size. If that fails, size is set to 0.
        No fallbacks to docker inspect or registry manifest for size calculation.
        """
        try:
            # First, ensure the image is pulled
            self.logger.info(f"Pulling Docker image: {image_name}")
            print(f"    🐳 Pulling image {image_name}...")
            
            start_time = time.time()
            pull_result = subprocess.run([
                'docker', 'pull', image_name
            ], capture_output=True, text=True, timeout=300)
            pull_duration = time.time() - start_time
            
            if pull_result.returncode != 0:
                self.logger.error(f"Failed to pull image {image_name} after {pull_duration:.1f}s: {pull_result.stderr}")
                print(f"    ⚠️  Failed to pull image: {pull_result.stderr}")
                return None
            
            self.logger.info(f"Successfully pulled image {image_name} in {pull_duration:.1f}s")
            
            # Get image inspect data for layers and metadata only
            self.logger.debug(f"Running docker inspect on {image_name}")
            inspect_result = subprocess.run([
                'docker', 'inspect', image_name
            ], capture_output=True, text=True, timeout=30)
            
            if inspect_result.returncode != 0:
                self.logger.error(f"Failed to inspect image {image_name}: {inspect_result.stderr}")
                print(f"    ⚠️  Failed to inspect image: {inspect_result.stderr}")
                return None
            
            inspect_data = json.loads(inspect_result.stdout)[0]
            self.logger.debug(f"Successfully parsed docker inspect data for {image_name}")
            
            # Get size ONLY from docker images command - simplified approach
            self.logger.info(f"Getting size using 'docker images' for {image_name}")
            print(f"    📏 Getting size using 'docker images' command...")
            
            image_size = 0
            
            # Try different image name variations to handle Docker Hub naming
            image_name_variations = [image_name]
            
            # For Docker Hub images, also try the short name without registry prefix
            if image_name.startswith('docker.io/library/'):
                short_name = image_name.replace('docker.io/library/', '')
                image_name_variations.append(short_name)
            elif image_name.startswith('docker.io/'):
                short_name = image_name.replace('docker.io/', '')
                image_name_variations.append(short_name)
            
            for variant in image_name_variations:
                self.logger.debug(f"Trying docker images with variant: {variant}")
                images_result = subprocess.run([
                    'docker', 'images', variant, '--format', '{{.Size}}'
                ], capture_output=True, text=True, timeout=30)
                
                if images_result.returncode == 0 and images_result.stdout.strip():
                    size_str = images_result.stdout.strip()
                    self.logger.info(f"Docker images reported size: '{size_str}' for {variant}")
                    print(f"    ✅ Docker images output: '{size_str}' (using name: {variant})")
                    
                    try:
                        # Convert human-readable size to bytes
                        if size_str.endswith('MB'):
                            image_size = int(float(size_str[:-2]) * 1024 * 1024)
                        elif size_str.endswith('GB'):
                            image_size = int(float(size_str[:-2]) * 1024 * 1024 * 1024)
                        elif size_str.endswith('KB'):
                            image_size = int(float(size_str[:-2]) * 1024)
                        elif size_str.endswith('B'):
                            image_size = int(size_str[:-1])
                        else:
                            # Try to parse as a number (bytes)
                            image_size = int(float(size_str))
                        
                        self.logger.info(f"Successfully parsed size: {image_size} bytes ({image_size / (1024*1024):.1f} MB) for {variant}")
                        print(f"    📏 Parsed size: {image_size / (1024*1024):.1f} MB")
                        break  # Success, stop trying other variations
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Could not parse size '{size_str}' for {variant}: {e}")
                        print(f"    ⚠️  Could not parse size '{size_str}' from {variant}")
                        continue  # Try next variation
                else:
                    self.logger.debug(f"Docker images command failed for variant {variant}")
            
            # Final result
            if image_size == 0:
                self.logger.warning(f"Docker images command failed for all variations of {image_name}, setting size to 0")
                print(f"    ⚠️  Docker images command failed for all name variations, setting size to 0")
                image_size = 0
            
            # Extract other manifest data
            layers_count = len(inspect_data.get('RootFS', {}).get('Layers', []))
            created_time = inspect_data.get('Created', '')
            digest = inspect_data.get('Id', '')
            
            manifest_data = {
                'size': image_size,  # Use docker images size or 0
                'layers': layers_count,
                'created': created_time,
                'digest': digest
            }
            
            # Log final results
            self.logger.info(f"Manifest data for {image_name}: size={image_size} bytes, layers={layers_count}")
            
            if image_size > 0:
                print(f"    � Size: {image_size / (1024*1024):.1f} MB, Layers: {layers_count}")
            else:
                print(f"    📊 Size: Unknown (0 bytes), Layers: {layers_count}")
            
            return manifest_data
            
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Docker operation timed out for {image_name}: {e}")
            print("    ⚠️  Docker operation timed out")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Docker inspect JSON for {image_name}: {e}")
            print(f"    ⚠️  Failed to parse Docker inspect output")
            return None
        except Exception as e:
            self.logger.error(f"Error getting manifest data for {image_name}: {e}")
            print(f"    ⚠️  Error getting manifest data: {e}")
            return None
    
    def scan_all_repositories(self, max_workers: int = 1) -> List[Dict]:
        """Scan all configured repositories sequentially to avoid SQLite threading issues"""
        self.logger.info(f"=== Starting scan of all repositories ===")
        self.logger.info(f"Configuration:")
        self.logger.info(f"  Repositories to scan: {len(self.image_patterns)}")
        self.logger.info(f"  Comprehensive scan: {self.comprehensive_scan}")
        self.logger.info(f"  Cleanup images: {self.cleanup_images}")
        self.logger.info(f"  Update existing: {self.update_existing}")
        self.logger.info(f"  Max tags per repo: {self.max_tags_per_repo}")
        
        all_results = []
        
        print(f"🔍 Scanning {len(self.image_patterns)} repositories sequentially...")
        
        for i, repo in enumerate(self.image_patterns, 1):
            self.logger.info(f"Processing repository {i}/{len(self.image_patterns)}: {repo}")
            print(f"\n📦 [{i}/{len(self.image_patterns)}] Processing repository: {repo}")
            try:
                start_time = datetime.now()
                results = self.scan_repository(repo)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                all_results.extend(results)
                self.logger.info(f"Completed {repo}: {len(results)} images analyzed in {duration:.1f}s")
                print(f"    ✅ Completed {repo}: {len(results)} images analyzed")
            except Exception as e:
                self.logger.error(f"Error scanning repository {repo}: {e}")
                print(f"    ❌ Error scanning repository {repo}: {e}")
        
        total_images = len(all_results)
        self.logger.info(f"=== Completed scan of all repositories ===")
        self.logger.info(f"Total images processed: {total_images}")
        
        # Log summary by repository
        repo_summary = {}
        for result in all_results:
            image_name = result.get('image', '')
            if 'mcr.microsoft.com/' in image_name:
                repo_part = image_name.split('mcr.microsoft.com/')[-1].split(':')[0]
                repo_summary[repo_part] = repo_summary.get(repo_part, 0) + 1
        
        self.logger.info(f"Images by repository:")
        for repo, count in sorted(repo_summary.items()):
            self.logger.info(f"  {repo}: {count} images")
        
        return all_results
    
    
    def save_database(self, results: List[Dict], filename: str = "azure_linux_images.json"):
        """Save scan results to a JSON database file (legacy support)"""
        database = {
            'scan_timestamp': datetime.now().isoformat(),
            'total_images': len(results),
            'images': results
        }
        
        with open(filename, 'w') as f:
            json.dump(database, f, indent=2)
        
        print(f"Legacy JSON database saved to {filename}")
        return database
    
    def cleanup_docker_images(self, image_names: List[str]) -> None:
        """Remove Docker images to free up disk space"""
        if not image_names:
            return
            
        self.logger.info(f"Starting cleanup of {len(image_names)} Docker images")
        print(f"🧹 Cleaning up {len(image_names)} Docker images to free disk space...")
        
        success_count = 0
        error_count = 0
        
        for image_name in image_names:
            try:
                # Remove the image
                result = subprocess.run([
                    'docker', 'rmi', '-f', image_name
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    success_count += 1
                    self.logger.debug(f"Successfully removed Docker image: {image_name}")
                    print(f"    ✅ Removed: {image_name}")
                else:
                    # Image might not exist locally, which is fine
                    if "No such image" not in result.stderr:
                        error_count += 1
                        self.logger.warning(f"Could not remove {image_name}: {result.stderr.strip()}")
                        print(f"    ⚠️  Could not remove {image_name}: {result.stderr.strip()}")
                    else:
                        self.logger.debug(f"Image {image_name} not found locally (already removed)")
                        
            except subprocess.TimeoutExpired:
                error_count += 1
                self.logger.warning(f"Timeout removing {image_name}")
                print(f"    ⚠️  Timeout removing {image_name}")
            except Exception as e:
                error_count += 1
                self.logger.error(f"Error removing {image_name}: {e}")
                print(f"    ⚠️  Error removing {image_name}: {e}")
        
        self.logger.info(f"Image cleanup completed: {success_count} removed, {error_count} errors")
        
        # Also run docker system prune to clean up dangling images and build cache
        try:
            self.logger.info("Running docker system prune to clean up dangling resources")
            print("🧹 Running docker system prune to clean up dangling resources...")
            result = subprocess.run([
                'docker', 'system', 'prune', '-f'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info("Docker system cleanup completed successfully")
                print("    ✅ Docker system cleanup completed")
            else:
                self.logger.error(f"Docker system prune failed: {result.stderr.strip()}")
                print(f"    ⚠️  Docker system prune failed: {result.stderr.strip()}")
                
        except Exception as e:
            self.logger.error(f"Error during docker system prune: {e}")
            print(f"    ⚠️  Error during docker system prune: {e}")

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        stats = self.db.get_vulnerability_statistics()
        language_stats = self.db.get_languages_summary()
        
        return {
            'database_stats': stats,
            'language_summary': language_stats
        }
    
    def scan_vulnerabilities(self, image_name: str, comprehensive: bool = False) -> Dict:
        """
        Scan image for vulnerabilities using Trivy only.
        - Always runs Trivy for vulnerability detection
        - If comprehensive=True, includes additional security checks (secrets, misconfigurations)
        """
        self.logger.info(f"Starting vulnerability scanning for {image_name}")
        result = {}
        
        # Always run Trivy for vulnerability scanning
        self.logger.debug(f"Running Trivy scan for {image_name}")
        trivy_data = self.scan_with_trivy(image_name, comprehensive)
        result.update(trivy_data)
        
        self.logger.info(f"Vulnerability scanning completed for {image_name}")
        return result
    
    def scan_with_trivy(self, image_name: str, comprehensive: bool = False) -> Dict:
        """Vulnerability and security scanning with Trivy"""
        try:
            if comprehensive:
                self.logger.info(f"Running comprehensive Trivy scan for {image_name}")
                print(f"    Running comprehensive security scan with Trivy for {image_name}")
                
                # Run Trivy comprehensive scan (vulnerabilities + secrets + misconfigurations)
                result = subprocess.run([
                    'trivy', 'image', '--format', 'json', 
                    '--security-checks', 'vuln,secret,config',
                    image_name
                ], capture_output=True, text=True, timeout=300)
            else:
                self.logger.info(f"Running Trivy vulnerability scan for {image_name}")
                print(f"    Scanning vulnerabilities with Trivy for {image_name}")
                
                # Run Trivy vulnerability scan only
                result = subprocess.run([
                    'trivy', 'image', '--format', 'json', 
                    '--security-checks', 'vuln',
                    image_name
                ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                trivy_result = self.parse_trivy_output(result.stdout, comprehensive)
                total_vulns = trivy_result.get('vulnerabilities', {}).get('total', 0)
                self.logger.info(f"Trivy scan completed for {image_name}: {total_vulns} vulnerabilities found")
                if comprehensive:
                    self.logger.info(f"Comprehensive findings: "
                                   f"{trivy_result.get('comprehensive_security', {}).get('secrets_found', 0)} secrets, "
                                   f"{trivy_result.get('comprehensive_security', {}).get('config_issues', 0)} config issues")
                return trivy_result
            else:
                self.logger.error(f"Trivy scan failed for {image_name}: {result.stderr}")
                print(f"    Trivy scan failed: {result.stderr}")
                return self.get_default_trivy_data()
        
        except FileNotFoundError:
            self.logger.warning(f"Trivy not found, skipping vulnerability scan for {image_name}")
            print("    Warning: Trivy not found, skipping vulnerability scan")
            return self.get_default_trivy_data()
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Trivy scan timed out for {image_name}")
            print("    Warning: Trivy scan timed out")
            return self.get_default_trivy_data()
        except Exception as e:
            self.logger.error(f"Error during Trivy scan for {image_name}: {e}")
            print(f"    Error during Trivy scan: {e}")
            return self.get_default_trivy_data()
    
    def extract_cvss_score_trivy(self, vulnerability: Dict) -> Optional[float]:
        """Extract CVSS score from Trivy vulnerability data"""
        try:
            # Try different possible locations for CVSS score in Trivy format
            cvss_locations = [
                ['CVSS', 'Score'],
                ['CVSS', 'BaseScore'],
                ['CvssScore'],
                ['Score']
            ]
            
            for location in cvss_locations:
                try:
                    value = vulnerability
                    for key in location:
                        if isinstance(value, dict):
                            value = value.get(key, {})
                        else:
                            break
                    
                    if isinstance(value, (int, float)):
                        return float(value)
                except:
                    continue
            
            return None
        except:
            return None
    
    def extract_cvss_score(self, vulnerability: Dict) -> Optional[float]:
        """Extract CVSS score from vulnerability data"""
        
        # Try different possible locations for CVSS score
        cvss_locations = [
            ['cvss', 'score'],
            ['cvss', 'baseScore'],
            ['cvssScore'],
            ['score']
        ]
        
        for location in cvss_locations:
            try:
                value = vulnerability
                for key in location:
                    value = value.get(key, {})
                
                if isinstance(value, (int, float)):
                    return float(value)
            except:
                continue
        
        return None
    
    def parse_trivy_output(self, trivy_json: str, comprehensive: bool = False) -> Dict:
        """Parse Trivy JSON output for vulnerability and security analysis"""
        try:
            data = json.loads(trivy_json)
            results = data.get('Results', [])
            
            # Initialize vulnerability counts
            vulnerability_counts = {
                'total': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'negligible': 0,
                'unknown': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'scanner': 'trivy'
            }
            
            vulnerability_details = []
            
            # Initialize comprehensive security analysis
            security_analysis = {
                'secrets_found': 0,
                'config_issues': 0,
                'license_issues': 0,
                'secret_details': [],
                'config_details': [],
                'license_details': [],
                'scan_timestamp': datetime.now().isoformat(),
                'scanner': 'trivy'
            }
            
            for result in results:
                # Process vulnerabilities
                vulnerabilities = result.get('Vulnerabilities', [])
                for vuln in vulnerabilities:
                    severity = vuln.get('Severity', 'unknown').lower()
                    
                    # Count by severity
                    if severity in vulnerability_counts:
                        vulnerability_counts[severity] += 1
                    else:
                        vulnerability_counts['unknown'] += 1
                    
                    vulnerability_counts['total'] += 1
                    
                    # Store detailed vulnerability info (limit to 100 for storage)
                    if len(vulnerability_details) < 100:
                        vuln_detail = {
                            'id': vuln.get('VulnerabilityID'),
                            'severity': severity,
                            'package_name': vuln.get('PkgName'),
                            'package_version': vuln.get('InstalledVersion'),
                            'fixed_version': vuln.get('FixedVersion'),
                            'description': vuln.get('Description', ''),
                            'cvss_score': self.extract_cvss_score_trivy(vuln)
                        }
                        vulnerability_details.append(vuln_detail)
                
                # Process comprehensive security data only if requested
                if comprehensive:
                    # Process secrets
                    secrets = result.get('Secrets', [])
                    security_analysis['secrets_found'] += len(secrets)
                    for secret in secrets[:10]:  # Limit for storage
                        security_analysis['secret_details'].append({
                            'rule_id': secret.get('RuleID'),
                            'category': secret.get('Category'),
                            'severity': secret.get('Severity', 'unknown'),
                            'title': secret.get('Title'),
                            'file_path': secret.get('StartLine')
                        })
                    
                    # Process misconfigurations
                    misconfigs = result.get('Misconfigurations', [])
                    security_analysis['config_issues'] += len(misconfigs)
                    for config in misconfigs[:10]:  # Limit for storage
                        security_analysis['config_details'].append({
                            'check_id': config.get('ID'),
                            'title': config.get('Title'),
                            'description': config.get('Description'),
                            'severity': config.get('Severity', 'unknown'),
                            'message': config.get('Message')
                        })
                    
                    # Process licenses (if available)
                    licenses = result.get('Licenses', [])
                    security_analysis['license_issues'] += len(licenses)
                    for license_info in licenses[:10]:  # Limit for storage
                        security_analysis['license_details'].append({
                            'name': license_info.get('Name'),
                            'confidence': license_info.get('Confidence'),
                            'file_path': license_info.get('FilePath')
                        })
            
            # Build the result structure
            result_data = {
                'vulnerabilities': vulnerability_counts,
                'vulnerability_details': vulnerability_details
            }
            
            # Add comprehensive security data if requested
            if comprehensive:
                result_data['comprehensive_security'] = security_analysis
            
            return result_data
            
        except Exception as e:
            print(f"    Error parsing Trivy output: {e}")
            return self.get_default_trivy_data()
    
    def get_default_trivy_data(self) -> Dict:
        """Return default Trivy data when scanning fails"""
        return {
            'vulnerabilities': {
                'total': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'negligible': 0,
                'unknown': 0,
                'scan_timestamp': None,
                'scanner': None
            },
            'vulnerability_details': [],
            'comprehensive_security': {
                'secrets_found': 0,
                'config_issues': 0,
                'license_issues': 0,
                'secret_details': [],
                'config_details': [],
                'license_details': [],
                'scan_timestamp': None,
                'scanner': None
            }
        }
    
    def _normalize_repository_path(self, repository: str) -> str:
        """Normalize repository path to work with MCR API
        
        Handles both formats:
        - Full MCR URL: mcr.microsoft.com/azurelinux/base/python -> azurelinux/base/python
        - Repository path: azurelinux/base/python -> azurelinux/base/python (unchanged)
        """
        try:
            # Remove MCR prefix if present
            if 'mcr.microsoft.com/' in repository:
                normalized = repository.replace('mcr.microsoft.com/', '')
                self.logger.debug(f"Removed MCR prefix: {repository} -> {normalized}")
            else:
                normalized = repository
            
            # Remove any tag if accidentally included (e.g., path:tag -> path)
            if ':' in normalized:
                normalized = normalized.split(':')[0]
                self.logger.debug(f"Removed tag from repository path: {repository} -> {normalized}")
            
            # Remove trailing slashes
            normalized = normalized.rstrip('/')
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing repository path '{repository}': {e}")
            return repository  # Return original if normalization fails
        

def main():
    """Main entry point for the registry scanner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scan Azure Linux base images")
    parser.add_argument('--comprehensive', action='store_true', 
                       help='Enable comprehensive security scanning with Trivy')
    parser.add_argument('--db-path', default='azure_linux_images.db',
                       help='Path to SQLite database')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Disable Docker image cleanup (keeps images locally)')
    parser.add_argument('--update-existing', action='store_true',
                       help='Update existing images in database (default: skip existing images)')
    parser.add_argument('--max-tags', type=int, default=0,
                       help='Maximum number of tags to scan per repository (default: 0 = all tags, use positive number to limit)')
    
    args = parser.parse_args()
    
    scanner = MCRRegistryScanner(
        db_path=args.db_path, 
        comprehensive_scan=args.comprehensive,
        cleanup_images=not args.no_cleanup,
        update_existing=args.update_existing,
        max_tags_per_repo=args.max_tags
    )
    
    print("Starting Azure Linux base image scan...")
    if args.comprehensive:
        print("🔍 Comprehensive security scanning enabled (Trivy with secrets & misconfigurations)")
    else:
        print("⚡ Fast vulnerability scanning enabled (Trivy vulnerabilities only)")
    print("This may take several minutes...")
    
    try:
        results = scanner.scan_all_repositories()
        
        print(f"\nScan completed. Found {len(results)} images.")
        
        # Get database statistics
        stats = scanner.get_database_stats()
        
        print("\n📊 Database Statistics:")
        db_stats = stats['database_stats']
        print(f"Total images: {db_stats['total_images']}")
        print(f"Zero vulnerability images: {db_stats['zero_vuln_images']}")
        print(f"Safe images (no critical/high): {db_stats['safe_images']}")
        print(f"Average vulnerabilities per image: {db_stats['avg_vulnerabilities']:.1f}")
        
        print("\n🚀 Language Summary:")
        for lang_stat in stats['language_summary'][:10]:  # Top 10
            print(f"  {lang_stat['language']}: {lang_stat['image_count']} images "
                  f"(avg {lang_stat['avg_vulnerabilities']:.1f} vulns)")
        
        # Save legacy JSON for backward compatibility
        scanner.save_database(results)
        
        return results
        
    except KeyboardInterrupt:
        print("\nScan interrupted")
    except Exception as e:
        print(f"Error during scan: {e}")
    finally:
        scanner.db.close()


if __name__ == "__main__":
    main()
