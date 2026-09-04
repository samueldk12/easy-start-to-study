from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

NETWORK = "clean-lakehouse_clean-lakehouse-net"
DEFAULT_ARGS = {
    "owner": "lakehouse",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="kafka_spark_iceberg_pipeline",
    default_args=DEFAULT_ARGS,
    schedule="@hourly",
    catchup=False,
    tags=["kafka", "spark", "iceberg", "bronze"],
) as dag:
    ensure_topic = DockerOperator(
        task_id="ensure_kafka_topic",
        image="confluentinc/cp-kafka:7.6.0",
        command=(
            "kafka-topics --bootstrap-server kafka:29092 --create --if-not-exists "
            "--topic cdc.ecommerce.orders --partitions 1 --replication-factor 1"
        ),
        network_mode=NETWORK,
        mount_tmp_dir=False,
        auto_remove="success",
    )
    run_spark = DockerOperator(
        task_id="run_spark_bronze_batch",
        image="clean-lakehouse-spark-master:latest",
        command=(
            "/opt/spark/bin/spark-submit --master spark://spark-master:7077 "
            "/opt/spark/work-dir/apps/kafka_batch_to_iceberg.py"
        ),
        network_mode=NETWORK,
        mount_tmp_dir=False,
        auto_remove="success",
    )
    log_mlflow = DockerOperator(
        task_id="log_mlflow_run",
        image="curlimages/curl:8.8.0",
        command=(
            "sh -c 'curl -sf \"http://mlflow:5000/api/2.0/mlflow/experiments/get-by-name?experiment_name=kafka-spark-pipeline\" "
            "|| curl -sf -X POST http://mlflow:5000/api/2.0/mlflow/experiments/create "
            "-H Content-Type:application/json -d \"{\\\"name\\\":\\\"kafka-spark-pipeline\\\"}\"; echo MLflow_API_OK'"
        ),
        network_mode=NETWORK,
        mount_tmp_dir=False,
        auto_remove="success",
    )

    ensure_topic >> run_spark >> log_mlflow
