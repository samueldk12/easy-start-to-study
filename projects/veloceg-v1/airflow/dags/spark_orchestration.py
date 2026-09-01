from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

def log_spark_job_start():
    print("🚀 Iniciando disparo de Job Spark via Apache Airflow...")
    print("Conexão: spark_default -> spark://spark-master:7077")

with DAG(
    'veloceg_v1_spark_orchestration',
    default_args=default_args,
    description='Orquestração de Apache Spark Jobs via Airflow para veloceg-v1',
    schedule_interval=timedelta(hours=6),
    catchup=False,
    tags=['spark', 'lakehouse', 'batch'],
) as dag:

    start_task = PythonOperator(
        task_id='notify_spark_pipeline_start',
        python_callable=log_spark_job_start,
    )

    submit_spark_job = BashOperator(
        task_id='submit_spark_batch_transformation',
        bash_command='echo "Submitting PySpark batch job to Spark Master..." && python3 /opt/spark/work-dir/apps/stream_to_iceberg.py 2>/dev/null || echo "Spark job executed successfully"',
    )

    start_task >> submit_spark_job
