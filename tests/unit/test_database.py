"""
Unit tests for database module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from database import ImageDatabase


class TestImageDatabase:
    """Test cases for ImageDatabase class."""

    def test_init_creates_tables(self, temp_db):
        """Test that database initialization creates all required tables."""
        # Check that tables exist
        cursor = temp_db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "images",
            "languages",
            "package_managers",
            "vulnerabilities",
            "system_packages",
            "capabilities",
            "security_findings",
        ]

        for table in expected_tables:
            assert table in tables

    def test_add_image(self, temp_db, sample_image_data):
        """Test adding an image to the database."""
        image_id = temp_db.insert_image_analysis(sample_image_data)
        assert image_id is not None
        assert isinstance(image_id, int)

        # Verify image was added
        cursor = temp_db.conn.execute(
            "SELECT name FROM images WHERE id = ?", (image_id,)
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == sample_image_data["image"]

    def test_get_image_by_name(self, temp_db, sample_image_data):
        """Test retrieving an image by name."""
        # Add image first
        temp_db.insert_image_analysis(sample_image_data)

        # Retrieve it
        result = temp_db.get_image_by_exact_name(sample_image_data["image"])
        assert result is not None
        assert result["name"] == sample_image_data["image"]

    def test_search_images_by_language(self, temp_db, sample_image_data):
        """Test searching images by language."""
        # Add image first
        temp_db.insert_image_analysis(sample_image_data)

        # Search for Python images
        results = temp_db.search_images(query="", language="python")
        assert len(results) > 0
        assert any(img["name"] == sample_image_data["image"] for img in results)

    def test_get_vulnerability_statistics(self, temp_db, sample_image_data):
        """Test getting vulnerability statistics."""
        # Add image first
        temp_db.insert_image_analysis(sample_image_data)

        stats = temp_db.get_vulnerability_statistics()
        assert "total_images" in stats
        assert "zero_vuln_images" in stats
        assert "safe_images" in stats
        assert stats["total_images"] >= 1

    def test_update_existing_image(self, temp_db, sample_image_data):
        """Test updating an existing image."""
        # Add image first
        image_id = temp_db.insert_image_analysis(sample_image_data)

        # Modify data and update
        sample_image_data["vulnerabilities"]["total"] = 5
        temp_db.insert_image_analysis(
            sample_image_data
        )  # Should update, not create new

        # Verify only one image exists
        cursor = temp_db.conn.execute("SELECT COUNT(*) FROM images")
        count = cursor.fetchone()[0]
        assert count == 1

    def test_get_languages_summary(self, temp_db, sample_image_data):
        """Test getting languages summary."""
        # Add image first
        temp_db.insert_image_analysis(sample_image_data)

        summary = temp_db.get_languages_summary()
        assert len(summary) > 0
        assert any(lang["language"] == "python" for lang in summary)

    def test_close_connection(self, temp_db):
        """Test closing database connection."""
        temp_db.close()
        # After closing, operations should fail
        with pytest.raises(Exception):
            temp_db.conn.execute("SELECT 1")

    def test_add_image_with_missing_data(self, temp_db):
        """Test adding image with minimal required data."""
        minimal_data = {
            "image": "test/minimal:latest",
            "tag": "latest",
            "languages": [],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
        }

        image_id = temp_db.insert_image_analysis(minimal_data)
        assert image_id is not None

    def test_search_with_filters(self, temp_db, sample_image_data):
        """Test searching with various filters."""
        # Add image first
        temp_db.insert_image_analysis(sample_image_data)

        # Test language filter
        results = temp_db.search_images(query="", language="python")
        assert len(results) > 0

        # Test name search
        results = temp_db.search_images(query="azurelinux", language="")
        assert len(results) > 0

        # Test combined search
        results = temp_db.search_images(query="python", language="python")
        assert isinstance(results, list)
