"""
Architecture Topology and Dependency Graph Engine
Maps relationships, data flows, and architectural dependencies between all tools in StackStudio.
"""

from typing import List, Dict, Any, Set, Optional
from studio.services.catalog import get_tool_by_id


# Predefined architectural relationships & data flows (source -> target -> label/type)
RELATIONSHIPS = [
    # CDC & Streaming Data Flows
    {"source": "postgres", "target": "kafka_connect", "label": "Logical WAL Replication (CDC)", "type": "cdc"},
    {"source": "mysql", "target": "kafka_connect", "label": "Binlog Streaming (CDC)", "type": "cdc"},
    {"source": "kafka_connect", "target": "kafka", "label": "Publishes CDC Events", "type": "streaming"},
    {"source": "kafka", "target": "schema_registry", "label": "Avro/JSON Schema Validation", "type": "governance"},
    {"source": "kafka_ui", "target": "kafka", "label": "Cluster Monitoring & Inspection", "type": "management"},
    {"source": "kafka_ui", "target": "schema_registry", "label": "Schema Browsing", "type": "management"},
    {"source": "kafka_ui", "target": "kafka_connect", "label": "Connector Lifecycle", "type": "management"},
    
    # Redpanda & Pulsar Streaming
    {"source": "redpanda", "target": "flink", "label": "Sub-ms Stream Processing", "type": "streaming"},
    {"source": "pulsar", "target": "flink", "label": "Pub/Sub Stream Ingestion", "type": "streaming"},
    {"source": "redpanda", "target": "spark", "label": "Kafka-compatible Structured Streaming", "type": "streaming"},

    # Storage, Lakehouse & Processing
    {"source": "kafka", "target": "spark", "label": "Structured Streaming (Bronze Ingestion)", "type": "streaming"},
    {"source": "kafka", "target": "flink", "label": "Continuous Stream Processing (Flink SQL)", "type": "streaming"},
    {"source": "flink", "target": "iceberg_rest", "label": "Streaming Sink (Silver Upserts)", "type": "storage"},
    {"source": "flink", "target": "doris", "label": "High-Throughput Stream Load", "type": "storage"},
    {"source": "flink", "target": "starrocks", "label": "Real-Time Sub-Second Stream Sink", "type": "storage"},
    {"source": "flink", "target": "clickhouse", "label": "Real-Time Aggregates Sink", "type": "storage"},
    {"source": "spark", "target": "iceberg_rest", "label": "ACID Table Commits (Silver Upserts)", "type": "storage"},
    {"source": "spark", "target": "minio", "label": "Parquet Data Files Storage", "type": "storage"},
    {"source": "iceberg_rest", "target": "minio", "label": "Metadata Storage (s3://lakehouse)", "type": "storage"},
    {"source": "trino", "target": "iceberg_rest", "label": "Distributed SQL Catalog Queries", "type": "query"},
    {"source": "trino", "target": "minio", "label": "S3 Data Reads & Filter Pushdown", "type": "query"},
    {"source": "doris", "target": "minio", "label": "Cold Storage Tiering / S3 Load", "type": "storage"},
    {"source": "starrocks", "target": "minio", "label": "Iceberg / Delta Lake External Queries", "type": "storage"},
    {"source": "dbt", "target": "trino", "label": "SQL Models & Gold Transformations", "type": "transformation"},
    {"source": "dbt", "target": "clickhouse", "label": "OLAP Data Mart Materializations", "type": "transformation"},
    {"source": "dbt", "target": "doris", "label": "Real-Time Analytics Models", "type": "transformation"},
    {"source": "dbt", "target": "postgres", "label": "Transactional Table Models", "type": "transformation"},
    
    # BI, Data Quality & Governança
    {"source": "superset", "target": "trino", "label": "Interactive SQL & Charts", "type": "analytics"},
    {"source": "superset", "target": "clickhouse", "label": "High-Speed OLAP Dashboards", "type": "analytics"},
    {"source": "superset", "target": "doris", "label": "Real-Time BI Dashboards", "type": "analytics"},
    {"source": "superset", "target": "postgres", "label": "Relational Data Analytics", "type": "analytics"},
    {"source": "metabase", "target": "postgres", "label": "Visual Business Analytics", "type": "analytics"},
    {"source": "metabase", "target": "trino", "label": "Cross-Database Queries", "type": "analytics"},
    {"source": "great_expectations", "target": "spark", "label": "Validates Batch Dataframes", "type": "governance"},
    {"source": "great_expectations", "target": "postgres", "label": "Asserts Table Constraints & Rules", "type": "governance"},
    {"source": "soda_core", "target": "clickhouse", "label": "Executes Data Contract Checks", "type": "governance"},
    {"source": "soda_core", "target": "postgres", "label": "Runs Data Quality Tests", "type": "governance"},
    {"source": "datahub", "target": "postgres", "label": "Metadata Backend DB", "type": "governance"},
    {"source": "datahub", "target": "kafka", "label": "Lineage & Schema Event Ingestion", "type": "governance"},
    {"source": "datahub", "target": "trino", "label": "Extracts Query Audit Logs", "type": "governance"},
    {"source": "ranger", "target": "hdfs", "label": "Fine-Grained HDFS ACLs", "type": "security"},
    {"source": "ranger", "target": "hive", "label": "Column & Row Level Security Policies", "type": "security"},
    {"source": "ranger", "target": "trino", "label": "Authorizes SQL Queries", "type": "security"},
    {"source": "ranger", "target": "kafka", "label": "Topic Authorization Policies", "type": "security"},

    # Orchestration & Workflow Automation
    {"source": "airflow", "target": "spark", "label": "Triggers Batch & Spark Jobs", "type": "orchestration"},
    {"source": "airflow", "target": "trino", "label": "Runs Gold Mart Aggregations", "type": "orchestration"},
    {"source": "airflow", "target": "dbt", "label": "Orchestrates dbt Run & Tests", "type": "orchestration"},
    {"source": "airflow", "target": "postgres", "label": "Metadata DB & Task State", "type": "metadata"},
    {"source": "temporal", "target": "postgres", "label": "Durable Workflow State DB", "type": "orchestration"},
    {"source": "n8n", "target": "postgres", "label": "Stores Flows & Credentials", "type": "orchestration"},
    {"source": "n8n", "target": "rabbitmq", "label": "Pub/Sub Workflow Triggers", "type": "orchestration"},
    {"source": "openmetadata", "target": "postgres", "label": "Metadata Storage & Ingestion", "type": "governance"},
    {"source": "openmetadata", "target": "trino", "label": "Extracts Query Lineage & DDLs", "type": "governance"},
    {"source": "openmetadata", "target": "kafka", "label": "Ingests Topic Catalog", "type": "governance"},

    # MLOps, Vector Search & AI
    {"source": "mlflow", "target": "minio", "label": "Model Artifacts & Weights (S3)", "type": "mlops"},
    {"source": "mlflow", "target": "postgres", "label": "Experiment Runs & Metrics DB", "type": "mlops"},
    {"source": "jupyterlab", "target": "spark", "label": "PySpark Master Remote Session", "type": "interactive"},
    {"source": "jupyterlab", "target": "mlflow", "label": "Logs Hyperparameters & Models", "type": "mlops"},
    {"source": "jupyterlab", "target": "qdrant", "label": "Generates & Queries Embeddings", "type": "vector"},
    {"source": "jupyterlab", "target": "milvus", "label": "Massive Vector Similarity Search", "type": "vector"},
    {"source": "jupyterlab", "target": "weaviate", "label": "Hybrid Semantic Search Queries", "type": "vector"},
    {"source": "jupyterlab", "target": "evidently", "label": "Calculates Drift & Quality Metrics", "type": "mlops"},
    {"source": "jupyterlab", "target": "dvc", "label": "Versions Datasets & Pipelines", "type": "mlops"},
    {"source": "jupyterlab", "target": "ollama", "label": "LangChain / LlamaIndex Calls", "type": "interactive"},
    {"source": "jupyterlab", "target": "localai", "label": "OpenAI API Client Calls", "type": "interactive"},
    {"source": "open_webui", "target": "ollama", "label": "Streams Local LLM Inferences", "type": "ai"},
    {"source": "open_webui", "target": "qdrant", "label": "Semantic RAG Search", "type": "vector"},
    {"source": "open_webui", "target": "milvus", "label": "Enterprise RAG Vector Lookups", "type": "vector"},
    {"source": "open_webui", "target": "weaviate", "label": "Multi-Modal Embeddings Search", "type": "vector"},

    # Backend, Proxy, Secrets & IAM
    {"source": "traefik", "target": "docker", "label": "Dynamic Service Discovery", "type": "proxy"},
    {"source": "traefik", "target": "authentik", "label": "Forward Auth Middleware", "type": "security"},
    {"source": "nginx", "target": "apigateway", "label": "Edge TLS Termination & Load Balancing", "type": "proxy"},
    {"source": "nginx", "target": "hasura", "label": "Proxies GraphQL Requests", "type": "proxy"},
    {"source": "apigateway", "target": "hasura", "label": "Rate-Limiting & JWT Auth Proxy", "type": "gateway"},
    {"source": "apigateway", "target": "keycloak", "label": "OAuth2 Token Validation", "type": "security"},
    {"source": "vault", "target": "keycloak", "label": "Manages Encryption Keys & Secrets", "type": "security"},
    {"source": "vault", "target": "authentik", "label": "Stores PKI & Signing Certs", "type": "security"},
    {"source": "hasura", "target": "postgres", "label": "Instant GraphQL & Real-Time Subscriptions", "type": "database"},
    {"source": "hasura", "target": "keycloak", "label": "Validates Claims & Role Permissions", "type": "security"},
    {"source": "keycloak", "target": "postgres", "label": "User Identities & Realm DB", "type": "security"},
    {"source": "authentik", "target": "postgres", "label": "User Directory & SAML/OIDC State", "type": "security"},
    {"source": "teleport", "target": "postgres", "label": "Zero-Trust Database Access Proxy", "type": "security"},
    {"source": "teleport", "target": "ubuntu_sandbox", "label": "Zero-Trust SSH Bastion Session", "type": "security"},
    {"source": "redis_commander", "target": "redis", "label": "Key-Value Inspection Web UI", "type": "management"},
    {"source": "pgadmin", "target": "postgres", "label": "Database Admin & SQL GUI", "type": "management"},

    # Telemetry, Observability & GitOps
    {"source": "opentelemetry", "target": "prometheus", "label": "Exports Aggregated Metrics", "type": "telemetry"},
    {"source": "opentelemetry", "target": "jaeger", "label": "Exports OTLP Traces (gRPC/HTTP)", "type": "telemetry"},
    {"source": "opentelemetry", "target": "loki", "label": "Exports Structured Logs", "type": "telemetry"},
    {"source": "loki", "target": "grafana", "label": "Log Exploration Datasource", "type": "observability"},
    {"source": "jaeger", "target": "grafana", "label": "Distributed Tracing Datasource", "type": "observability"},
    {"source": "prometheus", "target": "grafana", "label": "Metrics Datasource for Dashboards", "type": "observability"},
    {"source": "clickhouse", "target": "grafana", "label": "High-Speed Log Analytics Datasource", "type": "observability"},
    {"source": "postgres", "target": "grafana", "label": "Relational Business Metrics Datasource", "type": "observability"},
    {"source": "portainer", "target": "docker", "label": "Container Socket Management", "type": "devops"},
    {"source": "argocd", "target": "vscode", "label": "GitOps Sync with Git Repos", "type": "devops"},

    # SIEM, SOC, Network Security & Incident Response
    {"source": "suricata", "target": "wazuh", "label": "Streams Eve.json EDR/NSM Alerts", "type": "security"},
    {"source": "suricata", "target": "splunk", "label": "Network Intrusion Events Stream", "type": "security"},
    {"source": "suricata", "target": "elastic_security", "label": "ECS Network Threat Events", "type": "security"},
    {"source": "zeek", "target": "splunk", "label": "DNS, HTTP & SSL Connection Logs", "type": "security"},
    {"source": "zeek", "target": "elastic_security", "label": "Network Protocol Metadata Logs", "type": "security"},
    {"source": "zeek", "target": "wazuh", "label": "Correlation of Network Activity", "type": "security"},
    {"source": "wazuh", "target": "thehive", "label": "Auto-creates Security Incident Cases", "type": "security"},
    {"source": "wazuh", "target": "shuffle", "label": "Triggers SOAR Containment Playbooks", "type": "security"},
    {"source": "thehive", "target": "misp", "label": "Shares & Enriches IOCs", "type": "security"},
    {"source": "shuffle", "target": "thehive", "label": "Updates Case Status & Observables", "type": "security"},
    {"source": "shuffle", "target": "wazuh", "label": "Executes Active Response (Block IP)", "type": "security"},
    {"source": "openvas", "target": "thehive", "label": "Vulnerability Scan Findings Alert", "type": "security"},
    {"source": "nmap", "target": "openvas", "label": "Host Discovery & Port Feeds", "type": "security"},
    {"source": "metasploit", "target": "nmap", "label": "Imports Subnet Scan XML Targets", "type": "security"},

    # DevSecOps, AppSec & Vulnerability Management
    {"source": "sonarqube", "target": "defectdojo", "label": "Imports SAST Vulnerability Reports", "type": "security"},
    {"source": "trivy", "target": "defectdojo", "label": "Imports Container & CVE Scans", "type": "security"},
    {"source": "zap", "target": "defectdojo", "label": "Imports DAST Security Test Results", "type": "security"},
    {"source": "gitleaks", "target": "defectdojo", "label": "Pushes Detected Git Secret Leaks", "type": "security"},
    {"source": "trufflehog", "target": "defectdojo", "label": "Reports Verified Leaked Credentials", "type": "security"},
    {"source": "defectdojo", "target": "thehive", "label": "Escalates Critical Vulnerability Cases", "type": "security"},

    # Sandboxes, IaC & IDE
    {"source": "ansible", "target": "postgres", "label": "Automates Host & DDL Configuration", "type": "iac"},
    {"source": "terraform", "target": "minio", "label": "Provisions Buckets & S3 Policies", "type": "iac"},
    {"source": "vscode", "target": "spark", "label": "Develops & Edits PySpark Jobs", "type": "ide"},
    {"source": "vscode", "target": "flink", "label": "Develops PyFlink & Java Stream Jobs", "type": "ide"},
    {"source": "vscode", "target": "airflow", "label": "Authors Python DAG Pipelines", "type": "ide"},
    {"source": "vscode", "target": "dbt", "label": "Authors SQL Models & Macros", "type": "ide"},
    {"source": "vscode", "target": "postgres", "label": "Direct Database SQL Editing", "type": "ide"},
    {"source": "vscode", "target": "ansible", "label": "Authors Playbooks & Tasks", "type": "ide"},
    {"source": "vscode", "target": "terraform", "label": "Authors HCL Modules & Plans", "type": "ide"},
    {"source": "vscode", "target": "ubuntu_sandbox", "label": "Workspace Shell Access", "type": "ide"},
    {"source": "vscode", "target": "debian_sandbox", "label": "Workspace Shell Access", "type": "ide"},
    {"source": "vscode", "target": "alpine_sandbox", "label": "Workspace Shell Access", "type": "ide"},
    {"source": "vscode", "target": "arch_sandbox", "label": "Workspace Shell Access", "type": "ide"},
    {"source": "vscode", "target": "sonarqube", "label": "IDE Clean Code / SonarLint Sync", "type": "ide"},

    # Hadoop & Big Data Ecosystem
    {"source": "yarn", "target": "hdfs", "label": "Allocates Distributed Storage", "type": "storage"},
    {"source": "hive", "target": "hdfs", "label": "Warehouse Directory Storage", "type": "storage"},
    {"source": "hive", "target": "postgres", "label": "Metastore Relational DB (HMS)", "type": "metadata"},
    {"source": "spark", "target": "hdfs", "label": "Reads/Writes HDFS Blocks", "type": "storage"},
    {"source": "spark", "target": "hive", "label": "Hive Catalog & Schema Sharing", "type": "query"},
    {"source": "spark", "target": "yarn", "label": "Cluster Resource Allocation", "type": "orchestration"},
    {"source": "zeppelin", "target": "spark", "label": "Interactive Spark Session", "type": "interactive"},
    {"source": "zeppelin", "target": "hive", "label": "JDBC SQL Queries (HiveServer2)", "type": "query"},
    {"source": "zeppelin", "target": "hdfs", "label": "Direct File Exploration", "type": "interactive"},
]

