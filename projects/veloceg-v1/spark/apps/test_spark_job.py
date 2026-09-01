import sys
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

def main():
    print("=" * 60)
    print("🚀 [veloceg-v1] Conectando ao Spark Master: spark://spark-master:7077")
    print("=" * 60)

    # Conecta diretamente ao Master do cluster Standalone
    spark = SparkSession.builder \
        .appName("Veloceg-V1-Spark-Test-Job") \
        .master("spark://spark-master:7077") \
        .config("spark.executor.memory", "512m") \
        .config("spark.executor.cores", "1") \
        .config("spark.cores.max", "2") \
        .getOrCreate()

    print(f"✨ Conexão estabelecida com sucesso!")
    print(f"✨ Spark Master : {spark.sparkContext.master}")
    print(f"✨ App ID       : {spark.sparkContext.applicationId}")

    # Criação de um DataFrame distribuído
    data = [
        (1, "Veloceg-Alpha", 1500.0),
        (2, "Veloceg-Beta", 3200.5),
        (3, "Veloceg-Gamma", 4800.75),
        (4, "Veloceg-Delta", 950.2)
    ]
    columns = ["id", "servico", "valor"]

    df = spark.createDataFrame(data, columns) \
        .withColumn("timestamp", current_timestamp()) \
        .withColumn("status", lit("PROCESSADO_PELO_CLUSTER"))

    print("\n📊 Dados processados pelos Workers:")
    df.show(truncate=False)

    # Estimativa de Pi com RDD paralelo para forçar processamento no worker
    num_samples = 500000
    def inside(p):
        import random
        x, y = random.random(), random.random()
        return x*x + y*y < 1.0

    count = spark.sparkContext.parallelize(range(0, num_samples), 4).filter(inside).count()
    pi_aprox = 4.0 * count / num_samples
    print(f"🎯 Estimativa de Pi calculada nos Workers: {pi_aprox}")

    # Aguarda 5 segundos para permitir visualização confortável na UI
    time.sleep(5)

    print("=" * 60)
    print("🎉 Job concluído com sucesso!")
    print("=" * 60)

    spark.stop()

if __name__ == "__main__":
    main()
