"""
Integration Tests: RabbitMQ Message Broker via Management API
"""

import json
import pytest
import requests

RABBITMQ_MGMT_URL = "http://localhost:15672"
AUTH = ("guest", "guest")


@pytest.mark.integration
class TestRabbitMQIntegration:
    """Integration test suite for RabbitMQ."""

    def test_rabbitmq_overview(self, http_session):
        res = http_session.get(f"{RABBITMQ_MGMT_URL}/api/overview", auth=AUTH, timeout=4.0)
        assert res.status_code == 200
        data = res.json()
        assert "rabbitmq_version" in data
        assert "cluster_name" in data

    def test_declare_publish_and_consume_queue(self, http_session):
        queue_name = "velocelog_test_queue"
        vhost = "%2F"  # URL-encoded '/' default vhost

        # 1. Declare Queue
        declare_res = http_session.put(
            f"{RABBITMQ_MGMT_URL}/api/queues/{vhost}/{queue_name}",
            auth=AUTH,
            json={"auto_delete": False, "durable": False},
            timeout=4.0
        )
        assert declare_res.status_code in (201, 204)

        # 2. Publish Message
        pub_res = http_session.post(
            f"{RABBITMQ_MGMT_URL}/api/exchanges/{vhost}/amq.default/publish",
            auth=AUTH,
            json={
                "properties": {},
                "routing_key": queue_name,
                "payload": json.dumps({"order_id": 9999, "status": "QUEUED"}),
                "payload_encoding": "string"
            },
            timeout=4.0
        )
        assert pub_res.status_code == 200
        assert pub_res.json().get("routed") is True

        # 3. Get / Consume Message
        get_res = http_session.post(
            f"{RABBITMQ_MGMT_URL}/api/queues/{vhost}/{queue_name}/get",
            auth=AUTH,
            json={"count": 1, "ackmode": "ack_requeue_false", "encoding": "auto"},
            timeout=4.0
        )
        assert get_res.status_code == 200
        messages = get_res.json()
        assert len(messages) == 1
        payload = json.loads(messages[0]["payload"])
        assert payload["order_id"] == 9999

        # 4. Cleanup Queue
        del_res = http_session.delete(
            f"{RABBITMQ_MGMT_URL}/api/queues/{vhost}/{queue_name}",
            auth=AUTH,
            timeout=4.0
        )
        assert del_res.status_code == 204
