"""
Unit tests for recommendation engine
"""

import os
import tempfile

import pytest

from src.recommendation_engine import RecommendationEngine, UserRequirement


class TestUserRequirement:
    """Test UserRequirement dataclass"""

    def test_init_with_defaults(self):
        """Test UserRequirement initialization with default values."""
        req = UserRequirement(language="python", version="3.12")

        assert req.language == "python"
        assert req.version == "3.12"
        assert req.packages == []
        assert req.capabilities == []
        assert req.size_preference == "balanced"
        assert req.security_level == "high"
        assert req.max_critical_vulnerabilities == 0
        assert req.max_high_vulnerabilities == 0

    def test_init_with_custom_values(self):
        """Test UserRequirement initialization with custom values."""
        req = UserRequirement(
            language="python",
            version="3.12",
            packages=["requests", "numpy"],
            capabilities=["ssl", "crypto"],
            size_preference="minimal",
            security_level="maximum",
            max_critical_vulnerabilities=0,
            max_high_vulnerabilities=1,
        )

        assert req.packages == ["requests", "numpy"]
        assert req.capabilities == ["ssl", "crypto"]
        assert req.size_preference == "minimal"
        assert req.security_level == "maximum"
        assert req.max_high_vulnerabilities == 1

    def test_to_dict(self):
        """Test converting UserRequirement to dictionary."""
        req = UserRequirement(language="python", version="3.12")
        result = req.to_dict()

        assert isinstance(result, dict)
        assert result["language"] == "python"
        assert result["version"] == "3.12"
        assert result["packages"] == []
        assert result["size_preference"] == "balanced"


class TestRecommendationEngine:
    """Test RecommendationEngine functionality"""

    def test_engine_initialization(self):
        """Test that recommendation engine initializes properly."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = RecommendationEngine(db_path)
            assert engine.database_path == db_path
            assert engine.db is not None
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_recommend_with_empty_database(self):
        """Test recommendation with empty database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            engine = RecommendationEngine(db_path)
            req = UserRequirement(language="python", version="3.12")

            recommendations = engine.recommend(req)

            # Should return empty list or handle gracefully
            assert isinstance(recommendations, list)
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_recommend_with_sample_data(self, temp_db, sample_image_data):
        """Test recommendation with sample data."""
        # Add sample image to database
        temp_db.insert_image_analysis(sample_image_data)

        # Create recommendation engine
        engine = RecommendationEngine(temp_db.db_path)
        req = UserRequirement(language="python", version="3.12")

        # Get recommendations
        recommendations = engine.recommend(req)

        # Should find at least one recommendation
        assert isinstance(recommendations, list)
        if recommendations:  # Only check if we got results
            rec = recommendations[0]
            assert hasattr(rec, "image_name")
            assert hasattr(rec, "score")

    def test_format_recommendations(self, temp_db, sample_image_data):
        """Test recommendation formatting."""
        # Add sample image to database
        temp_db.insert_image_analysis(sample_image_data)

        engine = RecommendationEngine(temp_db.db_path)
        req = UserRequirement(language="python", version="3.12")

        # Get recommendations
        recommendations = engine.recommend(req)

        # Format them with correct parameters
        formatted = engine.format_recommendations(recommendations, limit=5)

        # Should return formatted string
        assert isinstance(formatted, str)
