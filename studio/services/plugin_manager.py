"""
Plugin Management and Discovery Engine for StackStudio
Allows dynamic loading, creation, and execution of custom tool plugins.
"""

import os
import yaml
import json
import shutil
from typing import List, Dict, Optional, Any
from studio.models import ToolPlugin, ToolOption


PLUGINS_DIR = os.path.abspath(os.path.join(".", "plugins"))


class PluginManager:
    @staticmethod
    def get_plugins_dir() -> str:
        os.makedirs(PLUGINS_DIR, exist_ok=True)
        return PLUGINS_DIR

    @staticmethod
    def list_plugins() -> List[ToolPlugin]:
        plugins_dir = PluginManager.get_plugins_dir()
        plugins: List[ToolPlugin] = []

        if not os.path.exists(plugins_dir):
            return plugins

        for entry in os.listdir(plugins_dir):
            plugin_folder = os.path.join(plugins_dir, entry)
            if os.path.isdir(plugin_folder):
                yaml_file = os.path.join(plugin_folder, "plugin.yaml")
                json_file = os.path.join(plugin_folder, "plugin.json")

                if os.path.exists(yaml_file):
                    try:
                        with open(yaml_file, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                            if data and isinstance(data, dict):
                                plugins.append(ToolPlugin(**data))
                    except Exception as e:
                        print(f"Error loading plugin from {yaml_file}: {e}")
                elif os.path.exists(json_file):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if data and isinstance(data, dict):
                                plugins.append(ToolPlugin(**data))
                    except Exception as e:
                        print(f"Error loading plugin from {json_file}: {e}")

        return plugins

    @staticmethod
    def get_plugin(plugin_id: str) -> Optional[ToolPlugin]:
        plugins = PluginManager.list_plugins()
        for p in plugins:
            if p.id == plugin_id:
                return p
        return None

    @staticmethod
    def save_plugin(plugin: ToolPlugin) -> ToolPlugin:
        plugins_dir = PluginManager.get_plugins_dir()
        plugin_folder = os.path.join(plugins_dir, plugin.id)
        os.makedirs(plugin_folder, exist_ok=True)

        # Synthesize compose_services if not manually specified
        if not plugin.compose_services:
            svc_name = plugin.id.replace("_", "-")
            svc_def: Dict[str, Any] = {
                "container_name": f"${{PROJECT_NAME}}-{svc_name}"
            }

            if plugin.source_type == "dockerfile" and plugin.dockerfile_content:
                # Save Dockerfile in plugin folder
                dockerfile_path = os.path.join(plugin_folder, "Dockerfile")
                with open(dockerfile_path, "w", encoding="utf-8") as df:
                    df.write(plugin.dockerfile_content)
                svc_def["build"] = {"context": f"./plugins/{plugin.id}"}
            elif plugin.source_type == "github" and plugin.git_url:
                git_url = plugin.git_url.strip()
                branch = plugin.git_branch or "main"
                subfolder = f":{plugin.git_subfolder.strip('/')}" if getattr(plugin, "git_subfolder", "") else ""
                svc_def["build"] = {"context": f"{git_url}#{branch}{subfolder}"}
            elif plugin.image:
                svc_def["image"] = plugin.image.strip()
            else:
                svc_def["image"] = f"{plugin.id}:latest"

            # Ports
            if plugin.default_port:
                c_port = plugin.container_port or plugin.default_port
                svc_def["ports"] = [f"${{{plugin.id.upper()}_PORT:-{plugin.default_port}}}:{c_port}"]

            # Environment variables
            if plugin.env_vars:
                svc_def["environment"] = {k: f"${{{k}:-{v}}}" for k, v in plugin.env_vars.items()}

            # Command
            if plugin.command:
                svc_def["command"] = plugin.command

            # Volumes
            if plugin.volumes:
                svc_def["volumes"] = plugin.volumes

            plugin.compose_services = {svc_name: svc_def}

        yaml_path = os.path.join(plugin_folder, "plugin.yaml")
        plugin_dict = plugin.dict()
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(plugin_dict, f, sort_keys=False, default_flow_style=False)

        return plugin

    @staticmethod
    def delete_plugin(plugin_id: str) -> bool:
        plugins_dir = PluginManager.get_plugins_dir()
        plugin_folder = os.path.join(plugins_dir, plugin_id)
        if os.path.exists(plugin_folder) and os.path.isdir(plugin_folder):
            shutil.rmtree(plugin_folder)
            return True
        return False

    @staticmethod
    def plugin_to_tool_option(plugin: ToolPlugin) -> ToolOption:
        return ToolOption(
            id=plugin.id,
            name=plugin.name,
            category=plugin.category,
            description=plugin.description,
            icon=plugin.icon,
            badge=plugin.badge,
            default_port=plugin.default_port,
            ui_url=plugin.ui_url,
            env_vars=plugin.env_vars,
            default_folders=plugin.default_folders,
            dependencies=plugin.dependencies,
            is_plugin=True
        )
