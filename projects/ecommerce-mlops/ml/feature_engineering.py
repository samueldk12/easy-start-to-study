"""
MLOps: Feature Store, Semantic Search & Model Training Script
"""

import json
from typing import List, Dict, Any


class FeatureTransformer:
    """Feature engineering pipeline for customer churn prediction."""

    @staticmethod
    def calculate_recency_score(days_since_last_order: int) -> float:
        if days_since_last_order < 0:
            raise ValueError("Days since last order cannot be negative")
        return max(0.0, 1.0 - (days_since_last_order / 365.0))

    @staticmethod
    def calculate_monetary_score(total_spend: float, avg_category_spend: float = 100.0) -> float:
        if total_spend < 0:
            raise ValueError("Total spend cannot be negative")
        return min(5.0, total_spend / max(1.0, avg_category_spend))

    @staticmethod
    def build_feature_vector(customer: Dict[str, Any]) -> Dict[str, float]:
        recency = FeatureTransformer.calculate_recency_score(customer.get("days_since_order", 30))
        monetary = FeatureTransformer.calculate_monetary_score(customer.get("total_spend", 0.0))
        frequency = float(customer.get("orders_count", 1))

        return {
            "customer_id": customer.get("customer_id"),
            "recency_score": round(recency, 4),
            "monetary_score": round(monetary, 4),
            "frequency_score": frequency,
            "churn_risk": "HIGH" if recency < 0.3 and frequency < 2 else "LOW"
        }
