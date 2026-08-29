from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'lakehouse',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    'gold_aggregations_dag',
    default_args=default_args,
    description='Gold Layer aggregations & Analytics Data Marts',
    schedule_interval='@hourly',
    catchup=False,
    tags=['gold', 'analytics', 'lakehouse']
) as dag:

    run_gold_mart = BashOperator(
        task_id='run_gold_mart',
        bash_command='echo "Executing Gold layer batch aggregation..."'
    )
