"""
Project Metadata Storage, Auto-Discovery & JSON Cache Engine
Supports offline-first JSON cache loading, stale-while-revalidate, and persistent caching.
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from studio.models import ProjectInfo, ContainerInfo
from studio.services.catalog import get_tool_by_id


REGISTRY_FILE = os.path.abspath(os.path.join(".", "projects", ".registry.json"))
CACHE_FILE = os.path.abspath(os.path.join(".", "projects", "projects_cache.json"))
PROJECTS_DIR = os.path.abspath(os.path.join(".", "projects"))


class ProjectStore:
    @staticmethod
    def _load_registry() -> Dict[str, Dict]:
        if not os.path.exists(REGISTRY_FILE):
            return {}
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _save_registry(registry: Dict[str, Dict]):
        os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

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
                dump_list.append(p_dict)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(dump_list, f, indent=2, ensure_ascii=False)
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
        custom_vscode_extensions: Optional[List[str]] = None
    ) -> ProjectInfo:
        registry = ProjectStore._load_registry()
        data = {
            "id": project_id,
            "name": name,
            "path": path,
            "description": description,
            "tools": tools,
            "include_templates": include_templates,
            "auto_install_extensions": auto_install_extensions,
            "custom_vscode_extensions": custom_vscode_extensions or [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
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
    def _dict_to_project_info(data: Dict) -> ProjectInfo:
        ui_links = []
        seen_urls = set()
        seen_names = set()

        def add_link(name: str, url: str, icon: str = "globe"):
            clean_url = url.rstrip("/")
            if clean_url not in seen_urls and name not in seen_names:
                seen_urls.add(clean_url)
                seen_names.add(name)
                ui_links.append({"name": name, "url": url, "icon": icon})

        # 1. Inspect project directory and docker-compose.yml for dynamic Web UIs (Next.js, Mailpit, Airflow, etc.)
        proj_path_str = data.get("path", "")
        has_next = False
        if proj_path_str and os.path.exists(proj_path_str):
            proj_dir = Path(proj_path_str)
            
            # Check for Next.js / React frontend in root or subdirectories
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
                    try:
                        with open(pkg, "r", encoding="utf-8", errors="replace") as pf:
                            p_data = json.load(pf)
                        deps = {**p_data.get("dependencies", {}), **p_data.get("devDependencies", {})}
                        if "next" in deps:
                            has_next = True
                            add_link("Next.js Web App", "http://localhost:3000", "globe")
                        elif "react" in deps or "vue" in deps or "vite" in deps:
                            add_link("Web Application", "http://localhost:3000", "globe")
                    except Exception:
                        pass

            # Inspect docker-compose.yml services and published ports
            compose_files = [proj_dir / "docker-compose.yml", proj_dir / "docker-compose.yaml", proj_dir / "compose.yaml"]
            for cf in compose_files:
                if cf.exists():
                    try:
                        with open(cf, "r", encoding="utf-8", errors="replace") as f:
                            c_data = yaml.safe_load(f)
                        if isinstance(c_data, dict) and "services" in c_data:
                            for svc_name, svc_conf in c_data.get("services", {}).items():
                                if not isinstance(svc_conf, dict):
                                    continue
                                for p in svc_conf.get("ports", []):
                                    p_str = str(p)
                                    if ":" in p_str:
                                        host_port = p_str.split(":")[0].strip().replace('"', '').replace("'", "")
                                        # Match service types
                                        if svc_name.lower() in ("web", "frontend", "app", "ui", "client") or host_port == "3000":
                                            name = "Next.js Web App" if has_next or "next" in str(svc_conf) else f"Web App ({svc_name})"
                                            add_link(name, f"http://localhost:{host_port}", "globe")
                                        elif svc_name.lower() in ("mailpit", "mailhog") and host_port in ("8025", "8026"):
                                            add_link("Mailpit Email UI", f"http://localhost:{host_port}", "mail")
                                        elif "airflow" in svc_name.lower() and host_port in ("8080", "8081", "8088", "8089"):
                                            add_link("Airflow Webserver", f"http://localhost:{host_port}", "git-merge")
                                        elif "superset" in svc_name.lower() or host_port in ("8088", "8094"):
                                            add_link("Superset BI", f"http://localhost:{host_port}", "pie-chart")
                                        elif "grafana" in svc_name.lower() or host_port in ("3000", "3005"):
                                            add_link("Grafana Dashboards", f"http://localhost:{host_port}", "layout-dashboard")
                                        elif "prometheus" in svc_name.lower() or host_port in ("9090", "9095"):
                                            add_link("Prometheus", f"http://localhost:{host_port}", "activity")
                                        elif "pgadmin" in svc_name.lower() or host_port == "5055":
                                            add_link("pgAdmin 4", f"http://localhost:{host_port}", "terminal")
                                        elif "keycloak" in svc_name.lower() or host_port == "8090":
                                            add_link("Keycloak IAM", f"http://localhost:{host_port}", "key")
                                        elif "minio" in svc_name.lower() and host_port in ("9001", "9091"):
                                            add_link("MinIO Console", f"http://localhost:{host_port}", "hard-drive")
                                        elif "trino" in svc_name.lower() and host_port == "8080":
                                            add_link("Trino UI", f"http://localhost:{host_port}", "database")
                                        elif "jupyter" in svc_name.lower() or host_port == "8888":
                                            add_link("JupyterLab", f"http://localhost:{host_port}", "book-open")
                                        elif "mlflow" in svc_name.lower() or host_port == "5001":
                                            add_link("MLflow UI", f"http://localhost:{host_port}", "activity")
                                        elif "metabase" in svc_name.lower() or host_port == "3006":
                                            add_link("Metabase BI", f"http://localhost:{host_port}", "pie-chart")
                                        elif "wazuh" in svc_name.lower() or host_port == "8444":
                                            add_link("Wazuh Dashboard", f"https://localhost:{host_port}", "shield")
                                        elif "splunk" in svc_name.lower() or host_port == "8001":
                                            add_link("Splunk Enterprise", f"http://localhost:{host_port}", "search")
                                        elif "sonarqube" in svc_name.lower() or host_port == "9003":
                                            add_link("SonarQube", f"http://localhost:{host_port}", "check-circle")
                                        elif "defectdojo" in svc_name.lower() or host_port == "8096":
                                            add_link("DefectDojo", f"http://localhost:{host_port}", "layers")
                                        elif "zap" in svc_name.lower() or host_port == "8097":
                                            add_link("OWASP ZAP", f"http://localhost:{host_port}", "crosshair")
                                        elif "n8n" in svc_name.lower() or host_port == "5678":
                                            add_link("n8n Automation", f"http://localhost:{host_port}", "git-branch")
                                        elif "rabbitmq" in svc_name.lower() and host_port == "15672":
                                            add_link("RabbitMQ Management", f"http://localhost:{host_port}", "message-square")
                                        elif "redis_commander" in svc_name.lower() or host_port == "8085":
                                            add_link("Redis Commander", f"http://localhost:{host_port}", "database")
                                        elif "kafka_ui" in svc_name.lower() or host_port == "8082":
                                            add_link("Kafka UI", f"http://localhost:{host_port}", "activity")
                    except Exception:
                        pass

        # 2. Links from registered catalog tools (fallback if not already mapped)
        for tool_id in data.get("tools", []):
            try:
                tool = get_tool_by_id(tool_id)
                if tool.ui_url:
                    if tool_id == "airflow" and any("808" in u["url"] for u in ui_links):
                        continue
                    if tool_id == "mailpit" and any("8025" in u["url"] for u in ui_links):
                        continue
                    add_link(tool.name, tool.ui_url, tool.icon)
            except Exception:
                continue

        containers = [ContainerInfo(**c) if isinstance(c, dict) else c for c in data.get("containers", [])]

        return ProjectInfo(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            description=data.get("description", ""),
            tools=data.get("tools", []),
            include_templates=data.get("include_templates", True),
            auto_install_extensions=data.get("auto_install_extensions", True),
            custom_vscode_extensions=data.get("custom_vscode_extensions", []),
            created_at=data.get("created_at", ""),
            status=data.get("status", "stopped"),
            visual_status=data.get("visual_status", "orange"),
            retry_count=data.get("retry_count", 0),
            containers=containers,
            ui_links=ui_links
        )
