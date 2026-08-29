from airflow.operators.dummy import DummyOperator

accucarte = DummyOperator(
    task_id = 'teste'
)