# Category colors for UI styling
CATEGORY_COLORS = {
    "data_engineering": {"bg": "#0284c7", "border": "#38bdf8", "text": "#e0f2fe", "label": "Engenharia de Dados"},
    "mlops": {"bg": "#7c3aed", "border": "#a78bfa", "text": "#ede9fe", "label": "MLOps & IA"},
    "backend": {"bg": "#059669", "border": "#34d399", "text": "#ecfdf5", "label": "Backend & Mensageria"},
    "devops": {"bg": "#d97706", "border": "#fbbf24", "text": "#fffbeb", "label": "DevOps & IaC"},
    "security_siem": {"bg": "#dc2626", "border": "#ef4444", "text": "#fef2f2", "label": "SIEM, SOC & Segurança"},
    "devsecops": {"bg": "#b91c1c", "border": "#f87171", "text": "#fff1f2", "label": "DevSecOps & AppSec"},
    "orchestration": {"bg": "#4f46e5", "border": "#818cf8", "text": "#eef2ff", "label": "Orquestração"},
    "os_sandboxes": {"bg": "#334155", "border": "#64748b", "text": "#f1f5f9", "label": "Sistemas Operacionais"},
    "plugins": {"bg": "#0891b2", "border": "#22d3ee", "text": "#cffafe", "label": "Custom & Plugins"}
}


