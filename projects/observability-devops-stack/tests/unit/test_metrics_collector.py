"""
Unit Tests: DevOps Metrics Aggregation & Prometheus Formatting
"""

import pytest
from monitoring.metrics_collector import MetricAggregator


@pytest.mark.unit
class TestMetricsCollector:
    def test_percentile_calculation(self):
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 100.0, 200.0, 300.0, 500.0, 1000.0]
        p50 = MetricAggregator.calculate_percentile(latencies, 50)
        p99 = MetricAggregator.calculate_percentile(latencies, 99)

        assert p50 == 100.0
        assert p99 == 1000.0

    def test_empty_latencies_returns_zero(self):
        assert MetricAggregator.calculate_percentile([], 95) == 0.0

    def test_format_prometheus_gauge(self):
        gauge = MetricAggregator.format_prometheus_gauge(
            "http_request_duration_ms",
            124.5,
            {"service": "api-gateway", "method": "POST", "status": "200"}
        )
        assert 'http_request_duration_ms{service="api-gateway",method="POST",status="200"} 124.5' == gauge

    def test_service_health_score(self):
        score = MetricAggregator.compute_service_health_score(980, 20)
        assert score == 98.0

        perfect_score = MetricAggregator.compute_service_health_score(0, 0)
        assert perfect_score == 100.0
