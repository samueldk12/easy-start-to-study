"""Read a bounded Kafka batch and persist it to Iceberg bronze."""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_date

spark = SparkSession.builder.appName("KafkaBatchToIceberg").getOrCreate()

topic = spark.conf.get("spark.pipeline.kafka.topic", "cdc.ecommerce.orders")
bootstrap = spark.conf.get("spark.pipeline.kafka.bootstrap", "kafka:29092")

df = (
    spark.read.format("kafka")
    .option("kafka.bootstrap.servers", bootstrap)
    .option("subscribe", topic)
    .option("startingOffsets", "earliest")
    .option("endingOffsets", "latest")
    .load()
)

bronze = df.select(
    col("key").cast("string").alias("kafka_key"),
    col("value").cast("string").alias("raw_payload"),
    current_timestamp().alias("ingestion_timestamp"),
    to_date(current_timestamp()).alias("ingestion_date"),
)

spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze")
spark.sql("""
CREATE TABLE IF NOT EXISTS lakehouse.bronze.orders_raw (
  kafka_key STRING,
  raw_payload STRING,
  ingestion_timestamp TIMESTAMP,
  ingestion_date DATE
) USING iceberg PARTITIONED BY (ingestion_date)
""")

bronze.writeTo("lakehouse.bronze.orders_raw").append()
print(f"kafka_batch_rows={bronze.count()} topic={topic}")
spark.stop()
