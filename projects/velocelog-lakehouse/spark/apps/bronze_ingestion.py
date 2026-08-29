# =============================================================================
# SPARK STRUCTURED STREAMING: RAW CDC INGESTION (BRONZE LAYER)
# =============================================================================
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_date

spark = SparkSession.builder.appName("Bronze_CDC_Ingestion").getOrCreate()

spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze")
spark.sql("""
    CREATE TABLE IF NOT EXISTS lakehouse.bronze.orders_raw (
        kafka_key STRING,
        raw_payload STRING,
        ingestion_timestamp TIMESTAMP,
        ingestion_date DATE
    )
    USING iceberg
    PARTITIONED BY (ingestion_date)
""")

stream_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "cdc.ecommerce.orders") \
    .option("startingOffsets", "earliest") \
    .load()

bronze_df = stream_df.select(
    col("key").cast("string").alias("kafka_key"),
    col("value").cast("string").alias("raw_payload"),
    current_timestamp().alias("ingestion_timestamp"),
    to_date(current_timestamp()).alias("ingestion_date")
)

query = bronze_df.writeStream \
    .format("iceberg") \
    .outputMode("append") \
    .trigger(processingTime="5 seconds") \
    .option("checkpointLocation", "s3://lakehouse/checkpoints/bronze_orders") \
    .toTable("lakehouse.bronze.orders_raw")

query.awaitTermination()
