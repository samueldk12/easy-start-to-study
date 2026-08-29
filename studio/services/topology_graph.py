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
    {"source": "vscode", "target": "spark", "label": "Develops & Edits PySpark Jobs", "type": "ide"},
    {"source": "vscode", "target": "airflow", "label": "Authors Python DAG Pipelines", "type": "ide"},
    {"source": "vscode", "target": "dbt", "label": "Authors SQL Models & Macros", "type": "ide"},
    {"source": "vscode", "target": "postgres", "label": "Direct Database SQL Editing", "type": "ide"},
    {"source": "vscode", "target": "ansible", "label": "Authors Playbooks & Tasks", "type": "ide"},
    {"source": "vscode", "target": "terraform", "label": "Authors HCL Modules & Plans", "type": "ide"},
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
                status_text = "Parado"
                health = None
                retry_count = 0

            node_status_map[tid] = v_status

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
                    "color": cat_info,
                    "visual_status": v_status,
                    "state": state,
                    "status_text": status_text,
                    "health": health,
                    "retry_count": retry_count
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
                    "color": CATEGORY_COLORS["devops"],
                    "visual_status": v_status,
                    "state": state,
                    "status_text": status_text,
                    "health": health,
                    "retry_count": retry_count
                })

        edges = []
        for rel in RELATIONSHIPS:
            if rel["source"] in tools_set and rel["target"] in tools_set:
                src_status = node_status_map.get(rel["source"], "orange")
                tgt_status = node_status_map.get(rel["target"], "orange")

                if src_status == "green" and tgt_status == "green":
                    edge_status = "active"  # Fluxo operando
                elif src_status == "red" or tgt_status == "red":
                    edge_status = "broken"  # Fluxo quebrado / com erro
                elif src_status == "yellow" or tgt_status == "yellow":
                    edge_status = "starting"  # Aguardando serviços inicializarem
                else:
                    edge_status = "inactive"  # Parado

                edges.append({
                    "source": rel["source"],
                    "target": rel["target"],
                    "label": rel["label"],
                    "type": rel["type"],
                    "status": edge_status
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    @staticmethod
    def generate_mermaid(tool_ids: List[str], containers_info: Optional[List[Any]] = None) -> str:
        """Generates a Mermaid.js flowchart markdown string for the project topology with health markers."""
        graph_data = TopologyGraphEngine.build_graph(tool_ids, containers_info)
        lines = ["flowchart TD"]
        
        status_emojis = {
            "green": "🟢",
            "yellow": "🟡",
            "orange": "🟠",
            "red": "🔴"
        }

        # Nodes
        for n in graph_data["nodes"]:
            emoji = status_emojis.get(n.get("visual_status", "orange"), "⚪")
            port_str = f" : {n['port']}" if n["port"] else ""
            lines.append(f'    {n["id"]}["{emoji} {n["name"]}{port_str}"]')

        # Edges
        for e in graph_data["edges"]:
            lines.append(f'    {e["source"]} -->|"{e["label"]}"| {e["target"]}')

        return "\n".join(lines)

    @staticmethod
    def generate_ascii_graph(tool_ids: List[str], containers_info: Optional[List[Any]] = None) -> str:
        """Generates an ASCII text representation of the topology with real-time health indicators."""
        graph_data = TopologyGraphEngine.build_graph(tool_ids, containers_info)
        lines = [
            "================================================================================",
            " 🕸️ TOPOLOGIA DA ARQUITETURA & SAÚDE DOS SERVIÇOS EM TEMPO REAL",
            "================================================================================"
        ]

        status_emojis = {
            "green": "🟢 ONLINE",
            "yellow": "🟡 SUBINDO",
            "orange": "🟠 PARADO",
            "red": "🔴 ERRO/CAIU"
        }

        lines.append("NÓS E SAÚDE:")
        for n in graph_data["nodes"]:
            badge = status_emojis.get(n.get("visual_status", "orange"), "🟠 PARADO")
            port = f"Porta: {n['port']}" if n['port'] else ""
            lines.append(f"  [{badge}] {n['name']} ({n['id']}) {port} | Status: {n.get('status_text', '-')}")

        lines.append("\nFLUXO DE DADOS & CONEXÕES:")
        if not graph_data["edges"]:
            lines.append("  (Sem conexões diretas entre os serviços selecionados)")
        else:
            for e in graph_data["edges"]:
                edge_indicator = "==[ATIVO]==" if e["status"] == "active" else ("--[SUBINDO]--" if e["status"] == "starting" else ("xx[FALHA]xx" if e["status"] == "broken" else "──(PARADO)──"))
                lines.append(f"  [{e['source']}] {edge_indicator} ({e['label']}) ────► [{e['target']}]")

        lines.append("================================================================================")
        return "\n".join(lines)
