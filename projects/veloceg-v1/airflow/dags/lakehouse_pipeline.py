from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'lakehouse',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'veloceg-v1_lakehouse_pipeline',
    default_args=default_args,
    description='Automated pipeline for veloceg-v1',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    t1 = BashOperator(
        task_id='verify_bronze_layer',
        bash_command='echo "Verifying Bronze ingest..."',
    )

    t2 = BashOperator(
        task_id='trigger_gold_aggregations',
        bash_command='echo "Executing Gold transforms with dbt and Trino..."',
    )

    t1 >> t2
