#!/bin/bash
set -e

echo "======================================================"
echo " Starting Event-Driven Lakehouse Local Environment..."
echo "======================================================"

docker compose up -d

echo "Waiting for services to initialize..."
sleep 10

docker compose ps

echo "Registering Debezium PostgreSQL CDC Connector..."
bash scripts/register-connector.sh

echo "======================================================"
echo " Environment ready!"
echo " - Postgres (OLTP): localhost:5432"
echo " - Kafka: localhost:9092"
echo " - Schema Registry: http://localhost:8081"
echo " - Kafka Connect (Debezium): http://localhost:8083"
echo " - MinIO Console: http://localhost:9001 (admin / password123)"
echo " - Iceberg REST Catalog: http://localhost:8181"
echo " - Spark Master UI: http://localhost:8080"
echo " - Trino UI: http://localhost:8085"
echo " - Airflow Webserver: http://localhost:8088 (admin / admin)"
echo "======================================================"
