.PHONY: start stop restart status logs test clean kafka-smoke spark-batch pipeline

start:
	docker compose up -d
	python tests/test_services.py

test:
	python -m pytest -q

kafka-smoke:
	bash scripts/kafka_smoke.sh

spark-batch:
	docker exec clean-lakehouse-spark-master /opt/spark/bin/spark-submit \
		--master spark://spark-master:7077 \
		--conf spark.sql.defaultCatalog=spark_catalog \
		--conf spark.pipeline.kafka.topic=$${KAFKA_TOPIC:-cdc.ecommerce.orders} \
		/opt/spark/work-dir/apps/kafka_batch_to_iceberg.py

pipeline: start kafka-smoke spark-batch

stop:
	docker compose down

pause:
	docker compose stop

resume:
	docker compose start

restart:
	docker compose restart

status:
	docker compose ps

logs:
	docker compose logs -f

clean:
	docker compose down -v
