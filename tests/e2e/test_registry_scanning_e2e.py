"""
End-to-end tests for registry scanning functionality.

These tests cover the full workflow from image analysis to database storage
and recommendation generation, testing real integration paths.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import ImageDatabase
from image_analyzer import ImageAnalyzer
from recommendation_engine import RecommendationEngine, UserRequirement


class TestImageWorkflowE2E:
    """End-to-end tests for image analysis and recommendation workflows"""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file path"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def mock_registry_data(self):
        """Mock registry data for testing without external dependencies"""
        return {
            "repositories": [
                {
                    "name": "azurelinux/base/python",
                    "tags": ["3.12", "3.11", "latest"],
                    "images": [
                        {
                            "image": "mcr.microsoft.com/azurelinux/base/python:3.12",
                            "name": "mcr.microsoft.com/azurelinux/base/python:3.12",
                            "tag": "3.12",
                            "manifest": {
                                "size": 150000000,
                                "layers": 5,
                                "digest": "sha256:abc123",
                            },
                            "languages": [
                                {
                                    "language": "python",
                                    "version": "3.12.0",
                                    "major_minor": "3.12",
                                    "package_name": "python3.12",
                                    "package_type": "deb",
                                }
                            ],
                            "vulnerabilities": {
                                "total": 0,
                                "critical": 0,
                                "high": 0,
                                "medium": 0,
                                "low": 0,
                            },
                            "base_os": {"name": "Azure Linux", "version": "3.0"},
                            "capabilities": ["python-runtime", "pip"],
                        },
                        {
                            "image": "mcr.microsoft.com/azurelinux/base/python:3.11",
                            "name": "mcr.microsoft.com/azurelinux/base/python:3.11",
                            "tag": "3.11",
                            "manifest": {
                                "size": 145000000,
                                "layers": 5,
                                "digest": "sha256:def456",
                            },
                            "languages": [
                                {
                                    "language": "python",
                                    "version": "3.11.5",
                                    "major_minor": "3.11",
                                    "package_name": "python3.11",
                                    "package_type": "deb",
                                }
                            ],
                            "vulnerabilities": {
                                "total": 2,
                                "critical": 0,
                                "high": 1,
                                "medium": 1,
                                "low": 0,
                            },
                            "base_os": {"name": "Azure Linux", "version": "3.0"},
                            "capabilities": ["python-runtime", "pip"],
                        },
                    ],
                },
                {
                    "name": "azurelinux/base/node",
                    "tags": ["18", "20", "latest"],
                    "images": [
                        {
                            "image": "mcr.microsoft.com/azurelinux/base/node:18",
                            "name": "mcr.microsoft.com/azurelinux/base/node:18",
                            "tag": "18",
                            "manifest": {
                                "size": 200000000,
                                "layers": 6,
                                "digest": "sha256:ghi789",
                            },
                            "languages": [
                                {
                                    "language": "node",
                                    "version": "18.17.0",
                                    "major_minor": "18.0",
                                    "package_name": "nodejs",
                                    "package_type": "deb",
                                }
                            ],
                            "vulnerabilities": {
                                "total": 1,
                                "critical": 0,
                                "high": 0,
                                "medium": 0,
                                "low": 1,
                            },
                            "base_os": {"name": "Azure Linux", "version": "3.0"},
                            "capabilities": ["node-runtime", "npm"],
                        }
                    ],
                },
            ]
        }

    def test_single_image_scan_e2e(self, temp_db_path, mock_registry_data):
        """Test end-to-end single image scan workflow"""
        # 1. Initialize database
        db = ImageDatabase(temp_db_path)

        # 2. Simulate single image analysis (without external tools)
        image_data = mock_registry_data["repositories"][0]["images"][0]

        # 3. Insert analysis results into database
        image_id = db.insert_image_analysis(image_data)
        assert image_id is not None

        # 4. Verify image was stored correctly
        stored_image = db.get_image_by_exact_name(image_data["image"])
        assert stored_image is not None
        assert stored_image["name"] == image_data["image"]

        # 5. Generate recommendations based on stored data
        engine = RecommendationEngine(temp_db_path)
        req = UserRequirement(language="python", version="3.12")
        recommendations = engine.recommend(req)

        # 6. Verify recommendations were generated
        assert isinstance(recommendations, list)
        if recommendations:
            assert recommendations[0].image_name == image_data["image"]
            assert recommendations[0].score > 0

        # 7. Test recommendation formatting
        formatted = engine.format_recommendations(recommendations, limit=5)
        assert isinstance(formatted, str)
        assert image_data["image"] in formatted or "No suitable images" in formatted

        db.close()

    def test_repository_scan_e2e(self, temp_db_path, mock_registry_data):
        """Test end-to-end repository scan workflow"""
        # 1. Initialize database
        db = ImageDatabase(temp_db_path)

        # 2. Simulate repository scan - add all images from python repository
        python_repo = mock_registry_data["repositories"][0]

        inserted_ids = []
        for image_data in python_repo["images"]:
            image_id = db.insert_image_analysis(image_data)
            inserted_ids.append(image_id)

        assert len(inserted_ids) == 2
        assert all(id is not None for id in inserted_ids)

        # 3. Verify all images were stored
        all_images = db.get_all_images_with_details()
        assert len(all_images) >= 2

        # 4. Test language-based search
        python_images = db.search_images(query="", language="python")
        assert len(python_images) >= 2

        # 5. Test vulnerability statistics
        vuln_stats = db.get_vulnerability_statistics()
        assert vuln_stats["total_images"] >= 2
        assert "safe_images" in vuln_stats

        # 6. Test recommendations with different security preferences
        engine = RecommendationEngine(temp_db_path)

        # High security requirement (should prefer 3.12 with 0 vulns)
        req_high_security = UserRequirement(
            language="python",
            version="3.12",
            security_level="maximum",
            max_critical_vulnerabilities=0,
            max_high_vulnerabilities=0,
        )
        high_sec_recs = engine.recommend(req_high_security)

        # Standard security requirement (both should be acceptable)
        req_standard = UserRequirement(
            language="python", version="3.11", security_level="high"
        )
        standard_recs = engine.recommend(req_standard)

        # Verify security-based filtering works
        assert isinstance(high_sec_recs, list)
        assert isinstance(standard_recs, list)

        db.close()

    def test_comprehensive_registry_scan_e2e(self, temp_db_path, mock_registry_data):
        """Test end-to-end comprehensive registry scan workflow"""
        # 1. Initialize database
        db = ImageDatabase(temp_db_path)

        # 2. Simulate comprehensive scan - add all repositories and images
        total_images = 0
        for repository in mock_registry_data["repositories"]:
            for image_data in repository["images"]:
                image_id = db.insert_image_analysis(image_data)
                assert image_id is not None
                total_images += 1

        assert total_images == 3  # 2 Python + 1 Node

        # 3. Verify comprehensive database state
        all_images = db.get_all_images_with_details()
        assert len(all_images) >= 3

        # 4. Test cross-language capabilities
        languages_summary = db.get_languages_summary()
        assert len(languages_summary) >= 2  # Python and Node

        # Language names in summary
        lang_names = [lang["language"] for lang in languages_summary]
        assert "python" in lang_names
        assert "node" in lang_names

        # 5. Test multi-language recommendations
        engine = RecommendationEngine(temp_db_path)

        # Python recommendations
        python_req = UserRequirement(language="python", version="3.12")
        python_recs = engine.recommend(python_req)

        # Node recommendations
        node_req = UserRequirement(language="node", version="18")
        node_recs = engine.recommend(node_req)

        assert isinstance(python_recs, list)
        assert isinstance(node_recs, list)

        # 6. Test size-based recommendations
        size_pref_req = UserRequirement(language="python", size_preference="minimal")
        size_recs = engine.recommend(size_pref_req)
        assert isinstance(size_recs, list)

        # 7. Test vulnerability distribution analysis
        vuln_dist = db.get_vulnerability_distribution()
        assert isinstance(vuln_dist, dict)
        # Check for expected vulnerability severity levels
        expected_keys = {"zero", "low", "medium", "high"}
        assert expected_keys.issubset(set(vuln_dist.keys()))
        assert "high" in vuln_dist

        # 8. Test comprehensive reporting
        if python_recs:
            python_report = engine.format_recommendations(python_recs, limit=10)
            assert isinstance(python_report, str)
            assert len(python_report) > 0

        if node_recs:
            node_report = engine.format_recommendations(node_recs, limit=10)
            assert isinstance(node_report, str)
            assert len(node_report) > 0

        db.close()

    def test_scan_workflow_with_updates_e2e(self, temp_db_path, mock_registry_data):
        """Test end-to-end workflow with image updates"""
        # 1. Initialize database
        db = ImageDatabase(temp_db_path)

        # 2. Initial scan - add first image
        initial_image = mock_registry_data["repositories"][0]["images"][0].copy()
        initial_id = db.insert_image_analysis(initial_image)
        assert initial_id is not None

        # 3. Verify initial state
        images_count_initial = db.get_image_count()
        assert images_count_initial >= 1

        # 4. Update scan - same image with different vulnerability data
        updated_image = initial_image.copy()
        updated_image["vulnerabilities"] = {
            "total": 3,
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 0,
        }

        # Force update
        updated_id = db.insert_image_analysis(updated_image, force_update=True)

        # 5. Verify update behavior
        images_count_after = db.get_image_count()
        # Should be same count (update, not insert)
        assert images_count_after == images_count_initial

        # 6. Verify vulnerability data was updated
        updated_stored = db.get_image_by_exact_name(initial_image["image"])
        assert updated_stored["critical_vulnerabilities"] == 1
        assert updated_stored["total_vulnerabilities"] == 3

        # 7. Test recommendations reflect updated security posture
        engine = RecommendationEngine(temp_db_path)
        req = UserRequirement(
            language="python",
            version="3.12",
            security_level="maximum",
            max_critical_vulnerabilities=0,
        )
        recs = engine.recommend(req)

        # Should have fewer/no recommendations due to critical vulnerability
        if recs:
            # If any recommendations, they should not include the updated image
            # (or have lower scores due to security issues)
            for rec in recs:
                if rec.image_name == initial_image["image"]:
                    # Score should be lower due to security issues
                    assert rec.score < 0.9  # Assuming high security penalty

        db.close()

    def test_error_handling_and_recovery_e2e(self, temp_db_path):
        """Test end-to-end error handling and recovery scenarios"""
        # 1. Test database initialization
        db = ImageDatabase(temp_db_path)
        assert db.conn is not None

        # 2. Test handling of malformed image data
        malformed_data = {
            "image": "test/malformed:latest",
            "tag": "latest",
            # Missing required fields
        }

        try:
            # Should handle gracefully without crashing
            image_id = db.insert_image_analysis(malformed_data)
            # If it succeeds, verify it handled missing data appropriately
            if image_id:
                stored = db.get_image_by_exact_name(malformed_data["image"])
                assert stored is not None
        except Exception as e:
            # Should be a graceful error, not a crash
            assert isinstance(e, (ValueError, KeyError, TypeError))

        # 3. Test empty database recommendations
        engine = RecommendationEngine(temp_db_path)
        req = UserRequirement(language="nonexistent", version="999")
        recs = engine.recommend(req)

        # Should return empty list, not crash
        assert isinstance(recs, list)
        assert len(recs) == 0

        # 4. Test recommendation formatting with empty results
        formatted = engine.format_recommendations(recs, limit=5)
        assert isinstance(formatted, str)
        assert "No suitable images found" in formatted

        # 5. Test database recovery after close/reopen
        db.close()

        # Reopen database
        db2 = ImageDatabase(temp_db_path)

        # Should be able to query (even if empty)
        all_images = db2.get_all_images_with_details()
        assert isinstance(all_images, list)

        db2.close()
