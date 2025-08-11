#!/usr/bin/env python3
"""
Database Population Helper

This script provides utilities to populate the SQLite database
with container image analysis data.
"""

import argparse
import sys
from typing import List

from database import ImageDatabase
from image_analyzer import ImageAnalyzer
from registry_scanner import MCRRegistryScanner


def populate_single_image(
    image_name: str, db_path: str = "azure_linux_images.db", comprehensive: bool = False
) -> bool:
    """Analyze and add a single image to the database"""

    print(f"📊 Analyzing single image: {image_name}")

    try:
        # Initialize database
        db = ImageDatabase(db_path)

        # Analyze the image
        analyzer = ImageAnalyzer(image_name)
        analysis = analyzer.analyze()

        # Add vulnerability scanning
        scanner = MCRRegistryScanner(db_path, comprehensive_scan=comprehensive)
        vulnerability_data = scanner.scan_vulnerabilities(image_name, comprehensive)
        analysis.update(vulnerability_data)

        # Save to database
        image_id = db.insert_image_analysis(analysis)

        print(f"✅ Successfully added image with ID: {image_id}")
        print(
            f"   Vulnerabilities: {analysis.get('vulnerabilities', {}).get('total', 0)}"
        )

        if comprehensive and "comprehensive_security" in analysis:
            comp_sec = analysis["comprehensive_security"]
            print(f"   Secrets: {comp_sec.get('secrets_found', 0)}")
            print(f"   Config issues: {comp_sec.get('config_issues', 0)}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Error analyzing {image_name}: {e}")
        return False


def populate_from_image_list(
    image_list_file: str,
    db_path: str = "azure_linux_images.db",
    comprehensive: bool = False,
) -> int:
    """Populate database from a list of image names in a file"""

    print(f"📋 Reading image list from: {image_list_file}")

    try:
        with open(image_list_file, "r") as f:
            images = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

        print(f"Found {len(images)} images to analyze")

        success_count = 0
        for i, image in enumerate(images, 1):
            print(f"\n[{i}/{len(images)}] Processing: {image}")

            if populate_single_image(image, db_path, comprehensive):
                success_count += 1
            else:
                print(f"⚠️  Skipping {image} due to error")

        print(f"\n✅ Successfully processed {success_count}/{len(images)} images")
        return success_count

    except FileNotFoundError:
        print(f"❌ Image list file not found: {image_list_file}")
        return 0
    except Exception as e:
        print(f"❌ Error reading image list: {e}")
        return 0


def create_sample_database(db_path: str = "azure_linux_images.db") -> bool:
    """Create a sample database with some test images for development"""

    print("🧪 Creating sample database for development/testing")

    # Sample images that are commonly available
    sample_images = [
        "mcr.microsoft.com/azurelinux/base/core:3.0",
        "python:3.12-slim",  # For comparison
        "node:18-alpine",  # For comparison
        "ubuntu:22.04",  # For comparison
    ]

    success_count = 0
    for image in sample_images:
        print(f"\n📊 Adding sample image: {image}")
        if populate_single_image(image, db_path, comprehensive=False):
            success_count += 1

    print(f"\n✅ Sample database created with {success_count} images")
    return success_count > 0


def migrate_from_json(json_file: str, db_path: str = "azure_linux_images.db") -> int:
    """Migrate data from old JSON database format to SQLite"""

    print(f"🔄 Migrating data from JSON file: {json_file}")

    try:
        import json

        with open(json_file, "r") as f:
            data = json.load(f)

        images = data.get("images", [])
        print(f"Found {len(images)} images in JSON file")

        db = ImageDatabase(db_path)
        success_count = 0

        for i, image_data in enumerate(images, 1):
            try:
                print(
                    f"[{i}/{len(images)}] Migrating: {image_data.get('image', 'unknown')}"
                )

                # Insert the analysis data
                image_id = db.insert_image_analysis(image_data)
                success_count += 1

            except Exception as e:
                print(f"⚠️  Error migrating image {i}: {e}")
                continue

        db.close()
        print(f"✅ Successfully migrated {success_count}/{len(images)} images")
        return success_count

    except FileNotFoundError:
        print(f"❌ JSON file not found: {json_file}")
        return 0
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return 0


def show_database_info(db_path: str = "azure_linux_images.db"):
    """Show information about the current database"""

    print(f"📊 Database Information: {db_path}")

    try:
        db = ImageDatabase(db_path)

        # Get statistics
        stats = db.get_vulnerability_statistics()
        language_stats = db.get_languages_summary()

        print(f"\n🗄️  Database Statistics:")
        print(f"   Total images: {stats.get('total_images', 0)}")
        print(f"   Zero vulnerability images: {stats.get('zero_vuln_images', 0)}")
        print(f"   Safe images (no critical/high): {stats.get('safe_images', 0)}")
        print(f"   Average vulnerabilities: {stats.get('avg_vulnerabilities', 0):.1f}")

        print(f"\n🚀 Language Summary:")
        for lang in language_stats[:10]:
            print(f"   {lang['language']}: {lang['image_count']} images")

        # Query some recent images
        recent_images = db.query_secure_images(max_critical=0, max_high=0)
        if recent_images:
            print(f"\n🛡️  Most Secure Images (no critical/high vulnerabilities):")
            for img in recent_images[:5]:
                languages = img.get("languages", "none")
                print(f"   {img['name']} - Languages: {languages}")

        db.close()

    except Exception as e:
        print(f"❌ Error reading database: {e}")


def main():
    """Main entry point for database population utilities"""

    parser = argparse.ArgumentParser(
        description="Populate SQLite database with container image analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --single python:3.12
  %(prog)s --image-list images.txt --comprehensive
  %(prog)s --sample-db
  %(prog)s --migrate old_database.json
  %(prog)s --info
        """,
    )

    # Action options
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--single", metavar="IMAGE", help="Analyze single image")
    action.add_argument("--image-list", metavar="FILE", help="Analyze images from file")
    action.add_argument(
        "--sample-db", action="store_true", help="Create sample database"
    )
    action.add_argument(
        "--migrate", metavar="JSON_FILE", help="Migrate from JSON database"
    )
    action.add_argument("--info", action="store_true", help="Show database information")

    # Options
    parser.add_argument(
        "--db-path", default="azure_linux_images.db", help="Path to SQLite database"
    )
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Enable comprehensive security scanning",
    )

    args = parser.parse_args()

    try:
        if args.single:
            success = populate_single_image(
                args.single, args.db_path, args.comprehensive
            )
            sys.exit(0 if success else 1)

        elif args.image_list:
            count = populate_from_image_list(
                args.image_list, args.db_path, args.comprehensive
            )
            sys.exit(0 if count > 0 else 1)

        elif args.sample_db:
            success = create_sample_database(args.db_path)
            sys.exit(0 if success else 1)

        elif args.migrate:
            count = migrate_from_json(args.migrate, args.db_path)
            sys.exit(0 if count > 0 else 1)

        elif args.info:
            show_database_info(args.db_path)
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
