"""
Unit tests for the nightly recommendations markdown generation.
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from generate_nightly_recommendations_md import (
    format_digest,
    get_languages,
    get_top_images_for_language,
    human_size,
)


class TestFormatDigest:
    """Test cases for digest formatting."""

    def test_format_digest_sha256(self):
        """Test formatting a standard sha256 digest."""
        digest = (
            "sha256:b834bbdd622c9200120f98468389132fcc7a94b19f5b1f24e7b3d7da25f0fbc0"
        )
        result = format_digest(digest)
        assert result == "sha256:b834bbdd622c"
        assert len(result) == 19  # "sha256:" (7) + 12 hash chars

    def test_format_digest_short_hash(self):
        """Test formatting a sha256 digest with shorter hash."""
        digest = "sha256:abc123"
        result = format_digest(digest)
        assert result == "sha256:abc123"

    def test_format_digest_none(self):
        """Test formatting None digest."""
        result = format_digest(None)
        assert result == ""

    def test_format_digest_empty_string(self):
        """Test formatting empty string digest."""
        result = format_digest("")
        assert result == ""

    def test_format_digest_non_sha256(self):
        """Test formatting a non-sha256 digest."""
        digest = "other:1234567890abcdef1234567890"
        result = format_digest(digest)
        # For non-sha256 digests, returns first 19 characters
        assert result == "other:1234567890abc"
        assert len(result) == 19


class TestHumanSize:
    """Test cases for human-readable size formatting."""

    def test_human_size_bytes(self):
        """Test size formatting for bytes."""
        assert human_size(500) == "500 B"

    def test_human_size_megabytes(self):
        """Test size formatting for megabytes."""
        assert human_size(1024 * 1024) == "1.0 MB"
        assert human_size(100 * 1024 * 1024) == "100.0 MB"

    def test_human_size_gigabytes(self):
        """Test size formatting for gigabytes."""
        assert human_size(1024 * 1024 * 1024) == "1.00 GB"

    def test_human_size_none(self):
        """Test size formatting for None value."""
        assert human_size(None) == "?"


class TestGetLanguages:
    """Test cases for getting languages from the database."""

    def test_get_languages_with_data(self):
        """Test getting languages from a database with data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            conn = sqlite3.connect(str(db_path))

            # Create tables
            conn.execute(
                """
                CREATE TABLE images (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    registry TEXT,
                    repository TEXT,
                    tag TEXT,
                    digest TEXT,
                    size_bytes INTEGER,
                    total_vulnerabilities INTEGER DEFAULT 0,
                    critical_vulnerabilities INTEGER DEFAULT 0,
                    high_vulnerabilities INTEGER DEFAULT 0
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE languages (
                    id INTEGER PRIMARY KEY,
                    image_id INTEGER,
                    language TEXT,
                    version TEXT
                )
            """
            )

            # Insert test data
            conn.execute(
                "INSERT INTO images (name, registry, repository, tag, digest, size_bytes) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    "test/python:3.12",
                    "test",
                    "python",
                    "3.12",
                    "sha256:abc123",
                    100000000,
                ),
            )
            conn.execute(
                "INSERT INTO languages (image_id, language, version) VALUES (?, ?, ?)",
                (1, "python", "3.12.0"),
            )
            conn.commit()

            languages = get_languages(conn)
            assert "python" in languages
            conn.close()

    def test_get_languages_empty_db(self):
        """Test getting languages from an empty database."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            conn = sqlite3.connect(str(db_path))

            conn.execute(
                """
                CREATE TABLE languages (
                    id INTEGER PRIMARY KEY,
                    image_id INTEGER,
                    language TEXT,
                    version TEXT
                )
            """
            )
            conn.commit()

            languages = get_languages(conn)
            assert languages == []
            conn.close()


class TestGetTopImagesForLanguage:
    """Test cases for getting top images for a language."""

    def test_get_top_images_includes_digest(self):
        """Test that top images query includes digest field."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            conn = sqlite3.connect(str(db_path))

            # Create tables
            conn.execute(
                """
                CREATE TABLE images (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    registry TEXT,
                    repository TEXT,
                    tag TEXT,
                    digest TEXT,
                    size_bytes INTEGER,
                    total_vulnerabilities INTEGER DEFAULT 0,
                    critical_vulnerabilities INTEGER DEFAULT 0,
                    high_vulnerabilities INTEGER DEFAULT 0
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE languages (
                    id INTEGER PRIMARY KEY,
                    image_id INTEGER,
                    language TEXT,
                    version TEXT
                )
            """
            )

            # Insert test data with digest
            test_digest = "sha256:testdigest123456789"
            conn.execute(
                """
                INSERT INTO images (name, registry, repository, tag, digest, size_bytes,
                                    total_vulnerabilities, critical_vulnerabilities, high_vulnerabilities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "mcr.microsoft.com/test/python:3.12",
                    "mcr.microsoft.com",
                    "test/python",
                    "3.12",
                    test_digest,
                    100000000,
                    5,
                    0,
                    1,
                ),
            )
            conn.execute(
                "INSERT INTO languages (image_id, language, version) VALUES (?, ?, ?)",
                (1, "python", "3.12.0"),
            )
            conn.commit()

            results = get_top_images_for_language(conn, "python", 10)

            assert len(results) == 1
            assert "digest" in results[0]
            assert results[0]["digest"] == test_digest
            assert results[0]["image"] == "mcr.microsoft.com/test/python:3.12"
            assert results[0]["version"] == "3.12.0"
            assert results[0]["total"] == 5
            assert results[0]["critical"] == 0
            assert results[0]["high"] == 1

            conn.close()

    def test_get_top_images_null_digest(self):
        """Test that top images handles NULL digest gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test.db"
            conn = sqlite3.connect(str(db_path))

            # Create tables
            conn.execute(
                """
                CREATE TABLE images (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    registry TEXT,
                    repository TEXT,
                    tag TEXT,
                    digest TEXT,
                    size_bytes INTEGER,
                    total_vulnerabilities INTEGER DEFAULT 0,
                    critical_vulnerabilities INTEGER DEFAULT 0,
                    high_vulnerabilities INTEGER DEFAULT 0
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE languages (
                    id INTEGER PRIMARY KEY,
                    image_id INTEGER,
                    language TEXT,
                    version TEXT
                )
            """
            )

            # Insert test data without digest
            conn.execute(
                """
                INSERT INTO images (name, registry, repository, tag, digest, size_bytes,
                                    total_vulnerabilities, critical_vulnerabilities, high_vulnerabilities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "mcr.microsoft.com/test/node:20",
                    "mcr.microsoft.com",
                    "test/node",
                    "20",
                    None,
                    80000000,
                    0,
                    0,
                    0,
                ),
            )
            conn.execute(
                "INSERT INTO languages (image_id, language, version) VALUES (?, ?, ?)",
                (1, "node", "20.0.0"),
            )
            conn.commit()

            results = get_top_images_for_language(conn, "node", 10)

            assert len(results) == 1
            assert "digest" in results[0]
            assert results[0]["digest"] is None

            conn.close()
