"""
Integration Tests: MinIO S3 Object Storage & Iceberg Bucket
"""

import json
import pytest
from botocore.exceptions import ClientError


@pytest.mark.integration
class TestMinIOS3Integration:
    """Integration test suite for MinIO Object Storage."""

    def test_list_buckets_and_lakehouse_exists(self, s3_client):
        response = s3_client.list_buckets()
        bucket_names = [b["Name"] for b in response.get("Buckets", [])]
        
        assert "lakehouse" in bucket_names, f"Bucket 'lakehouse' not found. Available buckets: {bucket_names}"

    def test_upload_and_download_file(self, s3_client):
        bucket_name = "lakehouse"
        test_key = "tests/integration_artifact.json"
        test_payload = {"project": "velocelog-lakehouse", "status": "testing", "timestamp": 1724932800}

        # Upload
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=json.dumps(test_payload).encode("utf-8"),
            ContentType="application/json"
        )

        # Download and verify
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
        content = json.loads(response["Body"].read().decode("utf-8"))
        assert content["project"] == "velocelog-lakehouse"
        assert content["status"] == "testing"

        # Cleanup
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
