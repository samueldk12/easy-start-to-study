import pytest
import os
import shutil
import yaml
from studio.services.catalog import get_catalog, get_tool_by_id, PRESETS
from studio.services.scaffolder import ProjectScaffolder
from studio.services.k8s_scaffolder import K8sScaffolder
from studio.services.topology_graph import TopologyGraphEngine
from studio.models import ProjectCreateRequest


@pytest.fixture
def temp_project_dir():
    test_dir = os.path.join(os.getcwd(), "tmp_test_expansion_project")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    yield test_dir
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_catalog_contains_all_new_tools():
    catalog = get_catalog()
    cat_ids = [c.id for c in catalog]
    
    assert "security_siem" in cat_ids
    assert "devsecops" in cat_ids
    assert "data_engineering" in cat_ids
    assert "backend" in cat_ids
    assert "devops" in cat_ids
    assert "mlops" in cat_ids

    # Verify Security Tools
    sec_tools = ["wazuh", "splunk", "elastic_security", "thehive", "misp", "shuffle", "suricata", "zeek", "openvas", "nmap", "metasploit"]
    for t in sec_tools:
        tool = get_tool_by_id(t)
        assert tool.id == t
        assert tool.category == "security_siem"

    # Verify DevSecOps Tools
    devsec_tools = ["sonarqube", "trivy", "defectdojo", "zap", "gitleaks", "trufflehog", "teleport", "authentik"]
    for t in devsec_tools:
        tool = get_tool_by_id(t)
        assert tool.id == t
        assert tool.category == "devsecops"

    # Verify Data & Lakehouse Tools
    data_tools = ["doris", "starrocks", "flink", "superset", "metabase", "great_expectations", "soda_core", "datahub", "ranger"]
    for t in data_tools:
        tool = get_tool_by_id(t)
        assert tool.id == t
        assert tool.category == "data_engineering"

    # Verify Backend & Messaging
    backend_tools = ["vault", "redpanda", "pulsar", "temporal", "n8n"]
    for t in backend_tools:
        tool = get_tool_by_id(t)
        assert tool.id == t
        assert tool.category == "backend"

    # Verify Observability & DevOps
    devops_tools = ["loki", "jaeger", "traefik", "argocd"]
    for t in devops_tools:
        tool = get_tool_by_id(t)
        assert tool.id == t
        assert tool.category == "devops"

    # Verify MLOps
    mlops_tools = ["milvus", "weaviate", "evidently", "dvc"]
    for t in mlops_tools:
        tool = get_tool_by_id(t)
        assert tool.id == t
        assert tool.category == "mlops"


def test_presets_exist():
    preset_ids = [p.id for p in PRESETS]
    expected_presets = [
        "siem_soc_defense",
        "devsecops_appsec_pipeline",
        "network_security_audit",
        "realtime_streaming_analytics",
        "cloud_native_gitops_observability",
        "advanced_rag_vector_mlops",
        "workflow_automation_integration"
    ]
    for ep in expected_presets:
        assert ep in preset_ids


def test_scaffold_siem_soc_stack(temp_project_dir):
    req = ProjectCreateRequest(
        name="Security Lab",
        description="SIEM SOC and Incident Response Stack",
        tools=["wazuh", "suricata", "thehive", "shuffle", "misp", "grafana", "postgres"]
    )
    scaffolder = ProjectScaffolder(req, temp_project_dir)
    scaffolder.scaffold()

    compose_file = os.path.join(temp_project_dir, "docker-compose.yml")
    assert os.path.exists(compose_file)
    with open(compose_file, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]
    assert "wazuh-manager" in services
    assert "wazuh-dashboard" in services
    assert "suricata" in services
    assert "thehive" in services
    assert "cortex" in services
    assert "shuffle-frontend" in services
    assert "misp" in services
    assert "grafana" in services
    assert "postgres" in services

    # Verify rules and seed files
    assert os.path.exists(os.path.join(temp_project_dir, "wazuh", "rules", "local_rules.xml"))
    assert os.path.exists(os.path.join(temp_project_dir, "suricata", "rules", "local.rules"))
    assert os.path.exists(os.path.join(temp_project_dir, ".env"))


