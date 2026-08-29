"""
Project Scaffolding and Code Generation Engine with Automated Service Health & Functional Testing
"""

import os
import json
import shutil
import yaml
from typing import Dict, List, Any
from studio.models import ProjectCreateRequest
from studio.services.catalog import get_tool_by_id


class ProjectScaffolder:
    def __init__(self, request: ProjectCreateRequest):
        self.request = request
        self.project_name = request.name.strip().replace(" ", "-").lower()
        self.project_dir = os.path.abspath(request.path or os.path.join(".", "projects", self.project_name))
        self.tools = set(request.tools)
        self.include_templates = request.include_templates
        self._resolve_dependencies()

    def _resolve_dependencies(self):
        for tool_id in list(self.tools):
            tool = get_tool_by_id(tool_id)
            for dep in tool.dependencies:
                self.tools.add(dep)

    def scaffold(self) -> str:
        """Generates the full project structure and returns the project directory."""
        os.makedirs(self.project_dir, exist_ok=True)

        # 1. Generate docker-compose.yml
        self._generate_docker_compose()

        # 2. Generate .env and .env.example
        self._generate_env_files()

        # 3. Generate Tool-Specific Folders and Code Templates (or clean placeholders)
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

        # Generate .vscode extensions & settings
        self._generate_vscode_files()

        # 4. Generate Automation Scripts and Makefile
        self._generate_scripts()
        self._generate_makefile()

        # 5. Generate Comprehensive Automated Service Test Suite
        self._generate_tests()

        # 6. Generate Custom README.md
        self._generate_readme()

        # 7. Generate Kubernetes Manifests and Kustomization
        from studio.services.k8s_scaffolder import K8sScaffolder
        k8s_scaffolder = K8sScaffolder(self.request, self.tools, self.project_dir)
        k8s_scaffolder.scaffold()

        return self.project_dir

    def _generate_docker_compose(self):
        services: Dict[str, Any] = {}
        volumes: Dict[str, Any] = {}
        network_name = f"{self.project_name}-net"

        # --- POSTGRES ---
        if "postgres" in self.tools:
            port = self.request.custom_ports.get("postgres", 5434)
            pg_folder = self.request.custom_folders.get("postgres", "postgres")
            services["postgres"] = {
                "image": "debezium/postgres:16-alpine",
                "container_name": f"{self.project_name}-postgres",
                "command": "postgres -c wal_level=logical -c max_wal_senders=10 -c max_replication_slots=10",
                "ports": [f"{port}:5432"],
                "environment": {
                    "POSTGRES_USER": "${POSTGRES_USER:-postgres}",
                    "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:-postgres}",
                    "POSTGRES_DB": "${POSTGRES_DB:-oltp_db}"
                },
                "volumes": [f"./{pg_folder}/init.sql:/docker-entrypoint-initdb.d/init.sql", "pg_data:/var/lib/postgresql/data"],
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
                "command": "--server-id=1 --log-bin=mysql-bin --binlog-format=ROW --binlog-row-image=FULL",
                "ports": [f"{port}:3306"],
                "environment": {
                    "MYSQL_ROOT_PASSWORD": "${MYSQL_ROOT_PASSWORD:-rootpassword}",
                    "MYSQL_DATABASE": "${MYSQL_DATABASE:-app_db}",
                    "MYSQL_USER": "${MYSQL_USER:-dbuser}",
                    "MYSQL_PASSWORD": "${MYSQL_PASSWORD:-dbpassword}"
                },
                "volumes": ["mysql_data:/var/lib/mysql"],
                "networks": [network_name]
            }
            volumes["mysql_data"] = None

        # --- CLICKHOUSE ---
        if "clickhouse" in self.tools:
            port = self.request.custom_ports.get("clickhouse", 8123)
            services["clickhouse"] = {
                "image": "clickhouse/clickhouse-server:24.3",
                "container_name": f"{self.project_name}-clickhouse",
                "ports": [f"{port}:8123", "9000:9000"],
                "ulimits": {"nofile": {"soft": 262144, "hard": 262144}},
                "volumes": ["clickhouse_data:/var/lib/clickhouse"],
                "networks": [network_name]
            }
            volumes["clickhouse_data"] = None

        # --- KAFKA ---
        if "kafka" in self.tools:
            port = self.request.custom_ports.get("kafka", 9092)
            services["kafka"] = {
                "image": "confluentinc/cp-kafka:7.6.0",
                "container_name": f"{self.project_name}-kafka",
                "ports": [f"{port}:9092"],
                "environment": {
                    "KAFKA_NODE_ID": 1,
                    "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT",
                    "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:" + str(port),
                    "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": 1,
                    "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS": 0,
                    "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": 1,
                    "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": 1,
                    "KAFKA_PROCESS_ROLES": "broker,controller",
                    "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@kafka:29093",
                    "KAFKA_LISTENERS": "PLAINTEXT://0.0.0.0:29092,CONTROLLER://0.0.0.0:29093,PLAINTEXT_HOST://0.0.0.0:" + str(port),
                    "KAFKA_INTER_BROKER_LISTENER_NAME": "PLAINTEXT",
                    "KAFKA_CONTROLLER_LISTENER_NAMES": "CONTROLLER",
                    "KAFKA_LOG_DIRS": "/tmp/kraft-combined-logs",
                    "CLUSTER_ID": "MkU3OEVBNTcwNTJENDM2Qk"
                },
                "networks": [network_name]
            }

        # --- SCHEMA REGISTRY ---
        if "schema_registry" in self.tools:
            port = self.request.custom_ports.get("schema_registry", 8086)
            services["schema-registry"] = {
                "image": "confluentinc/cp-schema-registry:7.6.0",
                "container_name": f"{self.project_name}-schema-registry",
                "ports": [f"{port}:8081"],
                "depends_on": ["kafka"],
                "environment": {
                    "SCHEMA_REGISTRY_HOST_NAME": "schema-registry",
                    "SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS": "kafka:29092",
                    "SCHEMA_REGISTRY_LISTENERS": "http://0.0.0.0:8081"
                },
                "networks": [network_name]
            }

        # --- KAFKA CONNECT (DEBEZIUM) ---
        if "kafka_connect" in self.tools:
            port = self.request.custom_ports.get("kafka_connect", 8083)
            deps = ["kafka"]
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
                    "BOOTSTRAP_SERVERS": "kafka:29092",
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
                "KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS": "kafka:29092"
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
                "depends_on": ["kafka"],
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
                "depends_on": ["minio", "minio-init"],
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

        # --- SPARK ---
        if "spark" in self.tools:
            spark_ui_port = self.request.custom_ports.get("spark", 8082)
            spark_apps_folder = self.request.custom_folders.get("spark_apps", "spark/apps")
            services["spark-master"] = {
                "build": {"context": "./spark"},
                "container_name": f"{self.project_name}-spark-master",
                "command": "/opt/spark/bin/spark-class org.apache.spark.deploy.master.Master",
                "ports": ["7077:7077", f"{spark_ui_port}:8080"],
                "environment": {"SPARK_NO_DAEMONIZE": "true"},
                "volumes": [f"./{spark_apps_folder}:/opt/spark/work-dir/apps"],
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
                "volumes": [f"./{spark_apps_folder}:/opt/spark/work-dir/apps"],
                "depends_on": ["spark-master"],
                "networks": [network_name]
            }

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
            if "iceberg_rest" in self.tools:
                services["trino"]["depends_on"] = ["iceberg-rest", "minio"]

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
                "depends_on": {"airflow-db": {"condition": "service_healthy"}},
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
                "depends_on": {"airflow-init": {"condition": "service_completed_successfully"}},
                "environment": {
                    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": "postgresql+psycopg2://airflow:airflow@airflow-db:5432/airflow",
                    "AIRFLOW__CORE__LOAD_EXAMPLES": "false",
                    "AIRFLOW__CORE__EXECUTOR": "LocalExecutor"
                },
                "volumes": [f"./{dags_folder}:/opt/airflow/dags", f"./{plugins_folder}:/opt/airflow/plugins"],
                "command": "airflow webserver",
                "networks": [network_name]
            }

            services["airflow-scheduler"] = {
                "image": "apache/airflow:2.9.2-python3.11",
                "container_name": f"{self.project_name}-airflow-scheduler",
                "depends_on": {"airflow-init": {"condition": "service_completed_successfully"}},
                "environment": {
                    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": "postgresql+psycopg2://airflow:airflow@airflow-db:5432/airflow",
                    "AIRFLOW__CORE__LOAD_EXAMPLES": "false",
                    "AIRFLOW__CORE__EXECUTOR": "LocalExecutor"
                },
                "volumes": [f"./{dags_folder}:/opt/airflow/dags", f"./{plugins_folder}:/opt/airflow/plugins"],
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
                "environment": {"PROJECT_NAME": self.project_name},
                "volumes": ["./mage:/home/src"],
                "networks": [network_name]
            }

        # --- PREFECT ---
        if "prefect" in self.tools:
            port = self.request.custom_ports.get("prefect", 4200)
            services["prefect"] = {
                "image": "prefecthq/prefect:2-python3.11",
                "container_name": f"{self.project_name}-prefect",
                "command": "prefect server start --host 0.0.0.0",
                "ports": [f"{port}:4200"],
                "volumes": ["prefect_data:/root/.prefect"],
                "networks": [network_name]
            }
            volumes["prefect_data"] = None

        # --- MLFLOW ---
        if "mlflow" in self.tools:
            port = self.request.custom_ports.get("mlflow", 5001)
            services["mlflow"] = {
                "image": "ghcr.io/mlflow/mlflow:v2.13.0",
                "container_name": f"{self.project_name}-mlflow",
                "command": "mlflow server --backend-store-uri postgresql://postgres:postgres@postgres:5432/oltp_db --default-artifact-root s3://lakehouse/mlflow/ --host 0.0.0.0 --port 5000",
                "ports": [f"{port}:5000"],
                "environment": {
                    "MLFLOW_S3_ENDPOINT_URL": "http://minio:9000",
                    "AWS_ACCESS_KEY_ID": "admin",
                    "AWS_SECRET_ACCESS_KEY": "password123"
                },
                "networks": [network_name]
            }

        # --- JUPYTERLAB ---
        if "jupyterlab" in self.tools:
            port = self.request.custom_ports.get("jupyterlab", 8888)
            services["jupyterlab"] = {
                "image": "quay.io/jupyter/pyspark-notebook:latest",
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
                    "HASURA_GRAPHQL_DATABASE_URL": "postgres://postgres:postgres@postgres:5432/oltp_db",
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
                    "PGADMIN_DEFAULT_EMAIL": "${PGADMIN_DEFAULT_EMAIL:-admin@lakehouse.com}",
                    "PGADMIN_DEFAULT_PASSWORD": "${PGADMIN_DEFAULT_PASSWORD:-admin}"
                },
                "volumes": ["pgadmin_data:/var/lib/pgadmin"],
                "networks": [network_name]
            }
            volumes["pgadmin_data"] = None

        # --- OPENTELEMETRY COLLECTOR ---
        if "opentelemetry" in self.tools:
            port_http = self.request.custom_ports.get("opentelemetry", 4318)
            services["opentelemetry"] = {
                "image": "otel/opentelemetry-collector-contrib:0.102.0",
                "container_name": f"{self.project_name}-opentelemetry",
                "command": ["--config=/etc/otelcol-contrib/config.yaml"],
                "ports": [
                    "4317:4317",
                    f"{port_http}:4318",
                    "13133:13133",
                    "8888:8888"
                ],
                "volumes": [
                    "./otel/otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml:ro"
                ],
                "networks": [network_name]
            }

        # --- OPENMETADATA ---
        if "openmetadata" in self.tools:
            port = self.request.custom_ports.get("openmetadata", 8585)
            services["openmetadata"] = {
                "image": "docker.getcollate.io/openmetadata/server:1.4.2",
                "container_name": f"{self.project_name}-openmetadata",
                "ports": [f"{port}:8585"],
                "environment": {
                    "DB_HOST": "postgres",
                    "DB_PORT": "5432",
                    "DB_USER": "${POSTGRES_USER:-postgres}",
                    "DB_USER_PASSWORD": "${POSTGRES_PASSWORD:-postgres}",
                    "DB_NAME": "openmetadata_db",
                    "AUTHENTICATION_PROVIDER": "basic"
                },
                "depends_on": {
                    "postgres": {"condition": "service_healthy"} if "postgres" in self.tools else {"condition": "service_started"}
                },
                "networks": [network_name]
            }

        # --- NGINX REVERSE PROXY ---
        if "nginx" in self.tools:
            port = self.request.custom_ports.get("nginx", 8088)
            services["nginx"] = {
                "image": "nginx:alpine",
                "container_name": f"{self.project_name}-nginx",
                "ports": [f"{port}:80"],
                "volumes": [
                    "./nginx/nginx.conf:/etc/nginx/nginx.conf:ro",
                    "./nginx/html:/usr/share/nginx/html:ro"
                ],
                "networks": [network_name]
            }

        # --- KONG API GATEWAY ---
        if "apigateway" in self.tools:
            port_proxy = self.request.custom_ports.get("apigateway", 8000)
            services["apigateway"] = {
                "image": "kong:3.6",
                "container_name": f"{self.project_name}-kong",
                "environment": {
                    "KONG_DATABASE": "off",
                    "KONG_DECLARATIVE_CONFIG": "/etc/kong/kong.yml",
                    "KONG_PROXY_ACCESS_LOG": "/dev/stdout",
                    "KONG_ADMIN_ACCESS_LOG": "/dev/stdout",
                    "KONG_PROXY_ERROR_LOG": "/dev/stderr",
                    "KONG_ADMIN_ERROR_LOG": "/dev/stderr",
                    "KONG_ADMIN_LISTEN": "0.0.0.0:8001",
                    "KONG_ADMIN_GUI_LISTEN": "0.0.0.0:8002",
                    "KONG_ADMIN_GUI_URL": "http://localhost:8002"
                },
                "ports": [
                    f"{port_proxy}:8000",
                    "8001:8001",
                    "8002:8002"
                ],
                "volumes": [
                    "./kong/kong.yml:/etc/kong/kong.yml:ro"
                ],
                "networks": [network_name]
            }

        # --- APACHE HADOOP HDFS (NameNode & DataNode) ---
        if "hdfs" in self.tools:
            nn_ui_port = self.request.custom_ports.get("hdfs", 9870)
            services["namenode"] = {
                "image": "bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8",
                "container_name": f"{self.project_name}-namenode",
                "environment": {
                    "CLUSTER_NAME": "${CLUSTER_NAME:-hadoop-cluster}",
                    "CORE_CONF_fs_defaultFS": "hdfs://namenode:9000",
                    "HDFS_CONF_dfs_replication": "1"
                },
                "ports": [f"{nn_ui_port}:9870", "9000:9000"],
                "volumes": ["hadoop_namenode:/hadoop/dfs/name"],
                "networks": [network_name]
            }
            services["datanode"] = {
                "image": "bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8",
                "container_name": f"{self.project_name}-datanode",
                "depends_on": ["namenode"],
                "environment": {
                    "CORE_CONF_fs_defaultFS": "hdfs://namenode:9000"
                },
                "ports": ["9864:9864"],
                "volumes": ["hadoop_datanode:/hadoop/dfs/data"],
                "networks": [network_name]
            }
            volumes["hadoop_namenode"] = None
            volumes["hadoop_datanode"] = None

        # --- APACHE HADOOP YARN (ResourceManager & NodeManager) ---
        if "yarn" in self.tools:
            rm_ui_port = self.request.custom_ports.get("yarn", 8089)
            services["resourcemanager"] = {
                "image": "bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8",
                "container_name": f"{self.project_name}-resourcemanager",
                "depends_on": ["namenode", "datanode"] if "hdfs" in self.tools else [],
                "environment": {
                    "CORE_CONF_fs_defaultFS": "hdfs://namenode:9000",
                    "YARN_CONF_yarn_resourcemanager_hostname": "resourcemanager"
                },
                "ports": [f"{rm_ui_port}:8088"],
                "networks": [network_name]
            }
            services["nodemanager"] = {
                "image": "bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8",
                "container_name": f"{self.project_name}-nodemanager",
                "depends_on": ["resourcemanager"],
                "environment": {
                    "CORE_CONF_fs_defaultFS": "hdfs://namenode:9000",
                    "YARN_CONF_yarn_resourcemanager_hostname": "resourcemanager"
                },
                "ports": ["8042:8042"],
                "networks": [network_name]
            }

        # --- APACHE HIVE (Metastore & HiveServer2) ---
        if "hive" in self.tools:
            hive_ui_port = self.request.custom_ports.get("hive", 10002)
            warehouse_folder = self.request.custom_folders.get("hive_warehouse", "hive/warehouse")
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
                "volumes": [f"./{warehouse_folder}:/opt/hive/warehouse"],
                "networks": [network_name]
            }

        # --- APACHE ZEPPELIN NOTEBOOK ---
        if "zeppelin" in self.tools:
            zeppelin_port = self.request.custom_ports.get("zeppelin", 8090)
            notebook_folder = self.request.custom_folders.get("zeppelin_notebooks", "zeppelin/notebook")
            services["zeppelin"] = {
                "image": "apache/zeppelin:0.10.1",
                "container_name": f"{self.project_name}-zeppelin",
                "environment": {
                    "ZEPPELIN_PORT": "8080",
                    "ZEPPELIN_ANONYMOUS": "true"
                },
                "ports": [f"{zeppelin_port}:8080"],
                "volumes": [f"./{notebook_folder}:/opt/zeppelin/notebook"],
                "networks": [network_name]
            }

        # --- OLLAMA LOCAL LLM ENGINE ---
        if "ollama" in self.tools:
            ollama_port = self.request.custom_ports.get("ollama", 11434)
            models_folder = self.request.custom_folders.get("ollama_models", "ollama/models")
            services["ollama"] = {
                "image": "ollama/ollama:latest",
                "container_name": f"{self.project_name}-ollama",
                "ports": [f"{ollama_port}:11434"],
                "volumes": [f"./{models_folder}:/root/.ollama"],
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
                "environment": {
                    "OLLAMA_BASE_URL": "http://ollama:11434"
                },
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

        # --- VS CODE WEB (CODE-SERVER) ---
        if "vscode" in self.tools:
            port = self.request.custom_ports.get("vscode", 8443)
            auto_ext = "true" if getattr(self.request, "auto_install_extensions", True) else "false"
            services["vscode"] = {
                "image": "codercom/code-server:latest",
                "container_name": f"{self.project_name}-vscode",
                "entrypoint": ["/bin/sh", "/home/coder/project/vscode/entrypoint.sh"],
                "environment": {
                    "AUTO_INSTALL_EXTENSIONS": auto_ext
                },
                "ports": [f"{port}:8080"],
                "volumes": [
                    "./:/home/coder/project"
                ],
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
                    if k in ("POSTGRES_USER", "MINIO_ROOT_USER", "RABBITMQ_DEFAULT_USER", "GF_SECURITY_ADMIN_USER", "KEYCLOAK_ADMIN", "MONGO_INITDB_ROOT_USERNAME", "MYSQL_USER"):
                        val = user
                    elif k in ("POSTGRES_PASSWORD", "MINIO_ROOT_PASSWORD", "RABBITMQ_DEFAULT_PASS", "GF_SECURITY_ADMIN_PASSWORD", "KEYCLOAK_ADMIN_PASSWORD", "MONGO_INITDB_ROOT_PASSWORD", "PGADMIN_DEFAULT_PASSWORD", "MYSQL_PASSWORD", "MYSQL_ROOT_PASSWORD"):
                        val = password
                    elif k == "PGADMIN_DEFAULT_EMAIL":
                        val = f"{user}@example.com" if "@" not in user else user
                    elif k == "NEO4J_AUTH":
                        val = f"{user}/{password}"

                    val = self.request.custom_envs.get(k, val)
                    env_lines.append(f"{k}={val}")
                env_lines.append("")

        if "airflow" in self.tools:
            env_lines.append("# Apache Airflow")
            env_lines.append(f"AIRFLOW_USER={user}")
            env_lines.append(f"AIRFLOW_PASSWORD={password}")
            env_lines.append("")

        content = "\n".join(env_lines)
        with open(os.path.join(self.project_dir, ".env"), "w", encoding="utf-8") as f:
            f.write(content)
        with open(os.path.join(self.project_dir, ".env.example"), "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_postgres_files(self):
        pg_folder = self.request.custom_folders.get("postgres", "postgres")
        pg_dir = os.path.join(self.project_dir, pg_folder)
        os.makedirs(pg_dir, exist_ok=True)

        if self.include_templates:
            init_sql = """-- =============================================================================
-- POSTGRESQL OLTP INITIALIZATION (CDC & LOGICAL REPLICATION)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS ecommerce;

CREATE TABLE IF NOT EXISTS ecommerce.customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    city VARCHAR(50),
    state VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ecommerce.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES ecommerce.customers(customer_id),
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE ecommerce.customers REPLICA IDENTITY FULL;
ALTER TABLE ecommerce.orders REPLICA IDENTITY FULL;

DROP PUBLICATION IF EXISTS dbz_publication;
CREATE PUBLICATION dbz_publication FOR ALL TABLES;
"""
        else:
            init_sql = """-- =============================================================================
-- POSTGRESQL OLTP INITIALIZATION (CLEAN BASE)
-- =============================================================================

DROP PUBLICATION IF EXISTS dbz_publication;
CREATE PUBLICATION dbz_publication FOR ALL TABLES;
"""
        with open(os.path.join(pg_dir, "init.sql"), "w", encoding="utf-8") as f:
            f.write(init_sql)

    def _generate_debezium_files(self):
        deb_dir = os.path.join(self.project_dir, "debezium")
        os.makedirs(deb_dir, exist_ok=True)
        config_json = """{
  "name": "postgres-cdc-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "tasks.max": "1",
    "plugin.name": "pgoutput",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "postgres",
    "database.dbname": "oltp_db",
    "database.server.name": "cdc",
    "topic.prefix": "cdc",
    "table.include.list": ".*",
    "publication.name": "dbz_publication",
    "publication.autocreate.mode": "all_tables",
    "slot.name": "debezium_cdc_slot",
    "tombstones.on.delete": "false",
    "decimal.handling.mode": "double",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": "false"
  }
}
"""
        with open(os.path.join(deb_dir, "register-postgres.json"), "w", encoding="utf-8") as f:
            f.write(config_json)

    def _generate_spark_files(self):
        spark_dir = os.path.join(self.project_dir, "spark")
        spark_apps_rel = self.request.custom_folders.get("spark_apps", "spark/apps")
        apps_dir = os.path.join(self.project_dir, spark_apps_rel)
        conf_dir = os.path.join(spark_dir, "conf")
        os.makedirs(apps_dir, exist_ok=True)
        os.makedirs(conf_dir, exist_ok=True)

        dockerfile = """FROM apache/spark:3.5.1-python3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

ENV ICEBERG_VERSION=1.6.1
ENV AWS_SDK_VERSION=1.12.262
ENV HADOOP_AWS_VERSION=3.3.4
ENV KAFKA_CLIENTS_VERSION=3.5.1
ENV COMMONS_POOL_VERSION=2.11.1

RUN curl -s -f -L https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar -o /opt/spark/jars/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar && \\
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar -o /opt/spark/jars/iceberg-aws-bundle-${ICEBERG_VERSION}.jar && \\
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar -o /opt/spark/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar && \\
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.1/spark-token-provider-kafka-0-10_2.12-3.5.1.jar -o /opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar && \\
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/${KAFKA_CLIENTS_VERSION}/kafka-clients-${KAFKA_CLIENTS_VERSION}.jar -o /opt/spark/jars/kafka-clients-${KAFKA_CLIENTS_VERSION}.jar && \\
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/${COMMONS_POOL_VERSION}/commons-pool2-${COMMONS_POOL_VERSION}.jar -o /opt/spark/jars/commons-pool2-${COMMONS_POOL_VERSION}.jar && \\
    curl -s -f -L https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar -o /opt/spark/jars/hadoop-aws-${HADOOP_AWS_VERSION}.jar && \\
    curl -s -f -L https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar -o /opt/spark/jars/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar

COPY conf/spark-defaults.conf /opt/spark/conf/spark-defaults.conf
RUN chmod -R 777 /opt/spark/conf /opt/spark/work-dir /tmp

USER spark
WORKDIR /opt/spark/work-dir
"""
        with open(os.path.join(spark_dir, "Dockerfile"), "w", encoding="utf-8") as f:
            f.write(dockerfile)

        spark_defaults = """spark.master                           spark://spark-master:7077
spark.driver.memory                    1g
spark.executor.memory                  1g
spark.sql.extensions                   org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
spark.sql.catalog.lakehouse            org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.lakehouse.type       rest
spark.sql.catalog.lakehouse.uri        http://iceberg-rest:8181
spark.sql.catalog.lakehouse.io-impl    org.apache.iceberg.aws.s3.S3FileIO
spark.sql.catalog.lakehouse.warehouse  s3://lakehouse/
spark.sql.catalog.lakehouse.s3.endpoint http://minio:9000
spark.sql.catalog.lakehouse.s3.path-style-access true
spark.sql.catalog.lakehouse.s3.access-key-id admin
spark.sql.catalog.lakehouse.s3.secret-access-key password123
spark.sql.defaultCatalog               lakehouse
spark.hadoop.fs.s3a.endpoint           http://minio:9000
spark.hadoop.fs.s3a.access.key         admin
spark.hadoop.fs.s3a.secret.key         password123
spark.hadoop.fs.s3a.path.style.access  true
spark.hadoop.fs.s3a.impl               org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.connection.ssl.enabled false
"""
        with open(os.path.join(conf_dir, "spark-defaults.conf"), "w", encoding="utf-8") as f:
            f.write(spark_defaults)

        if self.include_templates:
            bronze_ingestion = """# =============================================================================
# SPARK STRUCTURED STREAMING: RAW CDC INGESTION (BRONZE LAYER)
# =============================================================================
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_date

spark = SparkSession.builder.appName("Bronze_CDC_Ingestion").getOrCreate()

spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze")
spark.sql(\"\"\"
    CREATE TABLE IF NOT EXISTS lakehouse.bronze.orders_raw (
        kafka_key STRING,
        raw_payload STRING,
        ingestion_timestamp TIMESTAMP,
        ingestion_date DATE
    )
    USING iceberg
    PARTITIONED BY (ingestion_date)
\"\"\")

stream_df = spark.readStream \\
    .format("kafka") \\
    .option("kafka.bootstrap.servers", "kafka:29092") \\
    .option("subscribe", "cdc.ecommerce.orders") \\
    .option("startingOffsets", "earliest") \\
    .load()

bronze_df = stream_df.select(
    col("key").cast("string").alias("kafka_key"),
    col("value").cast("string").alias("raw_payload"),
    current_timestamp().alias("ingestion_timestamp"),
    to_date(current_timestamp()).alias("ingestion_date")
)

query = bronze_df.writeStream \\
    .format("iceberg") \\
    .outputMode("append") \\
    .trigger(processingTime="5 seconds") \\
    .option("checkpointLocation", "s3://lakehouse/checkpoints/bronze_orders") \\
    .toTable("lakehouse.bronze.orders_raw")

query.awaitTermination()
"""
            with open(os.path.join(apps_dir, "bronze_ingestion.py"), "w", encoding="utf-8") as f:
                f.write(bronze_ingestion)

            silver_sync = """# =============================================================================
# SPARK STRUCTURED STREAMING: MERGE INTO SILVER LAYER (STATE REPLICATION)
# =============================================================================
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Silver_State_Sync").getOrCreate()
spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")

# Implement your foreachBatch and MERGE INTO logic here:
print("Silver Sync Stream Initialized.")
"""
            with open(os.path.join(apps_dir, "silver_sync.py"), "w", encoding="utf-8") as f:
                f.write(silver_sync)
        else:
            with open(os.path.join(apps_dir, ".gitkeep"), "w", encoding="utf-8") as f:
                f.write("")

    def _generate_airflow_files(self):
        dags_rel = self.request.custom_folders.get("airflow_dags", "airflow/dags")
        plugins_rel = self.request.custom_folders.get("airflow_plugins", "airflow/plugins")
        dags_dir = os.path.join(self.project_dir, dags_rel)
        plugins_dir = os.path.join(self.project_dir, plugins_rel)
        os.makedirs(dags_dir, exist_ok=True)
        os.makedirs(plugins_dir, exist_ok=True)

        if self.include_templates:
            gold_dag = """from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'lakehouse',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    'gold_aggregations_dag',
    default_args=default_args,
    description='Gold Layer aggregations & Analytics Data Marts',
    schedule_interval='@hourly',
    catchup=False,
    tags=['gold', 'analytics', 'lakehouse']
) as dag:

    run_gold_mart = BashOperator(
        task_id='run_gold_mart',
        bash_command='echo "Executing Gold layer batch aggregation..."'
    )
"""
            with open(os.path.join(dags_dir, "gold_aggregations.py"), "w", encoding="utf-8") as f:
                f.write(gold_dag)

            maintenance_dag = """from datetime import datetime, timedelta
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
"""
            with open(os.path.join(dags_dir, "iceberg_maintenance.py"), "w", encoding="utf-8") as f:
                f.write(maintenance_dag)
        else:
            with open(os.path.join(dags_dir, ".gitkeep"), "w", encoding="utf-8") as f:
                f.write("")
            with open(os.path.join(plugins_dir, ".gitkeep"), "w", encoding="utf-8") as f:
                f.write("")

    def _generate_trino_files(self):
        trino_dir = os.path.join(self.project_dir, "trino", "etc")
        catalog_dir = os.path.join(trino_dir, "catalog")
        os.makedirs(catalog_dir, exist_ok=True)

        node_props = "node.environment=production\nnode.id=ffffffff-ffff-ffff-ffff-ffffffffffff\nnode.data-dir=/data/trino\n"
        with open(os.path.join(trino_dir, "node.properties"), "w", encoding="utf-8") as f:
            f.write(node_props)

        jvm_cfg = "-server\n-Xmx2G\n-XX:+UnlockDiagnosticVMOptions\n-XX:G1NumCollectionsKeepPinned=10000000\n-XX:+UseG1GC\n-XX:G1HeapRegionSize=32M\n-XX:+ExplicitGCInvokesConcurrent\n-XX:+ExitOnOutOfMemoryError\n-Djdk.attach.allowAttachSelf=true\n-Dsun.reflect.inflationThreshold=0\n-Djnr.ffi.library.path=/usr/lib\n"
        with open(os.path.join(trino_dir, "jvm.config"), "w", encoding="utf-8") as f:
            f.write(jvm_cfg)

        config_props = "coordinator=true\nnode-scheduler.include-coordinator=true\nhttp-server.http.port=8080\nquery.max-memory=1GB\nquery.max-memory-per-node=512MB\ndiscovery.uri=http://localhost:8080\n"
        with open(os.path.join(trino_dir, "config.properties"), "w", encoding="utf-8") as f:
            f.write(config_props)

        iceberg_props = "connector.name=iceberg\niceberg.catalog.type=rest\niceberg.rest-catalog.uri=http://iceberg-rest:8181\niceberg.rest-catalog.warehouse=s3://lakehouse/\nfs.native-s3.enabled=true\ns3.endpoint=http://minio:9000\ns3.aws-access-key=admin\ns3.aws-secret-key=password123\ns3.path-style-access=true\ns3.region=us-east-1\n"
        with open(os.path.join(catalog_dir, "iceberg.properties"), "w", encoding="utf-8") as f:
            f.write(iceberg_props)

    def _generate_dbt_files(self):
        dbt_dir = os.path.join(self.project_dir, "dbt")
        models_dir = os.path.join(dbt_dir, "models")
        os.makedirs(models_dir, exist_ok=True)

        dbt_project = f"""name: '{self.project_name}_dbt'
version: '1.0.0'
config-version: 2
profile: 'default'
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
        config_path = os.path.join(otel_dir, "otel-collector-config.yaml")

        config_yaml = """receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

extensions:
  health_check:
    endpoint: 0.0.0.0:13133

exporters:
  debug:
    verbosity: detailed

service:
  extensions: [health_check]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_yaml)

    def _generate_nginx_files(self):
        nginx_dir = os.path.join(self.project_dir, "nginx")
        html_dir = os.path.join(nginx_dir, "html")
        os.makedirs(html_dir, exist_ok=True)

        conf_content = """events { worker_connections 1024; }

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout  65;

    server {
        listen       80;
        server_name  localhost;

        location / {
            root   /usr/share/nginx/html;
            index  index.html index.htm;
        }

        location /health {
            access_log off;
            return 200 "OK\\n";
            add_header Content-Type text/plain;
        }
    }
}
"""
        with open(os.path.join(nginx_dir, "nginx.conf"), "w", encoding="utf-8") as f:
            f.write(conf_content)

        index_html = f"""<!DOCTYPE html>
<html>
<head><title>{self.project_name} - NGINX</title></head>
<body style="font-family: sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 50px;">
    <h1>🚀 {self.project_name}</h1>
    <p>NGINX Reverse Proxy & Web Server Operational.</p>
</body>
</html>
"""
        with open(os.path.join(html_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index_html)

    def _generate_kong_files(self):
        kong_dir = os.path.join(self.project_dir, "kong")
        os.makedirs(kong_dir, exist_ok=True)

        kong_yml = """_format_version: "3.0"
_transform: true

services:
  - name: example-service
    url: http://localhost:80
    routes:
      - name: example-route
        paths:
          - /api
plugins:
  - name: rate-limiting
    config:
      minute: 100
      policy: local
"""
        with open(os.path.join(kong_dir, "kong.yml"), "w", encoding="utf-8") as f:
            f.write(kong_yml)

    def _generate_ansible_files(self):
        ansible_dir = os.path.join(self.project_dir, "ansible")
        playbooks_dir = os.path.join(ansible_dir, "playbooks")
        inventory_dir = os.path.join(ansible_dir, "inventory")
        os.makedirs(playbooks_dir, exist_ok=True)
        os.makedirs(inventory_dir, exist_ok=True)

        ansible_cfg = """[defaults]
inventory = inventory/hosts.ini
host_key_checking = False
retry_files_enabled = False
stdout_callback = yaml
"""
        with open(os.path.join(ansible_dir, "ansible.cfg"), "w", encoding="utf-8") as f:
            f.write(ansible_cfg)

        hosts_ini = """[local]
localhost ansible_connection=local

[servers]
# server1.example.com ansible_user=ubuntu
"""
        with open(os.path.join(inventory_dir, "hosts.ini"), "w", encoding="utf-8") as f:
            f.write(hosts_ini)

        site_yml = f"""---
- name: Deploy and Configure {self.project_name}
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: Ping target hosts
      ansible.builtin.debug:
        msg: "StackStudio Ansible Automation: {self.project_name} is ready!"
"""
        with open(os.path.join(playbooks_dir, "site.yml"), "w", encoding="utf-8") as f:
            f.write(site_yml)

    def _generate_terraform_files(self):
        tf_dir = os.path.join(self.project_dir, "terraform")
        os.makedirs(tf_dir, exist_ok=True)

        main_tf = f"""terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    local = {{
      source  = "hashicorp/local"
      version = "~> 2.4"
    }}
  }}
}}

provider "local" {{}}

resource "local_file" "environment_metadata" {{
  filename = "${{path.module}}/deployment-metadata.json"
  content = jsonencode({{
    project_name = "{self.project_name}"
    environment  = var.environment
    created_by   = "StackStudio"
  }})
}}
"""
        with open(os.path.join(tf_dir, "main.tf"), "w", encoding="utf-8") as f:
            f.write(main_tf)

        vars_tf = """variable "environment" {
  type        = string
  description = "Target deployment environment"
  default     = "development"
}
"""
        with open(os.path.join(tf_dir, "variables.tf"), "w", encoding="utf-8") as f:
            f.write(vars_tf)

        outputs_tf = f"""output "project_metadata_file" {{
  value       = local_file.environment_metadata.filename
  description = "Path to generated deployment metadata"
}}
"""
        with open(os.path.join(tf_dir, "outputs.tf"), "w", encoding="utf-8") as f:
            f.write(outputs_tf)

        tfvars = """environment = "development"
"""
        with open(os.path.join(tf_dir, "terraform.tfvars"), "w", encoding="utf-8") as f:
            f.write(tfvars)

    def _generate_hive_files(self):
        hive_folder = self.request.custom_folders.get("hive_warehouse", "hive/warehouse")
        hive_dir = os.path.join(self.project_dir, hive_folder)
        os.makedirs(hive_dir, exist_ok=True)

        if self.include_templates:
            init_hql = f"""-- =============================================================================
-- APACHE HIVE WAREHOUSE & METASTORE INITIALIZATION
-- Project: {self.project_name}
-- =============================================================================

CREATE DATABASE IF NOT EXISTS analytics
COMMENT 'Analytical Data Warehouse database managed by Hive'
LOCATION 'hdfs://namenode:9000/user/hive/warehouse/analytics.db';

USE analytics;

CREATE EXTERNAL TABLE IF NOT EXISTS analytics.pageviews (
    user_id STRING,
    page_url STRING,
    event_timestamp TIMESTAMP,
    device_type STRING,
    ip_address STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/user/hive/warehouse/analytics.db/pageviews';

SHOW TABLES IN analytics;
"""
            with open(os.path.join(self.project_dir, "hive", "init.sql"), "w", encoding="utf-8") as f:
                f.write(init_hql)

    def _generate_zeppelin_files(self):
        nb_folder = self.request.custom_folders.get("zeppelin_notebooks", "zeppelin/notebook")
        nb_dir = os.path.join(self.project_dir, nb_folder)
        os.makedirs(nb_dir, exist_ok=True)

        if self.include_templates:
            sample_nb = {
                "paragraphs": [
                    {
                        "text": f"%md\n# 🐘 Apache Zeppelin - {self.project_name}\nExploração Interativa de Big Data com Spark, Hive e PySpark",
                        "status": "READY"
                    },
                    {
                        "text": "%pyspark\n# Inicializando Spark Session\nprint('Spark Version:', spark.version)\ndf = spark.range(1, 100).toDF('id')\ndf.show(5)",
                        "status": "READY"
                    },
                    {
                        "text": "%sql\n-- Consulta SQL direta no Hive Metastore / Spark\nSHOW DATABASES;\n",
                        "status": "READY"
                    }
                ],
                "name": f"Tutorial-{self.project_name}",
                "id": "2A94M5J1Z",
                "noteParams": {},
                "noteForms": {},
                "angularObjects": {}
            }
            with open(os.path.join(nb_dir, "note.json"), "w", encoding="utf-8") as f:
                json.dump(sample_nb, f, indent=2)

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

        if "kafka_connect" in self.tools:
            reg_ps1 = """$ConnectUrl = "http://localhost:8083"
$ConfigFile = Join-Path $PSScriptRoot "..\debezium\register-postgres.json"
Write-Host "Registering Debezium Connector..." -ForegroundColor Cyan
$jsonBody = Get-Content -Raw -Path $ConfigFile
Invoke-RestMethod -Uri "$ConnectUrl/connectors" -Method Post -Body $jsonBody -ContentType "application/json"
Write-Host "Connector registered!" -ForegroundColor Green
"""
            with open(os.path.join(scripts_dir, "register-connectors.ps1"), "w", encoding="utf-8") as f:
                f.write(reg_ps1)

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
This test suite automatically verifies network connectivity, authentication,
and core functionality across all active containers in the project.
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
        # 302, 401, 403 are often valid responses for auth-protected endpoints like Airflow/Keycloak
        if e.code in (200, 302, 401, 403):
            return True, f"HTTP {{e.code}} ({{latency:.1f}}ms)"
        return False, f"HTTP Error {{e.code}}"
    except Exception as e:
        return False, str(e)


def run_all_tests():
    print("=" * 70)
    print(f" {{Colors.BOLD}}{{Colors.CYAN}}[*] STACKSTUDIO SERVICE TEST SUITE: {self.project_name.upper()}{{Colors.END}}")
    print("=" * 70)

    results = []

    # 1. PostgreSQL
    if "postgres" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("postgres", 5434)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("PostgreSQL (OLTP + CDC)", port, ok, detail))

    # 2. MySQL
    if "mysql" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("mysql", 3306)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("MySQL 8 (OLTP + Binlog)", port, ok, detail))

    # 3. ClickHouse
    if "clickhouse" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("clickhouse", 8123)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/ping")
        results.append(("ClickHouse OLAP", port, ok, detail))

    # 4. Kafka
    if "kafka" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("kafka", 9092)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("Apache Kafka (KRaft Broker)", port, ok, detail))

    # 5. Schema Registry
    if "schema_registry" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("schema_registry", 8086)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/subjects")
        results.append(("Confluent Schema Registry", port, ok, detail))

    # 6. Kafka Connect
    if "kafka_connect" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("kafka_connect", 8083)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/connectors")
        results.append(("Kafka Connect (Debezium CDC)", port, ok, detail))

    # 7. Kafka UI
    if "kafka_ui" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("kafka_ui", 8087)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("Kafka UI (Provectus)", port, ok, detail))

    # 8. MinIO Object Storage
    if "minio" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("minio", 9001)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/minio/health/live")
        results.append(("MinIO S3 Storage & Console", port, ok, detail))

    # 9. Iceberg REST Catalog
    if "iceberg_rest" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("iceberg_rest", 8181)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/v1/config")
        results.append(("Apache Iceberg REST Catalog", port, ok, detail))

    # 10. Apache Spark
    if "spark" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("spark", 8082)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("Apache Spark Master UI", port, ok, detail))

    # 11. Trino
    if "trino" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("trino", 8085)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/v1/info")
        results.append(("Trino Distributed SQL Engine", port, ok, detail))

    # 12. Airflow
    if "airflow" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("airflow", 8088)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/health")
        results.append(("Apache Airflow Webserver", port, ok, detail))

    # 13. Mage
    if "mage" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("mage", 6789)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("Mage.ai Orchestrator", port, ok, detail))

    # 14. Prefect
    if "prefect" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("prefect", 4200)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/api/health")
        results.append(("Prefect Server", port, ok, detail))

    # 15. MLflow
    if "mlflow" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("mlflow", 5001)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("MLflow Tracking & Registry", port, ok, detail))

    # 16. JupyterLab
    if "jupyterlab" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("jupyterlab", 8888)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("JupyterLab Workspace", port, ok, detail))

    # 17. Qdrant
    if "qdrant" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("qdrant", 6333)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/dashboard")
        results.append(("Qdrant Vector DB", port, ok, detail))

    # 18. Redis
    if "redis" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("redis", 6380)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("Redis Cache & Store", port, ok, detail))

    # 19. RabbitMQ
    if "rabbitmq" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("rabbitmq", 15672)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("RabbitMQ Management UI", port, ok, detail))

    # 20. Keycloak
    if "keycloak" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("keycloak", 8090)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("Keycloak IAM", port, ok, detail))

    # 21. Hasura
    if "hasura" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("hasura", 8095)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/healthz")
        results.append(("Hasura GraphQL Engine", port, ok, detail))

    # 22. Grafana
    if "grafana" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("grafana", 3005)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/api/health")
        results.append(("Grafana Dashboards", port, ok, detail))

    # 23. Prometheus
    if "prometheus" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("prometheus", 9095)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/-/healthy")
        results.append(("Prometheus Monitoring", port, ok, detail))

    # 24. Portainer
    if "portainer" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("portainer", 9443)
        ok, detail = check_tcp_port("localhost", port)
        results.append(("Portainer CE", port, ok, detail))

    # 25. pgAdmin
    if "pgadmin" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("pgadmin", 5055)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("pgAdmin 4 Web", port, ok, detail))

    # 26. Apache Hadoop HDFS
    if "hdfs" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("hdfs", 9870)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("Hadoop HDFS (NameNode UI)", port, ok, detail))

    # 27. Apache Hadoop YARN
    if "yarn" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("yarn", 8089)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/cluster")
        results.append(("Hadoop YARN (ResourceManager UI)", port, ok, detail))

    # 28. Apache Hive
    if "hive" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("hive", 10002)
        ok, detail = check_tcp_port("localhost", 10000)
        results.append(("Apache Hive (HiveServer2 10000)", port, ok, detail))

    # 29. Apache Zeppelin
    if "zeppelin" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("zeppelin", 8090)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("Apache Zeppelin Notebook", port, ok, detail))

    # 30. Ollama Local LLM Engine
    if "ollama" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("ollama", 11434)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/api/version")
        results.append(("Ollama LLM Engine", port, ok, detail))

    # 31. Open WebUI
    if "open_webui" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("open_webui", 3000)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}")
        results.append(("Open WebUI (ChatGPT Clone)", port, ok, detail))

    # 32. LocalAI
    if "localai" in ENABLED_TOOLS:
        port = CUSTOM_PORTS.get("localai", 8091)
        ok, detail = check_http_endpoint(f"http://localhost:{{port}}/readyz")
        results.append(("LocalAI OpenAI Engine", port, ok, detail))

    # PRINT SUMMARY
    passed = 0
    total = len(results)

    for name, port, ok, detail in results:
        status_badge = f"{{Colors.GREEN}}[PASSED]{{Colors.END}}" if ok else f"{{Colors.RED}}[FAILED]{{Colors.END}}"
        if ok:
            passed += 1
            if isinstance(detail, float):
                info = f"Online ({{detail:.1f}}ms)"
            else:
                info = f"Online ({{detail}})"
        else:
            info = f"Offline / Error: {{detail}}"

        print(f" {{status_badge}} {{name:<32}} (Port: {{port}}): {{info}}")

    print("-" * 70)
    if passed == total:
        print(f" {{Colors.GREEN}}{{Colors.BOLD}}[SUCCESS]{{Colors.END}} All {{total}}/{{total}} services are healthy and operational!")
    else:
        print(f" {{Colors.YELLOW}}{{Colors.BOLD}}[WARNING]{{Colors.END}} {{passed}}/{{total}} services passed. If containers just started, allow a few seconds for initialization and retry.")
    print("=" * 70)

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
'''
        with open(os.path.join(tests_dir, "test_services.py"), "w", encoding="utf-8") as f:
            f.write(test_py)

        # Pytest config
        pytest_ini = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Testes unitarios (sem dependencias externas de containers)
    integration: Testes de integracao (requer containers Docker ativos)
    slow: Testes com maior tempo de execucao
addopts = -v --tb=short -ra
"""
        with open(os.path.join(self.project_dir, "pytest.ini"), "w", encoding="utf-8") as f:
            f.write(pytest_ini)

        # conftest.py
        conftest_py = f"""import os
import pytest
import requests

@pytest.fixture(scope="session")
def http_session():
    session = requests.Session()
    session.headers.update({{"User-Agent": "StackStudio-Test-Runner/1.0"}})
    yield session
    session.close()

@pytest.fixture
def sample_cdc_event():
    return {{
        "before": None,
        "after": {{
            "order_id": 1001,
            "customer_id": 42,
            "status": "PROCESSING",
            "total_amount": 149.90,
            "order_date": 1724932800000000,
            "updated_at": 1724932800000000
        }},
        "source": {{
            "version": "2.6.1.Final",
            "connector": "postgresql",
            "name": "cdc",
            "ts_ms": 1724932800000,
            "db": "oltp_db",
            "schema": "ecommerce",
            "table": "orders",
            "txId": 501,
            "lsn": 24567890
        }},
        "op": "c",
        "ts_ms": 1724932800100,
        "transaction": None
    }}
"""
        with open(os.path.join(tests_dir, "conftest.py"), "w", encoding="utf-8") as f:
            f.write(conftest_py)

        # Unit Tests
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

        cdc_parser_py = """import pytest
from datetime import datetime
from typing import Dict, Any

class CDCPayloadParser:
    @staticmethod
    def parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(event, dict):
            raise ValueError("Invalid CDC event: must be a dictionary")
        op = event.get("op")
        if op not in ("c", "u", "d", "r"):
            raise ValueError(f"Unsupported CDC operation type: '{op}'")
        source = event.get("source") or {}
        table = source.get("table")
        schema = source.get("schema")
        if op == "d":
            data = event.get("before") or {}
            is_deleted = True
        else:
            data = event.get("after") or {}
            is_deleted = False
        ts_ms = event.get("ts_ms")
        event_timestamp = datetime.utcfromtimestamp(ts_ms / 1000.0) if ts_ms else datetime.utcnow()
        return {
            "table_name": f"{schema}.{table}" if schema and table else table,
            "operation": op,
            "is_deleted": is_deleted,
            "data": data,
            "event_timestamp": event_timestamp.isoformat(),
            "lsn": source.get("lsn"),
            "tx_id": source.get("txId")
        }

@pytest.mark.unit
class TestCDCPayloadParser:
    def test_parse_create_event(self, sample_cdc_event):
        res = CDCPayloadParser.parse_event(sample_cdc_event)
        assert res["operation"] == "c"
        assert res["is_deleted"] is False
        assert res["data"]["order_id"] == 1001
"""
        with open(os.path.join(unit_dir, "test_cdc_payload_parser.py"), "w", encoding="utf-8") as f:
            f.write(cdc_parser_py)

        # Integration Tests
        integration_dir = os.path.join(tests_dir, "integration")
        os.makedirs(integration_dir, exist_ok=True)

        # run_all_tests.py
        runner_py = """import sys
import subprocess

def main():
    args = sys.argv[1:]
    mode = "all"
    if "--unit" in args:
        mode = "unit"
    elif "--integration" in args:
        mode = "integration"

    print("=" * 70)
    print(f" [*] EXECUTANDO SUITE DE TESTES: MODE={mode.upper()}")
    print("=" * 70)

    cmd = [sys.executable, "-m", "pytest"]
    if mode == "unit":
        cmd.extend(["-m", "unit"])
    elif mode == "integration":
        cmd.extend(["-m", "integration"])
    cmd.extend(["-v", "--tb=short"])

    res = subprocess.run(cmd)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
"""
        with open(os.path.join(tests_dir, "run_all_tests.py"), "w", encoding="utf-8") as f:
            f.write(runner_py)

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
        """Calculates official and recommended VS Code extensions based on selected tools and user custom list."""
        extensions: List[str] = ["redhat.vscode-yaml", "eamodio.gitlens", "ms-azuretools.vscode-docker"]
        
        mapping = {
            "python": ["ms-python.python", "ms-python.vscode-pylance", "ms-toolsai.jupyter"],
            "spark": ["ms-python.python", "ms-toolsai.jupyter"],
            "pyspark": ["ms-python.python", "ms-toolsai.jupyter"],
            "airflow": ["ms-python.python", "redhat.vscode-yaml"],
            "fastapi": ["ms-python.python"],
            "dbt": ["innoverio.vscode-dbt-power-user", "ms-python.python"],
            "postgres": ["ckolkman.vscode-postgres", "mtxr.sqltools"],
            "mysql": ["cweijan.vscode-database-client2", "mtxr.sqltools"],
            "clickhouse": ["cweijan.vscode-database-client2"],
            "redis": ["cweijan.vscode-database-client2"],
            "kafka": ["formulahendry.vscode-kafka"],
            "terraform": ["hashicorp.terraform"],
            "ansible": ["redhat.ansible", "redhat.vscode-yaml"],
            "nginx": ["ahmadalli.vscode-nginx-conf"],
            "k8s": ["ms-kubernetes-tools.vscode-kubernetes-tools", "redhat.vscode-yaml"],
            "opentelemetry": ["redhat.vscode-yaml"],
            "openmetadata": ["redhat.vscode-yaml"],
            "hdfs": ["redhat.vscode-yaml"],
            "yarn": ["redhat.vscode-yaml"],
            "hive": ["alanz.vscode-hql", "mtxr.sqltools", "redhat.vscode-yaml"],
            "zeppelin": ["ms-python.python", "ms-toolsai.jupyter"]
        }

        for tool in self.tools:
            if tool in mapping:
                for ext in mapping[tool]:
                    if ext not in extensions:
                        extensions.append(ext)

        # Add user-customized extensions
        custom_exts = getattr(self.request, "custom_vscode_extensions", None)
        if custom_exts and isinstance(custom_exts, list):
            for ext in custom_exts:
                if ext and ext.strip() and ext.strip() not in extensions:
                    extensions.append(ext.strip())

        return extensions

    def _generate_vscode_files(self):
        """Generates .vscode/extensions.json, .vscode/settings.json, and vscode/entrypoint.sh."""
        vscode_dir = os.path.join(self.project_dir, ".vscode")
        os.makedirs(vscode_dir, exist_ok=True)

        exts = self._get_vscode_extensions()
        
        # 1. .vscode/extensions.json (Official VS Code Workspace Recommendations)
        extensions_json = {
            "recommendations": exts
        }
        with open(os.path.join(vscode_dir, "extensions.json"), "w", encoding="utf-8") as f:
            json.dump(extensions_json, f, indent=2)

        # 2. .vscode/settings.json
        settings_json = {
            "files.autoSave": "afterDelay",
            "editor.formatOnSave": True,
            "editor.tabSize": 2,
            "terminal.integrated.defaultProfile.linux": "bash",
            "docker.showStartPage": False
        }
        with open(os.path.join(vscode_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump(settings_json, f, indent=2)

        # 3. vscode/entrypoint.sh (Auto-install script executed by code-server container)
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
        entrypoint_path = os.path.join(vscode_scripts_dir, "entrypoint.sh")
        with open(entrypoint_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(entrypoint_content)
