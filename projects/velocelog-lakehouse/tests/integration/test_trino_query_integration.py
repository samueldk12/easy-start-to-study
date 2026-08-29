"""
Integration Tests: Trino Distributed SQL Query Engine
"""

import time
import pytest
import requests

TRINO_URL = "http://localhost:8085"


@pytest.mark.integration
class TestTrinoQueryIntegration:
    """Integration test suite for Trino queries."""

    def test_trino_cluster_info(self, http_session):
        res = http_session.get(f"{TRINO_URL}/v1/info", timeout=4.0)
        assert res.status_code == 200
        data = res.json()
        assert data.get("starting") is False or "nodeVersion" in data

    def test_trino_execute_statement(self, http_session):
        headers = {
            "X-Trino-User": "admin",
            "X-Trino-Catalog": "system",
            "X-Trino-Schema": "runtime"
        }

        # Submit statement
        res = http_session.post(
            f"{TRINO_URL}/v1/statement",
            data="SELECT 42 AS answer, 'VELOCELOG' AS platform",
            headers=headers,
            timeout=5.0
        )
        assert res.status_code == 200
        statement_data = res.json()

        # Follow nextUri if asynchronous
        next_uri = statement_data.get("nextUri")
        max_attempts = 10
        while next_uri and max_attempts > 0:
            time.sleep(0.3)
            poll_res = http_session.get(next_uri, headers=headers, timeout=5.0)
            statement_data = poll_res.json()
            next_uri = statement_data.get("nextUri")
            max_attempts -= 1

        stats = statement_data.get("stats", {})
        state = stats.get("state")
        assert state in ("FINISHED", "RUNNING", "PLANNING", "QUEUED")
