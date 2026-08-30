"""
Project and Service Merger Engine for StackStudio.
Allows combining multiple projects/services into a unified Multi-Root Workspace Card,
with unified Docker Compose, shared network, and synchronized VS Code Web multi-root explorer.
"""

import os
import json
import yaml
import re
from typing import List, Dict, Any, Optional
from studio.models import ProjectInfo
from studio.services.project_store import ProjectStore, PROJECTS_DIR
from studio.services.docker_manager import find_next_free_port, is_port_in_use


class ProjectMerger:
    @staticmethod
    def merge_projects(name: str, project_ids: List[str], description: Optional[str] = None) -> ProjectInfo:
        if len(project_ids) < 2:
            raise ValueError("É necessário selecionar pelo menos 2 projetos para realizar o merge.")

        all_projects = ProjectStore.list_projects()
        target_projects: List[ProjectInfo] = []
        for pid in project_ids:
            found = next((p for p in all_projects if p.id == pid), None)
            if not found:
                raise ValueError(f"Projeto com ID '{pid}' não encontrado.")
            target_projects.append(found)

        # 1. Generate clean merged project ID & directory
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '-', name.strip().lower())
        safe_name = re.sub(r'-+', '-', safe_name).strip('-')
        merged_id = f"workspace-{safe_name}"
        merged_dir = os.path.join(PROJECTS_DIR, merged_id)
        os.makedirs(merged_dir, exist_ok=True)
        os.makedirs(os.path.join(merged_dir, ".vscode"), exist_ok=True)
        os.makedirs(os.path.join(merged_dir, "vscode"), exist_ok=True)

        # 2. Gather Tools, UI Links, Extensions and Database Connections
        combined_tools = set()
        combined_extensions = set([
            "ms-azuretools.vscode-docker",
            "ms-python.python",
            "ms-python.vscode-pylance",
            "ms-toolsai.jupyter",
            "cweijan.vscode-database-client2",
            "mtxr.sqltools",
            "mtxr.sqltools-driver-pg",
            "ckolkman.vscode-postgres",
            "redhat.vscode-yaml",
            "eamodio.gitlens"
        ])
        combined_sqltools = []
        combined_db_client = []
        allocated_host_ports = set()

        folders_list = []
        compose_services = {}
        merged_net_name = f"{merged_id}-net"

        # Allocate a free port for unified VS Code Web
        vscode_port = find_next_free_port(8445)
        allocated_host_ports.add(vscode_port)

        # 3. Process each source project
        for p in target_projects:
            for t in p.tools:
                combined_tools.add(t)
            for ext in (p.custom_vscode_extensions or []):
                combined_extensions.add(ext)

            folder_clean_name = p.name.strip()
            folder_slug = re.sub(r'[^a-zA-Z0-9_\-]', '-', p.id.lower())
            folders_list.append({
                "name": f"📦 {folder_clean_name}",
                "path": f"/home/coder/project/{folder_slug}"
            })

            cpath = None
            for fname in ["docker-compose.yml", "docker-compose.yaml", "compose.yaml"]:
                tmp = os.path.join(p.path, fname)
                if os.path.exists(tmp):
                    cpath = tmp
                    break

            if cpath:
                try:
                    with open(cpath, "r", encoding="utf-8", errors="replace") as f:
                        c_data = yaml.safe_load(f)
                    if isinstance(c_data, dict) and "services" in c_data:
                        for s_name, s_conf in c_data.get("services", {}).items():
                            if not isinstance(s_conf, dict):
                                continue
                            
                            if "vscode" in s_name.lower() or "code-server" in s_name.lower():
                                continue

                            merged_svc_name = s_name
                            if merged_svc_name in compose_services:
                                merged_svc_name = f"{p.id}-{s_name}"

                            new_conf = dict(s_conf)
                            new_conf["container_name"] = f"{merged_id}-{merged_svc_name}"

                            new_vols = []
                            for v in new_conf.get("volumes", []):
                                if isinstance(v, str):
                                    if ":" in v:
                                        parts = v.split(":")
                                        src = parts[0].strip()
                                        dest = ":".join(parts[1:]).strip()
                                        if src == "." or src.startswith("./") or src.startswith(".\\"):
                                            rel = src[1:].lstrip("/\\")
                                            abs_src = os.path.join(p.path, rel).replace("\\", "/").rstrip("/")
                                            new_vols.append(f"{abs_src}:{dest}")
                                        elif not os.path.isabs(src) and not src.startswith("/"):
                                            abs_src = os.path.join(p.path, src).replace("\\", "/").rstrip("/")
                                            new_vols.append(f"{abs_src}:{dest}")
                                        else:
                                            new_vols.append(v)
                                    else:
                                        if v == "." or v.startswith("./") or v.startswith(".\\"):
                                            rel = v[1:].lstrip("/\\")
                                            abs_src = os.path.join(p.path, rel).replace("\\", "/").rstrip("/")
                                            new_vols.append(abs_src)
                                        else:
                                            new_vols.append(v)
                                else:
                                    new_vols.append(v)
                            new_conf["volumes"] = new_vols

                            new_ports = []
                            for port_entry in new_conf.get("ports", []):
                                p_str = str(port_entry).strip().replace('"', '').replace("'", "")
                                if ":" in p_str:
                                    parts = p_str.split(":")
                                    h_port = int(parts[0])
                                    c_port = parts[1]
                                    if h_port in allocated_host_ports or is_port_in_use(h_port):
                                        h_port = find_next_free_port(h_port + 1)
                                    allocated_host_ports.add(h_port)
                                    new_ports.append(f"{h_port}:{c_port}")
                                else:
                                    new_ports.append(port_entry)
                            new_conf["ports"] = new_ports

                            new_conf["networks"] = [merged_net_name]
                            compose_services[merged_svc_name] = new_conf
                except Exception as e:
                    print(f"Error merging compose from {p.name}: {e}")

            src_vscode_settings = os.path.join(p.path, ".vscode", "settings.json")
            if os.path.exists(src_vscode_settings):
                try:
                    with open(src_vscode_settings, "r", encoding="utf-8") as f:
                        s_data = json.load(f)
                    for conn in s_data.get("sqltools.connections", []):
                        if conn not in combined_sqltools:
                            combined_sqltools.append(conn)
                    for conn in s_data.get("database.connections", []):
                        if conn not in combined_db_client:
                            combined_db_client.append(conn)
                except Exception:
                    pass

        # 4. Add Unified VS Code Web Service to Compose
        vscode_volumes = [
            "./:/home/coder/project"
        ]
        for p in target_projects:
            norm_path = p.path.replace("\\", "/")
            folder_slug = re.sub(r'[^a-zA-Z0-9_\-]', '-', p.id.lower())
            vscode_volumes.append(f"{norm_path}:/home/coder/project/{folder_slug}")

        compose_services["vscode"] = {
            "image": "codercom/code-server:latest",
            "container_name": f"{merged_id}-vscode",
            "restart": "unless-stopped",
            "entrypoint": [
                "/bin/sh",
                "/home/coder/project/vscode/entrypoint.sh"
            ],
            "environment": {
                "AUTO_INSTALL_EXTENSIONS": "true",
                "WORKSPACE_FILE": "/home/coder/project/workspace.code-workspace"
            },
            "ports": [
                f"{vscode_port}:8080"
            ],
            "volumes": vscode_volumes,
            "networks": [merged_net_name]
        }

        # 5. Write merged docker-compose.yml
        merged_compose_doc = {
            "name": merged_id,
            "services": compose_services,
            "networks": {
                merged_net_name: {
                    "driver": "bridge"
                }
            }
        }
        with open(os.path.join(merged_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
            yaml.dump(merged_compose_doc, f, default_flow_style=False, sort_keys=False)

        # 6. Write workspace.code-workspace (Multi-Root Workspace)
        workspace_json = {
            "folders": folders_list,
            "settings": {
                "files.autoSave": "afterDelay",
                "editor.formatOnSave": True,
                "editor.tabSize": 2,
                "terminal.integrated.defaultProfile.linux": "bash",
                "docker.showStartPage": False,
                "sqltools.useNodeRuntime": True,
                "sqltools.connections": combined_sqltools,
                "database.connections": combined_db_client,
                "database-client.connections": combined_db_client
            }
        }
        with open(os.path.join(merged_dir, "workspace.code-workspace"), "w", encoding="utf-8") as f:
            json.dump(workspace_json, f, indent=2)

        # 7. Write .vscode/extensions.json and .vscode/settings.json
        with open(os.path.join(merged_dir, ".vscode", "extensions.json"), "w", encoding="utf-8") as f:
            json.dump({"recommendations": list(combined_extensions)}, f, indent=2)

        with open(os.path.join(merged_dir, ".vscode", "settings.json"), "w", encoding="utf-8") as f:
            json.dump(workspace_json["settings"], f, indent=2)

        # 8. Write vscode/entrypoint.sh with auto multi-root startup
        exts_str = ' '.join(combined_extensions)
        entrypoint_content = f"""#!/bin/sh
set -e

echo "=== [StackStudio Multi-Root Workspace] Inicializando VS Code Web ==="

if [ "$AUTO_INSTALL_EXTENSIONS" = "true" ] && [ -f /home/coder/project/.vscode/extensions.json ]; then
  echo "Instalando extensoes oficiais recomendadas do Workspace Unificado..."
  for ext in {exts_str}; do
    echo " -> Instalando extensao: $ext"
    code-server --install-extension "$ext" --force || echo "  [AVISO] Nao foi possivel instalar $ext, continuando..."
  done
  echo "Extensoes oficiais configuradas com sucesso!"
fi

echo "Iniciando code-server com Multi-Root Workspace..."
if [ -f /home/coder/project/workspace.code-workspace ]; then
  exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project/workspace.code-workspace
else
  exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project
fi
"""
        with open(os.path.join(merged_dir, "vscode", "entrypoint.sh"), "w", encoding="utf-8", newline="\n") as f:
            f.write(entrypoint_content)

        # 9. Write README.md for the unified workspace
        proj_lines = "\n".join([f"- **{p.name}** (`{p.path}`)" for p in target_projects])
        readme_content = f"""# 🔀 Workspace Unificado: {name}

Este workspace unifica os seguintes projetos em uma única stack e ambiente de desenvolvimento:
{proj_lines}

## 💻 VS Code Multi-Root Workspace
Ao abrir o VS Code Web, todos os projetos acima são carregados simultaneamente na árvore de arquivos lateral.

- Arquivo do Workspace: `workspace.code-workspace`
- Porta do VS Code Web: `http://localhost:{vscode_port}`

## 🚀 Comandos Rápidos
- Iniciar Todos os Serviços: `docker compose up -d`
- Pausar Stack: `docker compose stop`
- Parar e Limpar: `docker compose down`
"""
        with open(os.path.join(merged_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)

        # 10. Build ProjectInfo and Register in ProjectStore
        merged_desc = description or f"Workspace unificado combinando {len(target_projects)} projetos: {', '.join([p.name for p in target_projects])}"
        
        info = ProjectInfo(
            id=merged_id,
            name=name,
            path=merged_dir,
            description=merged_desc,
            tools=list(combined_tools),
            include_templates=False,
            auto_install_extensions=True,
            custom_vscode_extensions=list(combined_extensions),
            launch_strategy="docker-compose",
            start_command="docker compose up -d",
            is_merged_workspace=True,
            merged_projects=[p.id for p in target_projects]
        )

        ProjectStore.register_project(
            project_id=merged_id,
            path=merged_dir,
            name=name,
            description=merged_desc,
            tools=list(combined_tools),
            auto_install_extensions=True,
            custom_vscode_extensions=list(combined_extensions),
            include_templates=False,
            custom_ports={"vscode": vscode_port},
            launch_strategy="docker-compose",
            is_merged_workspace=True,
            merged_projects=[p.id for p in target_projects]
        )

        return info
