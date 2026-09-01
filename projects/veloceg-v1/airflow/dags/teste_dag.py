from datetime import datetime, timedelta
from airflow.decorators import dag
from airflow.operators.python import PythonOperator
import time

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
}

def rodar_job_spark():
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder \
        .appName("Teste-Spark-Standalone") \
        .master("spark://spark-master:7077") \
        .config("spark.executor.memory", "512m") \
        .config("spark.executor.cores", "1") \
        .getOrCreate()
        
    num_samples = 200000
    def inside(p):
        import random
        x, y = random.random(), random.random()
        return x*x + y*y < 1.0

    count = spark.sparkContext.parallelize(range(0, num_samples), 2).filter(inside).count()
    print(f"Pi é aproximadamente: {4.0 * count / num_samples}")
    
    time.sleep(5)
    spark.stop()

@dag(
    dag_id="teste_spark_standalone",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["teste", "spark"],
)
def teste_spark():

    executar_pi = PythonOperator(
        task_id="calcular_pi_spark",
        python_callable=rodar_job_spark,
    )

    executar_pi

pipeline = teste_spark()