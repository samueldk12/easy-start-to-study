"""
Project Metadata Storage, Auto-Discovery & JSON Cache Engine
Supports offline-first JSON cache loading, stale-while-revalidate, and persistent caching.
"""

import os
import json
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
        registry = ProjectStore._load_registry()
        
        # Auto-discover projects in PROJECTS_DIR
        if os.path.exists(PROJECTS_DIR):
            for entry in os.listdir(PROJECTS_DIR):
                full_path = os.path.join(PROJECTS_DIR, entry)
                if os.path.isdir(full_path) and not entry.startswith("."):
                    compose_path = os.path.join(full_path, "docker-compose.yml")
                    if os.path.exists(compose_path) and entry not in registry:
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
    def delete_project(project_id: str):
        registry = ProjectStore._load_registry()
        if project_id in registry:
            del registry[project_id]
            ProjectStore._save_registry(registry)

        cached = ProjectStore.load_cache()
        updated_cache = [p for p in cached if p.id != project_id]
        ProjectStore.save_cache(updated_cache)

    @staticmethod
    def _dict_to_project_info(data: Dict) -> ProjectInfo:
        ui_links = []
        for tool_id in data.get("tools", []):
            try:
                tool = get_tool_by_id(tool_id)
                if tool.ui_url:
                    ui_links.append({"name": tool.name, "url": tool.ui_url, "icon": tool.icon})
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
