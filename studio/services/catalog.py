"""
Comprehensive Catalog of Tools and Docker Compose Service Definitions
"""

from typing import Dict, List
from studio.models import ToolOption, ToolCategory, ProjectPreset


CATEGORIES: List[ToolCategory] = [
    ToolCategory(
        id="data_engineering",
        name="Engenharia de Dados, Lakehouse & Governança",
        icon="database",
        description="Bancos transacionais, analíticos, mensageria CDC, streaming, armazenamento de objetos, catálogos ACID, BI e qualidade de dados.",
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
                id="doris",
                name="Apache Doris (Real-Time MPP)",
                category="data_engineering",
                description="Motor analítico MPP de alto desempenho para sub-second analytics, dashboards e queries em tempo real.",
                icon="database",
                badge="Real-Time OLAP",
                default_port=8030,
                ui_url="http://localhost:8030",
                default_folders={"init_sql": "doris/init.sql"}
            ),
            ToolOption(
                id="starrocks",
                name="StarRocks (Next-Gen MPP)",
                category="data_engineering",
                description="Banco analítico MPP de ultra-baixa latência para consultas vetoriais massivas e métricas em tempo real.",
                icon="zap",
                badge="Sub-Second OLAP",
                default_port=8031,
                ui_url="http://localhost:8031",
                default_folders={"init_sql": "starrocks/init.sql"}
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
                env_vars={"MINIO_ROOT_USER": "admin", "MINIO_ROOT_PASSWORD": "admin123"}
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
                id="flink",
                name="Apache Flink (Stateful Stream)",
                category="data_engineering",
                description="Motor líder para processamento distribuído de stream stateful com latência sub-milisegundo e event-time semantics.",
                icon="activity",
                badge="Stream Computing",
                default_port=8093,
                ui_url="http://localhost:8093",
                default_folders={"jobs": "flink/jobs", "conf": "flink/conf"}
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
                id="superset",
                name="Apache Superset (BI & Data Viz)",
                category="data_engineering",
                description="Plataforma visual de exploração de dados, dashboards interativos e SQL Lab conectado direto a Trino, ClickHouse e PostgreSQL.",
                icon="bar-chart",
                badge="BI & Analytics",
                default_port=8094,
                ui_url="http://localhost:8094",
                env_vars={"SUPERSET_ADMIN_USER": "admin", "SUPERSET_ADMIN_PASSWORD": "admin"},
                default_folders={"dashboards": "superset/dashboards", "sqllab": "superset/sqllab"}
            ),
            ToolOption(
                id="metabase",
                name="Metabase BI",
                category="data_engineering",
                description="Ferramenta de Business Intelligence simples e elegante para perguntas, gráficos e visualizações sem necessidade de SQL avançado.",
                icon="pie-chart",
                badge="Business Intel",
                default_port=3006,
                ui_url="http://localhost:3006",
                default_folders={"queries": "metabase/queries"}
            ),
            ToolOption(
                id="great_expectations",
                name="Great Expectations (Data Quality)",
                category="data_engineering",
                description="Framework de validação, documentação e profiling automático de qualidade de dados e contratos de esquemas.",
                icon="check-circle",
                badge="Data Quality",
                default_folders={"expectations": "great_expectations/expectations", "checkpoints": "great_expectations/checkpoints"}
            ),
            ToolOption(
                id="soda_core",
                name="Soda Core (Data Contracts)",
                category="data_engineering",
                description="Linguagem declarativa (SodaCL) para testes de confiabilidade, métricas e detecção de anomalias em pipelines de dados.",
                icon="check-square",
                badge="Data Contracts",
                default_folders={"checks": "soda/checks", "config": "soda/configuration.yml"}
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
            ),
            ToolOption(
                id="datahub",
                name="DataHub (LinkedIn)",
                category="data_engineering",
                description="Catálogo de metadados extensível, busca unificada de dados e grafo de linhagem 360° para arquiteturas corporativas de dados.",
                icon="layers",
                badge="Metadata & Lineage",
                default_port=9002,
                ui_url="http://localhost:9002",
                default_folders={"recipes": "datahub/recipes"}
            ),
            ToolOption(
                id="ranger",
                name="Apache Ranger (Security & Governance)",
                category="data_engineering",
                description="Plataforma de segurança de dados para controle de acesso granular baseado em políticas (RBAC/ABAC) sobre Hadoop, Spark, Kafka e Trino.",
                icon="lock",
                badge="Data Security / RBAC",
                default_port=6080,
                ui_url="http://localhost:6080",
                env_vars={"RANGER_ADMIN_USER": "admin", "RANGER_ADMIN_PASSWORD": "admin123"},
                default_folders={"policies": "ranger/policies"}
            ),
            ToolOption(
                id="hdfs",
                name="Apache Hadoop HDFS",
                category="data_engineering",
                description="Sistema de arquivos distribuído tolerante a falhas (HDFS) com NameNode e DataNode para armazenamento de Data Lakes massivos.",
                icon="hard-drive",
                badge="Distributed FS",
                default_port=9870,
                ui_url="http://localhost:9870",
                env_vars={"CLUSTER_NAME": "hadoop-cluster"}
            ),
            ToolOption(
                id="yarn",
                name="Apache Hadoop YARN",
                category="data_engineering",
                description="Gerenciador de recursos de cluster distribuído (YARN) com ResourceManager e NodeManager para execução de jobs de processamento.",
                icon="cpu",
                badge="Resource Manager",
                default_port=8089,
                ui_url="http://localhost:8089",
                dependencies=["hdfs"]
            ),
            ToolOption(
                id="hive",
                name="Apache Hive Metastore & Server",
                category="data_engineering",
                description="Data Warehouse distribuído com Hive Metastore (HMS) e HiveServer2 para consultas SQL sobre HDFS e S3/MinIO.",
                icon="database",
                badge="Data Warehouse / HMS",
                default_port=10002,
                ui_url="http://localhost:10002",
                dependencies=["postgres", "hdfs"],
                default_folders={"warehouse": "hive/warehouse"}
            ),
            ToolOption(
                id="zeppelin",
                name="Apache Zeppelin Notebook",
                category="data_engineering",
                description="Notebook colaborativo e interativo multi-linguagem (Spark, PySpark, SQL, Hive, Python, Shell) para análise e exploração de dados.",
                icon="book-open",
                badge="Interactive Notebook",
                default_port=8090,
                ui_url="http://localhost:8090",
                default_folders={"notebooks": "zeppelin/notebook"}
            )
        ]
    ),
    ToolCategory(
        id="backend",
        name="Backend, Mensageria & Integração",
        icon="server",
        description="Caches distribuídos, brokers de mensagens, segredos, autenticação/IAM, orquestração de microsserviços e automação visual.",
        tools=[
            ToolOption(
                id="redis",
                name="Redis & Redis Commander",
                category="backend",
                description="Banco chave-valor em memória para cache, sessões, rate-limiting e filas Pub/Sub com interface web Redis Commander.",
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
                id="redpanda",
                name="Redpanda (C++ Kafka Alternative)",
                category="backend",
                description="Broker de streaming em C++ compatível com Kafka, sem JVM, ultra-leve e com console web integrado para alta performance.",
                icon="zap",
                badge="C++ Streaming",
                default_port=8099,
                ui_url="http://localhost:8099",
                default_folders={"data": "redpanda/data"}
            ),
            ToolOption(
                id="pulsar",
                name="Apache Pulsar + Manager",
                category="backend",
                description="Plataforma de mensageria Pub/Sub distribuída multi-tenant com desacoplamento de storage e compute com interface Pulsar Manager.",
                icon="share-2",
                badge="Multi-Tenant PubSub",
                default_port=9527,
                ui_url="http://localhost:9527",
                default_folders={"conf": "pulsar/conf"}
            ),
            ToolOption(
                id="temporal",
                name="Temporal (Workflow Orchestration)",
                category="backend",
                description="Orquestrador de workflows de microsserviços com execução durável e tolerante a falhas (Temporal Server + Web UI).",
                icon="repeat",
                badge="Durable Workflows",
                default_port=8233,
                ui_url="http://localhost:8233",
                default_folders={"workflows": "temporal/workflows", "activities": "temporal/activities"}
            ),
            ToolOption(
                id="n8n",
                name="n8n (Workflow Automation)",
                category="backend",
                description="Plataforma de automação de fluxos e integração de APIs low-code com interface visual intuitiva e centenas de integrações.",
                icon="git-pull-request",
                badge="Low-Code Automation",
                default_port=5678,
                ui_url="http://localhost:5678",
                default_folders={"workflows": "n8n/workflows"}
            ),
            ToolOption(
                id="vault",
                name="HashiCorp Vault",
                category="backend",
                description="Gestão centralizada de segredos, certificados TLS, credenciais dinâmicas e criptografia como serviço com interface Web.",
                icon="lock",
                badge="Secrets / KMS",
                default_port=8200,
                ui_url="http://localhost:8200",
                env_vars={"VAULT_DEV_ROOT_TOKEN_ID": "root"},
                default_folders={"policies": "vault/policies", "config": "vault/config"}
            ),
            ToolOption(
                id="keycloak",
                name="Keycloak IAM",
                category="backend",
                description="Servidor de identidade e gestão de acessos corporativo (SSO, OAuth2, OpenID Connect).",
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
                default_port=8088,
                ui_url="http://localhost:8088",
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
        description="Métricas, agregação de logs, distributed tracing, ingress proxy, GitOps, IaC e dashboards.",
        tools=[
            ToolOption(
                id="grafana",
                name="Grafana Dashboards",
                category="devops",
                description="Plataforma de visualização de métricas, logs, traces e alertas em tempo real.",
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
                id="loki",
                name="Grafana Loki & Promtail",
                category="devops",
                description="Sistema de agregação e consulta de logs distribuídos nativo da stack Grafana (PLG Stack: Promtail + Loki + Grafana).",
                icon="file-text",
                badge="Log Aggregation",
                default_port=3100,
                ui_url="http://localhost:3100/ready",
                default_folders={"config": "loki/loki-config.yaml", "promtail": "loki/promtail-config.yaml"}
            ),
            ToolOption(
                id="jaeger",
                name="Jaeger Distributed Tracing",
                category="devops",
                description="Plataforma de rastreamento distribuído ponta-a-ponta para monitoramento de latência e resolução de problemas em microsserviços.",
                icon="activity",
                badge="Distributed Traces",
                default_port=16686,
                ui_url="http://localhost:16686"
            ),
            ToolOption(
                id="traefik",
                name="Traefik v3 Edge Router",
                category="devops",
                description="Reverse proxy moderno e edge router nativo de nuvem/Docker com auto-discovery dinâmico de serviços via labels.",
                icon="navigation",
                badge="Edge Proxy / Ingress",
                default_port=8081,
                ui_url="http://localhost:8081",
                default_folders={"dynamic_conf": "traefik/dynamic_conf.yml"}
            ),
            ToolOption(
                id="argocd",
                name="ArgoCD (GitOps CD)",
                category="devops",
                description="Padrão da indústria para entrega contínua declarativa (Continuous Delivery) e GitOps em clusters Kubernetes.",
                icon="git-commit",
                badge="GitOps CD",
                default_port=8098,
                ui_url="http://localhost:8098",
                default_folders={"applications": "argocd/applications"}
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
            ),
            ToolOption(
                id="vscode",
                name="VS Code Web (IDE)",
                category="devops",
                description="Ambiente de desenvolvimento completo do Visual Studio Code no navegador para editar códigos e scripts diretamente no browser.",
                icon="code",
                badge="Web IDE",
                default_port=8443,
                ui_url="http://localhost:8443/?folder=/home/coder/project",
                env_vars={"PASSWORD": "admin"}
            )
        ]
    ),
    ToolCategory(
        id="security_siem",
        name="🛡️ Segurança da Informação, SIEM & SOC",
        icon="shield",
        description="Plataformas de SIEM, XDR, detecção de ameaças, resposta a incidentes, inteligência de ameaças e auditoria de rede.",
        tools=[
            ToolOption(
                id="wazuh",
                name="Wazuh (SIEM & XDR)",
                category="security_siem",
                description="Plataforma unificada de SIEM e XDR para detecção de intrusões, monitoramento de integridade de arquivos (FIM) e análise de logs de segurança.",
                icon="shield",
                badge="SIEM / XDR",
                default_port=8444,
                ui_url="https://localhost:8444",
                env_vars={"INDEXER_PASSWORD": "admin", "WAZUH_API_PASSWORD": "admin"},
                default_folders={"rules": "wazuh/rules", "decoders": "wazuh/decoders"}
            ),
            ToolOption(
                id="splunk",
                name="Splunk Enterprise",
                category="security_siem",
                description="Plataforma corporativa para busca, análise, correlação de eventos e monitoramento em tempo real de big data de segurança.",
                icon="search",
                badge="Security Analytics",
                default_port=8001,
                ui_url="http://localhost:8001",
                env_vars={"SPLUNK_START_ARGS": "--accept-license", "SPLUNK_PASSWORD": "AdminPassword123!"},
                default_folders={"apps": "splunk/apps"}
            ),
            ToolOption(
                id="elastic_security",
                name="Elastic Security (SIEM)",
                category="security_siem",
                description="Solução de SIEM da Elastic com regras de detecção pré-construídas, Threat Hunting e correlação de eventos de endpoint.",
                icon="shield-check",
                badge="Elastic SIEM",
                default_port=5602,
                ui_url="http://localhost:5602/app/security",
                default_folders={"rules": "elastic_security/rules"}
            ),
            ToolOption(
                id="thehive",
                name="TheHive & Cortex (SIRP)",
                category="security_siem",
                description="Plataforma de gestão de resposta a incidentes de segurança (SIRP) integrada com motor de automação e análise de observáveis Cortex.",
                icon="activity",
                badge="Incident Response",
                default_port=9004,
                ui_url="http://localhost:9004",
                default_folders={"data": "thehive/data", "cortex": "cortex/analyzers"}
            ),
            ToolOption(
                id="misp",
                name="MISP (Threat Intelligence)",
                category="security_siem",
                description="Plataforma de compartilhamento e correlação de inteligência de ameaças cibernéticas (IOCs, CVEs, táticas MITRE ATT&CK).",
                icon="share-2",
                badge="Threat Intel / IOCs",
                default_port=8084,
                ui_url="http://localhost:8084",
                default_folders={"feeds": "misp/feeds"}
            ),
            ToolOption(
                id="shuffle",
                name="Shuffle SOAR",
                category="security_siem",
                description="Plataforma open-source de orquestração e automação de segurança (SOAR) para conectar alertas de SIEM a ações de contenção.",
                icon="repeat",
                badge="SOAR Automation",
                default_port=3001,
                ui_url="http://localhost:3001",
                default_folders={"workflows": "shuffle/workflows"}
            ),
            ToolOption(
                id="suricata",
                name="Suricata (Network IDS/IPS)",
                category="security_siem",
                description="Motor de alta performance para detecção e prevenção de intrusão de rede (IDS/IPS) e monitoramento de segurança de rede (NSM).",
                icon="eye",
                badge="Network IDS/IPS",
                default_folders={"rules": "suricata/rules", "config": "suricata/suricata.yaml"}
            ),
            ToolOption(
                id="zeek",
                name="Zeek Network Monitor",
                category="security_siem",
                description="Framework de monitoramento de segurança de rede e análise profunda de protocolos com geração de logs estruturados de conexões e DNS.",
                icon="activity",
                badge="Network Analysis",
                default_folders={"scripts": "zeek/scripts", "logs": "zeek/logs"}
            ),
            ToolOption(
                id="openvas",
                name="OpenVAS / Greenbone",
                category="security_siem",
                description="Scanner abrangente de vulnerabilidades em redes, servidores e aplicações com gerenciamento de postura de segurança.",
                icon="alert-triangle",
                badge="Vuln Scanner",
                default_port=9392,
                ui_url="https://localhost:9392",
                default_folders={"scans": "openvas/scans"}
            ),
            ToolOption(
                id="nmap",
                name="Nmap Security Scanner Sandbox",
                category="security_siem",
                description="Container isolado com Nmap, Ncat e scripts NSE para descoberta de hosts, auditoria de portas e mapeamento de superfície de ataque.",
                icon="terminal",
                badge="Network Audit",
                default_folders={"scans": "nmap/scans", "scripts": "nmap/scripts"}
            ),
            ToolOption(
                id="metasploit",
                name="Metasploit MSF Console Sandbox",
                category="security_siem",
                description="Ambiente controlado com Metasploit Framework para verificação de vulnerabilidades, auditoria de segurança e testes de intrusão defensivos.",
                icon="terminal",
                badge="Security Audit",
                default_folders={"workspace": "metasploit/workspace", "modules": "metasploit/modules"}
            )
        ]
    ),
    ToolCategory(
        id="devsecops",
        name="🔒 DevSecOps, AppSec & Gestão de Vulnerabilidades",
        icon="lock",
        description="Análise estática (SAST), dinâmica (DAST), escaneamento de containers, vazamento de segredos e acesso Zero Trust.",
        tools=[
            ToolOption(
                id="sonarqube",
                name="SonarQube (SAST & Clean Code)",
                category="devsecops",
                description="Inspeção contínua de qualidade de código e segurança (SAST) para detecção de vulnerabilidades, bugs e security hotspots.",
                icon="check-circle",
                badge="SAST / Code Quality",
                default_port=9003,
                ui_url="http://localhost:9003",
                default_folders={"conf": "sonarqube/conf"}
            ),
            ToolOption(
                id="trivy",
                name="Trivy Server (Container & Vuln Scanner)",
                category="devsecops",
                description="Scanner de vulnerabilidades para imagens de container, sistemas de arquivos, repositórios Git e configurações Kubernetes.",
                icon="shield-check",
                badge="Container Scanner",
                default_port=4954,
                ui_url="http://localhost:4954",
                default_folders={"reports": "trivy/reports"}
            ),
            ToolOption(
                id="defectdojo",
                name="OWASP DefectDojo",
                category="devsecops",
                description="Plataforma de orquestração de testes de segurança e agregação/triagem de vulnerabilidades (conecta Trivy, SonarQube, ZAP).",
                icon="layers",
                badge="Vulnerability Mgmt",
                default_port=8096,
                ui_url="http://localhost:8096",
                env_vars={"DEFECT_DOJO_ADMIN_USER": "admin", "DEFECT_DOJO_ADMIN_PASSWORD": "adminpassword123"},
                default_folders={"imports": "defectdojo/imports"}
            ),
            ToolOption(
                id="zap",
                name="OWASP ZAP (DAST Scanner)",
                category="devsecops",
                description="Scanner dinâmico de segurança de aplicações web (DAST) automatizado via API e interface web interativa.",
                icon="crosshair",
                badge="DAST Scanner",
                default_port=8097,
                ui_url="http://localhost:8097",
                default_folders={"scans": "zap/scans", "scripts": "zap/scripts"}
            ),
            ToolOption(
                id="gitleaks",
                name="Gitleaks (Secret Detection)",
                category="devsecops",
                description="Scanner estático para detecção de segredos vazados, chaves de API, senhas e tokens em repositórios Git.",
                icon="eye-off",
                badge="Secret Scanner",
                default_folders={"rules": "gitleaks/rules", "reports": "gitleaks/reports"}
            ),
            ToolOption(
                id="trufflehog",
                name="Trufflehog (High-Entropy Secrets)",
                category="devsecops",
                description="Detector profundo de segredos com verificação de credenciais em histórico git, arquivos e branches.",
                icon="search",
                badge="Secret Detection",
                default_folders={"reports": "trufflehog/reports"}
            ),
            ToolOption(
                id="teleport",
                name="Teleport Access Proxy (Zero Trust PAM)",
                category="devsecops",
                description="Proxy de acesso seguro e unificado para SSH, clusters Kubernetes, bancos de dados e aplicações web com Zero Trust.",
                icon="shield",
                badge="Zero Trust PAM",
                default_port=3080,
                ui_url="https://localhost:3080",
                default_folders={"config": "teleport/config"}
            ),
            ToolOption(
                id="authentik",
                name="Authentik (Identity & SSO)",
                category="devsecops",
                description="Servidor de autenticação e identidade open-source com suporte a SAML, OAuth2, Proxy de autenticação e fluxos flexíveis.",
                icon="user-check",
                badge="Identity / SSO",
                default_port=9006,
                ui_url="http://localhost:9006",
                env_vars={"AUTHENTIK_SECRET_KEY": "authentiksecretkey123"},
                default_folders={"custom_templates": "authentik/custom_templates"}
            )
        ]
    ),
    ToolCategory(
        id="mlops",
        name="MLOps & Inteligência Artificial",
        icon="cpu",
        description="Rastreamento de experimentos, inferência de LLMs locais, bancos vetoriais, feature stores e monitoramento de modelos.",
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
                id="ollama",
                name="Ollama Local LLM Engine",
                category="mlops",
                description="Servidor de inferência local ultra-rápido para execução de LLMs open-source (Llama 3.1/3.2, Mistral, Qwen 2.5, DeepSeek, Phi-3, Gemma) com suporte a CPU e GPU.",
                icon="cpu",
                badge="Local LLM Engine",
                default_port=11434,
                ui_url="http://localhost:11434",
                default_folders={"models": "ollama/models"}
            ),
            ToolOption(
                id="open_webui",
                name="Open WebUI (ChatGPT Clone)",
                category="mlops",
                description="Interface web moderna estilo ChatGPT/Claude para chat interativo com LLMs locais, upload de documentos RAG e gerenciamento de prompts.",
                icon="message-square",
                badge="Web AI Interface",
                default_port=3000,
                ui_url="http://localhost:3000",
                dependencies=["ollama"],
                env_vars={"OLLAMA_BASE_URL": "http://ollama:11434"}
            ),
            ToolOption(
                id="localai",
                name="LocalAI OpenAI-Compatible",
                category="mlops",
                description="Drop-in replacement da API OpenAI para geração de texto, embeddings, áudio e visão computacional localmente sem dependências em nuvem.",
                icon="zap",
                badge="OpenAI Drop-In",
                default_port=8091,
                ui_url="http://localhost:8091"
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
                id="milvus",
                name="Milvus Vector DB + Attu",
                category="mlops",
                description="Banco vetorial de altíssima escala para bilhões de vetores com interface visual Attu para gerenciamento de coleções e índices.",
                icon="database",
                badge="High-Scale Vector",
                default_port=8008,
                ui_url="http://localhost:8008",
                default_folders={"data": "milvus/data"}
            ),
            ToolOption(
                id="weaviate",
                name="Weaviate Vector Search",
                category="mlops",
                description="Banco vetorial nativo de nuvem com suporte a buscas híbridas (BM25 + vetorial) e integração direta com modelos de embedding.",
                icon="layers",
                badge="Vector Search",
                default_port=8079,
                ui_url="http://localhost:8079/v1/meta",
                default_folders={"data": "weaviate/data"}
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
                id="evidently",
                name="Evidently AI (Model & Data Drift)",
                category="mlops",
                description="Painel de monitoramento de drift de dados, qualidade de dados e degradação de performance de modelos de Machine Learning em produção.",
                icon="activity",
                badge="Model Monitoring",
                default_port=8009,
                ui_url="http://localhost:8009",
                default_folders={"reports": "evidently/reports", "workspace": "evidently/workspace"}
            ),
            ToolOption(
                id="dvc",
                name="DVC (Data Version Control)",
                category="mlops",
                description="Versionamento de dados, pipelines de treinamento e artefatos acoplado ao Git e buckets S3/MinIO.",
                icon="git-branch",
                badge="Data Versioning",
                default_folders={"data": "dvc/data"}
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
        name="Orquestração de Pipelines",
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
        id="os_sandboxes",
        name="💻 Sistemas Operacionais & Sandboxes",
        icon="terminal",
        description="Ambientes Linux puros e isolados para compilação, testes de rede, scripts shell e experimentação interativa com terminal web.",
        tools=[
            ToolOption(
                id="ubuntu_sandbox",
                name="Ubuntu 24.04 LTS Sandbox",
                category="os_sandboxes",
                description="Ambiente Ubuntu limpo e completo com bash, terminal interativo e volume montado para desenvolvimento e testes de scripts.",
                icon="terminal",
                badge="Linux OS",
                default_folders={"workspace": "workspace"}
            ),
            ToolOption(
                id="debian_sandbox",
                name="Debian 12 Bookworm Sandbox",
                category="os_sandboxes",
                description="Sistema Debian estável e confiável para criação de pacotes, testes de compatibilidade e scripts de infraestrutura.",
                icon="terminal",
                badge="Linux OS",
                default_folders={"workspace": "workspace"}
            ),
            ToolOption(
                id="alpine_sandbox",
                name="Alpine Linux Sandbox (5MB)",
                category="os_sandboxes",
                description="Sistema Alpine ultra-leve baseado em musl libc e BusyBox para testes rápidos de conectividade, rede e prototipação.",
                icon="terminal",
                badge="Lightweight OS",
                default_folders={"workspace": "workspace"}
            ),
            ToolOption(
                id="arch_sandbox",
                name="Arch Linux Rolling Sandbox",
                category="os_sandboxes",
                description="Distribuição rolling-release com o gerenciador de pacotes pacman para testes com as versões mais recentes de compiladores e bibliotecas.",
                icon="terminal",
                badge="Rolling Linux",
                default_folders={"workspace": "workspace"}
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
        description="Stack analítica com PostgreSQL, ClickHouse, MinIO, Iceberg, Trino, dbt, Superset, Airflow e Grafana.",
        icon="bar-chart-2",
        tools=["postgres", "clickhouse", "minio", "iceberg_rest", "trino", "dbt", "superset", "airflow", "grafana"]
    ),
    ProjectPreset(
        id="realtime_streaming_analytics",
        name="⚡ Real-Time Streaming & OLAP Engine",
        description="Stack de alta velocidade para processamento de streams em tempo real com Apache Flink, Redpanda, Doris, ClickHouse, Superset e MinIO.",
        icon="zap",
        tools=["flink", "redpanda", "doris", "clickhouse", "superset", "minio"]
    ),
    ProjectPreset(
        id="siem_soc_defense",
        name="🛡️ SIEM, SOC & Incident Response Lab",
        description="Ambiente de Security Operations Center com Wazuh SIEM/XDR, TheHive, Cortex, Shuffle SOAR, Suricata IDS, MISP Threat Intel e Grafana.",
        icon="shield",
        tools=["wazuh", "suricata", "thehive", "shuffle", "misp", "grafana", "postgres"]
    ),
    ProjectPreset(
        id="devsecops_appsec_pipeline",
        name="🔒 DevSecOps & AppSec Automated Pipeline",
        description="Pipeline de segurança contínua com SonarQube SAST, Trivy Container Scanner, OWASP DefectDojo, OWASP ZAP DAST, HashiCorp Vault e Gitleaks.",
        icon="lock",
        tools=["sonarqube", "trivy", "defectdojo", "zap", "vault", "gitleaks", "vscode"]
    ),
    ProjectPreset(
        id="network_security_audit",
        name="🕵️ Network Security & Vulnerability Auditing",
        description="Laboratório de análise e segurança de redes com Zeek Network Monitor, Suricata IDS, OpenVAS, Nmap Sandbox e Metasploit Framework.",
        icon="eye",
        tools=["zeek", "suricata", "openvas", "nmap", "metasploit", "vscode"]
    ),
    ProjectPreset(
        id="cloud_native_gitops_observability",
        name="☁️ Cloud-Native GitOps & Full Observability",
        description="Arquitetura nativa de nuvem com ArgoCD GitOps, Traefik Edge Router, Grafana Loki, Prometheus, Jaeger Tracing e Grafana Dashboards.",
        icon="cloud",
        tools=["argocd", "traefik", "loki", "prometheus", "jaeger", "grafana"]
    ),
    ProjectPreset(
        id="advanced_rag_vector_mlops",
        name="🧠 Advanced RAG, Vector Search & LLM Studio",
        description="Ambiente de IA Generativa corporativo com Milvus, Weaviate, Qdrant, Ollama, Open WebUI, Evidently AI, MLflow e JupyterLab.",
        icon="cpu",
        tools=["milvus", "weaviate", "qdrant", "ollama", "open_webui", "evidently", "mlflow", "jupyterlab", "minio"]
    ),
    ProjectPreset(
        id="workflow_automation_integration",
        name="🔄 Workflow Automation & API Orchestration",
        description="Plataforma de orquestração de microsserviços e integração low-code com Temporal, n8n, RabbitMQ, Redis e PostgreSQL.",
        icon="repeat",
        tools=["temporal", "n8n", "rabbitmq", "redis", "postgres"]
    ),
    ProjectPreset(
        id="hadoop_big_data_ecosystem",
        name="🐘 Hadoop & Big Data Ecosystem",
        description="Stack clássica e robusta de Big Data com HDFS NameNode/DataNode, YARN ResourceManager, Hive Metastore, Spark 3.5, Zeppelin Notebook, Ranger e PostgreSQL.",
        icon="server",
        tools=["hdfs", "yarn", "hive", "spark", "zeppelin", "ranger", "postgres", "minio"]
    ),
    ProjectPreset(
        id="local_llm_ai_stack",
        name="🧠 Local LLMs & GenAI Studio",
        description="Ambiente completo de Inteligência Artificial Generativa Local com Ollama (Llama/Mistral/Qwen), Open WebUI, Qdrant Vector DB, JupyterLab e PostgreSQL.",
        icon="cpu",
        tools=["ollama", "open_webui", "qdrant", "jupyterlab", "postgres", "minio"]
    ),
    ProjectPreset(
        id="linux_os_sandbox",
        name="🐧 Multi-Distro Linux Sandboxes & DevOps Lab",
        description="Ambiente de desenvolvimento e experimentação com contêineres de Ubuntu 24.04, Debian 12, Alpine Linux e Arch Linux com VS Code Web e Portainer.",
        icon="terminal",
        tools=["ubuntu_sandbox", "debian_sandbox", "alpine_sandbox", "arch_sandbox", "vscode", "portainer"]
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
