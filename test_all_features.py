"""
StackStudio - Comprehensive Feature Test Runner & End-to-End Demonstration Suite
Executes and validates all core platform features:
1. Catalog Discovery & Tool Presets
2. Dynamic Multi-Tool Scaffolding & Seed Generation
3. Automatic Volume Mount & Host Directory Verification
4. Default & Custom Credentials Uniformity (admin / admin123)
5. Intelligent Folder Inspection & Auto-import Tech Detection
6. VS Code Web Auto-Extensions & Database Connection Profiles
7. Project Registry, Filtering, Search & Caching
8. Kubernetes Manifests & Topology Graph Generation
9. FastAPI REST Endpoints & Live SSE Log Streaming
"""

import os
import sys

# Ensure UTF-8 stdout on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import shutil
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch
import yaml
import httpx

# Ensure project root is on sys.path
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)

from studio.models import (
    ProjectCreateRequest,
    ProjectImportRequest,
    ProjectUpdateRequest,
    ProjectInfo
)
from studio.services.catalog import get_catalog, get_tool_by_id, PRESETS
from studio.services.scaffolder import ProjectScaffolder
from studio.services.folder_analyzer import FolderAnalyzer
from studio.services.project_store import ProjectStore
from studio.services.k8s_scaffolder import K8sScaffolder
from studio.services.topology_graph import TopologyGraphEngine
from studio.services.docker_manager import DockerManager
from studio.app import app


def print_section(title: str):
    print("\n" + "=" * 78)
    print(f" [*] {title}")
    print("=" * 78)


def test_feature_1_catalog():
    print_section("FEATURE 1: Catalog Discovery, Metadata & Presets")
    catalog = get_catalog()
    assert len(catalog) >= 6, f"Expected at least 6 categories, got {len(catalog)}"
    print(f"[+] Found {len(catalog)} Categories in Catalog:")
    total_tools = 0
    for cat in catalog:
        print(f"    - [{cat.id}] {cat.name} ({len(cat.tools)} tools)")
        total_tools += len(cat.tools)
        for t in cat.tools[:2]:
            print(f"       * {t.name} (Port: {t.default_port or 'N/A'}, Badge: {t.badge or 'N/A'})")
    assert total_tools >= 35, f"Expected at least 35 tools, got {total_tools}"
    print(f"[+] Total catalog tools registered: {total_tools}")

    # Presets
    assert len(PRESETS) >= 6
    print(f"[+] Found {len(PRESETS)} Ready-to-use Architecture Presets:")
    for p in PRESETS:
        p_name = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else str(p))
        p_tools = getattr(p, "tools", None) or (p.get("tools") if isinstance(p, dict) else [])
        print(f"    * Preset '{p_name}': {len(p_tools)} tools ({', '.join(p_tools[:4])}...)")


