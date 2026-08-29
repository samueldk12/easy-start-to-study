"""
Integration Tests: Redis Key-Value Store & Pub/Sub
"""

import time
import pytest


@pytest.mark.integration
class TestRedisIntegration:
    """Integration test suite for Redis."""

    def test_redis_ping(self, redis_client):
        assert redis_client.ping() is True

    def test_redis_set_get_and_expire(self, redis_client):
        key = "velocelog:test:session_1001"
        value = "active_state"

        # Set
        redis_client.set(key, value, ex=60)

        # Get
        retrieved = redis_client.get(key)
        assert retrieved == value

        # Check TTL
        ttl = redis_client.ttl(key)
        assert 0 < ttl <= 60

        # Delete
        redis_client.delete(key)
        assert redis_client.get(key) is None

    def test_redis_pub_sub(self, redis_client):
        pubsub = redis_client.pubsub()
        channel = "velocelog:events:orders"
        pubsub.subscribe(channel)

        # Allow subscription to register
        time.sleep(0.2)

        # Publish
        redis_client.publish(channel, "order_created_1001")

        # Read message
        msg = None
        for _ in range(5):
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg:
                break
            time.sleep(0.1)

        assert msg is not None
        assert msg["data"] == "order_created_1001"
        pubsub.unsubscribe()
