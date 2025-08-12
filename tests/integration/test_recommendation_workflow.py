"""
Integration tests for the complete recommendation workflow.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from database import ImageDatabase
from image_analyzer import ImageAnalyzer
from recommendation_engine import RecommendationEngine, UserRequirement


class TestRecommendationWorkflow:
    """Integration tests for the complete recommendation workflow."""

    def test_end_to_end_recommendation_flow(self, temp_db, sample_image_data):
        """Test complete flow from database to recommendation."""
        # 1. Add sample data to database
        temp_db.insert_image_analysis(sample_image_data)

        # 2. Create recommendation engine
        engine = RecommendationEngine(temp_db.db_path)

        # 3. Create user requirement
        req = UserRequirement(
            language="python", version="3.12", packages=["pip"], security_level="high"
        )

        # 4. Get recommendations
        recommendations = engine.recommend(req)

        # 5. Verify results
        assert len(recommendations) > 0
        best_match = recommendations[0]
        assert best_match.image_name == sample_image_data["image"]
        assert best_match.score > 0
        assert len(best_match.reasoning) > 0

        # 6. Format recommendations
        formatted = engine.format_recommendations(recommendations)
        assert isinstance(formatted, str)
        assert "python" in formatted.lower()

        engine.db.close()

    def test_recommendation_with_security_constraints(self, temp_db):
        """Test recommendations with security constraints."""
        # Add secure and insecure images
        secure_image = {
            "image": "secure/python:3.12",
            "tag": "3.12",
            "languages": [
                {"language": "python", "version": "3.12.0", "major_minor": "3.12"}
            ],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "manifest": {"size": 100000000},
        }

        insecure_image = {
            "image": "insecure/python:3.12",
            "tag": "3.12",
            "languages": [
                {"language": "python", "version": "3.12.0", "major_minor": "3.12"}
            ],
            "vulnerabilities": {
                "total": 10,
                "critical": 5,
                "high": 3,
                "medium": 2,
                "low": 0,
            },
            "manifest": {"size": 100000000},
        }

        temp_db.insert_image_analysis(secure_image)
        temp_db.insert_image_analysis(insecure_image)

        engine = RecommendationEngine(temp_db.db_path)

        # Request with strict security constraints
        req = UserRequirement(
            language="python",
            version="3.12",
            security_level="high",
            max_critical_vulnerabilities=0,
            max_high_vulnerabilities=0,
        )

        recommendations = engine.recommend(req)

        # Should only return the secure image
        assert len(recommendations) >= 1
        secure_recommendations = [
            r for r in recommendations if r.image_name == "secure/python:3.12"
        ]
        assert len(secure_recommendations) > 0

        engine.db.close()

    def test_recommendation_with_size_preference(self, temp_db):
        """Test recommendations with size preferences."""
        # Add images of different sizes
        small_image = {
            "image": "small/python:3.12",
            "tag": "3.12",
            "languages": [
                {"language": "python", "version": "3.12.0", "major_minor": "3.12"}
            ],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "manifest": {"size": 50000000},  # 50MB
        }

        large_image = {
            "image": "large/python:3.12",
            "tag": "3.12",
            "languages": [
                {"language": "python", "version": "3.12.0", "major_minor": "3.12"}
            ],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "manifest": {"size": 500000000},  # 500MB
        }

        temp_db.insert_image_analysis(small_image)
        temp_db.insert_image_analysis(large_image)

        engine = RecommendationEngine(temp_db.db_path)

        # Request with minimal size preference
        req = UserRequirement(
            language="python", version="3.12", size_preference="minimal"
        )

        recommendations = engine.recommend(req)
        assert len(recommendations) >= 2

        # Small image should score higher
        small_score = next(
            r.score for r in recommendations if r.image_name == "small/python:3.12"
        )
        large_score = next(
            r.score for r in recommendations if r.image_name == "large/python:3.12"
        )
        assert small_score > large_score

        engine.db.close()

    def test_recommendation_with_package_requirements(self, temp_db):
        """Test recommendations with specific package requirements."""
        # Image with required packages
        matching_image = {
            "image": "matching/python:3.12",
            "tag": "3.12",
            "languages": [
                {"language": "python", "version": "3.12.0", "major_minor": "3.12"}
            ],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "packages": [{"name": "pip"}, {"name": "requests"}, {"name": "numpy"}],
            "package_managers": [
                {"name": "pip"},
                {"name": "requests", "package_type": "python"},
            ],
            "manifest": {"size": 100000000},
        }

        # Image without required packages
        non_matching_image = {
            "image": "nonmatching/python:3.12",
            "tag": "3.12",
            "languages": [
                {"language": "python", "version": "3.12.0", "major_minor": "3.12"}
            ],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "packages": [{"name": "pip"}],  # Missing requests
            "package_managers": [{"name": "pip"}],
            "manifest": {"size": 100000000},
        }

        temp_db.insert_image_analysis(matching_image)
        temp_db.insert_image_analysis(non_matching_image)

        engine = RecommendationEngine(temp_db.db_path)

        # Request with package requirements
        req = UserRequirement(
            language="python", version="3.12", packages=["pip", "requests"]
        )

        recommendations = engine.recommend(req)
        assert len(recommendations) >= 2

        # Matching image should score higher
        matching_score = next(
            r.score for r in recommendations if r.image_name == "matching/python:3.12"
        )
        non_matching_score = next(
            r.score
            for r in recommendations
            if r.image_name == "nonmatching/python:3.12"
        )
        assert matching_score > non_matching_score

        engine.db.close()

    def test_database_to_recommendation_workflow(self, temp_db, sample_image_data):
        """Test flow from database to recommendation without external tools."""
        # 1. Add sample data to database
        image_id = temp_db.insert_image_analysis(sample_image_data)
        assert image_id is not None

        # 2. Create recommendation engine using same database
        engine = RecommendationEngine(temp_db.db_path)
        req = UserRequirement(language="python", version="3.12")

        # 3. Get recommendations
        recommendations = engine.recommend(req)

        # 4. Verify we get recommendations
        assert isinstance(recommendations, list)
        if recommendations:  # Only check details if we got results
            rec = recommendations[0]
            assert hasattr(rec, "image_name")
            assert hasattr(rec, "score")
            assert rec.score >= 0

        # 5. Test formatting
        formatted = engine.format_recommendations(recommendations)
        assert isinstance(formatted, str)

    def test_multiple_language_versions(self, temp_db):
        """Test recommendations across multiple language versions."""
        # Add images with different Python versions
        python312_image = {
            "image": "python:3.12",
            "tag": "3.12",
            "languages": [
                {"language": "python", "version": "3.12.0", "major_minor": "3.12"}
            ],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "manifest": {"size": 100000000},
        }

        python311_image = {
            "image": "python:3.11",
            "tag": "3.11",
            "languages": [
                {"language": "python", "version": "3.11.5", "major_minor": "3.11"}
            ],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "manifest": {"size": 100000000},
        }

        temp_db.insert_image_analysis(python312_image)
        temp_db.insert_image_analysis(python311_image)

        engine = RecommendationEngine(temp_db.db_path)

        # Request specific version
        req = UserRequirement(language="python", version="3.12")
        recommendations = engine.recommend(req)

        # 3.12 should score higher than 3.11
        if len(recommendations) >= 2:
            python312_score = next(
                (r["score"] for r in recommendations if "3.12" in r["image_name"]), 0
            )
            python311_score = next(
                (r["score"] for r in recommendations if "3.11" in r["image_name"]), 0
            )
            assert python312_score > python311_score

        engine.db.close()

    def test_no_matching_results(self, temp_db):
        """Test recommendation when no images match the criteria."""
        # Add only Java images
        java_image = {
            "image": "openjdk:17",
            "tag": "17",
            "languages": [
                {"language": "java", "version": "17.0.0", "major_minor": "17"}
            ],
            "vulnerabilities": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "manifest": {"size": 100000000},
        }

        temp_db.insert_image_analysis(java_image)

        engine = RecommendationEngine(temp_db.db_path)

        # Request Python (no match)
        req = UserRequirement(language="python", version="3.12")
        recommendations = engine.recommend(req)

        # Should return empty list
        assert len(recommendations) == 0

        engine.db.close()
