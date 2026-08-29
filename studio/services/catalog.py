"""
Comprehensive Catalog of Tools and Docker Compose Service Definitions
"""

from typing import Dict, List
from studio.models import ToolOption, ToolCategory, ProjectPreset


CATEGORIES: List[ToolCategory] = [
    ToolCategory(
        id="data_engineering",
        name="Engenharia de Dados & Lakehouse",
        icon="database",
        description="Bancos transacionais, analíticos, mensageria CDC, streaming, armazenamento de objetos e catálogos ACID.",
        tools=[
            ToolOption(
                id="postgres",
                name="PostgreSQL (OLTP + CDC)",
                category="data_engineering",
                description="Banco relacional OLTP configurado com replicação lógica (wal_level=logical) para CDC com Debezium.",
                icon="database",
                badge="OLTP / CDC",
                default_port=5434,
                env_vars={"POSTGRES_USER": "postgres", "POSTGRES_PASSWORD": "postgres", "POSTGRES_DB": "oltp_db"},
                default_folders={"init_sql": "postgres/init.sql"}
            ),
            ToolOption(
                id="mysql",
                name="MySQL 8 (OLTP + Binlog)",
                category="data_engineering",
                description="Banco relacional com binlog format ROW habilitado para streaming de CDC.",
                icon="database",
                badge="OLTP / CDC",
                default_port=3306,
                env_vars={"MYSQL_ROOT_PASSWORD": "rootpassword", "MYSQL_DATABASE": "app_db", "MYSQL_USER": "dbuser", "MYSQL_PASSWORD": "dbpassword"},
                default_folders={"init_sql": "mysql/init.sql"}
            ),
            ToolOption(
                id="clickhouse",
                name="ClickHouse OLAP",
                category="data_engineering",
                description="Banco colunar de altíssimo desempenho para agregação e analytics em tempo real.",
                icon="bar-chart-2",
                badge="OLAP / Fast SQL",
                default_port=8123,
                ui_url="http://localhost:8123/play",
                default_folders={"init_sql": "clickhouse/init.sql"}
            ),
            ToolOption(
                id="kafka",
                name="Apache Kafka (KRaft)",
                category="data_engineering",
                description="Plataforma de streaming de eventos distribuída operando em modo KRaft (sem Zookeeper).",
                icon="activity",
                badge="Streaming Buffer",
                default_port=9092
            ),
            ToolOption(
                id="schema_registry",
                name="Schema Registry",
                category="data_engineering",
                description="Confluent Schema Registry para governança de esquemas Avro/JSON no Kafka.",
                icon="shield-check",
                badge="Schema Governance",
                default_port=8086,
                ui_url="http://localhost:8086",
                dependencies=["kafka"]
            ),
            ToolOption(
                id="kafka_connect",
                name="Kafka Connect + Debezium",
                category="data_engineering",
                description="Debezium Connector para captura de mutações (CDC) direto do PostgreSQL/MySQL para o Kafka.",
                icon="repeat",
                badge="CDC Engine",
                default_port=8083,
                ui_url="http://localhost:8083",
                dependencies=["kafka", "postgres"],
                default_folders={"connectors": "debezium"}
            ),
            ToolOption(
                id="kafka_ui",
                name="Kafka UI (Provectus)",
                category="data_engineering",
                description="Interface visual intuitiva para inspecionar tópicos, mensagens, partições, consumer lag e conectores.",
                icon="layout",
                badge="Web UI",
                default_port=8087,
                ui_url="http://localhost:8087",
                dependencies=["kafka"]
            ),
            ToolOption(
                id="minio",
                name="MinIO Object Storage",
                category="data_engineering",
                description="Armazenamento de objetos de alta performance compatível com a API AWS S3 para Lakehouses.",
                icon="hard-drive",
                badge="S3 Storage",
                default_port=9001,
                ui_url="http://localhost:9001",
                env_vars={"MINIO_ROOT_USER": "admin", "MINIO_ROOT_PASSWORD": "password123"}
            ),
            ToolOption(
                id="iceberg_rest",
                name="Apache Iceberg REST Catalog",
                category="data_engineering",
                description="Catálogo de metadados Iceberg REST para gerenciamento de tabelas ACID sobre MinIO/S3.",
                icon="layers",
                badge="Table Format",
                default_port=8181,
                ui_url="http://localhost:8181/v1/config",
                dependencies=["minio"]
            ),
            ToolOption(
                id="spark",
                name="Apache Spark 3.5 Cluster",
                category="data_engineering",
                description="Cluster Spark (Master & Worker) com suporte nativo a PySpark, Iceberg, Kafka e S3.",
                icon="zap",
                badge="Stream & Batch",
                default_port=8082,
                ui_url="http://localhost:8082",
                default_folders={"apps": "spark/apps", "conf": "spark/conf"}
            ),
            ToolOption(
                id="trino",
                name="Trino SQL Engine",
                category="data_engineering",
                description="Motor de consulta distribuído para execução de SQL ad-hoc e Time-Travel sobre Iceberg e S3.",
                icon="search",
                badge="Interactive SQL",
                default_port=8085,
                ui_url="http://localhost:8085",
                dependencies=["iceberg_rest", "minio"],
                default_folders={"etc": "trino/etc"}
            ),
            ToolOption(
                id="dbt",
                name="dbt Core",
                category="data_engineering",
                description="Framework de modelagem, transformação SQL, testes e documentação de dados (Data Build Tool).",
                icon="code",
                badge="Transformations",
                default_folders={"project": "dbt"}
            ),
            ToolOption(
                id="openmetadata",
                name="OpenMetadata & Governança",
                category="data_engineering",
                description="Catálogo unificado de governança de dados, linhagem ponta-a-ponta (lineage), dicionário e métricas de qualidade.",
                icon="shield-check",
                badge="Data Governance",
                default_port=8585,
                ui_url="http://localhost:8585",
                dependencies=["postgres"],
                env_vars={
                    "OPENMETADATA_PORT": "8585",
                    "DB_USER": "postgres",
                    "DB_USER_PASSWORD": "postgres_password"
                }
            )
        ]
    ),
    ToolCategory(
        id="mlops",
        name="MLOps & Inteligência Artificial",
        icon="cpu",
        description="Rastreamento de experimentos, registro de modelos, notebooks interativos e bancos de dados vetoriais.",
        tools=[
            ToolOption(
                id="mlflow",
                name="MLflow Tracking & Registry",
                category="mlops",
                description="Servidor de rastreamento de experimentos de Machine Learning, métricas e Model Registry.",
                icon="compass",
                badge="Model Tracking",
                default_port=5001,
                ui_url="http://localhost:5001",
                dependencies=["postgres", "minio"],
                default_folders={"artifacts": "mlflow/artifacts"}
            ),
            ToolOption(
                id="jupyterlab",
                name="JupyterLab Workspace",
                category="mlops",
                description="Ambiente interativo de desenvolvimento para Data Science e Engenharia de Dados.",
                icon="book-open",
                badge="Notebooks",
                default_port=8888,
                ui_url="http://localhost:8888",
                default_folders={"notebooks": "notebooks"}
            ),
            ToolOption(
                id="qdrant",
                name="Qdrant Vector DB",
                category="mlops",
                description="Banco de dados vetorial de alto desempenho para busca semântica, embeddings e pipelines RAG.",
                icon="box",
                badge="Vector DB / RAG",
                default_port=6333,
                ui_url="http://localhost:6333/dashboard"
            ),
            ToolOption(
                id="chromadb",
                name="ChromaDB",
                category="mlops",
                description="Banco vetorial open-source voltado para aplicações com LLMs e agentes de IA.",
                icon="database",
                badge="Vector DB",
                default_port=8000
            ),
            ToolOption(
                id="feast",
                name="Feast Feature Store",
                category="mlops",
                description="Feature Store para orquestrar features online (Redis) e offline (Parquet/Iceberg).",
                icon="grid",
                badge="Feature Store",
                dependencies=["redis", "postgres"],
                default_folders={"feature_repo": "feature_repo"}
            )
        ]
    ),
    ToolCategory(
        id="orchestration",
        name="Orquestração & Governança",
        icon="clock",
        description="Agendamento, dependências de pipelines e governança de rotinas de manutenção de dados.",
        tools=[
            ToolOption(
                id="airflow",
                name="Apache Airflow 2.9",
                category="orchestration",
                description="Orquestrador líder de mercado para automação de DAGs de manutenção de Lakehouse e agregações Gold.",
                icon="git-merge",
                badge="Orchestrator",
                default_port=8088,
                ui_url="http://localhost:8088",
                env_vars={"AIRFLOW_USER": "admin", "AIRFLOW_PASSWORD": "admin"},
                default_folders={"dags": "airflow/dags", "plugins": "airflow/plugins"}
            ),
            ToolOption(
                id="mage",
                name="Mage.ai",
                category="orchestration",
                description="Orquestrador moderno com desenvolvimento interativo de pipelines em tempo real e batch.",
                icon="wand-2",
                badge="Modern Orchestrator",
                default_port=6789,
                ui_url="http://localhost:6789",
                default_folders={"pipelines": "mage"}
            ),
            ToolOption(
                id="prefect",
                name="Prefect Server",
                category="orchestration",
                description="Motor de orquestração moderno orientado a fluxos Python e tarefas assíncronas.",
                icon="fast-forward",
                badge="Workflow Engine",
                default_port=4200,
                ui_url="http://localhost:4200",
                default_folders={"flows": "flows"}
            )
        ]
    ),
    ToolCategory(
        id="backend",
        name="Backend & Mensageria",
        icon="server",
        description="Caches distribuídos, brokers de mensagens, autenticação/IAM e motores de APIs instantâneas.",
        tools=[
            ToolOption(
                id="redis",
                name="Redis & Redis Commander",
                category="backend",
                description="Banco chave-valor em memória para cache, sessões, rate-limiting e filas Pub/Sub.",
                icon="archive",
                badge="Cache / NoSQL",
                default_port=6380,
                ui_url="http://localhost:8089"
            ),
            ToolOption(
                id="rabbitmq",
                name="RabbitMQ + Management",
                category="backend",
                description="Message broker AMQP altamente confiável com exchange routing e interface de gestão web.",
                icon="send",
                badge="AMQP Broker",
                default_port=15672,
                ui_url="http://localhost:15672",
                env_vars={"RABBITMQ_DEFAULT_USER": "guest", "RABBITMQ_DEFAULT_PASS": "guest"}
            ),
            ToolOption(
                id="keycloak",
                name="Keycloak IAM",
                category="backend",
                description="Servidor de identidade e gestão de acessos (SSO, OAuth2, OpenID Connect).",
                icon="key",
                badge="Auth / IAM",
                default_port=8090,
                ui_url="http://localhost:8090",
                env_vars={"KEYCLOAK_ADMIN": "admin", "KEYCLOAK_ADMIN_PASSWORD": "admin"}
            ),
            ToolOption(
                id="hasura",
                name="Hasura GraphQL Engine",
                category="backend",
                description="Motor de API GraphQL e REST instantânea com permissões granulares sobre PostgreSQL.",
                icon="share-2",
                badge="Instant GraphQL",
                default_port=8095,
                ui_url="http://localhost:8095",
                dependencies=["postgres"]
            ),
            ToolOption(
                id="elasticsearch",
                name="Elasticsearch + Kibana",
                category="backend",
                description="Motor de busca distribuído e dashboards analíticos de texto e logs com Kibana.",
                icon="search",
                badge="Search Engine",
                default_port=5601,
                ui_url="http://localhost:5601"
            ),
            ToolOption(
                id="nginx",
                name="NGINX Proxy & Web Server",
                category="backend",
                description="Servidor web de alta performance, proxy reverso, balanceador de carga HTTP e terminação SSL/TLS.",
                icon="globe",
                badge="Reverse Proxy / Web",
                default_port=8080,
                ui_url="http://localhost:8080",
                default_folders={"config": "nginx/nginx.conf", "html": "nginx/html"}
            ),
            ToolOption(
                id="apigateway",
                name="Kong API Gateway",
                category="backend",
                description="Gateway de APIs nativo de nuvem de alta performance para controle de tráfego, autenticação e rate limiting.",
                icon="shield",
                badge="API Gateway",
                default_port=8000,
                ui_url="http://localhost:8002",
                default_folders={"config": "kong/kong.yml"}
            )
        ]
    ),
    ToolCategory(
        id="devops",
        name="DevOps & Observabilidade",
        icon="pie-chart",
        description="Métricas, monitoramento de containers, interfaces de administração e dashboards.",
        tools=[
            ToolOption(
                id="grafana",
                name="Grafana Dashboards",
                category="devops",
                description="Plataforma de visualização de métricas, alertas e dashboards analíticos em tempo real.",
                icon="layout-dashboard",
                badge="Dashboards",
                default_port=3005,
                ui_url="http://localhost:3005",
                env_vars={"GF_SECURITY_ADMIN_USER": "admin", "GF_SECURITY_ADMIN_PASSWORD": "admin"}
            ),
            ToolOption(
                id="prometheus",
                name="Prometheus",
                category="devops",
                description="Sistema de monitoramento e banco de séries temporais para coleta de métricas.",
                icon="trending-up",
                badge="Metrics",
                default_port=9095,
                ui_url="http://localhost:9095"
            ),
            ToolOption(
                id="portainer",
                name="Portainer CE",
                category="devops",
                description="Interface gráfica web amigável para gerenciamento de containers, volumes e redes Docker.",
                icon="box",
                badge="Docker Management",
                default_port=9443,
                ui_url="https://localhost:9443"
            ),
            ToolOption(
                id="pgadmin",
                name="pgAdmin 4",
                category="devops",
                description="Ambiente visual web para administração e consultas avançadas em bancos PostgreSQL.",
                icon="terminal",
                badge="DB Admin",
                default_port=5055,
                ui_url="http://localhost:5055",
                dependencies=["postgres"],
                env_vars={"PGADMIN_DEFAULT_EMAIL": "admin@lakehouse.com", "PGADMIN_DEFAULT_PASSWORD": "admin"}
            ),
            ToolOption(
                id="opentelemetry",
                name="OpenTelemetry Collector",
                category="devops",
                description="Coletor de telemetria unificado para rastreamento distribuído (OTLP traces), métricas e logs agnóstico a vendors.",
                icon="activity",
                badge="OTel / Traces",
                default_port=4318,
                ui_url="http://localhost:13133",
                default_folders={"config": "otel/otel-collector-config.yaml"}
            ),
            ToolOption(
                id="ansible",
                name="Ansible Automation",
                category="devops",
                description="Automação de infraestrutura como código (IaC) e configuração de servidores com playbooks YAML sem agentes.",
                icon="terminal",
                badge="IaC / Automation",
                default_folders={"playbooks": "ansible/playbooks", "inventory": "ansible/inventory"}
            ),
            ToolOption(
                id="terraform",
                name="Terraform (IaC)",
                category="devops",
                description="Provisionamento e orquestração declarativa de infraestrutura como código multi-cloud com HashiCorp HCL.",
                icon="layers",
                badge="Infrastructure as Code",
                default_folders={"root": "terraform"}
            )
        ]
    )
]

