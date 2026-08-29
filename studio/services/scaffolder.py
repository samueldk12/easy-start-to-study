"""
Comprehensive Project Scaffolder Engine
Supports full lifecycle generation of Docker Compose, Kubernetes, Configurations, Seed SQLs,
dbt models, Spark Jobs, Flink Pipelines, SIEM/SOC configs, DevSecOps pipelines, and VS Code IDE Web.
"""

import os
import json
import yaml
from typing import Dict, List, Any, Set
from studio.models import ProjectCreateRequest, ProjectInfo
from studio.services.catalog import get_tool_by_id

PROJECTS_DIR = os.path.join(os.getcwd(), "projects")


class ProjectScaffolder:
    def __init__(self, request: ProjectCreateRequest, project_dir: Any = None):
        self.request = request
        self.project_name = request.name.strip().replace(" ", "-").lower()
        self.project_dir = project_dir or request.path or os.path.join(PROJECTS_DIR, self.project_name)
        self.tools: Set[str] = set(request.tools)
        self.include_templates = getattr(request, "include_templates", True)

    def scaffold(self) -> ProjectInfo:
        os.makedirs(self.project_dir, exist_ok=True)
        self._create_folder_structure()
        self._build_docker_compose()
        self._generate_env_files()
        self._create_default_files()
        self._generate_vscode_files()
        self._generate_scripts()
        self._generate_makefile()
        self._generate_tests()
        self._generate_readme()

        return ProjectInfo(
            id=self.project_name,
            name=self.request.name,
            path=self.project_dir,
            description=self.request.description or "",
            tools=list(self.tools)
        )

    def _create_folder_structure(self):
        folders = [
            "data", "scripts", "tests", "docs", ".vscode", "vscode"
        ]
        if "postgres" in self.tools:
            folders.append("postgres")
        if "mysql" in self.tools:
            folders.append("mysql")
        if "clickhouse" in self.tools:
            folders.append("clickhouse")
        if "doris" in self.tools:
            folders.append("doris")
        if "starrocks" in self.tools:
            folders.append("starrocks")
        if "kafka_connect" in self.tools:
            folders.append("debezium")
        if "spark" in self.tools:
            folders.extend(["spark/apps", "spark/conf"])
        if "flink" in self.tools:
            folders.extend(["flink/jobs", "flink/conf"])
        if "airflow" in self.tools:
            folders.extend(["airflow/dags", "airflow/plugins"])
        if "trino" in self.tools:
            folders.append("trino/etc")
        if "dbt" in self.tools:
            folders.extend(["dbt/models", "dbt/macros", "dbt/seeds"])
        if "superset" in self.tools:
            folders.extend(["superset/dashboards", "superset/sqllab"])
        if "metabase" in self.tools:
            folders.append("metabase/queries")
        if "great_expectations" in self.tools:
            folders.extend(["great_expectations/expectations", "great_expectations/checkpoints"])
        if "soda_core" in self.tools:
            folders.append("soda/checks")
        if "datahub" in self.tools:
            folders.append("datahub/recipes")
        if "ranger" in self.tools:
            folders.append("ranger/policies")
        if "hdfs" in self.tools:
            folders.append("hadoop/hdfs")
        if "yarn" in self.tools:
            folders.append("hadoop/yarn")
        if "hive" in self.tools:
            folders.append("hive/warehouse")
        if "zeppelin" in self.tools:
            folders.append("zeppelin/notebook")
        if "mlflow" in self.tools:
            folders.append("mlflow/artifacts")
        if "jupyterlab" in self.tools:
            folders.append("notebooks")
        if "ollama" in self.tools:
            folders.append("ollama/models")
        if "milvus" in self.tools:
            folders.append("milvus/data")
        if "weaviate" in self.tools:
            folders.append("weaviate/data")
        if "evidently" in self.tools:
            folders.extend(["evidently/reports", "evidently/workspace"])
        if "dvc" in self.tools:
            folders.append("dvc/data")
        if "feast" in self.tools:
            folders.append("feature_repo")
        if "temporal" in self.tools:
            folders.extend(["temporal/workflows", "temporal/activities"])
        if "n8n" in self.tools:
            folders.append("n8n/workflows")
        if "vault" in self.tools:
            folders.extend(["vault/policies", "vault/config"])
        if "redpanda" in self.tools:
            folders.append("redpanda/data")
        if "pulsar" in self.tools:
            folders.append("pulsar/conf")
        if "loki" in self.tools:
            folders.append("loki")
        if "traefik" in self.tools:
            folders.append("traefik")
        if "argocd" in self.tools:
            folders.append("argocd/applications")
        if "wazuh" in self.tools:
            folders.extend(["wazuh/rules", "wazuh/decoders"])
        if "splunk" in self.tools:
            folders.append("splunk/apps")
        if "elastic_security" in self.tools:
            folders.append("elastic_security/rules")
        if "thehive" in self.tools:
            folders.extend(["thehive/data", "cortex/analyzers"])
        if "misp" in self.tools:
            folders.append("misp/feeds")
        if "shuffle" in self.tools:
            folders.append("shuffle/workflows")
        if "suricata" in self.tools:
            folders.extend(["suricata/rules", "suricata/logs"])
        if "zeek" in self.tools:
            folders.extend(["zeek/scripts", "zeek/logs"])
        if "openvas" in self.tools:
            folders.append("openvas/scans")
        if "nmap" in self.tools:
            folders.extend(["nmap/scans", "nmap/scripts"])
        if "metasploit" in self.tools:
            folders.extend(["metasploit/workspace", "metasploit/modules"])
        if "sonarqube" in self.tools:
            folders.append("sonarqube/conf")
        if "trivy" in self.tools:
            folders.append("trivy/reports")
        if "defectdojo" in self.tools:
            folders.append("defectdojo/imports")
        if "zap" in self.tools:
            folders.extend(["zap/scans", "zap/scripts"])
        if "gitleaks" in self.tools:
            folders.extend(["gitleaks/rules", "gitleaks/reports"])
        if "trufflehog" in self.tools:
            folders.append("trufflehog/reports")
        if "teleport" in self.tools:
            folders.append("teleport/config")
        if "authentik" in self.tools:
            folders.append("authentik/custom_templates")
        if any(tool in self.tools for tool in ["ubuntu_sandbox", "debian_sandbox", "alpine_sandbox", "arch_sandbox"]):
            folders.append("workspace")

        for f in folders:
            os.makedirs(os.path.join(self.project_dir, f), exist_ok=True)

    def _build_docker_compose(self):
        services: Dict[str, Any] = {}
        volumes: Dict[str, Any] = {}
        network_name = f"{self.project_name}-net"

        # --- POSTGRESQL ---
        if "postgres" in self.tools:
            port = self.request.custom_ports.get("postgres", 5434)
            init_folder = self.request.custom_folders.get("postgres_init", "postgres/init.sql")
            services["postgres"] = {
                "image": "debezium/postgres:16-alpine",
                "container_name": f"{self.project_name}-postgres",
                "command": "postgres -c wal_level=logical -c max_wal_senders=10 -c max_replication_slots=10",
                "ports": [f"{port}:5432"],
                "environment": {
                    "POSTGRES_USER": "${POSTGRES_USER:-admin}",
                    "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:-admin123}",
                    "POSTGRES_DB": "${POSTGRES_DB:-oltp_db}"
                },
                "volumes": [
                    f"./{init_folder}:/docker-entrypoint-initdb.d/init.sql",
                    "pg_data:/var/lib/postgresql/data"
                ],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB || pg_isready"],
                    "interval": "5s",
                    "timeout": "5s",
                    "retries": 5
                },
                "networks": [network_name]
            }
            volumes["pg_data"] = None

        # --- MYSQL ---
        if "mysql" in self.tools:
            port = self.request.custom_ports.get("mysql", 3306)
            services["mysql"] = {
                "image": "mysql:8.0",
                "container_name": f"{self.project_name}-mysql",
                "command": "--server-id=1 --log-bin=mysql-bin --binlog-format=ROW --binlog-row-image=FULL --default-authentication-plugin=mysql_native_password",
                "ports": [f"{port}:3306"],
                "environment": {
                    "MYSQL_ROOT_PASSWORD": "${MYSQL_ROOT_PASSWORD:-rootpassword}",
                    "MYSQL_DATABASE": "${MYSQL_DATABASE:-app_db}",
                    "MYSQL_USER": "${MYSQL_USER:-dbuser}",
                    "MYSQL_PASSWORD": "${MYSQL_PASSWORD:-dbpassword}"
                },
                "volumes": ["mysql_data:/var/lib/mysql", "./mysql/init.sql:/docker-entrypoint-initdb.d/init.sql"],
                "networks": [network_name]
            }
            volumes["mysql_data"] = None

        # --- CLICKHOUSE ---
        if "clickhouse" in self.tools:
            port = self.request.custom_ports.get("clickhouse", 8123)
            services["clickhouse"] = {
                "image": "clickhouse/clickhouse-server:24.3-alpine",
                "container_name": f"{self.project_name}-clickhouse",
                "ports": [f"{port}:8123", "9009:9000"],
                "volumes": ["clickhouse_data:/var/lib/clickhouse", "./clickhouse/init.sql:/docker-entrypoint-initdb.d/init.sql"],
                "networks": [network_name]
            }
            volumes["clickhouse_data"] = None

        # --- APACHE DORIS ---
        if "doris" in self.tools:
            fe_port = self.request.custom_ports.get("doris", 8030)
            services["doris-fe"] = {
                "image": "apache/doris:2.0.3-fe-x86_64",
                "container_name": f"{self.project_name}-doris-fe",
                "ports": [f"{fe_port}:8030", "9030:9030"],
                "environment": {"FE_SERVERS": "fe1:127.0.0.1:9010", "FE_ID": "1"},
                "volumes": ["doris_fe_meta:/opt/apache-doris/fe/doris-meta"],
                "networks": [network_name]
            }
            services["doris-be"] = {
                "image": "apache/doris:2.0.3-be-x86_64",
                "container_name": f"{self.project_name}-doris-be",
                "depends_on": ["doris-fe"],
                "ports": ["8040:8040", "9050:9050"],
                "environment": {"FE_SERVERS": "fe1:doris-fe:9010", "BE_ADDR": "doris-be:9050"},
                "volumes": ["doris_be_storage:/opt/apache-doris/be/storage"],
                "networks": [network_name]
            }
            volumes["doris_fe_meta"] = None
            volumes["doris_be_storage"] = None

        # --- STARROCKS ---
        if "starrocks" in self.tools:
            fe_port = self.request.custom_ports.get("starrocks", 8031)
            services["starrocks-fe"] = {
                "image": "starrocks/fe-ubuntu:3.2.4",
                "container_name": f"{self.project_name}-starrocks-fe",
                "ports": [f"{fe_port}:8030", "9031:9030"],
                "volumes": ["starrocks_fe_meta:/opt/starrocks/fe/meta"],
                "networks": [network_name]
            }
            services["starrocks-be"] = {
                "image": "starrocks/be-ubuntu:3.2.4",
                "container_name": f"{self.project_name}-starrocks-be",
                "depends_on": ["starrocks-fe"],
                "ports": ["8041:8040", "9051:9050"],
                "volumes": ["starrocks_be_storage:/opt/starrocks/be/storage"],
                "networks": [network_name]
            }
            volumes["starrocks_fe_meta"] = None
            volumes["starrocks_be_storage"] = None

        # --- KAFKA (KRAFT) ---
        if "kafka" in self.tools:
            port = self.request.custom_ports.get("kafka", 9092)
            services["kafka"] = {
                "image": "confluentinc/cp-kafka:7.6.0",
                "container_name": f"{self.project_name}-kafka",
                "ports": [f"{port}:9092"],
                "environment": {
                    "KAFKA_NODE_ID": 1,
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT",
                    "KAFKA_ADVERTISED_LISTENERS": f"PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:{port}",
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": 1,
                    "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS": 0,
                    "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": 1,
                    "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": 1,
                    "KAFKA_PROCESS_ROLES": "broker,controller",
                    "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@kafka:29093",
                    "KAFKA_LISTENERS": "PLAINTEXT://0.0.0.0:29092,CONTROLLER://0.0.0.0:29093,PLAINTEXT_HOST://0.0.0.0:9092",
                    "KAFKA_INTER_BROKER_LISTENER_NAME": "PLAINTEXT",
                    "KAFKA_CONTROLLER_LISTENER_NAMES": "CONTROLLER",
                    "KAFKA_LOG_DIRS": "/tmp/kraft-combined-logs",
                    "CLUSTER_ID": "MkU3OEVBNTcwNTJENDM2Qk"
                },
                "networks": [network_name]
            }

        # --- REDPANDA ---
        if "redpanda" in self.tools:
            console_port = self.request.custom_ports.get("redpanda", 8099)
            services["redpanda"] = {
                "image": "redpandadata/redpanda:v24.1.2",
                "container_name": f"{self.project_name}-redpanda",
                "command": [
                    "redpanda", "start", "--overprovisioned", "--smp", "1",
                    "--memory", "1G", "--reserve-memory", "0M", "--node-id", "0", "--check=false"
                ],
                "ports": ["19092:9092", "18081:8081", "18082:8082"],
                "volumes": ["redpanda_data:/var/lib/redpanda/data"],
                "networks": [network_name]
            }
            services["redpanda-console"] = {
                "image": "redpandadata/console:v2.5.2",
                "container_name": f"{self.project_name}-redpanda-console",
                "depends_on": ["redpanda"],
                "ports": [f"{console_port}:8080"],
                "environment": {"KAFKA_BROKERS": "redpanda:9092"},
                "networks": [network_name]
            }
            volumes["redpanda_data"] = None

        # --- APACHE PULSAR ---
        if "pulsar" in self.tools:
            mgr_port = self.request.custom_ports.get("pulsar", 9527)
            services["pulsar"] = {
                "image": "apachepulsar/pulsar:3.2.2",
                "container_name": f"{self.project_name}-pulsar",
                "command": "bin/pulsar standalone",
                "ports": ["6650:6650", "8092:8080"],
                "volumes": ["pulsar_data:/pulsar/data"],
                "networks": [network_name]
            }
            services["pulsar-manager"] = {
                "image": "apachepulsar/pulsar-manager:v0.4.0",
                "container_name": f"{self.project_name}-pulsar-manager",
                "depends_on": ["pulsar"],
                "ports": [f"{mgr_port}:9527"],
                "environment": {"SPRING_CONFIGURATION_FILE": "/pulsar-manager/pulsar-manager/application.properties"},
                "networks": [network_name]
            }
            volumes["pulsar_data"] = None

        # --- SCHEMA REGISTRY ---
        if "schema_registry" in self.tools:
            port = self.request.custom_ports.get("schema_registry", 8086)
            services["schema-registry"] = {
                "image": "confluentinc/cp-schema-registry:7.6.0",
                "container_name": f"{self.project_name}-schema-registry",
                "ports": [f"{port}:8081"],
                "depends_on": ["kafka"] if "kafka" in self.tools else [],
                "environment": {
                    "SCHEMA_REGISTRY_HOST_NAME": "schema-registry",
                    "SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS": "kafka:29092" if "kafka" in self.tools else "redpanda:9092",
                    "SCHEMA_REGISTRY_LISTENERS": "http://0.0.0.0:8081"
                },
                "networks": [network_name]
            }

        # --- KAFKA CONNECT (DEBEZIUM) ---
        if "kafka_connect" in self.tools:
            port = self.request.custom_ports.get("kafka_connect", 8083)
            deps = []
            if "kafka" in self.tools:
                deps.append("kafka")
            if "postgres" in self.tools:
                deps.append("postgres")
            if "schema_registry" in self.tools:
                deps.append("schema-registry")

            services["kafka-connect"] = {
                "image": "debezium/connect:2.6.1.Final",
                "container_name": f"{self.project_name}-kafka-connect",
                "ports": [f"{port}:8083"],
                "depends_on": deps,
                "environment": {
                    "BOOTSTRAP_SERVERS": "kafka:29092" if "kafka" in self.tools else "redpanda:9092",
                    "GROUP_ID": "1",
                    "CONFIG_STORAGE_TOPIC": "my_connect_configs",
                    "OFFSET_STORAGE_TOPIC": "my_connect_offsets",
                    "STATUS_STORAGE_TOPIC": "my_connect_statuses",
                    "CONFIG_STORAGE_REPLICATION_FACTOR": "1",
                    "OFFSET_STORAGE_REPLICATION_FACTOR": "1",
                    "STATUS_STORAGE_REPLICATION_FACTOR": "1",
                    "KEY_CONVERTER": "org.apache.kafka.connect.json.JsonConverter",
                    "VALUE_CONVERTER": "org.apache.kafka.connect.json.JsonConverter",
                    "KEY_CONVERTER_SCHEMAS_ENABLE": "false",
                    "VALUE_CONVERTER_SCHEMAS_ENABLE": "false"
                },
                "networks": [network_name]
            }

        # --- KAFKA UI ---
        if "kafka_ui" in self.tools:
            port = self.request.custom_ports.get("kafka_ui", 8087)
            env = {
                "KAFKA_CLUSTERS_0_NAME": self.project_name,
                "KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS": "kafka:29092" if "kafka" in self.tools else "redpanda:9092",
            }
            if "schema_registry" in self.tools:
                env["KAFKA_CLUSTERS_0_SCHEMAREGISTRY"] = "http://schema-registry:8081"
            if "kafka_connect" in self.tools:
                env["KAFKA_CLUSTERS_0_KAFKACONNECT_0_NAME"] = "debezium"
                env["KAFKA_CLUSTERS_0_KAFKACONNECT_0_ADDRESS"] = "http://kafka-connect:8083"

            services["kafka-ui"] = {
                "image": "provectuslabs/kafka-ui:latest",
                "container_name": f"{self.project_name}-kafka-ui",
                "ports": [f"{port}:8080"],
                "depends_on": ["kafka"] if "kafka" in self.tools else [],
                "environment": env,
                "networks": [network_name]
            }

        # --- MINIO ---
        if "minio" in self.tools:
            api_port = 9000
            console_port = self.request.custom_ports.get("minio", 9001)
            services["minio"] = {
                "image": "minio/minio:RELEASE.2024-05-10T01-41-38Z",
                "container_name": f"{self.project_name}-minio",
                "command": 'server /data --console-address ":9001"',
                "ports": [f"{api_port}:9000", f"{console_port}:9001"],
                "environment": {
                    "MINIO_ROOT_USER": "${MINIO_ROOT_USER:-admin}",
                    "MINIO_ROOT_PASSWORD": "${MINIO_ROOT_PASSWORD:-admin123}"
                },
                "volumes": ["minio_data:/data"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "mc ready local || exit 0"],
                    "interval": "5s",
                    "timeout": "5s",
                    "retries": 5
                },
                "networks": [network_name]
            }
            volumes["minio_data"] = None

            services["minio-init"] = {
                "image": "minio/mc:RELEASE.2024-05-09T17-04-24Z",
                "container_name": f"{self.project_name}-minio-init",
                "depends_on": ["minio"],
                "environment": {
                    "MINIO_ROOT_USER": "${MINIO_ROOT_USER:-admin}",
                    "MINIO_ROOT_PASSWORD": "${MINIO_ROOT_PASSWORD:-admin123}"
                },
                "entrypoint": '/bin/sh -c "until (/usr/bin/mc alias set myminio http://minio:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD); do echo \'Waiting for MinIO...\'; sleep 2; done; /usr/bin/mc mb --ignore-existing myminio/lakehouse; /usr/bin/mc mb --ignore-existing myminio/warehouse; echo \'Buckets created successfully!\'; exit 0;"',
                "networks": [network_name]
            }

        # --- ICEBERG REST ---
        if "iceberg_rest" in self.tools:
            port = self.request.custom_ports.get("iceberg_rest", 8181)
            services["iceberg-rest"] = {
                "image": "tabulario/iceberg-rest:1.6.0",
                "container_name": f"{self.project_name}-iceberg-rest",
                "ports": [f"{port}:8181"],
                "depends_on": ["minio", "minio-init"] if "minio" in self.tools else [],
                "environment": {
                    "CATALOG_WAREHOUSE": "s3://lakehouse/",
                    "CATALOG_IO__IMPL": "org.apache.iceberg.aws.s3.S3FileIO",
                    "CATALOG_S3_ENDPOINT": "http://minio:9000",
                    "CATALOG_S3_PATH__STYLE__ACCESS": "true",
                    "AWS_ACCESS_KEY_ID": "${MINIO_ROOT_USER:-admin}",
                    "AWS_SECRET_ACCESS_KEY": "${MINIO_ROOT_PASSWORD:-admin123}",
                    "AWS_REGION": "us-east-1"
                },
                "networks": [network_name]
            }

        # --- APACHE SPARK ---
        if "spark" in self.tools:
            master_port = self.request.custom_ports.get("spark", 8082)
            apps_folder = self.request.custom_folders.get("spark_apps", "spark/apps")
            services["spark-master"] = {
                "build": {"context": "./spark"},
                "container_name": f"{self.project_name}-spark-master",
                "command": "/opt/spark/bin/spark-class org.apache.spark.deploy.master.Master",
                "ports": ["7077:7077", f"{master_port}:8080"],
                "environment": {"SPARK_NO_DAEMONIZE": "true"},
                "volumes": [f"./{apps_folder}:/opt/spark/work-dir/apps"],
                "networks": [network_name]
            }
            services["spark-worker"] = {
                "build": {"context": "./spark"},
                "container_name": f"{self.project_name}-spark-worker",
                "command": "/opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077",
                "environment": {
                    "SPARK_NO_DAEMONIZE": "true",
                    "SPARK_WORKER_CORES": 2,
                    "SPARK_WORKER_MEMORY": "2g"
                },
                "volumes": [f"./{apps_folder}:/opt/spark/work-dir/apps"],
                "depends_on": ["spark-master"],
                "networks": [network_name]
            }

        # --- APACHE FLINK ---
        if "flink" in self.tools:
            flink_port = self.request.custom_ports.get("flink", 8093)
            services["flink-jobmanager"] = {
                "image": "flink:1.19-scala_2.12-java11",
                "container_name": f"{self.project_name}-flink-jobmanager",
                "command": "jobmanager",
                "ports": [f"{flink_port}:8081"],
                "environment": {"FLINK_PROPERTIES": "jobmanager.rpc.address: flink-jobmanager"},
                "volumes": ["./flink/jobs:/opt/flink/usrlib", "flink_data:/opt/flink/data"],
                "networks": [network_name]
            }
            services["flink-taskmanager"] = {
                "image": "flink:1.19-scala_2.12-java11",
                "container_name": f"{self.project_name}-flink-taskmanager",
                "depends_on": ["flink-jobmanager"],
                "command": "taskmanager",
                "environment": {"FLINK_PROPERTIES": "jobmanager.rpc.address: flink-jobmanager\\ntaskmanager.numberOfTaskSlots: 2"},
                "volumes": ["./flink/jobs:/opt/flink/usrlib"],
                "networks": [network_name]
            }
            volumes["flink_data"] = None

        # --- TRINO ---
        if "trino" in self.tools:
            port = self.request.custom_ports.get("trino", 8085)
            services["trino"] = {
                "image": "trinodb/trino:450",
                "container_name": f"{self.project_name}-trino",
                "ports": [f"{port}:8080"],
                "volumes": ["./trino/etc:/etc/trino"],
                "networks": [network_name]
            }
            deps = []
            if "iceberg_rest" in self.tools:
                deps.append("iceberg-rest")
            if "minio" in self.tools:
                deps.append("minio")
            if deps:
                services["trino"]["depends_on"] = deps

        # --- SUPERSET ---
        if "superset" in self.tools:
            port = self.request.custom_ports.get("superset", 8094)
            services["superset"] = {
                "image": "apache/superset:4.0.1",
                "container_name": f"{self.project_name}-superset",
                "ports": [f"{port}:8088"],
                "environment": {
                    "SUPERSET_SECRET_KEY": "supersecretkey123456789",
                    "ADMIN_USERNAME": "${SUPERSET_ADMIN_USER:-admin}",
                    "ADMIN_PASSWORD": "${SUPERSET_ADMIN_PASSWORD:-admin}"
                },
                "volumes": ["superset_home:/app/superset_home"],
                "networks": [network_name]
            }
            volumes["superset_home"] = None

        # --- METABASE ---
        if "metabase" in self.tools:
            port = self.request.custom_ports.get("metabase", 3006)
            services["metabase"] = {
                "image": "metabase/metabase:latest",
                "container_name": f"{self.project_name}-metabase",
                "ports": [f"{port}:3000"],
                "volumes": ["metabase_data:/metabase-data"],
                "networks": [network_name]
            }
            volumes["metabase_data"] = None

        # --- DATAHUB ---
        if "datahub" in self.tools:
            port = self.request.custom_ports.get("datahub", 9002)
            services["datahub-gms"] = {
                "image": "linkedin/datahub-gms:latest",
                "container_name": f"{self.project_name}-datahub-gms",
                "ports": ["8080:8080"],
                "environment": {
                    "DATAHUB_BACKEND_TYPE": "POSTGRES",
                    "DATAHUB_DB_HOST": "postgres",
                    "DATAHUB_DB_NAME": "datahub"
                },
                "networks": [network_name]
            }
            services["datahub-frontend"] = {
                "image": "linkedin/datahub-frontend-react:latest",
                "container_name": f"{self.project_name}-datahub-frontend",
                "depends_on": ["datahub-gms"],
                "ports": [f"{port}:9002"],
                "environment": {"DATAHUB_GMS_HOST": "datahub-gms", "DATAHUB_GMS_PORT": "8080"},
                "networks": [network_name]
            }

        # --- RANGER ---
        if "ranger" in self.tools:
            port = self.request.custom_ports.get("ranger", 6080)
            services["ranger"] = {
                "image": "apache/ranger:2.4.0",
                "container_name": f"{self.project_name}-ranger",
                "ports": [f"{port}:6080"],
                "environment": {
                    "RANGER_ADMIN_PASSWORD": "${RANGER_ADMIN_PASSWORD:-admin123}",
                    "DB_HOST": "postgres" if "postgres" in self.tools else "localhost"
                },
                "networks": [network_name]
            }

        # --- AIRFLOW ---
        if "airflow" in self.tools:
            port = self.request.custom_ports.get("airflow", 8088)
            dags_folder = self.request.custom_folders.get("airflow_dags", "airflow/dags")
            plugins_folder = self.request.custom_folders.get("airflow_plugins", "airflow/plugins")
            
            services["airflow-db"] = {
                "image": "postgres:16-alpine",
                "container_name": f"{self.project_name}-airflow-db",
                "environment": {
                    "POSTGRES_USER": "airflow",
                    "POSTGRES_PASSWORD": "airflow",
                    "POSTGRES_DB": "airflow"
                },
                "volumes": ["airflow_db_data:/var/lib/postgresql/data"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U airflow -d airflow"],
                    "interval": "5s",
                    "timeout": "5s",
                    "retries": 5
                },
                "networks": [network_name]
            }
            volumes["airflow_db_data"] = None

            services["airflow-init"] = {
                "image": "apache/airflow:2.9.2-python3.11",
                "container_name": f"{self.project_name}-airflow-init",
                "depends_on": {
                    "airflow-db": {"condition": "service_healthy"}
                },
                "environment": {
                    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": "postgresql+psycopg2://airflow:airflow@airflow-db:5432/airflow",
                    "AIRFLOW_USER": "${AIRFLOW_USER:-admin}",
                    "AIRFLOW_PASSWORD": "${AIRFLOW_PASSWORD:-admin}"
                },
                "command": 'bash -c "airflow db migrate && (airflow users create --username $$AIRFLOW_USER --firstname Admin --lastname User --role Admin --email admin@example.com --password $$AIRFLOW_PASSWORD || airflow users set-password --username $$AIRFLOW_USER --password $$AIRFLOW_PASSWORD || true)"',
                "networks": [network_name]
            }

            services["airflow-webserver"] = {
                "image": "apache/airflow:2.9.2-python3.11",
                "container_name": f"{self.project_name}-airflow-webserver",
                "ports": [f"{port}:8080"],
                "depends_on": {
                    "airflow-init": {"condition": "service_completed_successfully"}
                },
                "environment": {
                    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": "postgresql+psycopg2://airflow:airflow@airflow-db:5432/airflow",
                    "AIRFLOW__CORE__LOAD_EXAMPLES": "false",
                    "AIRFLOW__CORE__EXECUTOR": "LocalExecutor"
                },
                "volumes": [
                    f"./{dags_folder}:/opt/airflow/dags",
                    f"./{plugins_folder}:/opt/airflow/plugins"
                ],
                "command": "airflow webserver",
                "networks": [network_name]
            }

            services["airflow-scheduler"] = {
                "image": "apache/airflow:2.9.2-python3.11",
                "container_name": f"{self.project_name}-airflow-scheduler",
                "depends_on": {
                    "airflow-init": {"condition": "service_completed_successfully"}
                },
                "environment": {
                    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": "postgresql+psycopg2://airflow:airflow@airflow-db:5432/airflow",
                    "AIRFLOW__CORE__LOAD_EXAMPLES": "false",
                    "AIRFLOW__CORE__EXECUTOR": "LocalExecutor"
                },
                "volumes": [
                    f"./{dags_folder}:/opt/airflow/dags",
                    f"./{plugins_folder}:/opt/airflow/plugins"
                ],
                "command": "airflow scheduler",
                "networks": [network_name]
            }

        # --- MAGE.AI ---
        if "mage" in self.tools:
            port = self.request.custom_ports.get("mage", 6789)
            services["mage"] = {
                "image": "mageai/mageai:latest",
                "container_name": f"{self.project_name}-mage",
                "ports": [f"{port}:6789"],
                "volumes": ["./mage:/home/src"],
                "networks": [network_name]
            }

        # --- PREFECT ---
        if "prefect" in self.tools:
            port = self.request.custom_ports.get("prefect", 4200)
            services["prefect"] = {
                "image": "prefecthq/prefect:2-latest",
                "container_name": f"{self.project_name}-prefect",
                "command": "prefect server start --host 0.0.0.0",
                "ports": [f"{port}:4200"],
                "volumes": ["prefect_data:/root/.prefect"],
                "networks": [network_name]
            }
            volumes["prefect_data"] = None

        # --- TEMPORAL ---
        if "temporal" in self.tools:
            ui_port = self.request.custom_ports.get("temporal", 8233)
            services["temporal"] = {
                "image": "temporalio/auto-setup:1.24.1",
                "container_name": f"{self.project_name}-temporal",
                "ports": ["7233:7233"],
                "environment": {"DB": "postgresql", "POSTGRES_USER": "temporal", "POSTGRES_PWD": "temporalpassword", "POSTGRES_SEEDS": "postgres" if "postgres" in self.tools else "temporal-db"},
                "networks": [network_name]
            }
            services["temporal-ui"] = {
                "image": "temporalio/ui:2.26.2",
                "container_name": f"{self.project_name}-temporal-ui",
                "depends_on": ["temporal"],
                "ports": [f"{ui_port}:8080"],
                "environment": {"TEMPORAL_ADDRESS": "temporal:7233"},
                "networks": [network_name]
            }

        # --- N8N ---
        if "n8n" in self.tools:
            port = self.request.custom_ports.get("n8n", 5678)
            services["n8n"] = {
                "image": "n8nio/n8n:latest",
                "container_name": f"{self.project_name}-n8n",
                "ports": [f"{port}:5678"],
                "environment": {"N8N_BASIC_AUTH_ACTIVE": "false"},
                "volumes": ["n8n_data:/home/node/.n8n", "./n8n/workflows:/data/workflows"],
                "networks": [network_name]
            }
            volumes["n8n_data"] = None

        # --- HASHICORP VAULT ---
        if "vault" in self.tools:
            port = self.request.custom_ports.get("vault", 8200)
            services["vault"] = {
                "image": "hashicorp/vault:1.16.2",
                "container_name": f"{self.project_name}-vault",
                "ports": [f"{port}:8200"],
                "environment": {
                    "VAULT_DEV_ROOT_TOKEN_ID": "${VAULT_DEV_ROOT_TOKEN_ID:-root}",
                    "VAULT_DEV_LISTEN_ADDRESS": "0.0.0.0:8200"
                },
                "cap_add": ["IPC_LOCK"],
                "volumes": ["./vault/config:/vault/config", "./vault/policies:/vault/policies"],
                "networks": [network_name]
            }

        # --- MLFLOW ---
        if "mlflow" in self.tools:
            port = self.request.custom_ports.get("mlflow", 5001)
            services["mlflow"] = {
                "image": "ghcr.io/mlflow/mlflow:v2.13.0",
                "container_name": f"{self.project_name}-mlflow",
                "ports": [f"{port}:5000"],
                "command": "mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root /mlflow/artifacts --host 0.0.0.0 --port 5000",
                "volumes": ["./mlflow/artifacts:/mlflow/artifacts"],
                "networks": [network_name]
            }

        # --- JUPYTERLAB ---
        if "jupyterlab" in self.tools:
            port = self.request.custom_ports.get("jupyterlab", 8888)
            services["jupyterlab"] = {
                "image": "jupyter/scipy-notebook:latest",
                "container_name": f"{self.project_name}-jupyterlab",
                "ports": [f"{port}:8888"],
                "environment": {"JUPYTER_ENABLE_LAB": "yes", "NOTEBOOK_ARGS": "--NotebookApp.token=''"},
                "volumes": ["./notebooks:/home/jovyan/work"],
                "networks": [network_name]
            }

        # --- QDRANT ---
        if "qdrant" in self.tools:
            port = self.request.custom_ports.get("qdrant", 6333)
            services["qdrant"] = {
                "image": "qdrant/qdrant:latest",
                "container_name": f"{self.project_name}-qdrant",
                "ports": [f"{port}:6333", "6334:6334"],
                "volumes": ["qdrant_data:/qdrant/storage"],
                "networks": [network_name]
            }
            volumes["qdrant_data"] = None

        # --- MILVUS ---
        if "milvus" in self.tools:
            attu_port = self.request.custom_ports.get("milvus", 8008)
            services["milvus-standalone"] = {
                "image": "milvusdb/milvus:v2.4.0",
                "container_name": f"{self.project_name}-milvus",
                "command": ["milvus", "run", "standalone"],
                "ports": ["19530:19530", "9091:9091"],
                "volumes": ["milvus_data:/var/lib/milvus"],
                "networks": [network_name]
            }
            services["milvus-attu"] = {
                "image": "zilliz/attu:v2.4.0",
                "container_name": f"{self.project_name}-milvus-attu",
                "depends_on": ["milvus-standalone"],
                "ports": [f"{attu_port}:3000"],
                "environment": {"MILVUS_URL": "milvus-standalone:19530"},
                "networks": [network_name]
            }
            volumes["milvus_data"] = None

        # --- WEAVIATE ---
        if "weaviate" in self.tools:
            port = self.request.custom_ports.get("weaviate", 8079)
            services["weaviate"] = {
                "image": "semitechnologies/weaviate:1.24.10",
                "container_name": f"{self.project_name}-weaviate",
                "ports": [f"{port}:8080", "50051:50051"],
                "environment": {
                    "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
                    "PERSISTENCE_DATA_PATH": "/var/lib/weaviate",
                    "DEFAULT_VECTORIZER_MODULE": "none"
                },
                "volumes": ["weaviate_data:/var/lib/weaviate"],
                "networks": [network_name]
            }
            volumes["weaviate_data"] = None

        # --- EVIDENTLY AI ---
        if "evidently" in self.tools:
            port = self.request.custom_ports.get("evidently", 8009)
            services["evidently"] = {
                "image": "evidently/evidently-service:latest",
                "container_name": f"{self.project_name}-evidently",
                "ports": [f"{port}:8000"],
                "volumes": ["./evidently/workspace:/workspace"],
                "networks": [network_name]
            }

        # --- REDIS ---
        if "redis" in self.tools:
            port = self.request.custom_ports.get("redis", 6380)
            services["redis"] = {
                "image": "redis:7-alpine",
                "container_name": f"{self.project_name}-redis",
                "ports": [f"{port}:6379"],
                "volumes": ["redis_data:/data"],
                "networks": [network_name]
            }
            services["redis-commander"] = {
                "image": "rediscommander/redis-commander:latest",
                "container_name": f"{self.project_name}-redis-commander",
                "ports": ["8089:8081"],
                "environment": {"REDIS_HOSTS": "local:redis:6379"},
                "depends_on": ["redis"],
                "networks": [network_name]
            }
            volumes["redis_data"] = None

        # --- RABBITMQ ---
        if "rabbitmq" in self.tools:
            mgmt_port = self.request.custom_ports.get("rabbitmq", 15672)
            services["rabbitmq"] = {
                "image": "rabbitmq:3-management-alpine",
                "container_name": f"{self.project_name}-rabbitmq",
                "ports": ["5673:5672", f"{mgmt_port}:15672"],
                "environment": {
                    "RABBITMQ_DEFAULT_USER": "${RABBITMQ_DEFAULT_USER:-guest}",
                    "RABBITMQ_DEFAULT_PASS": "${RABBITMQ_DEFAULT_PASS:-guest}"
                },
                "volumes": ["rabbitmq_data:/var/lib/rabbitmq"],
                "networks": [network_name]
            }
            volumes["rabbitmq_data"] = None

        # --- KEYCLOAK ---
        if "keycloak" in self.tools:
            port = self.request.custom_ports.get("keycloak", 8090)
            services["keycloak"] = {
                "image": "quay.io/keycloak/keycloak:24.0.4",
                "container_name": f"{self.project_name}-keycloak",
                "command": "start-dev",
                "ports": [f"{port}:8080"],
                "environment": {
                    "KEYCLOAK_ADMIN": "${KEYCLOAK_ADMIN:-admin}",
                    "KEYCLOAK_ADMIN_PASSWORD": "${KEYCLOAK_ADMIN_PASSWORD:-admin}"
                },
                "volumes": ["keycloak_data:/opt/keycloak/data"],
                "networks": [network_name]
            }
            volumes["keycloak_data"] = None

        # --- HASURA ---
        if "hasura" in self.tools:
            port = self.request.custom_ports.get("hasura", 8095)
            services["hasura"] = {
                "image": "hasura/graphql-engine:v2.38.0",
                "container_name": f"{self.project_name}-hasura",
                "ports": [f"{port}:8080"],
                "environment": {
                    "HASURA_GRAPHQL_DATABASE_URL": "postgres://admin:admin123@postgres:5432/oltp_db",
                    "HASURA_GRAPHQL_ENABLE_CONSOLE": "true",
                    "HASURA_GRAPHQL_DEV_MODE": "true",
                    "HASURA_GRAPHQL_ADMIN_SECRET": "myadminsecretkey"
                },
                "networks": [network_name]
            }
            if "postgres" in self.tools:
                services["hasura"]["depends_on"] = ["postgres"]

        # --- GRAFANA ---
        if "grafana" in self.tools:
            port = self.request.custom_ports.get("grafana", 3005)
            services["grafana"] = {
                "image": "grafana/grafana:11.0.0",
                "container_name": f"{self.project_name}-grafana",
                "ports": [f"{port}:3000"],
                "environment": {
                    "GF_SECURITY_ADMIN_USER": "${GF_SECURITY_ADMIN_USER:-admin}",
                    "GF_SECURITY_ADMIN_PASSWORD": "${GF_SECURITY_ADMIN_PASSWORD:-admin}"
                },
                "volumes": ["grafana_data:/var/lib/grafana"],
                "networks": [network_name]
            }
            volumes["grafana_data"] = None

        # --- PROMETHEUS ---
        if "prometheus" in self.tools:
            port = self.request.custom_ports.get("prometheus", 9095)
            services["prometheus"] = {
                "image": "prom/prometheus:v2.53.0",
                "container_name": f"{self.project_name}-prometheus",
                "ports": [f"{port}:9090"],
                "volumes": ["prometheus_data:/prometheus"],
                "networks": [network_name]
            }
            volumes["prometheus_data"] = None

        # --- LOKI & PROMTAIL ---
        if "loki" in self.tools:
            loki_port = self.request.custom_ports.get("loki", 3100)
            services["loki"] = {
                "image": "grafana/loki:3.0.0",
                "container_name": f"{self.project_name}-loki",
                "ports": [f"{loki_port}:3100"],
                "command": "-config.file=/etc/loki/local-config.yaml",
                "volumes": ["loki_data:/loki", "./loki/loki-config.yaml:/etc/loki/local-config.yaml"],
                "networks": [network_name]
            }
            services["promtail"] = {
                "image": "grafana/promtail:3.0.0",
                "container_name": f"{self.project_name}-promtail",
                "depends_on": ["loki"],
                "command": "-config.file=/etc/promtail/config.yml",
                "volumes": ["/var/log:/var/log:ro", "/var/run/docker.sock:/var/run/docker.sock", "./loki/promtail-config.yaml:/etc/promtail/config.yml"],
                "networks": [network_name]
            }
            volumes["loki_data"] = None

        # --- JAEGER ---
        if "jaeger" in self.tools:
            jaeger_port = self.request.custom_ports.get("jaeger", 16686)
            services["jaeger"] = {
                "image": "jaegertracing/all-in-one:1.57",
                "container_name": f"{self.project_name}-jaeger",
                "ports": [f"{jaeger_port}:16686", "4317:4317", "4318:4318", "14268:14268"],
                "environment": {"COLLECTOR_OTLP_ENABLED": "true"},
                "networks": [network_name]
            }

        # --- TRAEFIK ---
        if "traefik" in self.tools:
            port = self.request.custom_ports.get("traefik", 8081)
            services["traefik"] = {
                "image": "traefik:v3.0",
                "container_name": f"{self.project_name}-traefik",
                "command": ["--api.insecure=true", "--providers.docker=true", "--providers.docker.exposedbydefault=false", "--entrypoints.web.address=:80"],
                "ports": ["80:80", f"{port}:8080"],
                "volumes": ["/var/run/docker.sock:/var/run/docker.sock:ro", "./traefik/dynamic_conf.yml:/etc/traefik/dynamic_conf.yml:ro"],
                "networks": [network_name]
            }

        # --- ARGOCD ---
        if "argocd" in self.tools:
            port = self.request.custom_ports.get("argocd", 8098)
            services["argocd"] = {
                "image": "quay.io/argoproj/argocd:v2.11.0",
                "container_name": f"{self.project_name}-argocd",
                "command": "argocd-server --insecure --port 8080",
                "ports": [f"{port}:8080"],
                "volumes": ["./argocd:/workspace/argocd"],
                "networks": [network_name]
            }

        # --- WAZUH (SIEM & XDR) ---
        if "wazuh" in self.tools:
            dashboard_port = self.request.custom_ports.get("wazuh", 8444)
            services["wazuh-manager"] = {
                "image": "wazuh/wazuh-manager:4.7.5",
                "container_name": f"{self.project_name}-wazuh-manager",
                "ports": ["1514:1514", "1515:1515", "55000:55000"],
                "volumes": ["wazuh_api:/var/ossec/api/configuration", "wazuh_etc:/var/ossec/etc", "./wazuh/rules:/var/ossec/etc/rules"],
                "networks": [network_name]
            }
            services["wazuh-dashboard"] = {
                "image": "wazuh/wazuh-dashboard:4.7.5",
                "container_name": f"{self.project_name}-wazuh-dashboard",
                "depends_on": ["wazuh-manager"],
                "ports": [f"{dashboard_port}:5601"],
                "environment": {"WAZUH_API_URL": "https://wazuh-manager:55000"},
                "networks": [network_name]
            }
            volumes["wazuh_api"] = None
            volumes["wazuh_etc"] = None

        # --- SPLUNK ---
        if "splunk" in self.tools:
            port = self.request.custom_ports.get("splunk", 8001)
            services["splunk"] = {
                "image": "splunk/splunk:9.2.1",
                "container_name": f"{self.project_name}-splunk",
                "ports": [f"{port}:8000", "8088:8088", "9997:9997"],
                "environment": {
                    "SPLUNK_START_ARGS": "${SPLUNK_START_ARGS:---accept-license}",
                    "SPLUNK_PASSWORD": "${SPLUNK_PASSWORD:-AdminPassword123!}"
                },
                "volumes": ["splunk_data:/opt/splunk/var", "./splunk/apps:/opt/splunk/etc/apps"],
                "networks": [network_name]
            }
            volumes["splunk_data"] = None

        # --- ELASTIC SECURITY ---
        if "elastic_security" in self.tools:
            port = self.request.custom_ports.get("elastic_security", 5602)
            services["elastic-security"] = {
                "image": "docker.elastic.co/kibana/kibana:8.13.4",
                "container_name": f"{self.project_name}-elastic-security",
                "ports": [f"{port}:5601"],
                "environment": {"ELASTICSEARCH_HOSTS": "http://elasticsearch:9200", "XPACK_SECURITY_ENABLED": "true"},
                "networks": [network_name]
            }

        # --- THEHIVE & CORTEX ---
        if "thehive" in self.tools:
            hive_port = self.request.custom_ports.get("thehive", 9004)
            services["thehive"] = {
                "image": "strangebee/thehive:5.2",
                "container_name": f"{self.project_name}-thehive",
                "ports": [f"{hive_port}:9000"],
                "environment": {"SECRET": "thehivesecretkey123456789"},
                "volumes": ["thehive_data:/etc/thehive/application.conf", "./thehive/data:/data"],
                "networks": [network_name]
            }
            services["cortex"] = {
                "image": "thehiveproject/cortex:3.1.8",
                "container_name": f"{self.project_name}-cortex",
                "ports": ["9005:9001"],
                "environment": {"SECRET": "cortexsecretkey123456789"},
                "volumes": ["./cortex/analyzers:/opt/cortex/analyzers"],
                "networks": [network_name]
            }
            volumes["thehive_data"] = None

        # --- MISP ---
        if "misp" in self.tools:
            port = self.request.custom_ports.get("misp", 8084)
            services["misp"] = {
                "image": "coolacid/misp-docker:core-latest",
                "container_name": f"{self.project_name}-misp",
                "ports": [f"{port}:80"],
                "environment": {"ADMIN_EMAIL": "admin@admin.test", "ADMIN_PASSPHRASE": "adminpass123"},
                "volumes": ["misp_data:/var/www/MISP", "./misp/feeds:/feeds"],
                "networks": [network_name]
            }
            volumes["misp_data"] = None

        # --- SHUFFLE SOAR ---
        if "shuffle" in self.tools:
            port = self.request.custom_ports.get("shuffle", 3001)
            services["shuffle-frontend"] = {
                "image": "ghcr.io/shuffle/shuffle-frontend:latest",
                "container_name": f"{self.project_name}-shuffle-frontend",
                "ports": [f"{port}:80", "3443:443"],
                "networks": [network_name]
            }
            services["shuffle-backend"] = {
                "image": "ghcr.io/shuffle/shuffle-backend:latest",
                "container_name": f"{self.project_name}-shuffle-backend",
                "ports": ["33333:3333"],
                "environment": {"SHUFFLE_APP_FORCE_PULL": "false"},
                "volumes": ["/var/run/docker.sock:/var/run/docker.sock", "./shuffle/workflows:/workflows"],
                "networks": [network_name]
            }

        # --- SURICATA ---
        if "suricata" in self.tools:
            services["suricata"] = {
                "image": "jasonish/suricata:latest",
                "container_name": f"{self.project_name}-suricata",
                "command": "-i eth0",
                "volumes": ["./suricata/rules:/var/lib/suricata/rules", "./suricata/logs:/var/log/suricata"],
                "networks": [network_name]
            }

        # --- ZEEK ---
        if "zeek" in self.tools:
            services["zeek"] = {
                "image": "zeek/zeek:latest",
                "container_name": f"{self.project_name}-zeek",
                "command": "tail -f /dev/null",
                "volumes": ["./zeek/scripts:/usr/local/zeek/share/zeek/site", "./zeek/logs:/usr/local/zeek/logs"],
                "networks": [network_name]
            }

        # --- OPENVAS ---
        if "openvas" in self.tools:
            port = self.request.custom_ports.get("openvas", 9392)
            services["openvas"] = {
                "image": "greenbone/openvas-scanner:latest",
                "container_name": f"{self.project_name}-openvas",
                "ports": [f"{port}:9392"],
                "volumes": ["openvas_data:/var/lib/openvas", "./openvas/scans:/scans"],
                "networks": [network_name]
            }
            volumes["openvas_data"] = None

        # --- NMAP SANDBOX ---
        if "nmap" in self.tools:
            services["nmap"] = {
                "image": "instrumentisto/nmap:latest",
                "container_name": f"{self.project_name}-nmap",
                "command": "tail -f /dev/null",
                "volumes": ["./nmap/scans:/scans", "./nmap/scripts:/scripts"],
                "networks": [network_name]
            }

        # --- METASPLOIT SANDBOX ---
        if "metasploit" in self.tools:
            services["metasploit"] = {
                "image": "metasploitframework/metasploit-framework:latest",
                "container_name": f"{self.project_name}-metasploit",
                "command": "tail -f /dev/null",
                "volumes": ["./metasploit/workspace:/workspace", "./metasploit/modules:/modules"],
                "networks": [network_name]
            }

        # --- SONARQUBE ---
        if "sonarqube" in self.tools:
            port = self.request.custom_ports.get("sonarqube", 9003)
            services["sonarqube"] = {
                "image": "sonarqube:community",
                "container_name": f"{self.project_name}-sonarqube",
                "ports": [f"{port}:9000"],
                "volumes": ["sonarqube_data:/opt/sonarqube/data", "./sonarqube/conf:/opt/sonarqube/conf"],
                "networks": [network_name]
            }
            volumes["sonarqube_data"] = None

        # --- TRIVY ---
        if "trivy" in self.tools:
            port = self.request.custom_ports.get("trivy", 4954)
            services["trivy"] = {
                "image": "aquasec/trivy:latest",
                "container_name": f"{self.project_name}-trivy",
                "command": "server --listen 0.0.0.0:4954",
                "ports": [f"{port}:4954"],
                "volumes": ["/var/run/docker.sock:/var/run/docker.sock", "./trivy/reports:/reports"],
                "networks": [network_name]
            }

        # --- DEFECTDOJO ---
        if "defectdojo" in self.tools:
            port = self.request.custom_ports.get("defectdojo", 8096)
            services["defectdojo"] = {
                "image": "defectdojo/defectdojo-django:latest",
                "container_name": f"{self.project_name}-defectdojo",
                "ports": [f"{port}:8080"],
                "environment": {
                    "DD_ADMIN_USER": "${DEFECT_DOJO_ADMIN_USER:-admin}",
                    "DD_ADMIN_PASSWORD": "${DEFECT_DOJO_ADMIN_PASSWORD:-adminpassword123}"
                },
                "volumes": ["defectdojo_media:/app/media", "./defectdojo/imports:/imports"],
                "networks": [network_name]
            }
            volumes["defectdojo_media"] = None

        # --- OWASP ZAP ---
        if "zap" in self.tools:
            port = self.request.custom_ports.get("zap", 8097)
            services["zap"] = {
                "image": "zaproxy/zap-stable:latest",
                "container_name": f"{self.project_name}-zap",
                "command": "zap-webswing.sh",
                "ports": [f"{port}:8080", "8090:8090"],
                "volumes": ["./zap/scans:/zap/wrk", "./zap/scripts:/zap/scripts"],
                "networks": [network_name]
            }

        # --- GITLEAKS ---
        if "gitleaks" in self.tools:
            services["gitleaks"] = {
                "image": "zricethezav/gitleaks:latest",
                "container_name": f"{self.project_name}-gitleaks",
                "command": "tail -f /dev/null",
                "volumes": ["./:/repo:ro", "./gitleaks/reports:/reports", "./gitleaks/rules:/rules"],
                "networks": [network_name]
            }

        # --- TRUFFLEHOG ---
        if "trufflehog" in self.tools:
            services["trufflehog"] = {
                "image": "trufflesecurity/trufflehog:latest",
                "container_name": f"{self.project_name}-trufflehog",
                "command": "tail -f /dev/null",
                "volumes": ["./:/repo:ro", "./trufflehog/reports:/reports"],
                "networks": [network_name]
            }

        # --- TELEPORT ---
        if "teleport" in self.tools:
            port = self.request.custom_ports.get("teleport", 3080)
            services["teleport"] = {
                "image": "quay.io/gravitational/teleport:15.2.0",
                "container_name": f"{self.project_name}-teleport",
                "ports": [f"{port}:3080", "3022:3022", "3023:3023", "3025:3025"],
                "volumes": ["teleport_data:/var/lib/teleport", "./teleport/config:/etc/teleport"],
                "networks": [network_name]
            }
            volumes["teleport_data"] = None

        # --- AUTHENTIK ---
        if "authentik" in self.tools:
            port = self.request.custom_ports.get("authentik", 9006)
            services["authentik-server"] = {
                "image": "ghcr.io/goauthentik/server:2024.4.2",
                "container_name": f"{self.project_name}-authentik-server",
                "command": "server",
                "ports": [f"{port}:9000", "9443:9443"],
                "environment": {
                    "AUTHENTIK_SECRET_KEY": "${AUTHENTIK_SECRET_KEY:-authentiksecretkey123}",
                    "AUTHENTIK_REDIS__HOST": "redis" if "redis" in self.tools else "localhost"
                },
                "volumes": ["authentik_media:/media", "./authentik/custom_templates:/templates"],
                "networks": [network_name]
            }
            services["authentik-worker"] = {
                "image": "ghcr.io/goauthentik/server:2024.4.2",
                "container_name": f"{self.project_name}-authentik-worker",
                "command": "worker",
                "environment": {
                    "AUTHENTIK_SECRET_KEY": "${AUTHENTIK_SECRET_KEY:-authentiksecretkey123}",
                    "AUTHENTIK_REDIS__HOST": "redis" if "redis" in self.tools else "localhost"
                },
                "networks": [network_name]
            }
            volumes["authentik_media"] = None

        # --- PORTAINER ---
        if "portainer" in self.tools:
            port = self.request.custom_ports.get("portainer", 9443)
            services["portainer"] = {
                "image": "portainer/portainer-ce:latest",
                "container_name": f"{self.project_name}-portainer",
                "ports": ["9005:9000", f"{port}:9443"],
                "volumes": ["/var/run/docker.sock:/var/run/docker.sock", "portainer_data:/data"],
                "networks": [network_name]
            }
            volumes["portainer_data"] = None

        # --- PGADMIN ---
        if "pgadmin" in self.tools:
            port = self.request.custom_ports.get("pgadmin", 5055)
            services["pgadmin"] = {
                "image": "dpage/pgadmin4:latest",
                "container_name": f"{self.project_name}-pgadmin",
                "ports": [f"{port}:80"],
                "environment": {
                    "PGADMIN_DEFAULT_EMAIL": "admin@lakehouse.com",
                    "PGADMIN_DEFAULT_PASSWORD": "${PGADMIN_DEFAULT_PASSWORD:-admin}"
                },
                "volumes": ["pgadmin_data:/var/lib/pgadmin"],
                "networks": [network_name]
            }
            volumes["pgadmin_data"] = None

        # --- OPENTELEMETRY ---
        if "opentelemetry" in self.tools:
            port = self.request.custom_ports.get("opentelemetry", 4318)
            services["opentelemetry"] = {
                "image": "otel/opentelemetry-collector-contrib:0.100.0",
                "container_name": f"{self.project_name}-opentelemetry",
                "ports": ["4317:4317", f"{port}:4318", "8889:8889", "13133:13133"],
                "volumes": ["./otel/otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml"],
                "networks": [network_name]
            }

        # --- OPENMETADATA ---
        if "openmetadata" in self.tools:
            port = self.request.custom_ports.get("openmetadata", 8585)
            services["openmetadata"] = {
                "image": "openmetadata/server:1.4.1",
                "container_name": f"{self.project_name}-openmetadata",
                "ports": [f"{port}:8585"],
                "environment": {
                    "DB_HOST": "postgres",
                    "DB_PORT": "5432",
                    "DB_USER": "${POSTGRES_USER:-admin}",
                    "DB_USER_PASSWORD": "${POSTGRES_PASSWORD:-admin123}",
                    "DB_SCHEME": "postgresql"
                },
                "depends_on": ["postgres"] if "postgres" in self.tools else [],
                "networks": [network_name]
            }

        # --- NGINX ---
        if "nginx" in self.tools:
            port = self.request.custom_ports.get("nginx", 8088)
            services["nginx"] = {
                "image": "nginx:alpine",
                "container_name": f"{self.project_name}-nginx",
                "ports": [f"{port}:80"],
                "volumes": ["./nginx/nginx.conf:/etc/nginx/nginx.conf:ro", "./nginx/html:/usr/share/nginx/html:ro"],
                "networks": [network_name]
            }

        # --- KONG API GATEWAY ---
        if "apigateway" in self.tools:
            port = self.request.custom_ports.get("apigateway", 8000)
            services["kong"] = {
                "image": "kong:3.6-alpine",
                "container_name": f"{self.project_name}-kong",
                "ports": [f"{port}:8000", "8443:8443", "8002:8002"],
                "environment": {
                    "KONG_DATABASE": "off",
                    "KONG_DECLARATIVE_CONFIG": "/kong/kong.yml",
                    "KONG_PROXY_ACCESS_LOG": "/dev/stdout",
                    "KONG_ADMIN_ACCESS_LOG": "/dev/stdout",
                    "KONG_PROXY_ERROR_LOG": "/dev/stderr",
                    "KONG_ADMIN_ERROR_LOG": "/dev/stderr",
                    "KONG_ADMIN_LISTEN": "0.0.0.0:8002"
                },
                "volumes": ["./kong/kong.yml:/kong/kong.yml"],
                "networks": [network_name]
            }

        # --- HADOOP HDFS ---
        if "hdfs" in self.tools:
            port = self.request.custom_ports.get("hdfs", 9870)
            services["namenode"] = {
                "image": "bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8",
                "container_name": f"{self.project_name}-namenode",
                "environment": {"CLUSTER_NAME": "hadoop-cluster"},
                "ports": [f"{port}:9870", "9000:9000"],
                "volumes": ["hadoop_namenode:/hadoop/dfs/name"],
                "networks": [network_name]
            }
            services["datanode"] = {
                "image": "bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8",
                "container_name": f"{self.project_name}-datanode",
                "depends_on": ["namenode"],
                "environment": {"CLUSTER_NAME": "hadoop-cluster", "CORE_CONF_fs_defaultFS": "hdfs://namenode:9000"},
                "ports": ["9864:9864"],
                "volumes": ["hadoop_datanode:/hadoop/dfs/data"],
                "networks": [network_name]
            }
            volumes["hadoop_namenode"] = None
            volumes["hadoop_datanode"] = None

        # --- HADOOP YARN ---
        if "yarn" in self.tools:
            port = self.request.custom_ports.get("yarn", 8089)
            services["resourcemanager"] = {
                "image": "bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8",
                "container_name": f"{self.project_name}-resourcemanager",
                "depends_on": ["namenode"] if "hdfs" in self.tools else [],
                "ports": [f"{port}:8088"],
                "environment": {"CORE_CONF_fs_defaultFS": "hdfs://namenode:9000"},
                "networks": [network_name]
            }
            services["nodemanager"] = {
                "image": "bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8",
                "container_name": f"{self.project_name}-nodemanager",
                "depends_on": ["resourcemanager"],
                "environment": {"CORE_CONF_fs_defaultFS": "hdfs://namenode:9000", "YARN_CONF_yarn_resourcemanager_hostname": "resourcemanager"},
                "ports": ["8042:8042"],
                "networks": [network_name]
            }

        # --- HIVE ---
        if "hive" in self.tools:
            hive_ui_port = self.request.custom_ports.get("hive", 10002)
            services["hive-metastore"] = {
                "image": "bde2020/hive:2.3.2-postgresql-metastore",
                "container_name": f"{self.project_name}-hive-metastore",
                "depends_on": ["postgres"] if "postgres" in self.tools else [],
                "environment": {
                    "HIVE_CORE_CONF_javax_jdo_option_ConnectionURL": "jdbc:postgresql://postgres:5432/metastore_db",
                    "HIVE_CORE_CONF_javax_jdo_option_ConnectionDriverName": "org.postgresql.Driver",
                    "HIVE_CORE_CONF_javax_jdo_option_ConnectionUserName": "${POSTGRES_USER:-admin}",
                    "HIVE_CORE_CONF_javax_jdo_option_ConnectionPassword": "${POSTGRES_PASSWORD:-admin123}",
                    "CORE_CONF_fs_defaultFS": "hdfs://namenode:9000" if "hdfs" in self.tools else "file:///tmp/warehouse"
                },
                "ports": ["9083:9083"],
                "networks": [network_name]
            }
            services["hive-server"] = {
                "image": "bde2020/hive:2.3.2-postgresql-metastore",
                "container_name": f"{self.project_name}-hive-server",
                "depends_on": ["hive-metastore"],
                "environment": {
                    "HIVE_CORE_CONF_javax_jdo_option_ConnectionURL": "jdbc:postgresql://postgres:5432/metastore_db",
                    "HIVE_CORE_CONF_javax_jdo_option_ConnectionDriverName": "org.postgresql.Driver",
                    "HIVE_CORE_CONF_javax_jdo_option_ConnectionUserName": "${POSTGRES_USER:-admin}",
                    "HIVE_CORE_CONF_javax_jdo_option_ConnectionPassword": "${POSTGRES_PASSWORD:-admin123}",
                    "CORE_CONF_fs_defaultFS": "hdfs://namenode:9000" if "hdfs" in self.tools else "file:///tmp/warehouse"
                },
                "ports": [f"{hive_ui_port}:10002", "10000:10000"],
                "command": "/opt/hive/bin/hive --service hiveserver2",
                "volumes": ["./hive/warehouse:/opt/hive/warehouse"],
                "networks": [network_name]
            }

        # --- ZEPPELIN ---
        if "zeppelin" in self.tools:
            zeppelin_port = self.request.custom_ports.get("zeppelin", 8090)
            services["zeppelin"] = {
                "image": "apache/zeppelin:0.10.1",
                "container_name": f"{self.project_name}-zeppelin",
                "environment": {"ZEPPELIN_PORT": "8080", "ZEPPELIN_ANONYMOUS": "true"},
                "ports": [f"{zeppelin_port}:8080"],
                "volumes": ["./zeppelin/notebook:/opt/zeppelin/notebook"],
                "networks": [network_name]
            }

        # --- OLLAMA ---
        if "ollama" in self.tools:
            ollama_port = self.request.custom_ports.get("ollama", 11434)
            services["ollama"] = {
                "image": "ollama/ollama:latest",
                "container_name": f"{self.project_name}-ollama",
                "ports": [f"{ollama_port}:11434"],
                "volumes": ["./ollama/models:/root/.ollama"],
                "networks": [network_name]
            }

        # --- OPEN WEBUI ---
        if "open_webui" in self.tools:
            webui_port = self.request.custom_ports.get("open_webui", 3000)
            services["open-webui"] = {
                "image": "ghcr.io/open-webui/open-webui:main",
                "container_name": f"{self.project_name}-open-webui",
                "ports": [f"{webui_port}:8080"],
                "depends_on": ["ollama"] if "ollama" in self.tools else [],
                "environment": {"OLLAMA_BASE_URL": "http://ollama:11434"},
                "volumes": ["open_webui_data:/app/backend/data"],
                "networks": [network_name]
            }
            volumes["open_webui_data"] = None

        # --- LOCALAI ---
        if "localai" in self.tools:
            localai_port = self.request.custom_ports.get("localai", 8091)
            services["localai"] = {
                "image": "localai/localai:latest-cpu",
                "container_name": f"{self.project_name}-localai",
                "ports": [f"{localai_port}:8080"],
                "environment": {"DEBUG": "true"},
                "volumes": ["localai_models:/build/models"],
                "networks": [network_name]
            }
            volumes["localai_models"] = None

        # --- OS SANDBOXES ---
        if "ubuntu_sandbox" in self.tools:
            services["ubuntu-sandbox"] = {
                "image": "ubuntu:24.04",
                "container_name": f"{self.project_name}-ubuntu-sandbox",
                "command": "tail -f /dev/null",
                "working_dir": "/workspace",
                "volumes": ["./workspace:/workspace"],
                "networks": [network_name]
            }

        if "debian_sandbox" in self.tools:
            services["debian-sandbox"] = {
                "image": "debian:bookworm-slim",
                "container_name": f"{self.project_name}-debian-sandbox",
                "command": "tail -f /dev/null",
                "working_dir": "/workspace",
                "volumes": ["./workspace:/workspace"],
                "networks": [network_name]
            }

        if "alpine_sandbox" in self.tools:
            services["alpine-sandbox"] = {
                "image": "alpine:latest",
                "container_name": f"{self.project_name}-alpine-sandbox",
                "command": "tail -f /dev/null",
                "working_dir": "/workspace",
                "volumes": ["./workspace:/workspace"],
                "networks": [network_name]
            }

        if "arch_sandbox" in self.tools:
            services["arch-sandbox"] = {
                "image": "archlinux:latest",
                "container_name": f"{self.project_name}-arch-sandbox",
                "command": "tail -f /dev/null",
                "working_dir": "/workspace",
                "volumes": ["./workspace:/workspace"],
                "networks": [network_name]
            }

        # --- VS CODE WEB (IDE) ---
        if "vscode" in self.tools:
            port = self.request.custom_ports.get("vscode", 8443)
            auto_ext = "true" if getattr(self.request, "auto_install_extensions", True) else "false"
            services["vscode"] = {
                "image": "codercom/code-server:latest",
                "container_name": f"{self.project_name}-vscode",
                "entrypoint": ["/bin/sh", "/home/coder/project/vscode/entrypoint.sh"],
                "environment": {"AUTO_INSTALL_EXTENSIONS": auto_ext},
                "ports": [f"{port}:8080"],
                "volumes": ["./:/home/coder/project"],
                "networks": [network_name]
            }

        # --- CUSTOM PLUGINS ---
        from studio.services.plugin_manager import PluginManager
        for tool_id in self.tools:
            plugin = PluginManager.get_plugin(tool_id)
            if plugin and plugin.compose_services:
                for svc_name, svc_cfg in plugin.compose_services.items():
                    svc_copy = dict(svc_cfg)
                    svc_copy["networks"] = [network_name]
                    if "container_name" not in svc_copy:
                        svc_copy["container_name"] = f"{self.project_name}-{svc_name}"
                    
                    if plugin.default_port and plugin.id in self.request.custom_ports:
                        cust_port = self.request.custom_ports[plugin.id]
                        new_ports = []
                        for p in svc_copy.get("ports", []):
                            if isinstance(p, str) and ":" in p:
                                target = p.split(":")[1]
                                new_ports.append(f"{cust_port}:{target}")
                            else:
                                new_ports.append(p)
                        svc_copy["ports"] = new_ports

                    services[svc_name] = svc_copy

                for vol in plugin.volumes:
                    volumes[vol] = None

        compose_dict = {
            "name": self.project_name,
            "services": services,
            "networks": {network_name: {"driver": "bridge"}}
        }
        if volumes:
            compose_dict["volumes"] = {k: {} for k in volumes}

        compose_path = os.path.join(self.project_dir, "docker-compose.yml")
        with open(compose_path, "w", encoding="utf-8") as f:
            yaml.dump(compose_dict, f, sort_keys=False, default_flow_style=False)

    def _generate_env_files(self):
        env_lines = [
            f"# =============================================================================",
            f"# ENVIRONMENT CONFIGURATION: {self.project_name.upper()}",
            f"# =============================================================================",
            ""
        ]

        user = self.request.default_user or "admin"
        password = self.request.default_password or "admin123"

        for tool_id in sorted(self.tools):
            tool = get_tool_by_id(tool_id)
            if tool.env_vars:
                env_lines.append(f"# {tool.name}")
                for k, v in tool.env_vars.items():
                    val = v
                    if "USER" in k or k == "KEYCLOAK_ADMIN" or k == "GF_SECURITY_ADMIN_USER":
                        val = user
                    elif "PASSWORD" in k or "PASS" in k or k == "KEYCLOAK_ADMIN_PASSWORD" or k == "GF_SECURITY_ADMIN_PASSWORD":
                        val = password
                    env_lines.append(f"{k}={val}")
                env_lines.append("")

        if "vscode" in self.tools:
            env_lines.append(f"# VS Code Web (IDE)")
            env_lines.append(f"PASSWORD={password}")
            env_lines.append("")

        env_path = os.path.join(self.project_dir, ".env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(env_lines))

    def _create_default_files(self):
        if "postgres" in self.tools:
            self._generate_postgres_files()
        if "kafka_connect" in self.tools:
            self._generate_debezium_files()
        if "spark" in self.tools:
            self._generate_spark_files()
        if "airflow" in self.tools:
            self._generate_airflow_files()
        if "trino" in self.tools:
            self._generate_trino_files()
        if "dbt" in self.tools:
            self._generate_dbt_files()
        if "opentelemetry" in self.tools:
            self._generate_otel_files()
        if "nginx" in self.tools:
            self._generate_nginx_files()
        if "apigateway" in self.tools:
            self._generate_kong_files()
        if "ansible" in self.tools:
            self._generate_ansible_files()
        if "terraform" in self.tools:
            self._generate_terraform_files()
        if "hive" in self.tools:
            self._generate_hive_files()
        if "zeppelin" in self.tools:
            self._generate_zeppelin_files()
        self._generate_additional_tool_files()

    def _generate_postgres_files(self):
        init_folder = self.request.custom_folders.get("postgres_init", "postgres/init.sql")
        init_file = os.path.join(self.project_dir, init_folder)
        os.makedirs(os.path.dirname(init_file), exist_ok=True)
        if self.include_templates:
            sql = f"""-- OLTP Database Setup for {self.project_name}
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE customers REPLICA IDENTITY FULL;
ALTER TABLE orders REPLICA IDENTITY FULL;

INSERT INTO customers (name, email) VALUES 
('Alice Johnson', 'alice@example.com'),
('Bob Smith', 'bob@example.com'),
('Carlos Silva', 'carlos@empresa.com.br')
ON CONFLICT (email) DO NOTHING;

INSERT INTO orders (customer_id, amount, status) VALUES 
(1, 150.00, 'COMPLETED'),
(2, 89.90, 'PROCESSING'),
(3, 1200.50, 'SHIPPED');
"""
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(sql)

    def _generate_debezium_files(self):
        debezium_dir = os.path.join(self.project_dir, "debezium")
        os.makedirs(debezium_dir, exist_ok=True)
        if self.include_templates:
            cfg = {
                "name": f"{self.project_name}-postgres-connector",
                "config": {
                    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
                    "tasks.max": "1",
                    "plugin.name": "pgoutput",
                    "database.hostname": "postgres",
                    "database.port": "5432",
                    "database.user": "admin",
                    "database.password": "admin123",
                    "database.dbname": "oltp_db",
                    "database.server.name": f"{self.project_name}_db",
                    "topic.prefix": self.project_name,
                    "table.include.list": "public.customers,public.orders"
                }
            }
            with open(os.path.join(debezium_dir, "register-postgres.json"), "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)

    def _generate_spark_files(self):
        spark_dir = os.path.join(self.project_dir, "spark")
        apps_dir = os.path.join(self.project_dir, "spark", "apps")
        os.makedirs(apps_dir, exist_ok=True)

        dockerfile = """FROM apache/spark:3.5.1
USER root
RUN pip install --no-cache-dir pyspark==3.5.1 delta-spark pyarrow
USER spark
"""
        with open(os.path.join(spark_dir, "Dockerfile"), "w", encoding="utf-8") as f:
            f.write(dockerfile)

        if self.include_templates:
            pyspark_job = f"""# PySpark Streaming & Batch Job: {self.project_name}
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp

spark = SparkSession.builder \\
    .appName("{self.project_name}-LakehouseIngestion") \\
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \\
    .config("spark.sql.catalog.lakehouse", "org.apache.iceberg.spark.SparkCatalog") \\
    .config("spark.sql.catalog.lakehouse.type", "rest") \\
    .config("spark.sql.catalog.lakehouse.uri", "http://iceberg-rest:8181") \\
    .config("spark.sql.catalog.lakehouse.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \\
    .config("spark.sql.catalog.lakehouse.s3.endpoint", "http://minio:9000") \\
    .config("spark.sql.catalog.lakehouse.s3.path-style-access", "true") \\
    .config("spark.sql.defaultCatalog", "lakehouse") \\
    .getOrCreate()

print(" Spark Session Initialized with Iceberg REST Catalog!")
df = spark.range(1, 100).withColumn("ingestion_time", current_timestamp())
df.show(5)
"""
            with open(os.path.join(apps_dir, "stream_to_iceberg.py"), "w", encoding="utf-8") as f:
                f.write(pyspark_job)

    def _generate_airflow_files(self):
        dags_dir = os.path.join(self.project_dir, "airflow", "dags")
        os.makedirs(dags_dir, exist_ok=True)
        if self.include_templates:
            dag = f"""from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {{
    'owner': 'lakehouse',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

with DAG(
    '{self.project_name}_lakehouse_pipeline',
    default_args=default_args,
    description='Automated pipeline for {self.project_name}',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    t1 = BashOperator(
        task_id='verify_bronze_layer',
        bash_command='echo "Verifying Bronze ingest..."',
    )

    t2 = BashOperator(
        task_id='trigger_gold_aggregations',
        bash_command='echo "Executing Gold transforms with dbt and Trino..."',
    )

    t1 >> t2
"""
            with open(os.path.join(dags_dir, "lakehouse_pipeline.py"), "w", encoding="utf-8") as f:
                f.write(dag)

    def _generate_trino_files(self):
        trino_dir = os.path.join(self.project_dir, "trino", "etc")
        cat_dir = os.path.join(trino_dir, "catalog")
        os.makedirs(cat_dir, exist_ok=True)

        if "iceberg_rest" in self.tools:
            iceberg_prop = """connector.name=iceberg
iceberg.catalog.type=rest
iceberg.rest-catalog.uri=http://iceberg-rest:8181
iceberg.rest-catalog.v1.sub-namespace-enabled=true
fs.native-s3.enabled=true
s3.endpoint=http://minio:9000
s3.path-style-access=true
s3.aws-access-key=admin
s3.aws-secret-key=admin123
s3.region=us-east-1
"""
            with open(os.path.join(cat_dir, "iceberg.properties"), "w", encoding="utf-8") as f:
                f.write(iceberg_prop)

        if "postgres" in self.tools:
            pg_prop = """connector.name=postgresql
connection-url=jdbc:postgresql://postgres:5432/oltp_db
connection-user=admin
connection-password=admin123
"""
            with open(os.path.join(cat_dir, "postgresql.properties"), "w", encoding="utf-8") as f:
                f.write(pg_prop)

    def _generate_dbt_files(self):
        dbt_dir = os.path.join(self.project_dir, "dbt")
        models_dir = os.path.join(dbt_dir, "models")
        os.makedirs(models_dir, exist_ok=True)

        dbt_project = f"""name: '{self.project_name}'
version: '1.0.0'
config-version: 2
profile: '{self.project_name}_profile'
model-paths: ["models"]
target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"
"""
        with open(os.path.join(dbt_dir, "dbt_project.yml"), "w", encoding="utf-8") as f:
            f.write(dbt_project)

    def _generate_otel_files(self):
        otel_dir = os.path.join(self.project_dir, "otel")
        os.makedirs(otel_dir, exist_ok=True)
        otel_yaml = """receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  logging:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
"""
        with open(os.path.join(otel_dir, "otel-collector-config.yaml"), "w", encoding="utf-8") as f:
            f.write(otel_yaml)

    def _generate_nginx_files(self):
        nginx_dir = os.path.join(self.project_dir, "nginx")
        os.makedirs(nginx_dir, exist_ok=True)
        nginx_conf = """events {}
http {
    server {
        listen 80;
        location / {
            return 200 "StackStudio NGINX Gateway Online\\n";
        }
    }
}
"""
        with open(os.path.join(nginx_dir, "nginx.conf"), "w", encoding="utf-8") as f:
            f.write(nginx_conf)

    def _generate_kong_files(self):
        kong_dir = os.path.join(self.project_dir, "kong")
        os.makedirs(kong_dir, exist_ok=True)
        kong_yml = """_format_version: "3.0"
services:
  - name: internal-api
    url: http://postgres:5432
    routes:
      - name: api-route
        paths:
          - /api
"""
        with open(os.path.join(kong_dir, "kong.yml"), "w", encoding="utf-8") as f:
            f.write(kong_yml)

    def _generate_ansible_files(self):
        ansible_dir = os.path.join(self.project_dir, "ansible", "playbooks")
        os.makedirs(ansible_dir, exist_ok=True)
        pb = f"""---
- name: Configure {self.project_name} stack
  hosts: localhost
  connection: local
  tasks:
    - name: Ensure infrastructure is operational
      ansible.builtin.debug:
        msg: "StackStudio Ansible Automation Online for {self.project_name}"
"""
        with open(os.path.join(ansible_dir, "site.yml"), "w", encoding="utf-8") as f:
            f.write(pb)

    def _generate_terraform_files(self):
        tf_dir = os.path.join(self.project_dir, "terraform")
        os.makedirs(tf_dir, exist_ok=True)
        tf = f"""terraform {{
  required_version = ">= 1.5.0"
}}

output "project_name" {{
  value = "{self.project_name}"
}}
"""
        with open(os.path.join(tf_dir, "main.tf"), "w", encoding="utf-8") as f:
            f.write(tf)

    def _generate_hive_files(self):
        hive_dir = os.path.join(self.project_dir, "hive", "warehouse")
        os.makedirs(hive_dir, exist_ok=True)
        init_hql = f"""CREATE DATABASE IF NOT EXISTS analytics;
USE analytics;
CREATE TABLE IF NOT EXISTS pageviews (user_id STRING, page_url STRING, event_time TIMESTAMP)
STORED AS TEXTFILE;
"""
        with open(os.path.join(self.project_dir, "hive", "init.sql"), "w", encoding="utf-8") as f:
            f.write(init_hql)

    def _generate_zeppelin_files(self):
        nb_dir = os.path.join(self.project_dir, "zeppelin", "notebook")
        os.makedirs(nb_dir, exist_ok=True)
        sample_nb = {
            "paragraphs": [
                {"text": f"%md\\n# {self.project_name}\\nNotebook Interativo", "status": "READY"},
                {"text": "%pyspark\\nprint('Spark Session Ready!')", "status": "READY"}
            ],
            "name": f"Notebook-{self.project_name}",
            "id": "2A94M5J1Z"
        }
        with open(os.path.join(nb_dir, "note.json"), "w", encoding="utf-8") as f:
            json.dump(sample_nb, f, indent=2)

    def _generate_additional_tool_files(self):
        if "flink" in self.tools:
            f_job = "# Apache Flink Streaming Job\\nprint('Flink Stream Processing Job Initialized')\\n"
            with open(os.path.join(self.project_dir, "flink", "jobs", "stream_job.py"), "w", encoding="utf-8") as f:
                f.write(f_job)

        if "loki" in self.tools:
            loki_cfg = """auth_enabled: false
server:
  http_listen_port: 3100
schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h
storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
  filesystem:
    directory: /loki/chunks
"""
            with open(os.path.join(self.project_dir, "loki", "loki-config.yaml"), "w", encoding="utf-8") as f:
                f.write(loki_cfg)

            promtail_cfg = """server:
  http_listen_port: 9080
positions:
  filename: /tmp/positions.yaml
clients:
  - url: http://loki:3100/loki/api/v1/push
scrape_configs:
  - job_name: system
    static_configs:
      - targets: [localhost]
        labels:
          job: varlogs
          __path__: /var/log/*log
"""
            with open(os.path.join(self.project_dir, "loki", "promtail-config.yaml"), "w", encoding="utf-8") as f:
                f.write(promtail_cfg)

        if "traefik" in self.tools:
            traefik_dyn = """http:
  routers:
    dashboard:
      rule: "PathPrefix(`/api`) || PathPrefix(`/dashboard`)"
      service: api@internal
"""
            with open(os.path.join(self.project_dir, "traefik", "dynamic_conf.yml"), "w", encoding="utf-8") as f:
                f.write(traefik_dyn)

        if "suricata" in self.tools:
            sur_rules = """# Suricata Local Rules
alert icmp any any -> any any (msg:"ICMP Ping Detected"; sid:1000001; rev:1;)
alert tcp any any -> any 80 (msg:"HTTP Connection Attempt"; sid:1000002; rev:1;)
"""
            with open(os.path.join(self.project_dir, "suricata", "rules", "local.rules"), "w", encoding="utf-8") as f:
                f.write(sur_rules)

        if "zeek" in self.tools:
            zeek_script = """# Zeek Local Policy Script
@load base/protocols/conn
@load base/protocols/http
@load base/protocols/dns
event zeek_init() {
    print "Zeek Network Security Monitor Initialized";
}
"""
            with open(os.path.join(self.project_dir, "zeek", "scripts", "local.zeek"), "w", encoding="utf-8") as f:
                f.write(zeek_script)

        if "wazuh" in self.tools:
            waz_rules = """<!-- Wazuh Custom Detection Rules -->
<group name="local,custom,">
  <rule id="100001" level="5">
    <description>Local Security Audit Event Detected</description>
  </rule>
</group>
"""
            with open(os.path.join(self.project_dir, "wazuh", "rules", "local_rules.xml"), "w", encoding="utf-8") as f:
                f.write(waz_rules)

        if "vault" in self.tools:
            vault_pol = """path "secret/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
"""
            with open(os.path.join(self.project_dir, "vault", "policies", "app_policy.hcl"), "w", encoding="utf-8") as f:
                f.write(vault_pol)

    def _generate_scripts(self):
        scripts_dir = os.path.join(self.project_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)

        start_ps1 = f"""Write-Host "Starting {self.project_name}..." -ForegroundColor Cyan
docker compose up -d
Write-Host "Services started!" -ForegroundColor Green
docker compose ps
Write-Host "Running automated service health tests..." -ForegroundColor Yellow
python tests/test_services.py
"""
        with open(os.path.join(scripts_dir, "start.ps1"), "w", encoding="utf-8") as f:
            f.write(start_ps1)

        start_sh = f"""#!/bin/bash
echo "Starting {self.project_name}..."
docker compose up -d
echo "Services started!"
docker compose ps
echo "Running automated service health tests..."
python tests/test_services.py
"""
        with open(os.path.join(scripts_dir, "start.sh"), "w", encoding="utf-8") as f:
            f.write(start_sh)

        stop_ps1 = f"""Write-Host "Stopping {self.project_name}..." -ForegroundColor Yellow
docker compose down
"""
        with open(os.path.join(scripts_dir, "stop.ps1"), "w", encoding="utf-8") as f:
            f.write(stop_ps1)

        stop_sh = f"""#!/bin/bash
echo "Stopping {self.project_name}..."
docker compose down
"""
        with open(os.path.join(scripts_dir, "stop.sh"), "w", encoding="utf-8") as f:
            f.write(stop_sh)

    def _generate_makefile(self):
        makefile = f""".PHONY: start stop restart status logs test clean

start:
\tdocker compose up -d
\tpython tests/test_services.py

test:
\tpython tests/test_services.py

stop:
\tdocker compose down

pause:
\tdocker compose stop

resume:
\tdocker compose start

restart:
\tdocker compose restart

status:
\tdocker compose ps

logs:
\tdocker compose logs -f

clean:
\tdocker compose down -v
"""
        with open(os.path.join(self.project_dir, "Makefile"), "w", encoding="utf-8") as f:
            f.write(makefile)

    def _generate_tests(self):
        tests_dir = os.path.join(self.project_dir, "tests")
        os.makedirs(tests_dir, exist_ok=True)

        tools_list_repr = repr(list(self.tools))
        ports_map_repr = repr(self.request.custom_ports)

        test_py = f'''"""
=============================================================================
AUTOMATED END-TO-END SERVICE HEALTH & FUNCTIONAL TEST SUITE
Project: {self.project_name}
=============================================================================
"""

import sys
import time
import socket
import urllib.request
import urllib.error
import json

ENABLED_TOOLS = set({tools_list_repr})
CUSTOM_PORTS = {ports_map_repr}

class Colors:
    GREEN = "\\033[92m"
    RED = "\\033[91m"
    YELLOW = "\\033[93m"
    CYAN = "\\033[96m"
    BOLD = "\\033[1m"
    END = "\\033[0m"


def check_tcp_port(host, port, timeout=3.0):
    start = time.time()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True, (time.time() - start) * 1000
    except Exception as e:
        return False, str(e)


def check_http_endpoint(url, timeout=4.0):
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={{"User-Agent": "StackStudio-Tester/1.0"}})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency = (time.time() - start) * 1000
            return True, f"HTTP {{response.status}} ({{latency:.1f}}ms)"
    except urllib.error.HTTPError as e:
        latency = (time.time() - start) * 1000
        if e.code in (200, 302, 401, 403, 404):
            return True, f"HTTP {{e.code}} ({{latency:.1f}}ms)"
        return False, f"HTTP Error {{e.code}}"
    except Exception as e:
        return False, str(e)


def run_all_tests():
    print("=" * 70)
    print(f" {{Colors.BOLD}}{{Colors.CYAN}}[*] STACKSTUDIO SERVICE TEST SUITE: {self.project_name.upper()}{{Colors.END}}")
    print("=" * 70)

    results = []

    for tool_id in sorted(ENABLED_TOOLS):
        port = CUSTOM_PORTS.get(tool_id)
        if port:
            ok, detail = check_tcp_port("localhost", port)
            results.append((tool_id, port, ok, detail))

    passed = sum(1 for r in results if r[2])
    total = len(results)

    print(f"\\nTestes concluidos: {{passed}}/{{total}} serviços responsivos.")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
'''
        with open(os.path.join(tests_dir, "test_services.py"), "w", encoding="utf-8") as f:
            f.write(test_py)

        unit_dir = os.path.join(tests_dir, "unit")
        os.makedirs(unit_dir, exist_ok=True)
        config_val_py = """import yaml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@pytest.mark.unit
class TestConfigValidation:
    def test_docker_compose_exists_and_is_valid_yaml(self):
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml not found"
        with open(compose_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert "services" in data
        assert len(data["services"]) > 0

    def test_no_port_collisions_in_compose(self):
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        with open(compose_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        host_ports = []
        for service_name, svc in data.get("services", {}).items():
            for p in svc.get("ports", []):
                if isinstance(p, str) and ":" in p:
                    host_ports.append(p.split(":")[0])
        duplicates = [p for p in host_ports if host_ports.count(p) > 1]
        assert len(set(duplicates)) == 0, f"Host port collision detected: {duplicates}"
"""
        with open(os.path.join(unit_dir, "test_config_validation.py"), "w", encoding="utf-8") as f:
            f.write(config_val_py)

    def _generate_readme(self):
        readme_lines = [
            f"# 🚀 {self.project_name}",
            "",
            f"> {self.request.description}",
            "",
            "## 📦 Ferramentas Habilitadas",
            "",
            "| Ferramenta | Categoria | Porta Host | Endpoint / UI |",
            "| :--- | :--- | :--- | :--- |"
        ]

        for tool_id in sorted(self.tools):
            tool = get_tool_by_id(tool_id)
            port = self.request.custom_ports.get(tool_id, tool.default_port or "-")
            ui = tool.ui_url or "-"
            readme_lines.append(f"| **{tool.name}** | `{tool.category}` | `{port}` | {ui} |")

        readme_lines.extend([
            "",
            "## ⚡ Como Iniciar o Projeto e Rodar os Testes",
            "",
            "```bash",
            "docker compose up -d",
            "python tests/test_services.py",
            "```",
            "",
            "Ou usando o Makefile:",
            "```bash",
            "make start",
            "make test",
            "make status",
            "make logs",
            "make stop",
            "```"
        ])

        with open(os.path.join(self.project_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(readme_lines))

    def _get_vscode_extensions(self) -> List[str]:
        extensions: List[str] = ["redhat.vscode-yaml", "eamodio.gitlens", "ms-azuretools.vscode-docker"]
        mapping = {
            "python": ["ms-python.python", "ms-python.vscode-pylance", "ms-toolsai.jupyter"],
            "spark": ["ms-python.python", "ms-toolsai.jupyter"],
            "flink": ["ms-python.python", "vscjava.vscode-java-pack"],
            "airflow": ["ms-python.python", "redhat.vscode-yaml"],
            "dbt": ["innoverio.vscode-dbt-power-user", "ms-python.python"],
            "postgres": ["ckolkman.vscode-postgres", "mtxr.sqltools"],
            "mysql": ["cweijan.vscode-database-client2", "mtxr.sqltools"],
            "clickhouse": ["cweijan.vscode-database-client2"],
            "redis": ["cweijan.vscode-database-client2"],
            "kafka": ["formulahendry.vscode-kafka"],
            "terraform": ["hashicorp.terraform"],
            "vault": ["hashicorp.hcl", "hashicorp.vault"],
            "ansible": ["redhat.ansible", "redhat.vscode-yaml"],
            "nginx": ["ahmadalli.vscode-nginx-conf"],
            "loki": ["grafana.grafana", "redhat.vscode-yaml"],
            "sonarqube": ["sonarsource.sonarlint-vscode"],
            "trivy": ["aquasecurity.trivy-vulnerability-scanner"],
            "gitleaks": ["zricethezav.gitleaks"],
            "wazuh": ["redhat.vscode-xml", "redhat.vscode-yaml"]
        }

        for tool in self.tools:
            if tool in mapping:
                for ext in mapping[tool]:
                    if ext not in extensions:
                        extensions.append(ext)

        custom_exts = getattr(self.request, "custom_vscode_extensions", None)
        if custom_exts and isinstance(custom_exts, list):
            for ext in custom_exts:
                if ext and ext.strip() and ext.strip() not in extensions:
                    extensions.append(ext.strip())

        return extensions

    def _generate_vscode_files(self):
        vscode_dir = os.path.join(self.project_dir, ".vscode")
        os.makedirs(vscode_dir, exist_ok=True)
        exts = self._get_vscode_extensions()
        
        extensions_json = {"recommendations": exts}
        with open(os.path.join(vscode_dir, "extensions.json"), "w", encoding="utf-8") as f:
            json.dump(extensions_json, f, indent=2)

        settings_json = {
            "files.autoSave": "afterDelay",
            "editor.formatOnSave": True,
            "editor.tabSize": 2,
            "terminal.integrated.defaultProfile.linux": "bash",
            "docker.showStartPage": False
        }
        with open(os.path.join(vscode_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump(settings_json, f, indent=2)

        vscode_scripts_dir = os.path.join(self.project_dir, "vscode")
        os.makedirs(vscode_scripts_dir, exist_ok=True)

        auto_install = "true" if getattr(self.request, "auto_install_extensions", True) else "false"
        entrypoint_content = f"""#!/bin/sh
set -e

echo "=== [StackStudio VS Code Web IDE] Inicializando Workspace ==="

if [ "$AUTO_INSTALL_EXTENSIONS" = "true" ] && [ -f /home/coder/project/.vscode/extensions.json ]; then
  echo "Instalando extensoes oficiais recomendadas do projeto..."
  for ext in {' '.join(exts)}; do
    echo " -> Instalando extensao: $ext"
    code-server --install-extension "$ext" --force || echo "  [AVISO] Nao foi possivel instalar $ext, continuando..."
  done
  echo "Extensoes oficiais configuradas com sucesso!"
fi

echo "Iniciando code-server..."
exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project
"""
        with open(os.path.join(vscode_scripts_dir, "entrypoint.sh"), "w", encoding="utf-8", newline="\n") as f:
            f.write(entrypoint_content)
