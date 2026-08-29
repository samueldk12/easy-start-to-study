"""
FastAPI Server & REST API for StackStudio
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from studio.models import (
    ProjectCreateRequest, ProjectInfo, ToolCategory, ProjectPreset, ToolPlugin,
    ContainerExecRequest, FolderAnalyzeRequest, ProjectImportRequest, ProjectUpdateRequest
)
from studio.services.catalog import CATEGORIES, PRESETS
from studio.services.scaffolder import ProjectScaffolder
from studio.services.project_store import ProjectStore
from studio.services.docker_manager import DockerManager
from studio.services.folder_analyzer import FolderAnalyzer
from studio.services.topology_graph import TopologyGraphEngine

app = FastAPI(title="StackStudio API", description="Data & AI Stack Scaffolder and Orchestrator", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    index_file = os.path.join(BASE_DIR, "templates", "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


from studio.services.catalog import get_catalog as fetch_catalog, PRESETS
from studio.services.plugin_manager import PluginManager


@app.get("/api/catalog", response_model=List[ToolCategory])
async def get_catalog():
    return fetch_catalog()


@app.get("/api/plugins", response_model=List[ToolPlugin])
async def list_plugins():
    return PluginManager.list_plugins()


@app.post("/api/plugins", response_model=ToolPlugin)
async def create_plugin(plugin: ToolPlugin):
    if not plugin.id or not plugin.name:
        raise HTTPException(status_code=400, detail="Plugin ID and name are required.")
    return PluginManager.save_plugin(plugin)


@app.delete("/api/plugins/{plugin_id}")
async def delete_plugin(plugin_id: str):
    success = PluginManager.delete_plugin(plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found.")
    return {"message": f"Plugin '{plugin_id}' deleted successfully."}


@app.get("/api/presets", response_model=List[ProjectPreset])
async def get_presets():
    return PRESETS


async def enrich_and_cache_projects() -> List[ProjectInfo]:
    projects = ProjectStore.list_projects()
    
    # Asynchronously enrich with live Docker status
    async def enrich_status(proj: ProjectInfo):
        try:
            status_data = await DockerManager.get_project_status(proj.path)
            proj.status = status_data["status"]
            proj.visual_status = status_data.get("visual_status", "orange")
            proj.containers = status_data["containers"]

            # Auto-retry crashed/unhealthy containers
            if proj.visual_status == "red":
                restarted = await DockerManager.auto_retry_crashed_containers(proj.path)
                if restarted:
                    proj.retry_count += 1
        except Exception:
            proj.status = "stopped"
            proj.visual_status = "orange"
        return proj

    enriched = await asyncio.gather(*[enrich_status(p) for p in projects])
    # Persist the full project list with live status to projects_cache.json
    ProjectStore.save_cache(enriched)
    return enriched


@app.get("/api/projects", response_model=List[ProjectInfo])
async def list_projects(cached_only: bool = False, refresh: bool = False):
    cached = ProjectStore.load_cache()

    if cached_only:
        return cached if cached else ProjectStore.list_projects()

    if refresh or not cached:
        return await enrich_and_cache_projects()

    # Fast Path: Return cached JSON immediately and update in background ("por baixo dos panos")
    asyncio.create_task(enrich_and_cache_projects())
    return cached


@app.post("/api/projects/sync", response_model=List[ProjectInfo])
async def sync_projects_now():
    return await enrich_and_cache_projects()


@app.on_event("startup")
async def startup_cache_and_sync():
    # Warm up cache and perform initial background sync
    asyncio.create_task(enrich_and_cache_projects())


@app.post("/api/projects", response_model=ProjectInfo)
async def create_project(request: ProjectCreateRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required.")
    if not request.tools:
        raise HTTPException(status_code=400, detail="At least one tool must be selected.")

    scaffolder = ProjectScaffolder(request)
    project_dir = scaffolder.scaffold()

    project_id = scaffolder.project_name
    proj = ProjectStore.register_project(
        project_id=project_id,
        name=request.name,
        path=project_dir,
        description=request.description or "Projeto gerado via StackStudio",
        tools=list(scaffolder.tools),
        include_templates=request.include_templates,
        auto_install_extensions=request.auto_install_extensions,
        custom_vscode_extensions=request.custom_vscode_extensions
    )
    return proj


@app.post("/api/projects/analyze-folder")
async def analyze_folder(req: FolderAnalyzeRequest):
    """Scans a local directory, detects technologies, manifests and startup mechanism."""
    result = FolderAnalyzer.analyze(req.path)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.post("/api/projects/import", response_model=ProjectInfo)
async def import_existing_project(req: ProjectImportRequest):
    """Imports an existing folder as a StackStudio project with detected technologies and configs."""
    import re
    from pathlib import Path
    from datetime import datetime

    target_path = Path(req.path).resolve()
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Diretório '{req.path}' não encontrado ou inválido.")

    project_id = re.sub(r'[^a-zA-Z0-9_-]', '-', req.name.lower().strip())
    existing = ProjectStore.get_project(project_id)
    if existing:
        project_id = f"{project_id}-{int(datetime.now().timestamp())}"

    # Optionally write suggested docker-compose.yml if requested and missing
    compose_file = target_path / "docker-compose.yml"
    compose_file_alt = target_path / "compose.yaml"
    if req.auto_create_compose and req.compose_content and not compose_file.exists() and not compose_file_alt.exists():
        with open(compose_file, "w", encoding="utf-8") as f:
            f.write(req.compose_content)

    # Check if VS Code Web config should be set up
    if req.auto_install_extensions:
        try:
            tmp_req = ProjectCreateRequest(
                name=req.name,
                path=str(target_path),
                tools=req.tools or ["vscode_web"],
                custom_vscode_extensions=req.custom_vscode_extensions,
                auto_install_extensions=req.auto_install_extensions
            )
            scaff = ProjectScaffolder(tmp_req)
            scaff._generate_vscode_files()
        except Exception:
            pass

    # Register into ProjectStore
    imported_project = ProjectStore.register_project(
        project_id=project_id,
        name=req.name,
        path=str(target_path),
        description=req.description or f"Projeto importado de {target_path.name}",
        tools=req.tools,
        include_templates=req.include_templates,
        auto_install_extensions=req.auto_install_extensions,
        custom_vscode_extensions=req.custom_vscode_extensions
    )

    # Asynchronously enrich container status and update cache
    asyncio.create_task(enrich_and_cache_projects())

    return imported_project


@app.put("/api/projects/{project_id}", response_model=ProjectInfo)
async def update_project(project_id: str, update_req: ProjectUpdateRequest):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not update_req.tools:
        raise HTTPException(status_code=400, detail="At least one tool must remain in the project.")

    auto_ext = update_req.auto_install_extensions if update_req.auto_install_extensions is not None else proj.auto_install_extensions
    custom_exts = update_req.custom_vscode_extensions if update_req.custom_vscode_extensions is not None else proj.custom_vscode_extensions

    # Build create request to trigger re-scaffold with updated tools
    create_req = ProjectCreateRequest(
        name=proj.name,
        path=proj.path,
        description=update_req.description or proj.description,
        tools=update_req.tools,
        include_templates=proj.include_templates,
        default_user=update_req.default_user or "admin",
        default_password=update_req.default_password or "admin123",
        custom_ports=update_req.custom_ports,
        custom_envs=update_req.custom_envs,
        custom_folders=update_req.custom_folders,
        auto_install_extensions=auto_ext,
        custom_vscode_extensions=custom_exts
    )

    scaffolder = ProjectScaffolder(create_req)
    scaffolder.scaffold()

    updated_proj = ProjectStore.register_project(
        project_id=project_id,
        name=proj.name,
        path=proj.path,
        description=create_req.description,
        tools=list(scaffolder.tools),
        include_templates=proj.include_templates,
        auto_install_extensions=auto_ext,
        custom_vscode_extensions=custom_exts
    )
    return updated_proj


@app.get("/api/projects/{project_id}/graph")
async def get_project_topology_graph(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    # Asynchronously enrich with live Docker container health
    status_data = await DockerManager.get_project_status(proj.path)
    return TopologyGraphEngine.build_graph(proj.tools, status_data.get("containers", []))


@app.post("/api/graph/preview")
async def preview_topology_graph(payload: Dict[str, List[str]]):
    tools = payload.get("tools", [])
    return TopologyGraphEngine.build_graph(tools)


@app.post("/api/projects/{project_id}/start")
async def start_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.start_project(proj.path)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to start project")
    return {"message": "Project started successfully", "details": res}


@app.post("/api/projects/{project_id}/pause")
async def pause_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.pause_project(proj.path)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to pause project")
    return {"message": "Project paused successfully", "details": res}


@app.post("/api/projects/{project_id}/resume")
async def resume_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.resume_project(proj.path)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to resume project")
    return {"message": "Project resumed successfully", "details": res}


@app.post("/api/projects/{project_id}/stop")
async def stop_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.stop_project(proj.path)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to stop project")
    return {"message": "Project stopped successfully", "details": res}


@app.post("/api/projects/{project_id}/restart")
async def restart_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.restart_project(proj.path)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to restart project")
    return {"message": "Project restarted successfully", "details": res}


@app.post("/api/projects/{project_id}/services/{service_name}/start")
async def start_single_service(project_id: str, service_name: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    res = await DockerManager.start_service(proj.path, service_name)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to start service")
    return {"message": f"Service {service_name} started successfully", "details": res}


@app.post("/api/projects/{project_id}/services/{service_name}/stop")
async def stop_single_service(project_id: str, service_name: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    res = await DockerManager.stop_service(proj.path, service_name)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to stop service")
    return {"message": f"Service {service_name} stopped successfully", "details": res}


@app.post("/api/projects/{project_id}/services/{service_name}/restart")
async def restart_single_service(project_id: str, service_name: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    res = await DockerManager.restart_service(proj.path, service_name)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to restart service")
    return {"message": f"Service {service_name} restarted successfully", "details": res}


@app.post("/api/projects/{project_id}/services/{service_name}/exec")
async def exec_in_single_service(project_id: str, service_name: str, req: ContainerExecRequest):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    if not req.command or not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty.")

    res = await DockerManager.exec_in_container(
        proj.path,
        service_name,
        req.command.strip(),
        user=req.user,
        workdir=req.workdir
    )
    return res


@app.post("/api/custom-services/create", response_model=ToolPlugin)
async def create_custom_service(plugin: ToolPlugin):
    if not plugin.id or not plugin.name:
        raise HTTPException(status_code=400, detail="Service ID and Name are required.")
    
    # Normalize ID
    plugin.id = plugin.id.strip().lower().replace(" ", "_").replace("-", "_")
    
    # Save as ToolPlugin (which will auto-synthesize compose_services from source_type: image, dockerfile, github)
    saved = PluginManager.save_plugin(plugin)
    return saved


@app.get("/api/projects/{project_id}/manifests")
async def get_project_manifests(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    compose_path = os.path.join(proj.path, "docker-compose.yml")
    docker_compose_content = ""
    if os.path.exists(compose_path):
        with open(compose_path, "r", encoding="utf-8") as f:
            docker_compose_content = f.read()

    k8s_dir = os.path.join(proj.path, "k8s")
    k8s_files = {}
    if os.path.exists(k8s_dir) and os.path.isdir(k8s_dir):
        for root, _, files in os.walk(k8s_dir):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, proj.path).replace("\\", "/")
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            k8s_files[rel_path] = f.read()
                    except Exception:
                        pass

    cli_instructions = {
        "docker_compose_up": "docker compose up -d",
        "docker_compose_down": "docker compose down",
        "docker_compose_restart": "docker compose restart",
        "docker_service_start": "docker compose up -d <service>",
        "docker_service_restart": "docker compose restart <service>",
        "docker_service_logs": "docker compose logs -f <service>",
        "k8s_apply": "kubectl apply -k k8s/",
        "k8s_delete": "kubectl delete -k k8s/",
        "k8s_status": f"kubectl get all -n stack-{proj.name}"
    }

    return {
        "project_id": proj.id,
        "project_name": proj.name,
        "project_path": proj.path,
        "docker_compose": docker_compose_content,
        "k8s_files": k8s_files,
        "cli_instructions": cli_instructions
    }


@app.post("/api/projects/{project_id}/test")
async def test_project(project_id: str):
    import sys
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    test_file = os.path.join(proj.path, "tests", "test_services.py")
    if not os.path.exists(test_file):
        raise HTTPException(status_code=404, detail="test_services.py not found.")

    process = await asyncio.create_subprocess_exec(
        sys.executable, test_file,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    output = stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")
    return {
        "success": process.returncode == 0,
        "output": output
    }


from studio.services.k8s_manager import K8sManager


@app.post("/api/projects/{project_id}/k8s/deploy")
async def deploy_k8s_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await K8sManager.deploy_project(proj.path)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to deploy to Kubernetes")
    return {"message": "Project deployed to Kubernetes", "details": res}


@app.post("/api/projects/{project_id}/k8s/destroy")
async def destroy_k8s_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await K8sManager.destroy_project(proj.path)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to destroy Kubernetes resources")
    return {"message": "Kubernetes resources deleted", "details": res}


@app.get("/api/projects/{project_id}/k8s/status")
async def get_k8s_project_status(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    pods = await K8sManager.get_project_pods(proj.name)
    cluster_online = await K8sManager.is_cluster_available()
    return {
        "cluster_online": cluster_online,
        "namespace": f"stack-{proj.name}",
        "pods": pods
    }


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Stop containers before deleting registry
    await DockerManager.stop_project(proj.path)
    ProjectStore.delete_project(project_id)
    return {"message": "Project removed from registry"}


@app.get("/api/projects/{project_id}/logs")
async def stream_project_logs(project_id: str, service: Optional[str] = None, tail: int = 150):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    async def log_generator():
        svc_label = service if (service and service != "all") else "todos os serviços"
        yield f"data: [StackStudio SSE] Conectado ao fluxo de logs em tempo real ({svc_label})...\n\n"

        async for line in DockerManager.stream_logs(proj.path, service=service, tail=tail):
            clean_line = line.rstrip("\r\n")
            if clean_line:
                yield f"data: {clean_line}\n\n"

    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