PRESETS: List[ProjectPreset] = [
    ProjectPreset(
        id="lakehouse_event_driven",
        name="🌊 Event-Driven Lakehouse (CDC + Iceberg)",
        description="Arquitetura completa com PostgreSQL, Kafka KRaft, Debezium CDC, MinIO, Iceberg REST, Spark 3.5, Trino, Airflow e Kafka UI.",
        icon="waves",
        tools=["postgres", "kafka", "schema_registry", "kafka_connect", "kafka_ui", "minio", "iceberg_rest", "spark", "trino", "airflow"]
    ),
    ProjectPreset(
        id="mlops_platform",
        name="🤖 MLOps & Vector AI Platform",
        description="Ambiente para ciência de dados e IA com PostgreSQL, MinIO, MLflow, JupyterLab, Qdrant Vector DB, Redis e Grafana.",
        icon="cpu",
        tools=["postgres", "minio", "mlflow", "jupyterlab", "qdrant", "redis", "grafana"]
    ),
    ProjectPreset(
        id="backend_event_streaming",
        name="🚀 Microservices & Real-Time Backend",
        description="Stack para microsserviços modernos com PostgreSQL, Redis, RabbitMQ, Kafka, Keycloak, Hasura GraphQL e Portainer.",
        icon="server",
        tools=["postgres", "redis", "rabbitmq", "kafka", "keycloak", "hasura", "portainer"]
    ),
    ProjectPreset(
        id="modern_data_stack",
        name="📊 Modern Data Stack (Analytics & BI)",
        description="Stack analítica com PostgreSQL, ClickHouse, MinIO, Iceberg, Trino, dbt, Airflow e Grafana.",
        icon="bar-chart-2",
        tools=["postgres", "clickhouse", "minio", "iceberg_rest", "trino", "dbt", "airflow", "grafana"]
    )
]


