"""
Flask Web UI for Container Image Recommendations and Analysis Tool

This module provides a web-based interface for interacting with the
container base image database and recommendation engine.
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
import json
import os
import sys
import threading
import time
import queue
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import logging
from io import StringIO
import re

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import ImageDatabase
from recommendation_engine import RecommendationEngine, UserRequirement
from registry_scanner import MCRRegistryScanner
from image_analyzer import ImageAnalyzer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Global variables for streaming logs
scan_logs = {}  # Dictionary to store logs for each scan session
scan_status = {}  # Dictionary to store status for each scan session

class StreamingLogHandler:
    """Custom log handler to capture and stream logs"""
    
    def __init__(self, scan_id):
        self.scan_id = scan_id
        self.logs = queue.Queue()
        scan_logs[scan_id] = self.logs
        scan_status[scan_id] = {'active': True, 'completed': False, 'error': None}
    
    def emit(self, message):
        """Add a log message to the queue"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'type': 'info'
        }
        self.logs.put(log_entry)
    
    def emit_error(self, message):
        """Add an error message to the queue"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'type': 'error'
        }
        self.logs.put(log_entry)
        scan_status[self.scan_id]['error'] = message
    
    def complete(self, success=True):
        """Mark the scan as completed"""
        scan_status[self.scan_id]['active'] = False
        scan_status[self.scan_id]['completed'] = True
        
        if success:
            self.emit("✅ Scan completed successfully!")
        else:
            self.emit_error("❌ Scan failed!")

def cleanup_old_scans():
    """Clean up old scan logs to prevent memory leaks"""
    current_time = time.time()
    for scan_id in list(scan_logs.keys()):
        # Remove scans older than 1 hour
        try:
            scan_time = float(scan_id.split('_')[1])
            if current_time - scan_time > 3600:  # 1 hour
                del scan_logs[scan_id]
                del scan_status[scan_id]
        except (IndexError, ValueError):
            pass

# Add template filters
@app.template_filter('formatBytes')
def format_bytes_filter(bytes_value):
    """Format bytes as human readable string"""
    if not bytes_value or bytes_value == 0:
        return 'Unknown'
    
    try:
        bytes_value = int(bytes_value)
        if bytes_value == 0:
            return 'Unknown'
        
        k = 1024
        sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
        i = min(len(sizes) - 1, int(bytes_value.bit_length() / 10))
        
        if i == 0:
            return f"{bytes_value} {sizes[i]}"
        else:
            return f"{bytes_value / (k ** i):.1f} {sizes[i]}"
    except (ValueError, TypeError):
        return 'Unknown'

# Global instances
db_path = os.path.join(os.path.dirname(__file__), '..', 'azure_linux_images.db')
print(f"Looking for database at: {db_path}")

# Check if database exists
if not os.path.exists(db_path):
    print(f"Warning: Database not found at {db_path}")
    print("You may need to run a scan first or check the database path")

try:
    db = ImageDatabase(db_path)
    recommendation_engine = RecommendationEngine(db_path)
    # Enable debug logging for better troubleshooting
    recommendation_engine.enable_debug_logging()
    print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed: {e}")
    db = None
    recommendation_engine = None


@app.route('/')
def index():
    """Main dashboard page"""
    if not db:
        return render_template('error.html', error='Database connection failed. Please check if the database exists.')
    
    try:
        # Get database statistics
        stats = db.get_vulnerability_statistics()
        language_stats = db.get_languages_summary()
        
        return render_template('index.html', 
                             stats=stats, 
                             language_stats=language_stats[:10])
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/images')
def list_images():
    """List all images with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filters
    language_filter = request.args.get('language', '')
    security_filter = request.args.get('security', 'all')  # all, secure, vulnerable
    search_query = request.args.get('search', '')  # search parameter
    
    try:
        if search_query:
            # If there's a search query, use search functionality
            images = db.search_images(search_query, language_filter)
            # For search results, apply pagination manually
            total_count = len(images)
            start = (page - 1) * per_page
            end = start + per_page
            images = images[start:end]
        else:
            # Regular pagination
            images = db.get_all_images_with_details(
                page=page, 
                per_page=per_page,
                language_filter=language_filter,
                security_filter=security_filter
            )
            total_count = db.get_image_count(language_filter, security_filter)
        
        return render_template('images.html', 
                             images=images,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             language_filter=language_filter,
                             security_filter=security_filter,
                             search_query=search_query)
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/image/<int:image_id>')
def image_detail(image_id):
    """Detailed view of a specific image"""
    try:
        image = db.get_image_details(image_id)
        if not image:
            return render_template('error.html', error='Image not found')
        
        return render_template('image_detail.html', image=image)
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/recommend')
def recommend_form():
    """Recommendation form page"""
    return render_template('recommend.html')


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """API endpoint for getting recommendations"""
    try:
        data = request.get_json()
        
        # Create user requirement
        requirement = UserRequirement(
            language=data.get('language', 'python'),
            version=data.get('version', ''),
            packages=data.get('packages', []),
            size_preference=data.get('size_preference', 'balanced'),
            security_level=data.get('security_level', 'high'),
            max_vulnerabilities=data.get('max_vulnerabilities', 10),
            max_critical_vulnerabilities=data.get('max_critical_vulnerabilities', 0),
            max_high_vulnerabilities=data.get('max_high_vulnerabilities', 0)
        )
        
        # Get recommendations
        recommendations = recommendation_engine.recommend(requirement)
        
        # Convert to serializable format
        result = []
        for rec in recommendations[:5]:  # Top 5 recommendations
            # Calculate package match details for UI display
            total_required = len(requirement.packages) if requirement.packages else 0
            packages_found = 0
            
            if total_required > 0:
                # Get the actual package analysis from the recommendation engine
                image_name = rec.analysis_data.get('image', '')
                if image_name:
                    installed_packages_and_managers = recommendation_engine.get_system_packages_and_package_managers(image_name)
                    for package in requirement.packages:
                        if package.lower() in installed_packages_and_managers:
                            packages_found += 1
            
            result.append({
                'image_name': rec.image_name,
                'score': round(rec.score, 3),
                'reasoning': rec.reasoning,
                'language_match': rec.language_match,
                'version_match': rec.version_match,
                'package_compatibility': round(rec.package_compatibility, 3),
                'packages_found': packages_found,
                'total_required_packages': total_required,
                'size_score': round(rec.size_score, 3),
                'security_score': round(rec.security_score, 3),
                'vulnerabilities': rec.analysis_data.get('vulnerabilities', {}),
                'size_bytes': rec.analysis_data.get('manifest', {}).get('size', 0),
                'languages': rec.analysis_data.get('languages', [])
            })
        
        return jsonify({
            'success': True,
            'recommendations': result,
            'requirement': {
                'language': requirement.language,
                'version': requirement.version,
                'packages': requirement.packages,
                'size_preference': requirement.size_preference,
                'security_level': requirement.security_level
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """API endpoint to trigger a registry scan"""
    try:
        data = request.get_json()
        comprehensive = data.get('comprehensive', False)
        update_existing = data.get('update_existing', False)
        max_tags = data.get('max_tags', 5)  # Limit for UI scanning
        
        print("Scanning Key mcr registry image repositories...")
        if comprehensive:
            print("Comprehensive security scanning enabled (includes secrets, misconfigurations, and licenses)")
        print("🧹 Docker image cleanup enabled (images will be removed after analysis to save space)")
        
        if update_existing:
            print("🔄 Update mode: Will rescan and update existing images in database")
        else:
            print("⏭️  Skip mode: Will skip images already in database (use update_existing to rescan)")
            print("   💡 Duplicate prevention: Only newer scans or changed data will update existing images")
        
        print("This may take several minutes...")
        
        # Handle special case of scanning all tags (like CLI does)
        max_tags_param = None if max_tags == 0 else max_tags
        
        # Create scanner
        scanner = MCRRegistryScanner(
            db_path=db_path,
            comprehensive_scan=comprehensive,
            cleanup_images=True,
            update_existing=update_existing,
            max_tags_per_repo=max_tags_param or 999999  # Large number for "all"
        )
        
        # Scan all repositories
        results = scanner.scan_all_repositories()
        
        print(f"✅ Scan completed! Found {len(results)} images")
        print(f"📊 SQLite Database: {db_path}")
        
        # Save legacy JSON for backward compatibility (like CLI does)
        try:
            legacy_json_path = db_path.replace('.db', '.json')
            database = scanner.save_database(results, legacy_json_path)
            print(f"📄 Legacy JSON saved: {legacy_json_path}")
        except Exception as e:
            print(f"⚠️  Could not save legacy JSON: {e}")
        
        # Get and display database statistics (like CLI does)
        stats_message = ""
        try:
            stats = scanner.get_database_stats()
            db_stats = stats['database_stats']
            stats_message = f"""
Database Statistics:
- Total images in database: {db_stats.get('total_images', 0)}
- Zero vulnerability images: {db_stats.get('zero_vuln_images', 0)}
- Safe images (no critical/high): {db_stats.get('safe_images', 0)}
- Average vulnerabilities per image: {db_stats.get('avg_vulnerabilities', 0):.1f}"""
            
            if comprehensive:
                stats_message += "\n- Images with secrets: [Trivy data available]"
                stats_message += "\n- Images with config issues: [Trivy data available]"
            
            # Show language summary
            language_stats = stats.get('language_summary', [])
            if language_stats:
                stats_message += "\n\nTop Languages in Database:"
                for lang_stat in language_stats[:5]:  # Top 5
                    stats_message += f"\n- {lang_stat['language']}: {lang_stat['image_count']} images (avg {lang_stat['avg_vulnerabilities']:.1f} vulns)"
            
            print(f"\n📊 {stats_message}")
            
        except Exception as e:
            print(f"⚠️  Could not retrieve database statistics: {e}")
            stats_message = "Could not retrieve database statistics"
        
        # Close database connection (like CLI does)
        scanner.db.close()
        
        return jsonify({
            'success': True,
            'message': f'Scan completed. Analyzed {len(results)} images.',
            'images_scanned': len(results),
            'database_stats': stats_message,
            'database_path': db_path
        })
        
    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/stats')
def api_stats():
    """API endpoint to get database statistics"""
    try:
        stats = db.get_vulnerability_statistics()
        language_stats = db.get_languages_summary()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'language_stats': language_stats[:15]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/search')
def api_search():
    """API endpoint for searching images"""
    try:
        query = request.args.get('q', '')
        language = request.args.get('language', '')
        
        results = db.search_images(query, language)
        
        return jsonify({
            'success': True,
            'images': results[:20]  # Limit to 20 results, use 'images' key to match frontend
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/images/all')
def api_get_all_images():
    """API endpoint for getting all images for comparison picker"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)  # More images for picker
        search_query = request.args.get('search', '')
        
        if search_query:
            # Use search functionality
            images = db.search_images(search_query, '')
            total_count = len(images)
            # Apply pagination manually for search results
            start = (page - 1) * per_page
            end = start + per_page
            images = images[start:end]
        else:
            # Get all images with pagination
            images = db.get_all_images_with_details(
                page=page, 
                per_page=per_page,
                language_filter='',
                security_filter='all'
            )
            total_count = db.get_image_count('', 'all')
        
        return jsonify({
            'success': True,
            'images': images,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'has_more': (page * per_page) < total_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/image/<path:image_name>')
def api_get_image_by_name(image_name):
    """API endpoint for getting an image by exact name"""
    try:
        # URL decode the image name since it's URL encoded from the frontend
        from urllib.parse import unquote
        image_name = unquote(image_name)
        
        print(f"DEBUG: Looking up image by name: '{image_name}'")
        print(f"DEBUG: Image name length: {len(image_name)}")
        print(f"DEBUG: Image name repr: {repr(image_name)}")
        
        # First, let's see what images are actually in the database
        cursor = db.conn.execute("SELECT name FROM images LIMIT 5")
        sample_names = [row['name'] for row in cursor.fetchall()]
        print(f"DEBUG: Sample image names in DB: {sample_names}")
        
        # Check if there are any similar names
        cursor = db.conn.execute("SELECT name FROM images WHERE name LIKE ? LIMIT 3", (f"%{image_name.split('/')[-1]}%",))
        similar_names = [row['name'] for row in cursor.fetchall()]
        print(f"DEBUG: Similar names found: {similar_names}")
        
        image = db.get_image_by_exact_name(image_name)
        print(f"DEBUG: Database result: {image}")
        
        if image:
            print(f"DEBUG: Image found with ID: {image.get('id')}")
            return jsonify({
                'success': True,
                'image': image,
                'found': True
            })
        else:
            print(f"DEBUG: No image found with name: '{image_name}'")
            return jsonify({
                'success': True,
                'image': None,
                'found': False,
                'debug_info': {
                    'searched_name': image_name,
                    'sample_db_names': sample_names,
                    'similar_names': similar_names
                }
            })
        
    except Exception as e:
        print(f"DEBUG: Error in api_get_image_by_name: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/image/<int:image_id>/packages')
def api_get_image_packages(image_id):
    """API endpoint for getting system packages for an image"""
    try:
        cursor = db.conn.execute(
            "SELECT * FROM system_packages WHERE image_id = ? ORDER BY name", (image_id,)
        )
        packages = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'packages': packages,
            'count': len(packages)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/repositories')
def api_get_repositories():
    """API endpoint for getting the list of MCR repositories being scanned"""
    try:
        # Create a temporary scanner instance to get the repository list
        scanner = MCRRegistryScanner(
            db_path=db_path,
            comprehensive_scan=False,
            cleanup_images=True,
            update_existing=False,
            max_tags_per_repo=5
        )
        
        repositories = scanner.image_patterns
        
        return jsonify({
            'success': True,
            'repositories': repositories,
            'count': len(repositories)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/compare', methods=['POST'])
def api_compare_images():
    """API endpoint for comparing two images"""
    try:
        data = request.get_json()
        image1_id = data.get('image1_id')
        image2_id = data.get('image2_id')
        
        if not image1_id or not image2_id:
            return jsonify({'success': False, 'error': 'Two image IDs are required for comparison'})
        
        if image1_id == image2_id:
            return jsonify({'success': False, 'error': 'Cannot compare an image with itself'})
        
        # Get detailed information for both images
        image1 = db.get_image_details(image1_id)
        image2 = db.get_image_details(image2_id)
        
        if not image1:
            return jsonify({'success': False, 'error': f'Image with ID {image1_id} not found'})
        if not image2:
            return jsonify({'success': False, 'error': f'Image with ID {image2_id} not found'})
        
        # Get packages for both images
        cursor = db.conn.execute(
            "SELECT * FROM system_packages WHERE image_id = ? ORDER BY name", (image1_id,)
        )
        image1_packages = [dict(row) for row in cursor.fetchall()]
        
        cursor = db.conn.execute(
            "SELECT * FROM system_packages WHERE image_id = ? ORDER BY name", (image2_id,)
        )
        image2_packages = [dict(row) for row in cursor.fetchall()]
        
        # Compare packages
        packages1_set = {pkg['name']: pkg['version'] for pkg in image1_packages}
        packages2_set = {pkg['name']: pkg['version'] for pkg in image2_packages}
        
        common_packages = []
        different_versions = []
        unique_to_image1 = []
        unique_to_image2 = []
        
        all_package_names = set(packages1_set.keys()) | set(packages2_set.keys())
        
        for pkg_name in all_package_names:
            if pkg_name in packages1_set and pkg_name in packages2_set:
                version1 = packages1_set[pkg_name]
                version2 = packages2_set[pkg_name]
                if version1 == version2:
                    common_packages.append({
                        'name': pkg_name,
                        'version': version1
                    })
                else:
                    different_versions.append({
                        'name': pkg_name,
                        'version1': version1,
                        'version2': version2
                    })
            elif pkg_name in packages1_set:
                unique_to_image1.append({
                    'name': pkg_name,
                    'version': packages1_set[pkg_name]
                })
            else:
                unique_to_image2.append({
                    'name': pkg_name,
                    'version': packages2_set[pkg_name]
                })
        
        # Calculate comparison metrics
        size_diff = 0
        size_diff_percent = 0
        if image1.get('size_bytes') and image2.get('size_bytes'):
            size_diff = image2['size_bytes'] - image1['size_bytes']
            size_diff_percent = (size_diff / image1['size_bytes']) * 100 if image1['size_bytes'] > 0 else 0
        
        vuln_diff = {
            'total': (image2.get('total_vulnerabilities', 0) - image1.get('total_vulnerabilities', 0)),
            'critical': (image2.get('critical_vulnerabilities', 0) - image1.get('critical_vulnerabilities', 0)),
            'high': (image2.get('high_vulnerabilities', 0) - image1.get('high_vulnerabilities', 0)),
            'medium': (image2.get('medium_vulnerabilities', 0) - image1.get('medium_vulnerabilities', 0)),
            'low': (image2.get('low_vulnerabilities', 0) - image1.get('low_vulnerabilities', 0))
        }
        
        # Determine which image is "better" based on security and size
        security_score1 = (image1.get('critical_vulnerabilities', 0) * 4 + 
                          image1.get('high_vulnerabilities', 0) * 3 + 
                          image1.get('medium_vulnerabilities', 0) * 2 + 
                          image1.get('low_vulnerabilities', 0) * 1)
        
        security_score2 = (image2.get('critical_vulnerabilities', 0) * 4 + 
                          image2.get('high_vulnerabilities', 0) * 3 + 
                          image2.get('medium_vulnerabilities', 0) * 2 + 
                          image2.get('low_vulnerabilities', 0) * 1)
        
        recommendation = {
            'security_winner': 'image1' if security_score1 < security_score2 else 'image2' if security_score2 < security_score1 else 'tie',
            'size_winner': 'image1' if (image1.get('size_bytes', 0) < image2.get('size_bytes', 0)) else 'image2' if (image2.get('size_bytes', 0) < image1.get('size_bytes', 0)) else 'tie',
            'overall_recommendation': None
        };
        
        # Overall recommendation logic
        if recommendation['security_winner'] == recommendation['size_winner']:
            recommendation['overall_recommendation'] = recommendation['security_winner']
        elif recommendation['security_winner'] != 'tie':
            recommendation['overall_recommendation'] = recommendation['security_winner']  # Security wins
        elif recommendation['size_winner'] != 'tie':
            recommendation['overall_recommendation'] = recommendation['size_winner']
        else:
            recommendation['overall_recommendation'] = 'tie'
        
        return jsonify({
            'success': True,
            'comparison': {
                'image1': image1,
                'image2': image2,
                'size_comparison': {
                    'difference_bytes': size_diff,
                    'difference_percent': round(size_diff_percent, 2),
                    'winner': recommendation['size_winner']
                },
                'vulnerability_comparison': {
                    'differences': vuln_diff,
                    'winner': recommendation['security_winner'],
                    'security_score1': security_score1,
                    'security_score2': security_score2
                },
                'package_comparison': {
                    'common_packages': len(common_packages),
                    'different_versions': len(different_versions),
                    'unique_to_image1': len(unique_to_image1),
                    'unique_to_image2': len(unique_to_image2),
                    'details': {
                        'common': common_packages[:50],  # Limit for UI
                        'different_versions': different_versions[:50],
                        'unique_image1': unique_to_image1[:50],
                        'unique_image2': unique_to_image2[:50]
                    }
                },
                'recommendation': recommendation
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/scan')
def scan_page():
    """Registry scanning page"""
    return render_template('scan.html')


@app.route('/compare')
def compare_page():
    """Image comparison page"""
    return render_template('compare.html')


@app.route('/api/scan/stream/<scan_id>')
def stream_scan_logs(scan_id):
    """Server-Sent Events endpoint for streaming scan logs"""
    def generate():
        # Clean up old scans first
        cleanup_old_scans()
        
        if scan_id not in scan_logs:
            yield f"data: {json.dumps({'error': 'Scan session not found'})}\n\n"
            return
        
        log_queue = scan_logs[scan_id]
        
        while scan_status.get(scan_id, {}).get('active', False):
            try:
                # Get log with timeout
                log_entry = log_queue.get(timeout=1)
                yield f"data: {json.dumps(log_entry)}\n\n"
            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                continue
        
        # Send any remaining logs
        while not log_queue.empty():
            try:
                log_entry = log_queue.get_nowait()
                yield f"data: {json.dumps(log_entry)}\n\n"
            except queue.Empty:
                break
        
        # Send completion status
        status = scan_status.get(scan_id, {})
        if status.get('completed'):
            yield f"data: {json.dumps({'completed': True, 'error': status.get('error')})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/scan/start', methods=['POST'])
def api_scan_streaming():
    """API endpoint to start a streaming registry scan"""
    try:
        data = request.get_json()
        comprehensive = data.get('comprehensive', False)
        update_existing = data.get('update_existing', False)
        max_tags = data.get('max_tags', 5)
        
        # Generate unique scan ID
        scan_id = f"scan_{int(time.time())}"
        
        # Start the scan in a background thread
        def run_scan():
            log_handler = StreamingLogHandler(scan_id)
            
            try:
                log_handler.emit("🚀 Starting MCR registry scan...")
                log_handler.emit(f"📋 Configuration: comprehensive={comprehensive}, update_existing={update_existing}, max_tags={max_tags}")
                
                if comprehensive:
                    log_handler.emit("🔒 Comprehensive security scanning enabled (includes secrets, misconfigurations, and licenses)")
                
                log_handler.emit("🧹 Docker image cleanup enabled (images will be removed after analysis to save space)")
                
                if update_existing:
                    log_handler.emit("🔄 Update mode: Will rescan and update existing images in database")
                else:
                    log_handler.emit("⏭️  Skip mode: Will skip images already in database")
                
                log_handler.emit("⏱️  This may take several minutes...")
                
                # Handle special case of scanning all tags
                max_tags_param = None if max_tags == 0 else max_tags
                
                # Create scanner with custom logging
                scanner = MCRRegistryScanner(
                    db_path=db_path,
                    comprehensive_scan=comprehensive,
                    cleanup_images=True,
                    update_existing=update_existing,
                    max_tags_per_repo=max_tags_param or 999999
                )
                
                # Monkey patch the scanner's print statements to use our log handler
                original_print = print
                def custom_print(*args, **kwargs):
                    message = ' '.join(str(arg) for arg in args)
                    log_handler.emit(message)
                    original_print(*args, **kwargs)
                
                # Temporarily replace print
                import builtins
                builtins.print = custom_print
                
                try:
                    # Scan all repositories
                    results = scanner.scan_all_repositories()
                    
                    log_handler.emit(f"✅ Scan completed! Found {len(results)} images")
                    log_handler.emit(f"📊 SQLite Database: {db_path}")
                    
                    # Save legacy JSON
                    try:
                        legacy_json_path = db_path.replace('.db', '.json')
                        scanner.save_database(results, legacy_json_path)
                        log_handler.emit(f"📄 Legacy JSON saved: {legacy_json_path}")
                    except Exception as e:
                        log_handler.emit(f"⚠️  Could not save legacy JSON: {e}")
                    
                    # Get database statistics
                    try:
                        stats = scanner.get_database_stats()
                        db_stats = stats['database_stats']
                        
                        log_handler.emit("📊 Database Statistics:")
                        log_handler.emit(f"   • Total images: {db_stats.get('total_images', 0)}")
                        log_handler.emit(f"   • Zero vulnerability images: {db_stats.get('zero_vuln_images', 0)}")
                        log_handler.emit(f"   • Safe images (no critical/high): {db_stats.get('safe_images', 0)}")
                        log_handler.emit(f"   • Average vulnerabilities: {db_stats.get('avg_vulnerabilities', 0):.1f}")
                        
                        # Show language summary
                        language_stats = stats.get('language_summary', [])
                        if language_stats:
                            log_handler.emit("🔤 Top Languages in Database:")
                            for lang_stat in language_stats[:5]:
                                log_handler.emit(f"   • {lang_stat['language']}: {lang_stat['image_count']} images (avg {lang_stat['avg_vulnerabilities']:.1f} vulns)")
                        
                    except Exception as e:
                        log_handler.emit(f"⚠️  Could not retrieve database statistics: {e}")
                    
                    # Close database connection
                    scanner.db.close()
                    log_handler.complete(success=True)
                    
                finally:
                    # Restore original print
                    builtins.print = original_print
                    
            except Exception as e:
                log_handler.emit_error(f"Error during scan: {str(e)}")
                log_handler.complete(success=False)
        
        # Start the scan thread
        thread = threading.Thread(target=run_scan, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'message': 'Scan started successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/scan-repo/start', methods=['POST'])
def api_scan_repo_streaming():
    """API endpoint to start a streaming repository scan"""
    try:
        data = request.get_json()
        repository = data.get('repository', '').strip()
        comprehensive = data.get('comprehensive', False)
        update_existing = data.get('update_existing', False)
        max_tags = data.get('max_tags', 10)
        
        if not repository:
            return jsonify({'success': False, 'error': 'Repository name is required'})
        
        # Generate unique scan ID
        scan_id = f"repo_scan_{int(time.time())}"
        
        # Start the scan in a background thread
        def run_repo_scan():
            log_handler = StreamingLogHandler(scan_id)
            
            try:
                log_handler.emit(f"🚀 Starting repository scan for: {repository}")
                log_handler.emit(f"📋 Configuration: comprehensive={comprehensive}, update_existing={update_existing}, max_tags={max_tags}")
                
                if comprehensive:
                    log_handler.emit("🔒 Comprehensive security scanning enabled (includes secrets, misconfigurations, and licenses)")
                
                log_handler.emit("🧹 Docker image cleanup enabled (images will be removed after analysis to save space)")
                
                if update_existing:
                    log_handler.emit("🔄 Update mode: Will rescan and update existing images in database")
                else:
                    log_handler.emit("⏭️  Skip mode: Will skip images already in database")
                
                # Create scanner instance
                scanner = MCRRegistryScanner(
                    db_path=db_path,
                    comprehensive_scan=comprehensive,
                    cleanup_images=True,
                    update_existing=update_existing,
                    max_tags_per_repo=max_tags if max_tags > 0 else 999999
                )
                
                # Monkey patch the scanner's print statements to use our log handler
                original_print = print
                def custom_print(*args, **kwargs):
                    message = ' '.join(str(arg) for arg in args)
                    log_handler.emit(message)
                    original_print(*args, **kwargs)
                
                # Temporarily replace print
                import builtins
                builtins.print = custom_print
                
                try:
                    # Scan the specific repository
                    log_handler.emit(f"🔍 Scanning repository: {repository}")
                    results = scanner.scan_repository(repository)
                    
                    log_handler.emit(f"✅ Repository scan completed! Analyzed {len(results)} images")
                    
                    if len(results) == 0:
                        log_handler.emit("⚠️  No images were analyzed. This could mean:")
                        log_handler.emit("   • Repository doesn't exist or has no accessible tags")
                        log_handler.emit("   • All images were skipped (already in database)")
                        log_handler.emit("   • Repository tags were filtered out")
                    
                    # Get database statistics for this repository
                    try:
                        if len(results) > 0:
                            # Show summary of what was scanned
                            log_handler.emit("📊 Scan Summary:")
                            total_vulns = sum(r.get('vulnerabilities', {}).get('total', 0) for r in results)
                            avg_vulns = total_vulns / len(results) if len(results) > 0 else 0
                            log_handler.emit(f"   • Images analyzed: {len(results)}")
                            log_handler.emit(f"   • Average vulnerabilities: {avg_vulns:.1f}")
                            
                            # Count vulnerability distribution
                            critical_count = sum(1 for r in results if r.get('vulnerabilities', {}).get('critical', 0) > 0)
                            high_count = sum(1 for r in results if r.get('vulnerabilities', {}).get('high', 0) > 0)
                            safe_count = len(results) - critical_count - high_count
                            
                            log_handler.emit(f"   • Images with critical vulnerabilities: {critical_count}")
                            log_handler.emit(f"   • Images with high vulnerabilities: {high_count}")
                            log_handler.emit(f"   • Safe images (no critical/high): {safe_count}")
                        
                    except Exception as e:
                        log_handler.emit(f"⚠️  Could not retrieve scan statistics: {e}")
                    
                    # Close database connection
                    scanner.db.close()
                    log_handler.complete(success=True)
                    
                finally:
                    # Restore original print
                    builtins.print = original_print
                    
            except Exception as e:
                log_handler.emit_error(f"Error during repository scan: {str(e)}")
                log_handler.complete(success=False)
        
        # Start the scan thread
        thread = threading.Thread(target=run_repo_scan, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'message': 'Repository scan started successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/scan-image/start', methods=['POST'])
def api_scan_image_streaming():
    """API endpoint to start a streaming image scan"""
    try:
        data = request.get_json()
        image_name = data.get('image_name', '').strip()
        comprehensive = data.get('comprehensive', False)
        update_existing = data.get('update_existing', False)
        
        if not image_name:
            return jsonify({'success': False, 'error': 'Image name is required'})
        
        # Generate unique scan ID
        scan_id = f"image_scan_{int(time.time())}"
        
        # Start the scan in a background thread
        def run_image_scan():
            log_handler = StreamingLogHandler(scan_id)
            
            try:
                log_handler.emit(f"🚀 Starting image scan for: {image_name}")
                log_handler.emit(f"📋 Configuration: comprehensive={comprehensive}, update_existing={update_existing}")
                
                # Create scanner instance with SQLite database
                # Get database path, using the same convention as CLI
                json_db_path = os.path.join(os.path.dirname(__file__), '..', 'azure_linux_images.json')
                db_path = json_db_path.replace('.json', '.db')  # Use SQLite DB
                
                scanner = MCRRegistryScanner(
                    db_path=db_path,
                    comprehensive_scan=comprehensive,
                    cleanup_images=True,  # Always cleanup in web UI
                    update_existing=update_existing
                )
                
                # Check if image already exists before doing expensive analysis
                if scanner.db.image_exists(image_name):
                    if not update_existing:
                        log_handler.emit_error(f"❌ Error: Image {image_name} already exists in database")
                        log_handler.emit("💡 Use 'Update Existing' option to update the existing image")
                        log_handler.complete(success=False)
                        scanner.db.close()
                        return
                    else:
                        log_handler.emit(f"🔄 Image exists, updating with update_existing flag...")
                
                # Analyze the image
                log_handler.emit("🔍 Analyzing image structure...")
                analyzer = ImageAnalyzer(image_name)
                analysis = analyzer.analyze()
                
                # Add Docker manifest/inspect data for size and layers
                log_handler.emit("📊 Getting image manifest data...")
                manifest_data = get_docker_manifest_data(image_name, log_handler)
                if manifest_data:
                    analysis['manifest'] = manifest_data
                
                # Add vulnerability scanning
                if comprehensive:
                    log_handler.emit("🔍 Running comprehensive security scan (Trivy with secrets & misconfigurations)...")
                else:
                    log_handler.emit("⚡ Running fast vulnerability scan (Trivy vulnerabilities only)...")
                    
                vulnerability_data = scanner.scan_vulnerabilities(image_name, comprehensive)
                analysis.update(vulnerability_data)
                
                # Save to database (with duplicate prevention unless update_existing is True)
                force_update = update_existing  # Respect the update_existing flag
                image_id = scanner.db.insert_image_analysis(analysis, force_update=force_update)
                analysis['database_id'] = image_id
                
                log_handler.emit(f"✅ Image successfully added to database with ID: {image_id}")
                
                # Show vulnerability summary
                vuln_data = analysis.get('vulnerabilities', {})
                if vuln_data.get('total', 0) > 0:
                    log_handler.emit(f"�️  Vulnerability Summary:")
                    log_handler.emit(f"   Total: {vuln_data['total']} vulnerabilities")
                    log_handler.emit(f"   🔴 Critical: {vuln_data.get('critical', 0)}")
                    log_handler.emit(f"   🟠 High: {vuln_data.get('high', 0)}")
                    log_handler.emit(f"   🟡 Medium: {vuln_data.get('medium', 0)}")
                    log_handler.emit(f"   🔵 Low: {vuln_data.get('low', 0)}")
                else:
                    log_handler.emit("✅ No vulnerabilities found!")
                
                # Show comprehensive security results if available
                if 'comprehensive_security' in analysis:
                    comp_data = analysis['comprehensive_security']
                    log_handler.emit(f"🔒 Security Analysis (Trivy):")
                    log_handler.emit(f"   � Secrets found: {comp_data.get('secrets_found', 0)}")
                    log_handler.emit(f"   ⚙️  Configuration issues: {comp_data.get('config_issues', 0)}")
                    log_handler.emit(f"   📋 License issues: {comp_data.get('license_issues', 0)}")
                
                # Clean up the Docker image if cleanup is enabled
                if scanner.cleanup_images:
                    log_handler.emit("🧹 Cleaning up Docker images...")
                    scanner.cleanup_docker_images([image_name])
                
                scanner.db.close()
                log_handler.complete(success=True)
                
            except Exception as e:
                log_handler.emit_error(f"Error during image scan: {str(e)}")
                log_handler.complete(success=False)
        
        # Start the scan thread
        thread = threading.Thread(target=run_image_scan, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'message': 'Image scan started successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/analyze-and-recommend', methods=['POST'])
def api_analyze_and_recommend():
    """API endpoint for analyzing an image and getting recommendations based on its contents"""
    try:
        data = request.get_json()
        image_name = data.get('image_name', '').strip()
        
        if not image_name:
            return jsonify({'success': False, 'error': 'Image name is required'})
        
        # Validate image name format
        if not re.match(r'^[a-zA-Z0-9._/-]+:[a-zA-Z0-9._-]+$|^[a-zA-Z0-9._/-]+$', image_name):
            return jsonify({'success': False, 'error': 'Invalid image name format'})
        
        # Add default tag if not specified
        if ':' not in image_name:
            image_name += ':latest'
        
        # Create user requirement from form data
        requirement = UserRequirement(
            language='',  # Will be filled from analysis
            version='',   # Will be filled from analysis
            packages=[],  # Will be filled from analysis
            size_preference=data.get('size_preference', 'balanced'),
            security_level=data.get('security_level', 'high'),
            max_vulnerabilities=data.get('max_vulnerabilities', 10),
            max_critical_vulnerabilities=data.get('max_critical_vulnerabilities', 0),
            max_high_vulnerabilities=data.get('max_high_vulnerabilities', 0)
        )
        
        # First, check if image exists in database
        print(f"Checking if image exists in database: {image_name}")
        analysis, recommendations, final_requirement = recommendation_engine.recommend_from_existing_image(image_name, requirement)
        
        print(f"Found {len(recommendations)} recommendations")
        if final_requirement:
            print(f"Final search criteria - Language: {final_requirement.language}, Version: {final_requirement.version}")
        
        if analysis is None:
            # Image not in database - suggest scanning
            return jsonify({
                'success': False, 
                'error': f'Image "{image_name}" not found in the system database. Please scan this image first using the scan functionality.',
                'image_not_found': True,
                'suggested_action': 'scan_image'
            })
        
        # Extract information from database analysis
        detected_languages = analysis.get('languages', [])
        system_packages = analysis.get('system_packages', [])
        package_managers = analysis.get('package_managers', [])
        
        if not detected_languages:
            # Provide more detailed error message
            total_packages = len(system_packages) + len(package_managers)
            return jsonify({
                'success': False, 
                'error': f'No programming language runtimes detected in the stored analysis for "{image_name}". Found {len(system_packages)} system packages and {len(package_managers)} package managers, but no language runtimes were identified. This might indicate that the image analysis needs to be updated or the image contains only system libraries.',
                'analysis_incomplete': True,
                'suggested_action': 'rescan_image',
                'partial_analysis': {
                    'system_packages_count': len(system_packages),
                    'package_managers_count': len(package_managers),
                    'total_packages': total_packages
                }
            })
        
        # Get all packages (system + package managers)
        all_packages = list(set(system_packages + package_managers))
        
        # The recommendation_engine.recommend_from_existing_image already returns the recommendations
        # based on the detected languages, so we don't need to recreate the UserRequirement
        
        # Extract the primary language for display (the recommendation engine chose the best one)
        primary_language = detected_languages[0] if detected_languages else {'language': 'unknown', 'version': ''}
        
        # Convert to serializable format (same as existing recommend endpoint)
        result = []
        for rec in recommendations[:5]:  # Top 5 recommendations
            # Calculate package match details for UI display
            total_required = len(all_packages) if all_packages else 0
            packages_found = 0
            
            if total_required > 0:
                # Get the actual package analysis from the recommendation engine
                rec_image_name = rec.analysis_data.get('image', '')
                if rec_image_name:
                    installed_packages_and_managers = recommendation_engine.get_system_packages_and_package_managers(rec_image_name)
                    for package in all_packages:
                        if package.lower() in installed_packages_and_managers:
                            packages_found += 1
            
            result.append({
                'image_name': rec.image_name,
                'score': round(rec.score, 3),
                'reasoning': rec.reasoning,
                'language_match': rec.language_match,
                'version_match': rec.version_match,
                'package_compatibility': round(rec.package_compatibility, 3),
                'packages_found': packages_found,
                'total_required_packages': total_required,
                'size_score': round(rec.size_score, 3),
                'security_score': round(rec.security_score, 3),
                'vulnerabilities': rec.analysis_data.get('vulnerabilities', {}),
                'size_bytes': rec.analysis_data.get('manifest', {}).get('size', 0),
                'languages': rec.analysis_data.get('languages', [])
            })
        
        return jsonify({
            'success': True,
            'analyzed_image': image_name,
            'analysis': {
                'languages': detected_languages,
                'system_packages_count': len(system_packages),
                'package_managers_count': len(package_managers),
                'total_packages': len(all_packages),
                'size_bytes': analysis.get('manifest', {}).get('size', 0),
                'vulnerabilities': analysis.get('vulnerabilities', {})
            },
            'recommendations': result,
            'requirement': {
                'language': final_requirement.language,
                'version': final_requirement.version,
                'packages': final_requirement.packages,
                'size_preference': final_requirement.size_preference,
                'security_level': final_requirement.security_level
            }
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in analyze-and-recommend: {error_details}")
        return jsonify({'success': False, 'error': f'Analysis failed: {str(e)}'})

def get_docker_manifest_data(image_name: str, log_handler) -> Optional[Dict]:
    """Get Docker image manifest data with size only from docker images command
    
    Uses docker images command to get compressed size. If docker images fails
    or cannot be parsed, size is set to 0. No fallbacks to docker inspect for size.
    """
    try:
        # First, ensure the image is pulled
        log_handler.emit(f"   🐳 Pulling image {image_name}...")
        pull_result = subprocess.run([
            'docker', 'pull', image_name
        ], capture_output=True, text=True, timeout=300)
        
        if pull_result.returncode != 0:
            log_handler.emit(f"   ⚠️  Failed to pull image: {pull_result.stderr}")
            return None
        
        # Get image inspect data for layers and metadata
        inspect_result = subprocess.run([
            'docker', 'inspect', image_name
        ], capture_output=True, text=True, timeout=30)
        
        if inspect_result.returncode != 0:
            log_handler.emit(f"   ⚠️  Failed to inspect image: {inspect_result.stderr}")
            return None
        
        inspect_data = json.loads(inspect_result.stdout)[0]
        
        # Get the size from docker images command with name variation support
        actual_size = 0  # Default to 0
        
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
            images_result = subprocess.run([
                'docker', 'images', variant, '--format', '{{.Size}}'
            ], capture_output=True, text=True, timeout=30)
            
            if images_result.returncode == 0 and images_result.stdout.strip():
                size_str = images_result.stdout.strip()
                try:
                    # Convert human-readable size to bytes (e.g., "211MB" -> bytes)
                    if size_str.endswith('MB'):
                        actual_size = int(float(size_str[:-2]) * 1024 * 1024)
                    elif size_str.endswith('GB'):
                        actual_size = int(float(size_str[:-2]) * 1024 * 1024 * 1024)
                    elif size_str.endswith('KB'):
                        actual_size = int(float(size_str[:-2]) * 1024)
                    elif size_str.endswith('B'):
                        actual_size = int(size_str[:-1])
                    else:
                        # Try to parse as a number (bytes)
                        actual_size = int(float(size_str))
                    log_handler.emit(f"   📏 Parsed size: {actual_size / (1024*1024):.1f} MB from docker images (using name: {variant})")
                    break  # Success, stop trying other variations
                except (ValueError, IndexError):
                    log_handler.emit(f"   ⚠️  Could not parse size '{size_str}' from {variant}")
                    continue  # Try next variation
        
        if actual_size == 0:
            log_handler.emit(f"   ⚠️  Failed to get size from docker images for all name variations, setting size to 0")
        
        # Extract relevant manifest data
        manifest_data = {
            'size': actual_size,  # Use docker images size or 0
            'layers': len(inspect_data.get('RootFS', {}).get('Layers', [])),
            'created': inspect_data.get('Created', ''),
            'digest': inspect_data.get('RepoDigests', [None])[0] if inspect_data.get('RepoDigests') else None
        }
        
        # Log final results
        if actual_size > 0:
            log_handler.emit(f"   📊 Size: {actual_size / (1024*1024):.1f} MB, Layers: {manifest_data['layers']}")
        else:
            log_handler.emit(f"   📊 Size: Unknown (0 bytes), Layers: {manifest_data['layers']}")
        return manifest_data
        
    except subprocess.TimeoutExpired:
        log_handler.emit("   ⚠️  Docker operation timed out")
        return None
    except Exception as e:
        log_handler.emit(f"   ⚠️  Error getting manifest data: {e}")
        return None


if __name__ == '__main__':
    # Run the Flask development server
    app.run(
        host='0.0.0.0',  # Allow connections from any IP
        port=8080,       # Use port 8080 as configured in start.sh
        debug=True,      # Enable debug mode for development
        threaded=True    # Enable threaded mode for better performance
    )
