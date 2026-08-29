from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'lakehouse',
    'start_date': datetime(2024, 1, 1),
    'retries': 1
}

with DAG(
    'iceberg_maintenance_dag',
    default_args=default_args,
    description='Iceberg Maintenance: Compaction and Snapshot Expiration',
    schedule_interval='@daily',
    catchup=False,
    tags=['governance', 'iceberg', 'maintenance']
) as dag:

    compact_files = BashOperator(
        task_id='rewrite_data_files',
        bash_command='echo "Compacting small Parquet files in Iceberg..."'
    )

    expire_snapshots = BashOperator(
        task_id='expire_snapshots',
        bash_command='echo "Expiring old snapshots..."'
    )

    compact_files >> expire_snapshots