def get_catalog() -> List[ToolCategory]:
    from studio.services.plugin_manager import PluginManager
    import copy

    categories_copy = copy.deepcopy(CATEGORIES)
    plugins = PluginManager.list_plugins()

    cat_map = {c.id: c for c in categories_copy}
    custom_plugins_cat = None

    for plugin in plugins:
        tool_opt = PluginManager.plugin_to_tool_option(plugin)
        if plugin.category in cat_map:
            cat_map[plugin.category].tools.append(tool_opt)
        else:
            if not custom_plugins_cat:
                custom_plugins_cat = ToolCategory(
                    id="plugins",
                    name="🧩 Plugins & Ferramentas Customizadas",
                    icon="puzzle",
                    description="Ferramentas adicionadas dinamicamente via sistema de plugins.",
                    tools=[]
                )
                categories_copy.append(custom_plugins_cat)
            custom_plugins_cat.tools.append(tool_opt)

    return categories_copy


def get_tool_by_id(tool_id: str) -> ToolOption:
    # 1. Search in static catalog
    for cat in CATEGORIES:
        for tool in cat.tools:
            if tool.id == tool_id:
                return tool

    # 2. Search in plugins
    from studio.services.plugin_manager import PluginManager
    plugin = PluginManager.get_plugin(tool_id)
    if plugin:
        return PluginManager.plugin_to_tool_option(plugin)

    raise ValueError(f"Tool with id '{tool_id}' not found in catalog or plugins.")
