"""
Project Metadata Storage and Discovery
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from studio.models import ProjectInfo, ToolOption
from studio.services.catalog import get_tool_by_id


REGISTRY_FILE = os.path.abspath(os.path.join(".", "projects", ".registry.json"))


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
    def register_project(project_id: str, name: str, path: str, description: str, tools: List[str], include_templates: bool = True, auto_install_extensions: bool = True, custom_vscode_extensions: Optional[List[str]] = None) -> ProjectInfo:
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
        return ProjectStore._dict_to_project_info(data)

    @staticmethod
    def list_projects() -> List[ProjectInfo]:
        registry = ProjectStore._load_registry()
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
            ui_links=ui_links
        )
