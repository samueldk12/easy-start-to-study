import pytest
from datetime import datetime
from typing import Dict, Any

class CDCPayloadParser:
    @staticmethod
    def parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(event, dict):
            raise ValueError("Invalid CDC event: must be a dictionary")
        op = event.get("op")
        if op not in ("c", "u", "d", "r"):
            raise ValueError(f"Unsupported CDC operation type: '{op}'")
        source = event.get("source") or {}
        table = source.get("table")
        schema = source.get("schema")
        if op == "d":
            data = event.get("before") or {}
            is_deleted = True
        else:
            data = event.get("after") or {}
            is_deleted = False
        ts_ms = event.get("ts_ms")
        event_timestamp = datetime.utcfromtimestamp(ts_ms / 1000.0) if ts_ms else datetime.utcnow()
        return {
            "table_name": f"{schema}.{table}" if schema and table else table,
            "operation": op,
            "is_deleted": is_deleted,
            "data": data,
            "event_timestamp": event_timestamp.isoformat(),
            "lsn": source.get("lsn"),
            "tx_id": source.get("txId")
        }

@pytest.mark.unit
class TestCDCPayloadParser:
    def test_parse_create_event(self, sample_cdc_event):
        res = CDCPayloadParser.parse_event(sample_cdc_event)
        assert res["operation"] == "c"
        assert res["is_deleted"] is False
        assert res["data"]["order_id"] == 1001
