FROM apache/airflow:2.9.2-python3.11

USER root
# Install Java JDK (required for SparkSubmitOperator and PySpark) & system utilities
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
           openjdk-17-jre-headless \
           procps \
           curl \
           git \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.2/constraints-3.11.txt" -r /requirements.txt
