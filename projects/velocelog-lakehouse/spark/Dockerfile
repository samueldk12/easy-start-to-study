FROM apache/spark:3.5.1-python3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

ENV ICEBERG_VERSION=1.6.1
ENV AWS_SDK_VERSION=1.12.262
ENV HADOOP_AWS_VERSION=3.3.4
ENV KAFKA_CLIENTS_VERSION=3.5.1
ENV COMMONS_POOL_VERSION=2.11.1

RUN curl -s -f -L https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar -o /opt/spark/jars/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar && \
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar -o /opt/spark/jars/iceberg-aws-bundle-${ICEBERG_VERSION}.jar && \
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar -o /opt/spark/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar && \
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.1/spark-token-provider-kafka-0-10_2.12-3.5.1.jar -o /opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar && \
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/${KAFKA_CLIENTS_VERSION}/kafka-clients-${KAFKA_CLIENTS_VERSION}.jar -o /opt/spark/jars/kafka-clients-${KAFKA_CLIENTS_VERSION}.jar && \
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/${COMMONS_POOL_VERSION}/commons-pool2-${COMMONS_POOL_VERSION}.jar -o /opt/spark/jars/commons-pool2-${COMMONS_POOL_VERSION}.jar && \
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar -o /opt/spark/jars/hadoop-aws-${HADOOP_AWS_VERSION}.jar && \
    curl -s -f -L https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar -o /opt/spark/jars/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar

COPY conf/spark-defaults.conf /opt/spark/conf/spark-defaults.conf
RUN chmod -R 777 /opt/spark/conf /opt/spark/work-dir /tmp

USER spark
WORKDIR /opt/spark/work-dir