class TopologyGraphEngine:
    @staticmethod
    def build_graph(tool_ids: List[str], containers_info: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Builds nodes and filtered edges for the selected list of tools, enriched with real-time health data."""
        tools_set: Set[str] = set(tool_ids)
        
        # Add internal services if present in catalog (like redis_commander if redis is selected)
        if "redis" in tools_set:
            tools_set.add("redis_commander")

        # Map containers by normalized service name
        containers_map: Dict[str, Dict[str, Any]] = {}
        if containers_info:
            for c in containers_info:
                c_dict = c if isinstance(c, dict) else (c.dict() if hasattr(c, "dict") else c.__dict__)
                svc = str(c_dict.get("service", "")).lower()
                cname = str(c_dict.get("name", "")).lower()
                containers_map[svc] = c_dict
                containers_map[cname] = c_dict

        nodes = []
        node_status_map = {}

        for tid in sorted(tools_set):
            # Match live container data
            c_data = containers_map.get(tid)
            if not c_data:
                # Fuzzy match (e.g. spark -> spark-master, postgres -> project-postgres)
                for k, v in containers_map.items():
                    if tid in k or k in tid:
                        c_data = v
                        break

            if c_data:
                v_status = c_data.get("visual_status", "orange")
                state = c_data.get("state", "stopped")
                status_text = c_data.get("status", "Stopped")
                health = c_data.get("health")
                retry_count = c_data.get("retry_count", 0)
            else:
                v_status = "orange"
                state = "stopped"
                status_text = "Stopped"
                health = None
                retry_count = 0

            node_status_map[tid] = v_status

            try:
                tool_def = get_tool_by_id(tid)
                label = tool_def.name
                cat_id = tool_def.category
                icon = tool_def.icon
                badge = tool_def.badge or "Service"
                ui_url = tool_def.ui_url
                port = tool_def.default_port
            except Exception:
                label = tid.replace("_", " ").title()
                cat_id = "backend"
                icon = "box"
                badge = "Service"
                ui_url = None
                port = None

            colors = CATEGORY_COLORS.get(cat_id, CATEGORY_COLORS["backend"])

            nodes.append({
                "id": tid,
                "label": label,
                "category": cat_id,
                "category_label": colors["label"],
                "icon": icon,
                "badge": badge,
                "ui_url": ui_url,
                "port": port,
                "visual_status": v_status,
                "state": state,
                "status_text": status_text,
                "health": health,
                "retry_count": retry_count,
                "style": {
                    "bg": colors["bg"],
                    "border": colors["border"],
                    "text": colors["text"]
                }
            })

        # Filter edges where both source and target exist in the selected tools
        edges = []
        for rel in RELATIONSHIPS:
            src = rel["source"]
            tgt = rel["target"]
            if src in tools_set and tgt in tools_set:
                src_status = node_status_map.get(src, "orange")
                tgt_status = node_status_map.get(tgt, "orange")
                
                # Active if both source and target are running (green)
                is_active = (src_status == "green" and tgt_status == "green")
                
                edge_color = "#10b981" if is_active else ("#ef4444" if src_status == "red" or tgt_status == "red" else "#64748b")
                
                edges.append({
                    "source": src,
                    "target": tgt,
                    "label": rel["label"],
                    "type": rel["type"],
                    "active": is_active,
                    "color": edge_color
                })

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges
        }
