"""
Integration Tests: Kafka Ecosystem (Schema Registry, Kafka Connect, Kafka UI)
"""

import pytest
import requests


@pytest.mark.integration
class TestKafkaEcosystemIntegration:
    """Integration test suite for Kafka ecosystem components."""

    def test_schema_registry_subjects(self, http_session):
        res = http_session.get("http://localhost:8086/subjects", timeout=4.0)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_kafka_connect_plugins(self, http_session):
        res = http_session.get("http://localhost:8083/connector-plugins", timeout=4.0)
        assert res.status_code == 200
        plugins = [p.get("class") for p in res.json()]
        assert any("PostgresConnector" in p for p in plugins)

    def test_kafka_ui_healthy(self, http_session):
        res = http_session.get("http://localhost:8087", timeout=4.0)
        assert res.status_code == 200
        assert "Kafka UI" in res.text or "<html" in res.text.lower()
