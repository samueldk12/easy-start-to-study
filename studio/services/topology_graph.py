"""
Architecture Topology and Dependency Graph Engine
Maps relationships, data flows, and architectural dependencies between all tools in StackStudio.
"""

from typing import List, Dict, Any, Set
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
    
    # Storage, Lakehouse & Processing
    {"source": "kafka", "target": "spark", "label": "Structured Streaming (Bronze Ingestion)", "type": "streaming"},
    {"source": "spark", "target": "iceberg_rest", "label": "ACID Table Commits (Silver Upserts)", "type": "storage"},
    {"source": "spark", "target": "minio", "label": "Parquet Data Files Storage", "type": "storage"},
    {"source": "iceberg_rest", "target": "minio", "label": "Metadata Storage (s3://lakehouse)", "type": "storage"},
    {"source": "trino", "target": "iceberg_rest", "label": "Distributed SQL Catalog Queries", "type": "query"},
    {"source": "trino", "target": "minio", "label": "S3 Data Reads & Filter Pushdown", "type": "query"},
    {"source": "dbt", "target": "trino", "label": "SQL Models & Gold Transformations", "type": "transformation"},
    {"source": "dbt", "target": "clickhouse", "label": "OLAP Data Mart Materializations", "type": "transformation"},
    {"source": "dbt", "target": "postgres", "label": "Transactional Table Models", "type": "transformation"},
    
    # Orchestration & Lineage
    {"source": "airflow", "target": "spark", "label": "Triggers Batch & Spark Jobs", "type": "orchestration"},
    {"source": "airflow", "target": "trino", "label": "Runs Gold Mart Aggregations", "type": "orchestration"},
    {"source": "airflow", "target": "dbt", "label": "Orchestrates dbt Run & Tests", "type": "orchestration"},
    {"source": "airflow", "target": "postgres", "label": "Metadata DB & Task State", "type": "metadata"},
    {"source": "openmetadata", "target": "postgres", "label": "Metadata Storage & Ingestion", "type": "governance"},
    {"source": "openmetadata", "target": "trino", "label": "Extracts Query Lineage & DDLs", "type": "governance"},
    {"source": "openmetadata", "target": "kafka", "label": "Ingests Topic Catalog", "type": "governance"},

    # MLOps & Vector Search
    {"source": "mlflow", "target": "minio", "label": "Model Artifacts & Weights (S3)", "type": "mlops"},
    {"source": "mlflow", "target": "postgres", "label": "Experiment Runs & Metrics DB", "type": "mlops"},
    {"source": "jupyterlab", "target": "spark", "label": "PySpark Master Remote Session", "type": "interactive"},
    {"source": "jupyterlab", "target": "mlflow", "label": "Logs Hyperparameters & Models", "type": "mlops"},
    {"source": "jupyterlab", "target": "qdrant", "label": "Generates & Queries Embeddings", "type": "vector"},
    {"source": "jupyterlab", "target": "postgres", "label": "Queries Training Datasets", "type": "interactive"},
    {"source": "jupyterlab", "target": "redis", "label": "Fetches Real-Time Features", "type": "mlops"},

    # Backend, Proxy & Security
    {"source": "nginx", "target": "apigateway", "label": "Edge TLS Termination & Load Balancing", "type": "proxy"},
    {"source": "nginx", "target": "hasura", "label": "Proxies GraphQL Requests", "type": "proxy"},
    {"source": "apigateway", "target": "hasura", "label": "Rate-Limiting & JWT Auth Proxy", "type": "gateway"},
    {"source": "apigateway", "target": "keycloak", "label": "OAuth2 Token Validation", "type": "security"},
    {"source": "hasura", "target": "postgres", "label": "Instant GraphQL & Real-Time Subscriptions", "type": "database"},
    {"source": "hasura", "target": "keycloak", "label": "Validates Claims & Role Permissions", "type": "security"},
    {"source": "keycloak", "target": "postgres", "label": "User Identities & Realm DB", "type": "security"},
    {"source": "redis_commander", "target": "redis", "label": "Key-Value Inspection Web UI", "type": "management"},
    {"source": "pgadmin", "target": "postgres", "label": "Database Admin & SQL GUI", "type": "management"},

    # Telemetry, Observability & Analytics
    {"source": "opentelemetry", "target": "prometheus", "label": "Exports Aggregated Metrics", "type": "telemetry"},
    {"source": "prometheus", "target": "grafana", "label": "Metrics Datasource for Dashboards", "type": "observability"},
    {"source": "clickhouse", "target": "grafana", "label": "High-Speed Log Analytics Datasource", "type": "observability"},
    {"source": "postgres", "target": "grafana", "label": "Relational Business Metrics Datasource", "type": "observability"},
    {"source": "portainer", "target": "docker", "label": "Container Socket Management", "type": "devops"},
    {"source": "ansible", "target": "postgres", "label": "Automates Host & DDL Configuration", "type": "iac"},
    {"source": "terraform", "target": "minio", "label": "Provisions Buckets & S3 Policies", "type": "iac"},
]

