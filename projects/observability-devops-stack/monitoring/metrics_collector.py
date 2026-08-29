"""
DevOps Observability: Metrics Collector & Prometheus Exposition Generator
"""

import time
from typing import Dict, List, Any


class MetricAggregator:
    """Aggregates latency percentiles and generates Prometheus exposition format."""

    @staticmethod
    def calculate_percentile(latencies: List[float], percentile: float) -> float:
        if not latencies:
            return 0.0
        sorted_vals = sorted(latencies)
        idx = int(len(sorted_vals) * (percentile / 100.0))
        idx = min(idx, len(sorted_vals) - 1)
        return round(sorted_vals[idx], 2)

    @staticmethod
    def format_prometheus_gauge(metric_name: str, value: float, labels: Dict[str, str]) -> str:
        label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
        return f"{metric_name}{{{label_str}}} {value}"

    @staticmethod
    def compute_service_health_score(success_count: int, error_count: int) -> float:
        total = success_count + error_count
        if total == 0:
            return 100.0
        return round((success_count / total) * 100.0, 2)
