#!/usr/bin/env python3
"""
Database Reset Script

This script provides functionality to reset the Azure Linux container image database.
It can be used as a standalone script or imported by other modules.
"""

import os
import sys
from pathlib import Path
from typing import Dict

from database import ImageDatabase


def reset_database(db_path: str, force: bool = False) -> Dict:
    """
    Reset the database by clearing all data.

    Args:
        db_path: Path to the database file
        force: If True, skip confirmation prompt

    Returns:
        Dictionary with reset statistics and status
    """

    print(f"🗑️  Resetting database: {db_path}")

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"📝 Database file does not exist: {db_path}")
        print("✅ No action needed - database is already clear")
        return {
            "status": "no_action",
            "message": "Database file does not exist",
            "db_path": db_path,
        }

    # Ask for confirmation unless forced
    if not force:
        print("⚠️  WARNING: This will permanently delete all data in the database!")
        try:
            if sys.stdin.isatty():  # Check if running interactively
                confirmation = input("Type 'YES' to confirm database reset: ")
                if confirmation != "YES":
                    print("❌ Database reset cancelled")
                    return {
                        "status": "cancelled",
                        "message": "Reset cancelled by user",
                        "db_path": db_path,
                    }
            else:
                print("🤖 Running in non-interactive mode, proceeding with reset...")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Database reset cancelled")
            return {
                "status": "cancelled",
                "message": "Reset cancelled by user interrupt",
                "db_path": db_path,
            }

    try:
        # Connect to database and get statistics before clearing
        print("📊 Getting current database statistics...")
        db = ImageDatabase(db_path)

        # Get current statistics
        try:
            current_stats = db.get_vulnerability_statistics()
            total_images = current_stats.get("total_images", 0)
            print(f"📊 Current database contains {total_images} images")
        except Exception as e:
            print(f"⚠️  Could not get current statistics: {e}")
            total_images = "unknown"

        # Reset the database
        print("🔄 Clearing all data from database...")
        reset_stats = db.reset_database()

        # Log the results
        cleared_records = reset_stats["clear_stats"]["total_records_cleared"]

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

        return {
            "status": "success",
            "message": "Database reset completed successfully",
            "db_path": db_path,
            "reset_stats": reset_stats,
            "cleared_records": cleared_records,
        }

    except Exception as e:
        error_msg = f"Error during database reset: {e}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "db_path": db_path,
            "error": str(e),
        }


def main():
    """Main entry point for standalone script execution"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Reset the Azure Linux container image database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Reset default database with confirmation
  %(prog)s --database /path/to/custom.db     # Reset custom database location
  %(prog)s --force                           # Reset without confirmation prompt
  %(prog)s --database azure_linux_images.db --force  # Reset specific DB without prompt
        """,
    )

    parser.add_argument(
        "--database",
        "-d",
        default="azure_linux_images.db",
        help="Path to database file (default: azure_linux_images.db)",
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompt and reset immediately",
    )

    args = parser.parse_args()

    # Use the database path directly (should already be SQLite)
    db_path = args.database

    print("🔄 Azure Linux Container Image Database Reset Tool")
    print("=" * 50)

    result = reset_database(db_path, force=args.force)

    if result["status"] == "success":
        print(f"\n✅ Success: {result['message']}")
        return 0
    elif result["status"] == "cancelled":
        print(f"\n❌ Cancelled: {result['message']}")
        return 1
    elif result["status"] == "no_action":
        print(f"\n📝 No action: {result['message']}")
        return 0
    else:
        print(f"\n❌ Error: {result['message']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
