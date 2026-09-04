#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${KAFKA_CONTAINER:-clean-lakehouse-kafka}"
BOOTSTRAP="${KAFKA_BOOTSTRAP:-localhost:29092}"
TOPIC="${KAFKA_TOPIC:-cdc.ecommerce.orders}"
MESSAGE="${1:-{\"order_id\":\"smoke-$(date +%s)\",\"amount\":42.5}}"

docker exec "$CONTAINER" /bin/kafka-topics \
  --bootstrap-server "$BOOTSTRAP" --create --if-not-exists \
  --topic "$TOPIC" --partitions 1 --replication-factor 1 >/dev/null

printf '%s\n' "$MESSAGE" | docker exec -i "$CONTAINER" /bin/kafka-console-producer \
  --bootstrap-server "$BOOTSTRAP" --topic "$TOPIC"

echo "Mensagem publicada em $TOPIC: $MESSAGE"
