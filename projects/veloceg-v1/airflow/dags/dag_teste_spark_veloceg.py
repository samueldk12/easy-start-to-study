"""
DAG de Teste: Execução de Aplicação Spark no veloceg-v1
======================================================
Esta DAG executa um job PySpark conectando diretamente ao Spark Master (spark://spark-master:7077).
Não requer provedores externos do Airflow.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'retries': 0,
}

def executar_job_spark_pyspark():
    import sys
    import time
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import current_timestamp, lit

    print("=" * 60)
    print("🚀 [Airflow] Iniciando Sessão PySpark apontando para spark://spark-master:7077")
    print("=" * 60)

    spark = SparkSession.builder \
        .appName("Airflow-Veloceg-Spark-Test") \
        .master("spark://spark-master:7077") \
        .config("spark.executor.memory", "512m") \
        .config("spark.executor.cores", "1") \
        .config("spark.cores.max", "2") \
        .getOrCreate()

    print(f"✅ Conectado com Sucesso ao Cluster Spark Master!")
    print(f"📍 Application ID: {spark.sparkContext.applicationId}")
    print(f"📍 Versão Spark : {spark.version}")

    # DataFrame de teste
    dados = [
        (1, "Ingestao_Postgres_CDC", "CONCLUIDO"),
        (2, "Stream_Kafka_Topics", "CONCLUIDO"),
        (3, "Iceberg_Lakehouse_Sync", "CONCLUIDO"),
        (4, "Trino_Query_Validation", "CONCLUIDO"),
    ]
    df = spark.createDataFrame(dados, ["id", "etapa", "status"]) \
        .withColumn("data_hora", current_timestamp())

    print("\n📊 Tabela Processada no Spark Cluster:")
    df.show(truncate=False)

    # Processamento paralelo (RDD) para mobilizar os Workers
    amostras = 500000
    def dentro(p):
        import random
        x, y = random.random(), random.random()
        return x * x + y * y < 1.0

    contagem = spark.sparkContext.parallelize(range(0, amostras), 4).filter(dentro).count()
    pi_calc = 4.0 * contagem / amostras
    print(f"🎯 Cálculo distribuído de Pi ({amostras} amostras): {pi_calc}")

    # Pausa de 8 segundos para dar tempo de visualizar no Spark Master UI
    print("⏳ Mantendo aplicação ativa por 8 segundos para conferência na Web UI...")
    time.sleep(8)

    spark.stop()
    print("🏁 Job Spark finalizado com sucesso!")

with DAG(
    dag_id='teste_spark_veloceg_v1',
    default_args=default_args,
    description='Executa um Job Spark no cluster Standalone do veloceg-v1',
    schedule_interval=None,
    catchup=False,
    tags=['spark', 'veloceg-v1', 'teste'],
) as dag:

    inicio = BashOperator(
        task_id='notificacao_inicio',
        bash_command='echo "Iniciando submissão do job Spark ao cluster veloceg-v1..."',
    )

    executar_spark = PythonOperator(
        task_id='executar_spark_cluster',
        python_callable=executar_job_spark_pyspark,
    )

    fim = BashOperator(
        task_id='notificacao_fim',
        bash_command='echo "✅ Aplicação Spark executada e finalizada no veloceg-v1!"',
    )

    inicio >> executar_spark >> fim
