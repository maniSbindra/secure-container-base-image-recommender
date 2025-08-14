#!/usr/bin/env python3
"""
Azure Linux Base Image Recommendation CLI

Command-line interface for finding secure Azure Linux base images
based on language and package requirements.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from image_analyzer import ImageAnalyzer
from recommendation_engine import RecommendationEngine, UserRequirement
from registry_scanner import MCRRegistryScanner


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser"""

    parser = argparse.ArgumentParser(
        description="Find secure Azure Linux base images for your projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --language python --version 3.12
  %(prog)s --language node --version 18 --packages express,lodash
  %(prog)s --language java --version 17 --size minimal
  %(prog)s --analyze mcr.microsoft.com/azurelinux/base/python:3.12
  %(prog)s --scan-image mcr.microsoft.com/azurelinux/base/python:3.12
  %(prog)s --scan-image mcr.microsoft.com/azurelinux/base/python:3.12 --comprehensive
  %(prog)s --scan-image mcr.microsoft.com/azurelinux/base/python:3.12 --update-existing
  %(prog)s --scan-repo mcr.microsoft.com/azurelinux/base/python --comprehensive
  %(prog)s --scan-repo azurelinux/base/nodejs --max-tags 5
  %(prog)s --scan --comprehensive
  %(prog)s --scan --no-cleanup  # Keep Docker images locally
  %(prog)s --scan --update-existing  # Rescan existing images
  %(prog)s --scan --max-tags 0  # Scan ALL tags (can be slow)
  %(prog)s --reset-database  # Clear all data and start fresh
  %(prog)s --clear-database  # Same as --reset-database
        """,
    )

    # Main operation modes
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument(
        "--recommend",
        "-r",
        action="store_true",
        help="Recommend base images (default mode)",
    )
    operation.add_argument(
        "--analyze", "-a", metavar="IMAGE", help="Analyze a specific container image"
    )
    operation.add_argument(
        "--scan",
        "-s",
        action="store_true",
        help="Scan MCR AzureLinux registry and update database",
    )
    operation.add_argument(
        "--scan-repo",
        metavar="REPO",
        help="Scan a specific repository (e.g., mcr.microsoft.com/azurelinux/base/python or azurelinux/base/python)",
    )
    operation.add_argument(
        "--scan-image",
        metavar="IMAGE",
        help="Analyze and add a specific image to the database",
    )
    operation.add_argument(
        "--reset-database",
        action="store_true",
        help="Reset the database by clearing all data (use with caution)",
    )
    operation.add_argument(
        "--clear-database",
        action="store_true",
        help="Clear all data from the database (same as --reset-database)",
    )

    # Recommendation parameters
    rec_group = parser.add_argument_group("recommendation options")
    rec_group.add_argument(
        "--language",
        "-l",
        help="Programming language (e.g., python, node, java, go)",
        required=False,
    )
    rec_group.add_argument(
        "--version", "-v", help="Language version (e.g., 3.12, 18, 17)"
    )
    rec_group.add_argument(
        "--packages", "-p", help="Comma-separated list of required packages"
    )
    rec_group.add_argument(
        "--size",
        choices=["minimal", "balanced", "full"],
        default="balanced",
        help="Size preference (default: balanced)",
    )
    rec_group.add_argument(
        "--security",
        choices=["standard", "high", "maximum"],
        default="high",
        help="Security level preference (default: high)",
    )

    # Output options
    output_group = parser.add_argument_group("output options")
    output_group.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "dockerfile"],
        default="text",
        help="Output format (default: text)",
    )
    output_group.add_argument(
        "--limit",
        "-n",
        type=int,
        default=5,
        help="Maximum number of recommendations (default: 5)",
    )
    output_group.add_argument("--output", "-o", help="Output file (default: stdout)")

    # Database options
    db_group = parser.add_argument_group("database options")
    db_group.add_argument(
        "--database",
        "-d",
        default="azure_linux_images.db",
        help="Path to SQLite database (default: azure_linux_images.db)",
    )
    db_group.add_argument(
        "--comprehensive",
        action="store_true",
        help="Enable comprehensive security scanning with Trivy (slower but more thorough)",
    )
    db_group.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Disable Docker image cleanup after analysis (keeps images locally)",
    )
    db_group.add_argument(
        "--update-existing",
        action="store_true",
        help="Update existing images in database (applies to scan and scan-image operations)",
    )
    db_group.add_argument(
        "--max-tags",
        type=int,
        default=10,
        help="Maximum number of tags to scan per repository (default: 10, use 0 for all tags)",
    )

    return parser


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration for CLI operations"""

    # Configure root logger
    log_level = logging.DEBUG if verbose else logging.INFO

    # Setup console handler
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Configure logger
    logger = logging.getLogger("azure_linux_cli")
    logger.setLevel(log_level)

    # Only add handler if not already present
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


def handle_recommend(args) -> int:
    """Handle recommendation requests"""

    if not args.language:
        print("Error: --language is required for recommendations")
        return 1

    # Create user requirements
    packages = []
    if args.packages:
        packages = [pkg.strip() for pkg in args.packages.split(",")]

    requirements = UserRequirement(
        language=args.language,
        version=args.version,
        packages=packages,
        size_preference=args.size,
        security_level=args.security,
    )

    # Get recommendations
    engine = RecommendationEngine(args.database)
    recommendations = engine.recommend(requirements)

    if not recommendations:
        print(f"No suitable Azure Linux images found for {args.language}")
        if args.version:
            print(f"with version {args.version}")
        print("\nTry:")
        print("- Running --scan to update the database")
        print("- Using a different version")
        print("- Checking if the language is supported")
        return 1

    # Format output
    if args.format == "json":
        output = format_json_output(recommendations[: args.limit])
    elif args.format == "dockerfile":
        output = format_dockerfile_output(recommendations[0])  # Best recommendation
    else:
        output = engine.format_recommendations(recommendations, args.limit)

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Recommendations saved to {args.output}")
    else:
        print(output)

    return 0


def handle_analyze(args) -> int:
    """Handle image analysis requests"""

    print(f"Analyzing image: {args.analyze}")

    try:
        # Basic image analysis
        analyzer = ImageAnalyzer(args.analyze)
        result = analyzer.analyze()

        # Add vulnerability scanning
        scanner = MCRRegistryScanner(comprehensive_scan=args.comprehensive)
        vulnerability_data = scanner.scan_vulnerabilities(
            args.analyze, args.comprehensive
        )
        result.update(vulnerability_data)

        if args.format == "json":
            output = json.dumps(result, indent=2)
        else:
            output = format_analysis_output(result)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Analysis saved to {args.output}")
        else:
            print(output)

        return 0

    except Exception as e:
        print(f"Error analyzing image: {e}")
        return 1


def handle_reset_database(args) -> int:
    """Handle database reset requests"""

    # Setup logging
    logger = setup_logging(getattr(args, "verbose", False))
    logger.info("CLI: Starting database reset operation")

    db_path = args.database

    print(f"🗑️  Resetting database: {db_path}")
    print("⚠️  WARNING: This will permanently delete all data in the database!")

    # Check if database exists
    if not os.path.exists(db_path):
        logger.info(f"Database file does not exist: {db_path}")
        print(f"📝 Database file does not exist: {db_path}")
        print("✅ No action needed - database is already clear")
        return 0

    # Ask for confirmation (unless running in non-interactive mode)
    try:
        if sys.stdin.isatty():  # Check if running interactively
            confirmation = input("Type 'YES' to confirm database reset: ")
            if confirmation != "YES":
                logger.info("Database reset cancelled by user")
                print("❌ Database reset cancelled")
                return 0
        else:
            logger.info("Running in non-interactive mode, proceeding with reset")
            print("🤖 Running in non-interactive mode, proceeding with reset...")
    except (EOFError, KeyboardInterrupt):
        logger.info("Database reset cancelled by user")
        print("\n❌ Database reset cancelled")
        return 0

    try:
        # Import here to avoid circular dependency
        from database import ImageDatabase

        # Connect to database and get statistics before clearing
        logger.info(f"Connecting to database: {db_path}")
        db = ImageDatabase(db_path)

        # Get current statistics
        try:
            current_stats = db.get_vulnerability_statistics()
            total_images = current_stats.get("total_images", 0)
            logger.info(f"Current database contains {total_images} images")
            print(f"📊 Current database contains {total_images} images")
        except Exception as e:
            logger.warning(f"Could not get current statistics: {e}")
            print(f"⚠️  Could not get current statistics: {e}")
            total_images = "unknown"

        # Reset the database
        logger.info("Performing database reset")
        print("🔄 Clearing all data from database...")

        reset_stats = db.reset_database()

        # Log the results
        cleared_records = reset_stats["clear_stats"]["total_records_cleared"]
        logger.info(
            f"Database reset completed. Cleared {cleared_records} total records"
        )

        print("✅ Database reset completed successfully!")
        print(f"📊 Reset Summary:")
        print(f"   🗑️  Total records cleared: {cleared_records}")

        if reset_stats["clear_stats"]["stats_before"]:
            stats_before = reset_stats["clear_stats"]["stats_before"]
            print(f"   📋 Details:")
            for table, count in stats_before.items():
                if count > 0:
                    print(f"      - {table}: {count}")

        print(f"   🕐 Reset timestamp: {reset_stats['reset_timestamp']}")
        print(f"   📁 Database location: {db_path}")
        print("\n🎉 Database is now empty and ready for new data!")
        print("💡 You can now run scans to populate it with fresh image data.")

        # Close database connection
        db.close()
        logger.info("Database reset operation completed successfully")

        return 0

    except Exception as e:
        logger.error(f"Error during database reset: {e}")
        print(f"❌ Error during database reset: {e}")
        return 1


def handle_scan_image(args) -> int:
    """Handle scanning a single image"""

    # Setup logging
    logger = setup_logging(getattr(args, "verbose", False))
    logger.info(f"CLI: Starting image scan for {args.scan_image}")

    print(f"Scanning image: {args.scan_image}")

    try:
        db_path = args.database
        logger.info(f"Using database path: {db_path}")

        scanner = MCRRegistryScanner(
            db_path=db_path,
            comprehensive_scan=args.comprehensive,
            cleanup_images=not args.no_cleanup,
            update_existing=args.update_existing,
        )

        logger.info(
            f"Scanner configuration: comprehensive={args.comprehensive}, cleanup={not args.no_cleanup}, update_existing={args.update_existing}"
        )

        results = scanner.scan_image(args.scan_image)

        if not results:
            logger.warning(f"No data found for image: {args.scan_image}")
            print(f"No data found for image: {args.scan_image}")
            return 1

        logger.info(f"Scan completed successfully: {len(results)} images processed")
        print(f"✅ Scan completed! Found {len(results)} images")
        print(f"📊 SQLite Database: {db_path}")

        # Show database statistics
        try:
            stats = scanner.get_database_stats()
            db_stats = stats["database_stats"]
            logger.info(
                f"Database statistics: {db_stats.get('total_images', 0)} total images"
            )
            print(f"\n📊 Database Statistics:")
            print(f"  Total images in database: {db_stats.get('total_images', 0)}")
            print(f"  Zero vulnerability images: {db_stats.get('zero_vuln_images', 0)}")
            print(f"  Safe images (no critical/high): {db_stats.get('safe_images', 0)}")
            print(
                f"  Average vulnerabilities per image: {db_stats.get('avg_vulnerabilities', 0):.1f}"
            )

            if args.comprehensive:
                print(f"  Images with secrets: [Trivy data available]")
                print(f"  Images with config issues: [Trivy data available]")

        except Exception as e:
            logger.error(f"Could not retrieve database statistics: {e}")
            print(f"⚠️  Could not retrieve database statistics: {e}")

        # Close database connection
        scanner.db.close()
        logger.info("Image scan completed successfully")

        return 0

    except Exception as e:
        logger.error(f"Error during image scan: {e}")
        print(f"Error during scan: {e}")
        return 1


def handle_scan_repo(args) -> int:
    """Handle scanning a single repository"""

    # Setup logging
    logger = setup_logging(getattr(args, "verbose", False))
    logger.info(f"CLI: Starting repository scan for {args.scan_repo}")

    print(f"Scanning repository: {args.scan_repo}")

    # Parse the repository path to handle both formats:
    # - Full image path: mcr.microsoft.com/azurelinux/base/python
    # - MCR repository path: azurelinux/base/python
    try:
        if "mcr.microsoft.com/" in args.scan_repo:
            # Extract repository from full image path
            repository = args.scan_repo.replace("mcr.microsoft.com/", "")
            logger.info(f"Extracted repository path: {repository}")
            print(f"  📋 Extracted repository path: {repository}")
        else:
            # Use as-is (assume it's already a repository path)
            repository = args.scan_repo

        # Remove any tag if accidentally included
        if ":" in repository:
            repository = repository.split(":")[0]
            logger.info(f"Removed tag from repository path: {repository}")
            print(f"  📋 Removed tag from repository path: {repository}")

    except Exception as e:
        logger.error(f"Error parsing repository path '{args.scan_repo}': {e}")
        print(f"  ❌ Error parsing repository path '{args.scan_repo}': {e}")
        return 1

    try:
        db_path = args.database
        logger.info(f"Using database path: {db_path}")

        scanner = MCRRegistryScanner(
            db_path=db_path,
            comprehensive_scan=args.comprehensive,
            cleanup_images=not args.no_cleanup,
            update_existing=args.update_existing,
            max_tags_per_repo=args.max_tags or 999999,  # Large number for "all"
        )

        logger.info(
            f"Scanner configuration: comprehensive={args.comprehensive}, cleanup={not args.no_cleanup}, update_existing={args.update_existing}, max_tags={args.max_tags or 'unlimited'}"
        )

        results = scanner.scan_repository(repository)

        logger.info(f"Repository scan completed: {len(results)} images processed")
        print(f"✅ Scan completed! Found {len(results)} images in {repository}")
        print(f"📊 SQLite Database: {db_path}")

        # Show database statistics
        try:
            stats = scanner.get_database_stats()
            db_stats = stats["database_stats"]
            logger.info(
                f"Database statistics: {db_stats.get('total_images', 0)} total images"
            )
            print(f"\n📊 Database Statistics:")
            print(f"  Total images in database: {db_stats.get('total_images', 0)}")
            print(f"  Zero vulnerability images: {db_stats.get('zero_vuln_images', 0)}")
            print(f"  Safe images (no critical/high): {db_stats.get('safe_images', 0)}")
            print(
                f"  Average vulnerabilities per image: {db_stats.get('avg_vulnerabilities', 0):.1f}"
            )

            if args.comprehensive:
                print(f"  Images with secrets: [Trivy data available]")
                print(f"  Images with config issues: [Trivy data available]")

        except Exception as e:
            logger.error(f"Could not retrieve database statistics: {e}")
            print(f"⚠️  Could not retrieve database statistics: {e}")

        # Close database connection
        scanner.db.close()
        logger.info("Repository scan completed successfully")

        return 0

    except Exception as e:
        logger.error(f"Error during repository scan: {e}")
        print(f"Error during scan: {e}")
        return 1


def handle_scan_all_mcr(args) -> int:
    """Handle registry scanning requests"""

    # Setup logging
    logger = setup_logging(getattr(args, "verbose", False))
    logger.info(f"CLI: Starting scan of all MCR repositories")

    print("Scanning Azure Linux registry...")
    if args.comprehensive:
        logger.info("Comprehensive security scanning enabled")
        print(
            "Comprehensive security scanning enabled (includes secrets, misconfigurations, and licenses)"
        )
    if not args.no_cleanup:
        logger.info("Docker image cleanup enabled")
        print(
            "🧹 Docker image cleanup enabled (images will be removed after analysis to save space)"
        )
    else:
        logger.info("Docker image cleanup disabled")
        print("⚠️  Docker image cleanup disabled (images will be kept locally)")

    if args.update_existing:
        logger.info("Update mode: Will rescan existing images")
        print("🔄 Update mode: Will rescan and update existing images in database")
    else:
        logger.info("Skip mode: Will skip existing images")
        print(
            "⏭️  Skip mode: Will skip images already in database (use --update-existing to rescan)"
        )
        print(
            "   💡 Duplicate prevention: Only newer scans or changed data will update existing images"
        )

    print("This may take several minutes...")

    try:
        db_path = args.database
        # Handle special case of scanning all tags
        max_tags = None if args.max_tags == 0 else args.max_tags

        logger.info(f"Using database path: {db_path}")
        logger.info(f"Max tags per repository: {max_tags or 'unlimited'}")

        scanner = MCRRegistryScanner(
            db_path=db_path,
            comprehensive_scan=args.comprehensive,
            cleanup_images=not args.no_cleanup,
            update_existing=args.update_existing,
            max_tags_per_repo=max_tags or 999999,  # Large number for "all"
        )
        results = scanner.scan_all_repositories()

        logger.info(f"All repositories scan completed: {len(results)} images processed")
        print(f"✅ Scan completed! Found {len(results)} images")
        print(f"📊 SQLite Database: {db_path}")

        # Show database statistics
        try:
            stats = scanner.get_database_stats()
            db_stats = stats["database_stats"]
            logger.info(
                f"Final database statistics: {db_stats.get('total_images', 0)} total images"
            )
            print(f"\n📊 Database Statistics:")
            print(f"  Total images in database: {db_stats.get('total_images', 0)}")
            print(f"  Zero vulnerability images: {db_stats.get('zero_vuln_images', 0)}")
            print(f"  Safe images (no critical/high): {db_stats.get('safe_images', 0)}")
            print(
                f"  Average vulnerabilities per image: {db_stats.get('avg_vulnerabilities', 0):.1f}"
            )

            if args.comprehensive:
                print(f"  Images with secrets: [Trivy data available]")
                print(f"  Images with config issues: [Trivy data available]")

            # Show language summary
            language_stats = stats.get("language_summary", [])
            if language_stats:
                print(f"\n🚀 Top Languages in Database:")
                for lang_stat in language_stats[:5]:  # Top 5
                    print(
                        f"  {lang_stat['language']}: {lang_stat['image_count']} images "
                        f"(avg {lang_stat['avg_vulnerabilities']:.1f} vulns)"
                    )

        except Exception as e:
            logger.error(f"Could not retrieve database statistics: {e}")
            print(f"⚠️  Could not retrieve database statistics: {e}")

        # Close database connection
        scanner.db.close()
        logger.info("All repositories scan completed successfully")

        return 0

    except Exception as e:
        logger.error(f"Error during all repositories scan: {e}")
        print(f"Error during scan: {e}")
        return 1


def format_json_output(recommendations) -> str:
    """Format recommendations as JSON"""

    output = []
    for rec in recommendations:
        output.append(
            {
                "image": rec.image_name,
                "score": rec.score,
                "language_match": rec.language_match,
                "version_match": rec.version_match,
                "reasoning": rec.reasoning,
                "size_mb": rec.analysis_data.get("manifest", {}).get("size", 0)
                / (1024 * 1024),
                "languages": rec.analysis_data.get("languages", []),
                "capabilities": rec.analysis_data.get("capabilities", []),
            }
        )

    return json.dumps(output, indent=2)


def format_dockerfile_output(recommendation) -> str:
    """Format recommendation as Dockerfile snippet"""

    return f"""# Recommended Azure Linux base image
FROM {recommendation.image_name}

# Image score: {recommendation.score:.2f}/1.00
# Reasons: {', '.join(recommendation.reasoning)}

# Your application code here
COPY . /app
WORKDIR /app

# Example build commands (adjust as needed)
# RUN pip install -r requirements.txt  # For Python
# RUN npm install                      # For Node.js
# RUN mvn clean package               # For Java

CMD ["your-app-command"]
"""


def format_analysis_output(analysis) -> str:
    """Format analysis results as human-readable text"""

    output = []
    output.append(f"📊 Analysis Results for {analysis['image']}")
    output.append("=" * 60)

    # Base OS
    base_os = analysis.get("base_os", {})
    if base_os:
        output.append(
            f"\n🖥️  Base OS: {base_os.get('name', 'unknown')} {base_os.get('version', '')}"
        )

    # Languages
    languages = analysis.get("languages", [])
    if languages:
        output.append(f"\n🚀 Languages:")
        for lang in languages:
            verified = "✅" if lang.get("verified", False) else "📦"
            output.append(
                f"   {verified} {lang['language']} {lang.get('version', 'unknown')}"
            )

    # Package Managers
    package_managers = analysis.get("package_managers", [])
    if package_managers:
        output.append(f"\n📦 Package Managers:")
        for pm in package_managers:
            output.append(f"   • {pm['name']} {pm.get('version', '')}")

    # Capabilities
    capabilities = analysis.get("capabilities", [])
    if capabilities:
        output.append(f"\n⚡ Capabilities: {', '.join(capabilities)}")

    # Size
    manifest = analysis.get("manifest", {})
    if manifest.get("size"):
        size_mb = manifest["size"] / (1024 * 1024)
        output.append(
            f"\n💾 Size: {size_mb:.1f} MB ({manifest.get('layers', 0)} layers)"
        )

    # Recommendations
    recommendations = analysis.get("recommendations", {})
    if recommendations:
        best_for = recommendations.get("best_for", [])
        if best_for:
            output.append(f"\n🎯 Best for: {', '.join(best_for[:5])}")

        frameworks = recommendations.get("compatible_frameworks", [])
        if frameworks:
            output.append(f"🔧 Compatible frameworks: {', '.join(frameworks[:5])}")

    # Vulnerability Information
    vulnerabilities = analysis.get("vulnerabilities", {})
    if vulnerabilities:
        output.append(f"\n🔐 Security Scan Results:")

        total_vulns = vulnerabilities.get("total", 0)
        critical = vulnerabilities.get("critical", 0)
        high = vulnerabilities.get("high", 0)
        medium = vulnerabilities.get("medium", 0)
        low = vulnerabilities.get("low", 0)

        if total_vulns == 0:
            output.append("   ✅ No vulnerabilities found")
        else:
            output.append(f"   📊 Total vulnerabilities: {total_vulns}")
            if critical > 0:
                output.append(f"   🔴 Critical: {critical}")
            if high > 0:
                output.append(f"   🟠 High: {high}")
            if medium > 0:
                output.append(f"   🟡 Medium: {medium}")
            if low > 0:
                output.append(f"   🔵 Low: {low}")

        scanner = vulnerabilities.get("scanner")
        if scanner:
            output.append(f"   🔍 Scanned with: {scanner}")

        scan_time = vulnerabilities.get("scan_timestamp")
        if scan_time:
            output.append(f"   ⏰ Scan time: {scan_time}")

    # Comprehensive Security (Trivy results)
    comprehensive_security = analysis.get("comprehensive_security", {})
    if comprehensive_security:
        output.append(f"\n🛡️  Comprehensive Security Scan:")

        secrets = comprehensive_security.get("secrets_found", 0)
        configs = comprehensive_security.get("config_issues", 0)
        licenses = comprehensive_security.get("license_issues", 0)

        if secrets == 0 and configs == 0 and licenses == 0:
            output.append("   ✅ No security issues found")
        else:
            if secrets > 0:
                output.append(f"   🔑 Secrets found: {secrets}")
            if configs > 0:
                output.append(f"   ⚙️  Configuration issues: {configs}")
            if licenses > 0:
                output.append(f"   📄 License issues: {licenses}")

    # Vulnerability Details (top 5)
    vulnerability_details = analysis.get("vulnerability_details", [])
    if vulnerability_details:
        output.append(f"\n🔍 Top Vulnerabilities:")
        for vuln in vulnerability_details[:5]:
            severity = vuln.get("severity", "unknown").upper()
            vuln_id = vuln.get("id", "unknown")
            package = vuln.get("package_name", "unknown")
            version = vuln.get("package_version", "unknown")

            severity_emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🔵",
                "NEGLIGIBLE": "⚪",
                "UNKNOWN": "⚫",
            }.get(severity, "⚫")

            output.append(
                f"   {severity_emoji} {vuln_id} - {package}:{version} ({severity})"
            )

            if vuln.get("fixed_version"):
                output.append(f"      Fix: upgrade to {vuln['fixed_version']}")

    output.append("")  # Add blank line at end

    return "\n".join(output)


