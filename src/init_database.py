#!/usr/bin/env python3
"""
Database Initialization Script

This script creates a fresh SQLite database with all required tables
for the Azure Linux container image analysis system.
"""

import os
import sys
from pathlib import Path
from database import ImageDatabase

def main():
    """Initialize a fresh database"""
    
    # Database path (in the parent directory)
    db_path = Path(__file__).parent.parent / "azure_linux_images.db"
    
    print(f"Initializing database at: {db_path}")
    
    # Remove existing database if it exists
    if db_path.exists():
        print(f"Removing existing database: {db_path}")
        db_path.unlink()
    
    # Create new database
    print("Creating new database with all tables...")
    db = ImageDatabase(str(db_path))
    
    # Verify tables were created
    cursor = db.conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n✅ Database initialized successfully!")
    print(f"📁 Location: {db_path}")
    print(f"📊 Tables created: {len(tables)}")
    
    for table in tables:
        print(f"  - {table}")
    
    # Get table info for the main images table
    cursor = db.conn.execute("PRAGMA table_info(images)")
    columns = cursor.fetchall()
    
    print(f"\n🗂️  Main 'images' table has {len(columns)} columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Close database
    db.close()
    
    print(f"\n🎉 Database is ready for use!")
    print(f"You can now run scans to populate it with image data.")

if __name__ == "__main__":
    main()