def test_scaffold_devsecops_pipeline(temp_project_dir):
    req = ProjectCreateRequest(
        name="DevSecOps AppSec",
        description="Automated Security Pipeline",
        tools=["sonarqube", "trivy", "defectdojo", "zap", "vault", "gitleaks", "vscode"]
    )
    scaffolder = ProjectScaffolder(req, temp_project_dir)
    scaffolder.scaffold()

    compose_file = os.path.join(temp_project_dir, "docker-compose.yml")
    with open(compose_file, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]
    assert "sonarqube" in services
    assert "trivy" in services
    assert "defectdojo" in services
    assert "zap" in services
    assert "vault" in services
    assert "gitleaks" in services
    assert "vscode" in services

    # Verify VS Code extensions for DevSecOps
    extensions_file = os.path.join(temp_project_dir, ".vscode", "extensions.json")
    assert os.path.exists(extensions_file)
    with open(extensions_file, "r", encoding="utf-8") as f:
        ext_data = yaml.safe_load(f)
    assert "sonarsource.sonarlint-vscode" in ext_data["recommendations"]
    assert "aquasecurity.trivy-vulnerability-scanner" in ext_data["recommendations"]
    assert "zricethezav.gitleaks" in ext_data["recommendations"]


def test_scaffold_realtime_analytics_and_observability(temp_project_dir):
    req = ProjectCreateRequest(
        name="Realtime Observability",
        description="Flink Doris Loki Jaeger Traefik",
        tools=["flink", "doris", "starrocks", "redpanda", "loki", "jaeger", "traefik", "superset"]
    )
    scaffolder = ProjectScaffolder(req, temp_project_dir)
    scaffolder.scaffold()

    compose_file = os.path.join(temp_project_dir, "docker-compose.yml")
    with open(compose_file, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]
    assert "flink-jobmanager" in services
    assert "flink-taskmanager" in services
    assert "doris-fe" in services
    assert "doris-be" in services
    assert "starrocks-fe" in services
    assert "starrocks-be" in services
    assert "redpanda" in services
    assert "redpanda-console" in services
    assert "loki" in services
    assert "promtail" in services
    assert "jaeger" in services
    assert "traefik" in services
    assert "superset" in services


def test_k8s_scaffolding_expansion(temp_project_dir):
    req = ProjectCreateRequest(
        name="K8s Enterprise Stack",
        description="Comprehensive K8s Deployment",
        tools=["postgres", "flink", "superset", "vault", "loki", "wazuh", "sonarqube", "traefik", "argocd"]
    )
    k8s = K8sScaffolder(req, set(req.tools), temp_project_dir)
    k8s.scaffold()

    k8s_dir = os.path.join(temp_project_dir, "k8s")
    assert os.path.exists(os.path.join(k8s_dir, "kustomization.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "postgres.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "flink.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "superset.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "vault.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "loki.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "wazuh.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "sonarqube.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "traefik.yaml"))
    assert os.path.exists(os.path.join(k8s_dir, "argocd.yaml"))


def test_topology_graph_security_and_data_flows():
    tools = [
        "suricata", "wazuh", "thehive", "misp", "shuffle", "sonarqube", "defectdojo",
        "flink", "doris", "superset", "loki", "jaeger", "grafana"
    ]
    graph = TopologyGraphEngine.build_graph(tools)

    assert graph["total_nodes"] == len(tools)
    assert graph["total_edges"] > 0

    edges = graph["edges"]
    src_tgt = [(e["source"], e["target"]) for e in edges]

    # Verify Security data flows
    assert ("suricata", "wazuh") in src_tgt
    assert ("wazuh", "thehive") in src_tgt
    assert ("thehive", "misp") in src_tgt
    assert ("shuffle", "thehive") in src_tgt
    assert ("sonarqube", "defectdojo") in src_tgt

    # Verify Data & Observability flows
    assert ("flink", "doris") in src_tgt
    assert ("superset", "doris") in src_tgt
    assert ("loki", "grafana") in src_tgt
    assert ("jaeger", "grafana") in src_tgt
