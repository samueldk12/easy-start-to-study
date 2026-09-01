"""
Project Metadata Storage, Auto-Discovery & JSON Cache Engine
Supports offline-first JSON cache loading, stale-while-revalidate, and persistent caching.
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from studio.models import ProjectInfo, ContainerInfo
from studio.services.catalog import get_tool_by_id


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTRY_FILE = os.path.join(_PROJECT_ROOT, "projects", ".registry.json")
CACHE_FILE = os.path.join(_PROJECT_ROOT, "projects", "projects_cache.json")
PROJECTS_DIR = os.path.join(_PROJECT_ROOT, "projects")


class ProjectStore:
    @staticmethod
    def _to_json_compatible(obj: Any) -> Any:
        if obj is None or isinstance(obj, (int, float, str, bool)):
            return obj
        if isinstance(obj, (list, tuple, set)):
            return [ProjectStore._to_json_compatible(x) for x in obj]
        if hasattr(obj, "model_dump"):
            return ProjectStore._to_json_compatible(obj.model_dump())
        if hasattr(obj, "dict"):
            return ProjectStore._to_json_compatible(obj.dict())
        if isinstance(obj, dict):
            return {str(k): ProjectStore._to_json_compatible(v) for k, v in obj.items()}
        if isinstance(obj, (datetime, Path)):
            return str(obj)
        return str(obj)

    @staticmethod
    def _load_registry() -> Dict[str, Dict]:
        if not os.path.exists(REGISTRY_FILE):
            return {}
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _save_registry(registry: Dict[str, Any]):
        os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
        try:
            serializable = ProjectStore._to_json_compatible(registry)
            temp_file = REGISTRY_FILE + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2, ensure_ascii=False)
            if os.path.exists(REGISTRY_FILE):
                os.replace(temp_file, REGISTRY_FILE)
            else:
                os.rename(temp_file, REGISTRY_FILE)
        except Exception as e:
            print(f"[ProjectStore] Error saving registry: {e}")

    @staticmethod
    def load_cache() -> List[ProjectInfo]:
        """
        Loads the cached project list directly from projects_cache.json for instant UI loading.
        """
        if not os.path.exists(CACHE_FILE):
            return []
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []
            
            projects = []
            for item in data:
                try:
                    containers = [ContainerInfo(**c) if isinstance(c, dict) else c for c in item.get("containers", [])]
                    item_copy = dict(item)
                    item_copy["containers"] = containers
                    projects.append(ProjectInfo(**item_copy))
                except Exception:
                    continue
            return projects
        except Exception:
            return []

    @staticmethod
    def save_cache(projects: List[ProjectInfo]):
        """
        Saves the enriched projects list (including live status and containers) to projects_cache.json.
        """
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        try:
            dump_list = []
            for p in projects:
                p_dict = p.model_dump() if hasattr(p, "model_dump") else p.dict()
                p_dict["last_cached"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                dump_list.append(ProjectStore._to_json_compatible(p_dict))
            temp_file = CACHE_FILE + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(dump_list, f, indent=2, ensure_ascii=False)
            if os.path.exists(CACHE_FILE):
                os.replace(temp_file, CACHE_FILE)
            else:
                os.rename(temp_file, CACHE_FILE)
        except Exception as e:
            print(f"[ProjectStore] Error saving projects cache: {e}")

    @staticmethod
    def register_project(
        project_id: str,
        name: str,
        path: str,
        description: str,
        tools: List[str],
        include_templates: bool = True,
        auto_install_extensions: bool = True,
        custom_vscode_extensions: Optional[List[str]] = None,
        is_merged_workspace: bool = False,
        merged_projects: Optional[List[str]] = None,
        **kwargs
    ) -> ProjectInfo:
        path_str = path.path if hasattr(path, "path") else str(path or "")
        registry = ProjectStore._load_registry()
        data = {
            "id": project_id,
            "name": name,
            "path": path_str,
            "description": description,
            "tools": tools,
            "include_templates": include_templates,
            "auto_install_extensions": auto_install_extensions,
            "custom_vscode_extensions": custom_vscode_extensions or [],
            "is_merged_workspace": is_merged_workspace,
            "merged_projects": merged_projects or [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_used_at": datetime.now().isoformat(),
        }
        data.update(kwargs)
        registry[project_id] = data
        ProjectStore._save_registry(registry)

        proj_info = ProjectStore._dict_to_project_info(data)

        # Update cache immediately with the new project
        cached = ProjectStore.load_cache()
        updated_cache = [p for p in cached if p.id != project_id]
        updated_cache.insert(0, proj_info)
        ProjectStore.save_cache(updated_cache)

        return proj_info

    @staticmethod
    def list_projects() -> List[ProjectInfo]:
        """
        Lists registered projects and automatically discovers any new project folder on disk.
        """
        # Auto-discover projects in PROJECTS_DIR and user projects folder (~/projects)
        search_dirs = [PROJECTS_DIR]
        user_projects_dir = os.path.abspath(os.path.join(os.path.expanduser("~"), "projects"))
        if os.path.exists(user_projects_dir) and user_projects_dir not in search_dirs:
            search_dirs.append(user_projects_dir)

        registry = ProjectStore._load_registry()
        registry_changed = False
        for s_dir in search_dirs:
            if os.path.exists(s_dir):
                for entry in os.listdir(s_dir):
                    full_path = os.path.join(s_dir, entry)
                    if os.path.isdir(full_path) and not entry.startswith("."):
                        compose_path = os.path.join(full_path, "docker-compose.yml")
                        compose_alt = os.path.join(full_path, "compose.yaml")
                        if (os.path.exists(compose_path) or os.path.exists(compose_alt)) and entry not in registry:
                            registry[entry] = {
                                "id": entry,
                                "name": entry.replace("-", " ").title(),
                                "path": full_path,
                                "description": f"Projeto auto-detectado: {entry}",
                                "tools": [],
                                "include_templates": True,
                                "auto_install_extensions": True,
                                "custom_vscode_extensions": [],
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            registry_changed = True
        if registry_changed:
            ProjectStore._save_registry(registry)

        projects: List[ProjectInfo] = []
        for p_id, data in registry.items():
            if os.path.exists(data.get("path", "")):
                projects.append(ProjectStore._dict_to_project_info(data))

        return sorted(projects, key=lambda x: x.created_at, reverse=True)

    @staticmethod
    def get_project(project_id: str) -> Optional[ProjectInfo]:
        registry = ProjectStore._load_registry()
        if project_id in registry:
            return ProjectStore._dict_to_project_info(registry[project_id])
        return None

    @staticmethod
    def delete_project(project_id: str) -> bool:
        registry = ProjectStore._load_registry()
        found = False
        if project_id in registry:
            del registry[project_id]
            ProjectStore._save_registry(registry)
            found = True

        cached = ProjectStore.load_cache()
        updated_cache = [p for p in cached if p.id != project_id]
        ProjectStore.save_cache(updated_cache)
        return found

    @staticmethod
    def touch_last_used(project_id: str):
        """Updates last_used_at timestamp when a project is accessed/started."""
        registry = ProjectStore._load_registry()
        if project_id in registry:
            registry[project_id]["last_used_at"] = datetime.now().isoformat()
            ProjectStore._save_registry(registry)

    @staticmethod
    def update_project_governance(project_id: str, auto_cleanup_days: int = 15, clean_images: bool = True, clean_volumes: bool = False) -> bool:
        """Updates governance settings for a specific project."""
        registry = ProjectStore._load_registry()
        if project_id not in registry:
            return False
        registry[project_id]["auto_cleanup_days"] = auto_cleanup_days
        registry[project_id]["clean_images_on_idle"] = clean_images
        registry[project_id]["clean_volumes_on_idle"] = clean_volumes
        ProjectStore._save_registry(registry)
        return True

    _COMPOSE_CACHE: Dict[str, Tuple[float, Any]] = {}
    _PKG_CACHE: Dict[str, Tuple[float, bool, bool]] = {}

    @staticmethod
    def extract_ui_links(
        proj_path: str,
        tools: Optional[List[str]] = None,
        containers: Optional[List[ContainerInfo]] = None,
        is_merged: bool = False
    ) -> List[Dict[str, str]]:
        """
        Dynamically extracts all active Web UIs, Admin Portals, and Dashboards for a project
        from docker-compose files, live containers, and registered catalog tools with mtime caching.
        """
        ui_links = []
        seen_urls = set()
        seen_names = set()

        def add_link(name: str, url: str, icon: str = "globe"):
            clean_url = url.rstrip("/")
            if clean_url not in seen_urls and name not in seen_names:
                seen_urls.add(clean_url)
                seen_names.add(name)
                ui_links.append({"name": name, "url": url, "icon": icon})

        path_raw = proj_path.path if hasattr(proj_path, "path") else str(proj_path or "")
        has_next = False
        if path_raw and os.path.exists(path_raw):
            proj_dir = Path(path_raw)
            
            # Check for Next.js / React frontend with mtime cache
            pkg_candidates = [
                proj_dir / "package.json",
                proj_dir / "app" / "package.json",
                proj_dir / "frontend" / "package.json",
                proj_dir / "web" / "package.json",
                proj_dir / "ui" / "package.json",
                proj_dir / "client" / "package.json"
            ]
            for pkg in pkg_candidates:
                if pkg.exists():
                    pkg_str = str(pkg)
                    mtime = os.path.getmtime(pkg)
                    cached = ProjectStore._PKG_CACHE.get(pkg_str)
                    if cached and cached[0] == mtime:
                        is_next, is_react = cached[1], cached[2]
                        if is_next:
                            has_next = True
                            add_link("Next.js Web App", "http://localhost:3000", "globe")
                        elif is_react:
                            add_link("Web Application", "http://localhost:3000", "globe")
                    else:
                        try:
                            with open(pkg, "r", encoding="utf-8", errors="replace") as pf:
                                p_data = json.load(pf)
                            deps = {**p_data.get("dependencies", {}), **p_data.get("devDependencies", {})}
                            is_next = "next" in deps
                            is_react = "react" in deps or "vue" in deps or "vite" in deps
                            ProjectStore._PKG_CACHE[pkg_str] = (mtime, is_next, is_react)
                            if is_next:
                                has_next = True
                                add_link("Next.js Web App", "http://localhost:3000", "globe")
                            elif is_react:
                                add_link("Web Application", "http://localhost:3000", "globe")
                        except Exception:
                            pass

            # Inspect docker-compose.yml services and published ports with mtime cache
            compose_files = [proj_dir / "docker-compose.yml", proj_dir / "docker-compose.yaml", proj_dir / "compose.yaml"]
            for cf in compose_files:
                if cf.exists():
                    cf_str = str(cf)
                    mtime = os.path.getmtime(cf)
                    cached = ProjectStore._COMPOSE_CACHE.get(cf_str)
                    if cached and cached[0] == mtime:
                        c_data = cached[1]
                    else:
                        try:
                            with open(cf, "r", encoding="utf-8", errors="replace") as f:
                                c_data = yaml.safe_load(f)
                            ProjectStore._COMPOSE_CACHE[cf_str] = (mtime, c_data)
                        except Exception:
                            c_data = None

                    if isinstance(c_data, dict) and "services" in c_data:
                        for svc_name, svc_conf in c_data.get("services", {}).items():
                            if not isinstance(svc_conf, dict):
                                continue
                            svc_lower = svc_name.lower()
                            image_lower = str(svc_conf.get("image", "")).lower()

                            for p in svc_conf.get("ports", []):
                                p_str = str(p)
                                if ":" in p_str:
                                    parts = p_str.split(":")
                                    host_port = parts[0].strip().replace('"', '').replace("'", "")
                                    container_port = parts[1].split("/")[0].strip().replace('"', '').replace("'", "") if len(parts) > 1 else ""

                                    # VS Code
                                    if "vscode" in svc_lower or "code-server" in svc_lower or "coder" in image_lower:
                                        is_ws = (proj_dir / "workspace.code-workspace").exists() or is_merged
                                        if is_ws:
                                            add_link("VS Code Multi-Root Workspace", f"http://localhost:{host_port}/?workspace=/home/coder/project/workspace.code-workspace", "code")
                                        else:
                                            add_link("VS Code Web (IDE)", f"http://localhost:{host_port}/?folder=/home/coder/project", "code")
                                    # Airflow Webserver
                                    elif "airflow" in svc_lower and ("webserver" in svc_lower or container_port == "8080" or "webserver" in str(svc_conf.get("command", ""))):
                                        add_link("Airflow Webserver", f"http://localhost:{host_port}", "git-merge")
                                    # MinIO Console
                                    elif "minio" in svc_lower and (container_port == "9001" or host_port in ("9001", "9007", "9091") or (not container_port and host_port != "9000")):
                                        add_link("MinIO Console", f"http://localhost:{host_port}", "hard-drive")
                                    # Spark Master Web UI (ignore RPC port 7077/7078)
                                    elif ("spark" in svc_lower and "master" in svc_lower) or ("spark" in svc_lower and container_port == "8080"):
                                        if container_port != "7077" and host_port not in ("7077", "7078"):
                                            add_link("Spark Master UI", f"http://localhost:{host_port}", "zap")
                                    # Trino UI
                                    elif "trino" in svc_lower:
                                        add_link("Trino UI", f"http://localhost:{host_port}", "database")
                                    # Kafka UI
                                    elif "kafka-ui" in svc_lower or "kafka_ui" in svc_lower or "kafka-ui" in image_lower:
                                        add_link("Kafka UI", f"http://localhost:{host_port}", "activity")
                                    # JupyterLab
                                    elif "jupyter" in svc_lower or "notebook" in image_lower:
                                        add_link("JupyterLab", f"http://localhost:{host_port}", "book-open")
                                    # Schema Registry API
                                    elif "schema-registry" in svc_lower or "schema_registry" in svc_lower:
                                        add_link("Schema Registry", f"http://localhost:{host_port}", "shield-check")
                                    # Kafka Connect API
                                    elif ("kafka-connect" in svc_lower or "kafka_connect" in svc_lower or "debezium/connect" in image_lower) and "postgres" not in svc_lower:
                                        add_link("Kafka Connect (Debezium)", f"http://localhost:{host_port}", "repeat")
                                    # Iceberg REST Catalog
                                    elif "iceberg-rest" in svc_lower or "iceberg_rest" in svc_lower or "iceberg" in image_lower:
                                        add_link("Iceberg REST Catalog", f"http://localhost:{host_port}", "layers")
                                    # Mailpit / Mailhog
                                    elif "mailpit" in svc_lower or "mailhog" in svc_lower or container_port in ("8025", "8026"):
                                        add_link("Mailpit Email UI", f"http://localhost:{host_port}", "mail")
                                    # Superset BI
                                    elif "superset" in svc_lower:
                                        add_link("Superset BI", f"http://localhost:{host_port}", "pie-chart")
                                    # Metabase BI
                                    elif "metabase" in svc_lower:
                                        add_link("Metabase BI", f"http://localhost:{host_port}", "pie-chart")
                                    # Grafana
                                    elif "grafana" in svc_lower:
                                        add_link("Grafana Dashboards", f"http://localhost:{host_port}", "layout-dashboard")
                                    # Prometheus
                                    elif "prometheus" in svc_lower:
                                        add_link("Prometheus", f"http://localhost:{host_port}", "activity")
                                    # pgAdmin
                                    elif "pgadmin" in svc_lower:
                                        add_link("pgAdmin 4", f"http://localhost:{host_port}", "terminal")
                                    # Keycloak
                                    elif "keycloak" in svc_lower:
                                        add_link("Keycloak IAM", f"http://localhost:{host_port}", "key")
                                    # MLflow
                                    elif "mlflow" in svc_lower:
                                        add_link("MLflow UI", f"http://localhost:{host_port}", "activity")
                                    # Wazuh
                                    elif "wazuh" in svc_lower:
                                        add_link("Wazuh Dashboard", f"https://localhost:{host_port}", "shield")
                                    # Splunk
                                    elif "splunk" in svc_lower:
                                        add_link("Splunk Enterprise", f"http://localhost:{host_port}", "search")
                                    # SonarQube
                                    elif "sonarqube" in svc_lower:
                                        add_link("SonarQube", f"http://localhost:{host_port}", "check-circle")
                                    # DefectDojo
                                    elif "defectdojo" in svc_lower:
                                        add_link("DefectDojo", f"http://localhost:{host_port}", "layers")
                                    # OWASP ZAP
                                    elif "zap" in svc_lower:
                                        add_link("OWASP ZAP", f"http://localhost:{host_port}", "crosshair")
                                    # n8n Automation
                                    elif "n8n" in svc_lower:
                                        add_link("n8n Automation", f"http://localhost:{host_port}", "git-branch")
                                    # RabbitMQ Management
                                    elif "rabbitmq" in svc_lower and (container_port in ("15672", "15671") or host_port in ("15672", "15673")):
                                        add_link("RabbitMQ Management", f"http://localhost:{host_port}", "message-square")
                                    # Redis Commander
                                    elif "redis" in svc_lower and "commander" in svc_lower:
                                        add_link("Redis Commander", f"http://localhost:{host_port}", "database")
                                    # ClickHouse
                                    elif "clickhouse" in svc_lower and container_port in ("8123", "80"):
                                        add_link("ClickHouse Web Play", f"http://localhost:{host_port}/play", "bar-chart-2")
                                    # Apache Doris
                                    elif "doris" in svc_lower:
                                        add_link("Apache Doris Web UI", f"http://localhost:{host_port}", "database")
                                    # StarRocks
                                    elif "starrocks" in svc_lower:
                                        add_link("StarRocks Web UI", f"http://localhost:{host_port}", "zap")
                                    # Redpanda Console
                                    elif "redpanda" in svc_lower and "console" in svc_lower:
                                        add_link("Redpanda Console", f"http://localhost:{host_port}", "activity")
                                    # Pulsar Manager
                                    elif "pulsar" in svc_lower and "manager" in svc_lower:
                                        add_link("Pulsar Manager", f"http://localhost:{host_port}", "activity")
                                    # Portainer
                                    elif "portainer" in svc_lower:
                                        add_link("Portainer Docker UI", f"http://localhost:{host_port}", "server")
                                    # Kibana
                                    elif "kibana" in svc_lower:
                                        add_link("Kibana Dashboard", f"http://localhost:{host_port}", "layout-dashboard")
                                    # OpenSearch Dashboards
                                    elif "opensearch" in svc_lower and "dashboards" in svc_lower:
                                        add_link("OpenSearch Dashboards", f"http://localhost:{host_port}", "layout-dashboard")
                                    # Jaeger
                                    elif "jaeger" in svc_lower and (container_port in ("16686", "80") or host_port in ("16686", "16687")):
                                        add_link("Jaeger Tracing UI", f"http://localhost:{host_port}", "activity")
                                    # OpenMetadata
                                    elif "openmetadata" in svc_lower:
                                        add_link("OpenMetadata UI", f"http://localhost:{host_port}", "database")
                                    # DataHub
                                    elif "datahub" in svc_lower:
                                        add_link("DataHub UI", f"http://localhost:{host_port}", "database")
                                    # Prefect
                                    elif "prefect" in svc_lower:
                                        add_link("Prefect UI", f"http://localhost:{host_port}", "git-branch")
                                    # Dagster
                                    elif "dagster" in svc_lower:
                                        add_link("Dagster Dagit UI", f"http://localhost:{host_port}", "git-branch")
                                    # Temporal
                                    elif "temporal" in svc_lower and "ui" in svc_lower:
                                        add_link("Temporal Web UI", f"http://localhost:{host_port}", "git-branch")
                                    # Vault
                                    elif "vault" in svc_lower and (container_port == "8200" or host_port in ("8200", "8201")):
                                        add_link("HashiCorp Vault UI", f"http://localhost:{host_port}", "key")
                                    # Open WebUI (LLM)
                                    elif "open-webui" in svc_lower or "open_webui" in svc_lower or "webui" in svc_lower:
                                        add_link("Open WebUI (LLM)", f"http://localhost:{host_port}", "cpu")
                                    # Dify
                                    elif "dify" in svc_lower:
                                        add_link("Dify AI App Platform", f"http://localhost:{host_port}", "cpu")
                                    # Flowise
                                    elif "flowise" in svc_lower:
                                        add_link("Flowise AI Workflow", f"http://localhost:{host_port}", "cpu")
                                    # Langfuse
                                    elif "langfuse" in svc_lower:
                                        add_link("Langfuse LLM Observability", f"http://localhost:{host_port}", "activity")
                                    # Qdrant Dashboard
                                    elif "qdrant" in svc_lower:
                                        add_link("Qdrant Dashboard", f"http://localhost:{host_port}/dashboard", "database")
                                    # Frontends / Web Apps
                                    elif svc_lower in ("web", "frontend", "app", "ui", "client") or host_port in ("3000", "3001", "3002", "3003", "5173", "5174", "8000"):
                                        name = "Next.js Web App" if has_next or "next" in str(svc_conf) else f"Web App ({svc_name})"
                                        add_link(name, f"http://localhost:{host_port}", "globe")

        # 2. Links from registered catalog tools (fallback ONLY if no link for that service category is found)
        for tool_id in (tools or []):
            try:
                tool = get_tool_by_id(tool_id)
                if tool and tool.ui_url:
                    tool_key = tool_id.replace("_", "-").lower()
                    already_covered = any(
                        tool_key in u["name"].lower() or 
                        tool_id in u["name"].lower() or 
                        (tool_id == "airflow" and "airflow" in u["name"].lower()) or
                        (tool_id == "minio" and "minio" in u["name"].lower()) or
                        (tool_id == "spark" and "spark" in u["name"].lower()) or
                        (tool_id == "kafka_ui" and "kafka" in u["name"].lower()) or
                        (tool_id == "kafka_connect" and "connect" in u["name"].lower()) or
                        (tool_id == "trino" and "trino" in u["name"].lower()) or
                        (tool_id == "iceberg_rest" and "iceberg" in u["name"].lower())
                        for u in ui_links
                    )
                    if not already_covered:
                        add_link(tool.name, tool.ui_url, tool.icon)
            except Exception:
                continue

        return ui_links

    @staticmethod
    def _dict_to_project_info(data: Dict) -> ProjectInfo:
        path_raw = data.path if hasattr(data, "path") else (data.get("path") if isinstance(data, dict) else "")
        proj_path_str = path_raw.path if hasattr(path_raw, "path") else str(path_raw or "")
        is_merged = data.get("is_merged_workspace", False) or (bool(proj_path_str) and os.path.exists(os.path.join(proj_path_str, "workspace.code-workspace")))
        
        containers = [ContainerInfo(**c) if isinstance(c, dict) else c for c in data.get("containers", [])]
        tools_list = data.get("tools", [])

        # Extract dynamic UI links
        ui_links = ProjectStore.extract_ui_links(
            proj_path=proj_path_str,
            tools=tools_list,
            containers=containers,
            is_merged=is_merged
        )

        return ProjectInfo(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            description=data.get("description", ""),
            tools=tools_list,
            include_templates=data.get("include_templates", True),
            auto_install_extensions=data.get("auto_install_extensions", True),
            custom_vscode_extensions=data.get("custom_vscode_extensions", []),
            created_at=data.get("created_at", ""),
            last_used_at=data.get("last_used_at"),
            auto_cleanup_days=data.get("auto_cleanup_days", 15),
            clean_images_on_idle=data.get("clean_images_on_idle", True),
            clean_volumes_on_idle=data.get("clean_volumes_on_idle", False),
            status=data.get("status", "stopped"),
            visual_status=data.get("visual_status", "orange"),
            retry_count=data.get("retry_count", 0),
            containers=containers,
            ui_links=ui_links,
            is_merged_workspace=is_merged,
            merged_projects=data.get("merged_projects", [])
        )
