#!/bin/bash
set -e

CONNECT_URL="http://localhost:8083"
CONFIG_FILE="../debezium/register-postgres.json"

echo "Checking Kafka Connect status at $CONNECT_URL..."
until curl -s -f "$CONNECT_URL/connectors" > /dev/null; do
    echo "Kafka Connect is starting up, waiting 5 seconds..."
    sleep 5
done

echo "Kafka Connect is ready!"
echo "Registering Debezium PostgreSQL CDC Connector..."

curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" \
  "$CONNECT_URL/connectors/" \
  -d @"$CONFIG_FILE"

echo ""
echo "Connector status:"
curl -s "$CONNECT_URL/connectors/postgres-cdc-connector/status" | jq . || curl -s "$CONNECT_URL/connectors/postgres-cdc-connector/status"
echo ""
