"""
Integration Tests: Apache Iceberg REST Catalog
"""

import pytest
import requests

ICEBERG_REST_URL = "http://localhost:8181"


@pytest.mark.integration
class TestIcebergRESTIntegration:
    """Integration test suite for Iceberg REST Catalog API."""

    def test_iceberg_config_endpoint(self, http_session):
        res = http_session.get(f"{ICEBERG_REST_URL}/v1/config", timeout=4.0)
        assert res.status_code == 200

        data = res.json()
        assert "defaults" in data or "overrides" in data

    def test_iceberg_list_namespaces(self, http_session):
        res = http_session.get(f"{ICEBERG_REST_URL}/v1/namespaces", timeout=4.0)
        assert res.status_code in (200, 404)
