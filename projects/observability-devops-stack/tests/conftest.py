import os
import pytest
import requests

@pytest.fixture(scope="session")
def http_session():
    session = requests.Session()
    session.headers.update({"User-Agent": "StackStudio-Test-Runner/1.0"})
    yield session
    session.close()

@pytest.fixture
def sample_cdc_event():
    return {
        "before": None,
        "after": {
            "order_id": 1001,
            "customer_id": 42,
            "status": "PROCESSING",
            "total_amount": 149.90,
            "order_date": 1724932800000000,
            "updated_at": 1724932800000000
        },
        "source": {
            "version": "2.6.1.Final",
            "connector": "postgresql",
            "name": "cdc",
            "ts_ms": 1724932800000,
            "db": "oltp_db",
            "schema": "ecommerce",
            "table": "orders",
            "txId": 501,
            "lsn": 24567890
        },
        "op": "c",
        "ts_ms": 1724932800100,
        "transaction": None
    }
