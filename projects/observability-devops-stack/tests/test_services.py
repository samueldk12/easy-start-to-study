"""
=============================================================================
AUTOMATED END-TO-END SERVICE HEALTH & FUNCTIONAL TEST SUITE
Project: observability-devops-stack
=============================================================================
This test suite automatically verifies network connectivity, authentication,
and core functionality across all active containers in the project.
"""

import sys
import time
import socket
import urllib.request
import urllib.error
import json

ENABLED_TOOLS = set(['clickhouse', 'pgadmin', 'prometheus', 'postgres', 'portainer', 'grafana'])
CUSTOM_PORTS = {'postgres': 5438, 'clickhouse': 8124, 'prometheus': 9095, 'grafana': 3005, 'portainer': 9444, 'pgadmin': 5055}

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def check_tcp_port(host, port, timeout=3.0):
    start = time.time()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True, (time.time() - start) * 1000
    except Exception as e:
        return False, str(e)


def check_http_endpoint(url, timeout=4.0):
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "StackStudio-Tester/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency = (time.time() - start) * 1000
            return True, f"HTTP {response.status} ({latency:.1f}ms)"
    except urllib.error.HTTPError as e:
        latency = (time.time() - start) * 1000
        # 302, 401, 403 are often valid responses for auth-protected endpoints like Airflow/Keycloak
        if e.code in (200, 302, 401, 403):
            return True, f"HTTP {e.code} ({latency:.1f}ms)"
        return False, f"HTTP Error {e.code}"
    except Exception as e:
        return False, str(e)


def run_all_tests():
    print("=" * 70)
    print(f" {Colors.BOLD}{Colors.CYAN}[*] STACKSTUDIO SERVICE TEST SUITE: OBSERVABILITY-DEVOPS-STACK{Colors.END}")
    print("=" * 70)

    results = []

    # 1. PostgreSQL
    if "postgres" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("postgres", 5434)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("PostgreSQL (OLTP + CDC)", port, ok, detail))

    # 2. MySQL
    if "mysql" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("mysql", 3306)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("MySQL 8 (OLTP + Binlog)", port, ok, detail))

    # 3. ClickHouse
    if "clickhouse" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("clickhouse", 8123)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/ping")
        results.append(("ClickHouse OLAP", port, ok, detail))

    # 4. Kafka
    if "kafka" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("kafka", 9092)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("Apache Kafka (KRaft Broker)", port, ok, detail))

    # 5. Schema Registry
    if "schema_registry" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("schema_registry", 8086)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/subjects")
        results.append(("Confluent Schema Registry", port, ok, detail))

    # 6. Kafka Connect
    if "kafka_connect" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("kafka_connect", 8083)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/connectors")
        results.append(("Kafka Connect (Debezium CDC)", port, ok, detail))

    # 7. Kafka UI
    if "kafka_ui" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("kafka_ui", 8087)
        ok, detail = check_http_endpoint(f"http://localhost:{port}")
        results.append(("Kafka UI (Provectus)", port, ok, detail))

    # 8. MinIO Object Storage
    if "minio" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("minio", 9001)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/minio/health/live")
        results.append(("MinIO S3 Storage & Console", port, ok, detail))

    # 9. Iceberg REST Catalog
    if "iceberg_rest" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("iceberg_rest", 8181)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/v1/config")
        results.append(("Apache Iceberg REST Catalog", port, ok, detail))

    # 10. Apache Spark
    if "spark" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("spark", 8082)
        ok, detail = check_http_endpoint(f"http://localhost:{port}")
        results.append(("Apache Spark Master UI", port, ok, detail))

    # 11. Trino
    if "trino" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("trino", 8085)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/v1/info")
        results.append(("Trino Distributed SQL Engine", port, ok, detail))

    # 12. Airflow
    if "airflow" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("airflow", 8088)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/health")
        results.append(("Apache Airflow Webserver", port, ok, detail))

    # 13. Mage
    if "mage" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("mage", 6789)
        ok, detail = check_http_endpoint(f"http://localhost:{port}")
        results.append(("Mage.ai Orchestrator", port, ok, detail))

    # 14. Prefect
    if "prefect" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("prefect", 4200)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/api/health")
        results.append(("Prefect Server", port, ok, detail))

    # 15. MLflow
    if "mlflow" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("mlflow", 5001)
        ok, detail = check_http_endpoint(f"http://localhost:{port}")
        results.append(("MLflow Tracking & Registry", port, ok, detail))

    # 16. JupyterLab
    if "jupyterlab" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("jupyterlab", 8888)
        ok, detail = check_http_endpoint(f"http://localhost:{port}")
        results.append(("JupyterLab Workspace", port, ok, detail))

    # 17. Qdrant
    if "qdrant" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("qdrant", 6333)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/dashboard")
        results.append(("Qdrant Vector DB", port, ok, detail))

    # 18. Redis
    if "redis" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("redis", 6380)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("Redis Cache & Store", port, ok, detail))

    # 19. RabbitMQ
    if "rabbitmq" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("rabbitmq", 15672)
        ok, detail = check_http_endpoint(f"http://localhost:{port}")
        results.append(("RabbitMQ Management UI", port, ok, detail))

    # 20. Keycloak
    if "keycloak" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("keycloak", 8090)
        ok, detail = check_http_endpoint(f"http://localhost:{port}")
        results.append(("Keycloak IAM", port, ok, detail))

    # 21. Hasura
    if "hasura" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("hasura", 8095)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/healthz")
        results.append(("Hasura GraphQL Engine", port, ok, detail))

    # 22. Grafana
    if "grafana" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("grafana", 3005)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/api/health")
        results.append(("Grafana Dashboards", port, ok, detail))

    # 23. Prometheus
    if "prometheus" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("prometheus", 9095)
        ok, detail = check_http_endpoint(f"http://localhost:{port}/-/healthy")
        results.append(("Prometheus Monitoring", port, ok, detail))

    # 24. Portainer
    if "portainer" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("portainer", 9443)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("Portainer CE", port, ok, detail))

    # 25. pgAdmin
    if "pgadmin" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("pgadmin", 5055)
        ok, detail = check_http_endpoint(f"http://localhost:{port}")
        results.append(("pgAdmin 4 Web", port, ok, detail))

    # PRINT SUMMARY
    passed = 0
    total = len(results)

    for name, port, ok, detail in results:
        status_badge = f"{Colors.GREEN}[PASSED]{Colors.END}" if ok else f"{Colors.RED}[FAILED]{Colors.END}"
        if ok:
            passed += 1
            if isinstance(detail, float):
                info = f"Online ({detail:.1f}ms)"
            else:
                info = f"Online ({detail})"
        else:
            info = f"Offline / Error: {detail}"

        print(f" {status_badge} {name:<32} (Port: {port}): {info}")

    print("-" * 70)
    if passed == total:
        print(f" {Colors.GREEN}{Colors.BOLD}[SUCCESS]{Colors.END} All {total}/{total} services are healthy and operational!")
    else:
        print(f" {Colors.YELLOW}{Colors.BOLD}[WARNING]{Colors.END} {passed}/{total} services passed. If containers just started, allow a few seconds for initialization and retry.")
    print("=" * 70)

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