# Category colors for UI styling
CATEGORY_COLORS = {
    "data_engineering": {"bg": "#0284c7", "border": "#38bdf8", "text": "#e0f2fe", "label": "Engenharia de Dados"},
    "mlops": {"bg": "#7c3aed", "border": "#a78bfa", "text": "#ede9fe", "label": "MLOps & IA"},
    "backend": {"bg": "#059669", "border": "#34d399", "text": "#ecfdf5", "label": "Backend & Mensageria"},
    "devops": {"bg": "#d97706", "border": "#fbbf24", "text": "#fffbeb", "label": "DevOps & IaC"},
    "orchestration": {"bg": "#4f46e5", "border": "#818cf8", "text": "#eef2ff", "label": "Orquestração"},
    "plugins": {"bg": "#0891b2", "border": "#22d3ee", "text": "#cffafe", "label": "Plugin"}
}


class TopologyGraphEngine:
    @staticmethod
    def build_graph(tool_ids: List[str]) -> Dict[str, Any]:
        """Builds nodes and filtered edges for the selected list of tools."""
        tools_set: Set[str] = set(tool_ids)
        
        # Add internal services if present in catalog (like redis_commander if redis is selected)
        if "redis" in tools_set:
            tools_set.add("redis_commander")

        nodes = []
        for tid in sorted(tools_set):
            try:
                tool = get_tool_by_id(tid)
                cat_info = CATEGORY_COLORS.get(tool.category, CATEGORY_COLORS["devops"])
                nodes.append({
                    "id": tool.id,
                    "name": tool.name,
                    "category": tool.category,
                    "category_label": cat_info["label"],
                    "badge": tool.badge,
                    "icon": tool.icon,
                    "port": tool.default_port,
                    "ui_url": tool.ui_url,
                    "color": cat_info
                })
            except Exception:
                nodes.append({
                    "id": tid,
                    "name": tid.upper(),
                    "category": "custom",
                    "category_label": "Custom",
                    "badge": "Service",
                    "icon": "box",
                    "port": None,
                    "ui_url": None,
                    "color": CATEGORY_COLORS["devops"]
                })

        edges = []
        for rel in RELATIONSHIPS:
            if rel["source"] in tools_set and rel["target"] in tools_set:
                edges.append({
                    "source": rel["source"],
                    "target": rel["target"],
                    "label": rel["label"],
                    "type": rel["type"]
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    @staticmethod
    def generate_mermaid(tool_ids: List[str]) -> str:
        """Generates a Mermaid.js flowchart markdown string for the project topology."""
        graph_data = TopologyGraphEngine.build_graph(tool_ids)
        lines = ["flowchart TD"]
        
        # Nodes
        for n in graph_data["nodes"]:
            port_str = f" : {n['port']}" if n["port"] else ""
            lines.append(f'    {n["id"]}["{n["name"]}{port_str}"]')

        # Edges
        for e in graph_data["edges"]:
            lines.append(f'    {e["source"]} -->|"{e["label"]}"| {e["target"]}')

        return "\n".join(lines)

    @staticmethod
    def generate_ascii_graph(tool_ids: List[str]) -> str:
        """Generates an ASCII text representation of the topology for CLI output."""
        graph_data = TopologyGraphEngine.build_graph(tool_ids)
        lines = [
            "================================================================",
            " 🕸️ TOPOLOGIA DA ARQUITETURA & FLUXO DE DADOS",
            "================================================================"
        ]

        if not graph_data["edges"]:
            lines.append("Serviços ativos (sem conexões diretas entre si):")
            for n in graph_data["nodes"]:
                lines.append(f"  • [{n['name']}] (Porta: {n['port'] or '-'})")
        else:
            lines.append("Conexões e Fluxo de Dados:")
            for e in graph_data["edges"]:
                lines.append(f"  [{e['source']}] ────({e['label']})────► [{e['target']}]")

        lines.append("================================================================")
        return "\n".join(lines)
