"""
Unit Tests: Feature Engineering & Preprocessing for MLOps
"""

import pytest
from ml.feature_engineering import FeatureTransformer


@pytest.mark.unit
class TestFeatureEngineering:
    def test_recency_score_calculation(self):
        score_recent = FeatureTransformer.calculate_recency_score(0)
        assert score_recent == 1.0

        score_old = FeatureTransformer.calculate_recency_score(365)
        assert score_old == 0.0

    def test_negative_days_raises_error(self):
        with pytest.raises(ValueError):
            FeatureTransformer.calculate_recency_score(-5)

    def test_feature_vector_building(self):
        customer = {
            "customer_id": 101,
            "days_since_order": 10,
            "total_spend": 250.0,
            "orders_count": 5
        }
        vector = FeatureTransformer.build_feature_vector(customer)
        assert vector["customer_id"] == 101
        assert vector["recency_score"] > 0.9
        assert vector["monetary_score"] == 2.5
        assert vector["churn_risk"] == "LOW"

    def test_high_churn_risk_detection(self):
        customer = {
            "customer_id": 102,
            "days_since_order": 300,
            "total_spend": 20.0,
            "orders_count": 1
        }
        vector = FeatureTransformer.build_feature_vector(customer)
        assert vector["churn_risk"] == "HIGH"