def handle_scan_image(args) -> int:
    """Handle adding a single image to the database"""

    print(f"Analyzing and adding image to database: {args.scan_image}")

    try:
        # Create scanner instance
        db_path = args.database
        scanner = MCRRegistryScanner(
            db_path=db_path,
            comprehensive_scan=args.comprehensive,
            cleanup_images=not args.no_cleanup,
            update_existing=getattr(args, "update_existing", False),
        )

        # Check if image already exists before doing expensive analysis
        if scanner.db.image_exists(args.scan_image):
            if not getattr(args, "update_existing", False):
                print(f"❌ Error: Image {args.scan_image} already exists in database")
                print(f"💡 Use --update-existing flag to update the existing image")
                print(
                    f"   Example: python src/cli.py --scan-image {args.scan_image} --update-existing --comprehensive"
                )
                scanner.db.close()
                return 1
            else:
                print(f"🔄 Image exists, updating with --update-existing flag...")

        # Analyze the image
        analyzer = ImageAnalyzer(args.scan_image)
        analysis = analyzer.analyze()

        # Add Docker manifest/inspect data for size and layers
        print("📊 Getting image manifest data...")
        manifest_data = get_docker_manifest_data(args.scan_image)
        if manifest_data:
            analysis["manifest"] = manifest_data

        # Add vulnerability scanning
        if args.comprehensive:
            print(
                "🔍 Running comprehensive security scan (Trivy with secrets & misconfigurations)..."
            )
        else:
            print("⚡ Running fast vulnerability scan (Trivy vulnerabilities only)...")

        vulnerability_data = scanner.scan_vulnerabilities(
            args.scan_image, args.comprehensive
        )
        analysis.update(vulnerability_data)

        # Save to database (with duplicate prevention unless update_existing is True)
        force_update = getattr(
            args, "update_existing", False
        )  # Respect the --update-existing flag
        image_id = scanner.db.insert_image_analysis(analysis, force_update=force_update)
        analysis["database_id"] = image_id

        print(f"✅ Image successfully added to database with ID: {image_id}")

        # Display analysis results
        print(format_analysis_output(analysis))

        # Show vulnerability summary
        vuln_data = analysis.get("vulnerabilities", {})
        if vuln_data.get("total", 0) > 0:
            print(f"🛡️  Vulnerability Summary:")
            print(f"   Total: {vuln_data['total']} vulnerabilities")
            print(f"   🔴 Critical: {vuln_data.get('critical', 0)}")
            print(f"   🟠 High: {vuln_data.get('high', 0)}")
            print(f"   🟡 Medium: {vuln_data.get('medium', 0)}")
            print(f"   🔵 Low: {vuln_data.get('low', 0)}")
        else:
            print("✅ No vulnerabilities found!")

        # Show comprehensive security results if available
        if "comprehensive_security" in analysis:
            comp_data = analysis["comprehensive_security"]
            print(f"\n🔒 Security Analysis (Trivy):")
            print(f"   🔍 Secrets found: {comp_data.get('secrets_found', 0)}")
            print(f"   ⚙️  Configuration issues: {comp_data.get('config_issues', 0)}")
            print(f"   📋 License issues: {comp_data.get('license_issues', 0)}")

        # Clean up the Docker image if cleanup is enabled
        if scanner.cleanup_images:
            scanner.cleanup_docker_images([args.scan_image])

        scanner.db.close()
        return 0

    except Exception as e:
        print(f"❌ Error adding image to database: {e}")
        return 1