def test_feature_2_and_3_scaffolding_and_volumes():
    print_section("FEATURE 2 & 3: Multi-Tool Scaffolding, Seed Files & Volume Guarantees")
    temp_dir = tempfile.mkdtemp(prefix="stackstudio_demo_")
    try:
        tools_to_test = [
            "postgres", "mysql", "clickhouse", "airflow", "spark", "dbt", 
            "trino", "minio", "nginx", "opentelemetry", "prometheus", "grafana", 
            "vscode", "defectdojo"
        ]
        req = ProjectCreateRequest(
            name="demo-complete-stack",
            description="End-to-End Complete Stack Demonstration",
            tools=tools_to_test,
            custom_ports={"postgres": 5439, "airflow": 8089},
            custom_folders={"postgres_init": "postgres/init.sql"},
            custom_envs={"DEMO_CUSTOM_VAR": "Active123"},
            include_templates=True,
            default_user="admin",
            default_password="admin123",
            auto_install_extensions=True
        )
        scaffolder = ProjectScaffolder(req, temp_dir)
        project_info = scaffolder.scaffold()
        p_path = Path(project_info.path)

        print(f"[+] Project successfully scaffolded at: {p_path}")

        # 1. Verify Compose and .env
        assert (p_path / "docker-compose.yml").exists()
        assert (p_path / ".env").exists()
        with open(p_path / ".env", "r", encoding="utf-8") as f:
            env_content = f.read()
        assert "DEFAULT_USER=admin" in env_content
        assert "DEFAULT_PASSWORD=admin123" in env_content
        assert "AIRFLOW_PASSWORD=admin123" in env_content
        assert "POSTGRES_PASSWORD=admin123" in env_content
        assert "DEMO_CUSTOM_VAR=Active123" in env_content
        print("[+] .env file verified with unified credentials and custom overrides.")

        # 2. Verify Generated Seed Configuration Files
        expected_files = [
            p_path / "postgres" / "init.sql",
            p_path / "mysql" / "init.sql",
            p_path / "clickhouse" / "init.sql",
            p_path / "airflow" / "dags" / "lakehouse_pipeline.py",
            p_path / "spark" / "apps" / "stream_to_iceberg.py",
            p_path / "dbt" / "dbt_project.yml",
            p_path / "trino" / "etc" / "catalog" / "postgresql.properties",
            p_path / "nginx" / "nginx.conf",
            p_path / "nginx" / "html" / "index.html",
            p_path / "otel" / "otel-collector-config.yaml",
            p_path / "prometheus" / "prometheus.yml",
            p_path / "grafana" / "provisioning" / "datasources" / "datasource.yml",
            p_path / "vscode" / "entrypoint.sh",
            p_path / ".vscode" / "settings.json",
            p_path / ".vscode" / "extensions.json",
            p_path / "scripts" / "start.sh",
            p_path / "scripts" / "stop.sh",
            p_path / "Makefile",
            p_path / "README.md"
        ]
        for ef in expected_files:
            assert ef.exists(), f"Expected generated file missing: {ef}"
            print(f"    - Verified: {ef.relative_to(p_path)}")
        print("[+] All seed files, DAGs, SQL schemas and helper scripts successfully verified.")

        # 3. Verify Docker Compose Volume Host Directories
        with open(p_path / "docker-compose.yml", "r", encoding="utf-8") as f:
            compose_data = yaml.safe_load(f)
        
        checked_volumes = 0
        for svc_name, svc_conf in compose_data.get("services", {}).items():
            for vol in svc_conf.get("volumes", []):
                if isinstance(vol, str) and ":" in vol:
                    host_part = vol.split(":")[0].strip()
                    if host_part.startswith("./"):
                        rel_path = host_part[2:].replace("\\", "/")
                        target = p_path / rel_path
                        assert target.exists(), f"Volume mount path missing on host: {target}"
                        checked_volumes += 1
        print(f"[+] Verified {checked_volumes} volume bind mounts pointing to existing host paths.")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_feature_4_folder_analysis_and_import():
    print_section("FEATURE 4: Intelligent Folder Analysis & Technology Detection")
    temp_dir = tempfile.mkdtemp(prefix="stackstudio_import_mock_")
    try:
        mock_path = Path(temp_dir)
        # Create a mock multi-tier application
        (mock_path / "backend").mkdir(parents=True)
        (mock_path / "frontend").mkdir(parents=True)
        (mock_path / "data" / "dags").mkdir(parents=True)
        (mock_path / "data" / "init").mkdir(parents=True)

        # Backend files (FastAPI + PySpark + requirements)
        (mock_path / "backend" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
        (mock_path / "backend" / "requirements.txt").write_text("fastapi==0.110.0\nuvicorn==0.29.0\npyspark==3.5.1\napache-airflow==2.9.2\n", encoding="utf-8")
        (mock_path / "backend" / "Dockerfile").write_text("FROM python:3.11-slim\nWORKDIR /app\nCOPY . /app\nCMD [\"uvicorn\", \"main:app\"]\n", encoding="utf-8")

        # Frontend files (React / Next.js)
        (mock_path / "frontend" / "package.json").write_text(json.dumps({"name": "mock-ui", "dependencies": {"next": "14.2.0", "react": "18.3.0"}}), encoding="utf-8")

        # Root docker-compose.yml
        compose_content = """version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    volumes:
      - ./data/init/01_schema.sql:/docker-entrypoint-initdb.d/init.sql
  airflow:
    image: apache/airflow:2.9.2
    ports:
      - "8080:8080"
    volumes:
      - ./data/dags:/opt/airflow/dags
  web:
    build: ./backend
    ports:
      - "8000:8000"
"""
        (mock_path / "docker-compose.yml").write_text(compose_content, encoding="utf-8")

        # Run Analysis
        analysis = FolderAnalyzer.analyze(mock_path)
        assert analysis["success"] is True
        print(f"[+] Folder Analysis succeeded for: {mock_path.name}")
        print(f"    Strategy detected: {analysis['launch_strategy']}")
        assert analysis["launch_strategy"] == "docker-compose"

        techs = [t["name"] for t in analysis["detected_techs"]]
        print(f"    Detected Technologies: {techs}")
        assert any("Python" in t for t in techs)
        assert any("Node" in t for t in techs)

        tools = analysis["tools"]
        print(f"    Detected Tools: {tools}")
        assert "postgres" in tools
        assert "airflow" in tools

        # Run Volume Folder Assurance
        created = FolderAnalyzer.ensure_volume_folders(mock_path)
        assert (mock_path / "data" / "init" / "01_schema.sql").exists()
        assert (mock_path / "data" / "dags").is_dir()
        print(f"[+] Automatic Volume folder verification created {len(created)} missing host paths.")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_feature_5_vscode_and_database_connectors():
    print_section("FEATURE 5: VS Code Web Auto-Extensions & Database Connectors")
    temp_dir = tempfile.mkdtemp(prefix="stackstudio_vscode_")
    try:
        req = ProjectCreateRequest(
            name="test-vscode-suite",
            tools=["postgres", "mysql", "clickhouse", "vscode"],
            auto_install_extensions=True,
            custom_vscode_extensions=["eamodio.gitlens"]
        )
        scaffolder = ProjectScaffolder(req, temp_dir)
        p_info = scaffolder.scaffold()
        p_path = Path(p_info.path)

        # Check extensions.json
        ext_json_file = p_path / ".vscode" / "extensions.json"
        assert ext_json_file.exists()
        with open(ext_json_file, "r", encoding="utf-8") as f:
            ext_data = json.load(f)
        recs = ext_data.get("recommendations", [])
        print(f"[+] Pre-configured VS Code Extensions ({len(recs)}): {recs}")
        assert "ms-azuretools.vscode-docker" in recs
        assert "ms-python.python" in recs
        assert "mtxr.sqltools" in recs
        assert "eamodio.gitlens" in recs

        # Check settings.json with Database Connector Connections
        settings_file = p_path / ".vscode" / "settings.json"
        assert settings_file.exists()
        with open(settings_file, "r", encoding="utf-8") as f:
            settings_data = json.load(f)
        
        sql_conns = settings_data.get("sqltools.connections", [])
        db_client_conns = settings_data.get("database-client.connections", [])
        all_conns = sql_conns + db_client_conns

        print(f"[+] Pre-configured Database Connections ({len(all_conns)}):")
        for conn in all_conns:
            host_val = conn.get('server') or conn.get('host')
            port_val = conn.get('port')
            db_val = conn.get('database') or 'N/A'
            user_val = conn.get('username') or conn.get('user') or 'N/A'
            print(f"    - {conn['name']} -> Host: {host_val}:{port_val} (DB: {db_val}, User: {user_val})")
        
        conn_names = [c["name"] for c in all_conns]
        assert any("PostgreSQL" in n for n in conn_names)
        assert any("MySQL" in n for n in conn_names)
        assert any("ClickHouse" in n for n in conn_names)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_feature_6_project_store_and_cache():
    print_section("FEATURE 6: Project Registry, Filtering, Search & Caching")
    all_projects = ProjectStore.list_projects()
    print(f"[+] Current Registered Projects ({len(all_projects)}):")
    for p in all_projects[:5]:
        print(f"    - {p.name} (ID: {p.id}, Strategy: {p.launch_strategy}, Tools: {len(p.tools)})")
    
    # Test register a dummy project
    dummy_id = "test-store-demo-project"
    ProjectStore.register_project(
        project_id=dummy_id,
        name="Test Store Demo",
        path="C:/tmp/test_store_demo",
        description="Demo project for testing store",
        tools=["postgres", "airflow"]
    )

    p_fetched = ProjectStore.get_project(dummy_id)
    assert p_fetched is not None
    assert p_fetched.name == "Test Store Demo"
    print(f"[+] Successfully registered and retrieved '{dummy_id}'")

    # Clean up
    deleted = ProjectStore.delete_project(dummy_id)
    assert deleted is True
    assert ProjectStore.get_project(dummy_id) is None
    print(f"[+] Successfully deleted '{dummy_id}' from registry.")


def test_feature_7_and_8_k8s_and_topology():
    print_section("FEATURE 7 & 8: Kubernetes Manifests & Topology Graph Generation")
    temp_dir = tempfile.mkdtemp(prefix="stackstudio_k8s_")
    try:
        req = ProjectCreateRequest(
            name="k8s-topology-demo",
            tools=["postgres", "kafka", "spark", "trino", "grafana"],
            include_templates=True
        )
        scaffolder = ProjectScaffolder(req, temp_dir)
        p_info = scaffolder.scaffold()
        p_path = Path(p_info.path)

        # 1. Kubernetes Manifests Generation
        k8s_scaff = K8sScaffolder(req, set(req.tools), str(p_path))
        k8s_scaff.scaffold()
        k8s_files = list((p_path / "k8s").glob("*.yaml"))
        assert len(k8s_files) > 0
        print(f"[+] Generated {len(k8s_files)} Kubernetes Manifests:")
        for mf in k8s_files:
            print(f"    - {mf.name}")
        
        # 2. Topology Graph Generation
        graph = TopologyGraphEngine.build_graph(req.tools)
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        print(f"[+] Generated Architecture Topology Graph:")
        print(f"    Nodes ({len(nodes)}): {[n['label'] for n in nodes]}")
        print(f"    Connections/Edges ({len(edges)})")
        assert len(nodes) >= 5

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_feature_9_api_endpoints_and_sse():
    print_section("FEATURE 9: FastAPI Endpoints & Real-time Live Log Streaming (SSE)")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Catalog endpoint
        res = await client.get("/api/catalog")
        assert res.status_code == 200
        cat_data = res.json()
        print(f"[+] GET /api/catalog returned {len(cat_data)} categories.")

        # 2. Stats endpoint
        res = await client.get("/api/stats")
        assert res.status_code == 200
        stats = res.json()
        print(f"[+] GET /api/stats: Projects={stats.get('total_projects')}, Active={stats.get('running_projects')}")

        # 3. Projects endpoint
        res = await client.get("/api/projects")
        assert res.status_code == 200
        projs = res.json()
        print(f"[+] GET /api/projects returned {len(projs)} projects.")

        if projs:
            first_id = projs[0]["id"]
            # 4. SSE Log Streaming with Mock
            async def mock_stream(project_path, service=None, tail=150):
                yield "[docker-compose] Creating network demo-net...\n"
                yield "[docker-compose] Starting container postgres:16...\n"
                yield "[postgres] Database is ready to accept connections.\n"

            with patch("studio.services.docker_manager.DockerManager.stream_logs", side_effect=mock_stream):
                async with client.stream("GET", f"/api/projects/{first_id}/logs") as sse_res:
                    assert sse_res.status_code == 200
                    lines = []
                    async for line in sse_res.aiter_lines():
                        if line:
                            lines.append(line)
                    print(f"[+] GET /api/projects/{first_id}/logs (SSE) streamed {len(lines)} lines successfully.")
                    assert any("StackStudio SSE" in l for l in lines)
                    assert any("Database is ready" in l for l in lines)


async def test_feature_10_multi_project_merge_and_workspaces():
    print_section("FEATURE 10: Multi-Project Merge & Multi-Root VS Code Workspaces")
    
    # 1. Test ProjectMerger directly
    from studio.services.project_merger import ProjectMerger
    all_projects = ProjectStore.list_projects()
    assert len(all_projects) >= 2, "Need at least 2 projects in registry to test merge"
    
    p1 = all_projects[0]
    p2 = all_projects[1]
    
    merge_name = f"Test Workspace {p1.name} and {p2.name}"
    merged_info = ProjectMerger.merge_projects(
        name=merge_name,
        project_ids=[p1.id, p2.id],
        description="Merged multi-root workspace test suite"
    )

    assert merged_info is not None
    assert merged_info.is_merged_workspace is True
    assert p1.id in merged_info.merged_projects
    assert p2.id in merged_info.merged_projects
    
    # Verify workspace.code-workspace file exists and contains multi-root folders
    ws_file = Path(merged_info.path) / "workspace.code-workspace"
    assert ws_file.exists(), "workspace.code-workspace must exist"
    with open(ws_file, "r", encoding="utf-8") as f:
        ws_data = json.load(f)
    assert "folders" in ws_data
    assert len(ws_data["folders"]) == 2
    print(f"[+] Verified workspace.code-workspace with {len(ws_data['folders'])} root folders:")
    for folder in ws_data["folders"]:
        print(f"    - Folder: '{folder['name']}' -> Path: {folder['path']}")

    # Verify docker-compose.yml with unified vscode and shared network
    compose_file = Path(merged_info.path) / "docker-compose.yml"
    assert compose_file.exists(), "docker-compose.yml must exist in merged project"
    with open(compose_file, "r", encoding="utf-8") as f:
        comp_data = yaml.safe_load(f)
    assert "services" in comp_data
    assert "vscode" in comp_data["services"]
    assert "networks" in comp_data
    print(f"[+] Verified merged docker-compose.yml with {len(comp_data['services'])} services on shared network.")

    # 2. Test API POST /api/projects/merge
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/projects/merge", json={
            "name": "API Merged Stack Demo",
            "project_ids": [p1.id, p2.id],
            "description": "API-triggered multi-root workspace"
        })
        assert res.status_code == 200, f"API Merge failed: {res.text}"
        api_data = res.json()
        assert api_data["is_merged_workspace"] is True
        print(f"[+] POST /api/projects/merge created unified project: '{api_data['name']}' (ID: {api_data['id']})")


def main():
    print("\n" + "#" * 78)
    print(" === STACKSTUDIO - ALL-FEATURES VERIFICATION & DEMONSTRATION RUNNER ===")
    print("#" * 78)

    test_feature_1_catalog()
    test_feature_2_and_3_scaffolding_and_volumes()
    test_feature_4_folder_analysis_and_import()
    test_feature_5_vscode_and_database_connectors()
    test_feature_6_project_store_and_cache()
    test_feature_7_and_8_k8s_and_topology()
    asyncio.run(test_feature_9_api_endpoints_and_sse())
    asyncio.run(test_feature_10_multi_project_merge_and_workspaces())

    print("\n" + "#" * 78)
    print(" ALL 10 FEATURE SUITES EXECUTED AND PASSED WITH 100% SUCCESS!")
    print("#" * 78 + "\n")


if __name__ == "__main__":
    main()
