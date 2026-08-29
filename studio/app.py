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
from studio.models import ProjectCreateRequest, ProjectInfo, ToolCategory, ProjectPreset
from studio.services.catalog import CATEGORIES, PRESETS
from studio.services.scaffolder import ProjectScaffolder
from studio.services.project_store import ProjectStore
from studio.services.docker_manager import DockerManager

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
from studio.models import ToolPlugin


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


@app.get("/api/projects", response_model=List[ProjectInfo])
async def list_projects():
    projects = ProjectStore.list_projects()
    
    # Asynchronously enrich with live Docker status
    async def enrich_status(proj: ProjectInfo):
        try:
            status_data = await DockerManager.get_project_status(proj.path)
            proj.status = status_data["status"]
            proj.containers = status_data["containers"]
        except Exception:
            proj.status = "stopped"
        return proj

    enriched = await asyncio.gather(*[enrich_status(p) for p in projects])
    return enriched


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
        include_templates=request.include_templates
    )
    return proj


from studio.models import ProjectUpdateRequest
from studio.services.topology_graph import TopologyGraphEngine


@app.put("/api/projects/{project_id}", response_model=ProjectInfo)
async def update_project(project_id: str, update_req: ProjectUpdateRequest):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not update_req.tools:
        raise HTTPException(status_code=400, detail="At least one tool must remain in the project.")

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
        custom_folders=update_req.custom_folders
    )

    scaffolder = ProjectScaffolder(create_req)
    scaffolder.scaffold()

    updated_proj = ProjectStore.register_project(
        project_id=project_id,
        name=proj.name,
        path=proj.path,
        description=create_req.description,
        tools=list(scaffolder.tools),
        include_templates=proj.include_templates
    )
    return updated_proj


@app.get("/api/projects/{project_id}/graph")
async def get_project_topology_graph(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    return TopologyGraphEngine.build_graph(proj.tools)


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
async def stream_project_logs(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    async def log_generator():
        async for line in DockerManager.stream_logs(proj.path):
            yield f"data: {line.strip()}\n\n"

    return StreamingResponse(log_generator(), media_type="text/event-stream")