def get_docker_manifest_data(image_name: str) -> Optional[Dict]:
    """Get Docker image manifest data with size only from docker images command

    Uses docker images command to get compressed size. If docker images fails
    or cannot be parsed, size is set to 0. No fallbacks to docker inspect for size.
    """
    try:
        # First, ensure the image is pulled
        print(f"   🐳 Pulling image {image_name}...")
        pull_result = subprocess.run(
            ["docker", "pull", image_name], capture_output=True, text=True, timeout=300
        )

        if pull_result.returncode != 0:
            print(f"   ⚠️  Failed to pull image: {pull_result.stderr}")
            return None

        # Get image inspect data for layers and metadata
        inspect_result = subprocess.run(
            ["docker", "inspect", image_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if inspect_result.returncode != 0:
            print(f"   ⚠️  Failed to inspect image: {inspect_result.stderr}")
            return None

        inspect_data = json.loads(inspect_result.stdout)[0]

        # Get the size from docker images command with name variation support
        actual_size = 0  # Default to 0

        # Try different image name variations to handle Docker Hub naming
        image_name_variations = [image_name]

        # For Docker Hub images, also try the short name without registry prefix
        if image_name.startswith("docker.io/library/"):
            short_name = image_name.replace("docker.io/library/", "")
            image_name_variations.append(short_name)
        elif image_name.startswith("docker.io/"):
            short_name = image_name.replace("docker.io/", "")
            image_name_variations.append(short_name)

        for variant in image_name_variations:
            images_result = subprocess.run(
                ["docker", "images", variant, "--format", "{{.Size}}"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if images_result.returncode == 0 and images_result.stdout.strip():
                size_str = images_result.stdout.strip()
                try:
                    # Convert human-readable size to bytes (e.g., "211MB" -> bytes)
                    if size_str.endswith("MB"):
                        actual_size = int(float(size_str[:-2]) * 1024 * 1024)
                    elif size_str.endswith("GB"):
                        actual_size = int(float(size_str[:-2]) * 1024 * 1024 * 1024)
                    elif size_str.endswith("KB"):
                        actual_size = int(float(size_str[:-2]) * 1024)
                    elif size_str.endswith("B"):
                        actual_size = int(size_str[:-1])
                    else:
                        # Try to parse as a number (bytes)
                        actual_size = int(float(size_str))
                    print(
                        f"   📏 Parsed size: {actual_size / (1024*1024):.1f} MB from docker images (using name: {variant})"
                    )
                    break  # Success, stop trying other variations
                except (ValueError, IndexError):
                    print(f"   ⚠️  Could not parse size '{size_str}' from {variant}")
                    continue  # Try next variation

        if actual_size == 0:
            print(
                f"   ⚠️  Failed to get size from docker images for all name variations, setting size to 0"
            )

        # Extract relevant manifest data
        manifest_data = {
            "size": actual_size,  # Use docker images size or 0
            "layers": len(inspect_data.get("RootFS", {}).get("Layers", [])),
            "created": inspect_data.get("Created", ""),
            "digest": inspect_data.get("Id", ""),  # Use the Id field for digest
        }

        # Log digest information
        if manifest_data["digest"]:
            print(f"   🔐 Digest (from Id): {manifest_data['digest']}")
        else:
            print(f"   ⚠️  No digest found in Id field")

        if actual_size > 0:
            print(
                f"   📊 Size: {actual_size / (1024*1024):.1f} MB, Layers: {manifest_data['layers']}"
            )
        else:
            print(f"   📊 Size: Unknown (0 bytes), Layers: {manifest_data['layers']}")
        return manifest_data

    except subprocess.TimeoutExpired:
        print("   ⚠️  Docker operation timed out")
        return None
    except Exception as e:
        print(f"   ⚠️  Error getting manifest data: {e}")
        return None


def main():
    """Main entry point"""

    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=True)  # Enable debug logging for CLI operations

    # Handle different operation modes
    if args.analyze:
        return handle_analyze(args)
    elif args.scan:
        return handle_scan_all_mcr(args)
    elif args.scan_repo:
        return handle_scan_repo(args)
    elif args.scan_image:
        return handle_scan_image(args)
    elif args.reset_database or args.clear_database:
        return handle_reset_database(args)
    else:
        # Default to recommend mode
        args.recommend = True
        return handle_recommend(args)


if __name__ == "__main__":
    sys.exit(main())
