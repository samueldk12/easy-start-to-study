"""
FastAPI Server & REST API for StackStudio
"""

import os
import sys
import asyncio
import time
import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=os.getenv("STUDIO_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("stackstudio")

# Fix Windows asyncio proactor pipe close ResourceWarning/ValueError on SSE client disconnect
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_del = _ProactorBasePipeTransport.__del__
        def _safe_del(self):
            try:
                _orig_del(self)
            except Exception:
                pass
        _ProactorBasePipeTransport.__del__ = _safe_del
    except Exception:
        pass
    try:
        from asyncio.base_subprocess import BaseSubprocessTransport
        _orig_sub_del = BaseSubprocessTransport.__del__
        def _safe_sub_del(self):
            try:
                _orig_sub_del(self)
            except Exception:
                pass
        BaseSubprocessTransport.__del__ = _safe_sub_del
    except Exception:
        pass
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from studio.models import (
    ProjectCreateRequest, ProjectInfo, ToolCategory, ProjectPreset, ToolPlugin,
    ContainerExecRequest, FolderAnalyzeRequest, ProjectImportRequest, ProjectUpdateRequest,
    ProjectMergeRequest, ProjectGovernanceRequest, VaultPasswordRequest, VaultChangePasswordRequest,
    CredentialCreateRequest, CredentialUpdateRequest, CredentialApplyRequest
)
from studio.services.credential_vault import (
    CredentialVault, VaultLockedError, VaultNotInitializedError, InvalidPasswordError
)
from studio.services.project_governance import ProjectGovernance
from studio.services.catalog import CATEGORIES, PRESETS
from studio.services.scaffolder import ProjectScaffolder
from studio.services.project_store import ProjectStore
from studio.services.docker_manager import DockerManager
from studio.services.folder_analyzer import FolderAnalyzer
from studio.services.topology_graph import TopologyGraphEngine
from studio.services.project_merger import ProjectMerger
from studio.services.state_tracker import StateTracker
from studio.services.network_inspector import NetworkInspector, is_port_bound

# Subprocess / IO safety limits
TEST_SUBPROCESS_TIMEOUT_S = float(os.getenv("STUDIO_TEST_TIMEOUT_S", "120"))
MAX_MANIFEST_FILES = 500
MAX_MANIFEST_FILE_BYTES = 2 * 1024 * 1024  # 2 MiB


async def _run_startup_tasks():
    """Startup tasks: reconcile crash state and warm up project cache."""
    try:
        reconcile_info = await StateTracker.reconcile_on_startup()
        logger.info(
            "Reconciled managed state: %d active, %d interrupted",
            len(reconcile_info.get('active_projects', [])),
            len(reconcile_info.get('interrupted_projects', [])),
        )
    except Exception:
        logger.exception("Error during startup reconciliation")

    # Warm up cache and perform initial background sync (defined later in module)
    asyncio.create_task(enrich_and_cache_projects())


@asynccontextmanager
async def lifespan(app):
    await _run_startup_tasks()
    yield


app = FastAPI(title="StackStudio API", description="Data & AI Stack Scaffolder and Orchestrator", version="1.0.0", lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info("%s %s -> %d (%.1fms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": app.version}


def _read_template_cached(path: str, _cache: Dict[str, str] = {}) -> str:
    """Reads a template file once per process; templates are static assets bundled with the app."""
    if path not in _cache:
        with open(path, "r", encoding="utf-8") as f:
            _cache[path] = f.read()
    return _cache[path]


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    index_file = os.path.join(BASE_DIR, "templates", "index.html")
    content = _read_template_cached(index_file)
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache"})


@app.get("/network", response_class=HTMLResponse)
@app.get("/containers", response_class=HTMLResponse)
@app.get("/topology", response_class=HTMLResponse)
async def serve_network_ui(request: Request):
    network_file = os.path.join(BASE_DIR, "templates", "network.html")
    content = _read_template_cached(network_file)
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache"})


@app.get("/api/network/overview")
async def get_network_overview():
    """Returns comprehensive stats, active containers, mapped ports, and inter-service connection topology."""
    return await NetworkInspector.get_full_overview()


@app.get("/api/network/containers")
async def get_network_containers():
    """Returns active running containers across all projects."""
    return await NetworkInspector.get_active_containers()


@app.get("/api/network/ports")
async def get_network_ports():
    """Returns all mapped host ports and protocols."""
    return await NetworkInspector.get_all_port_mappings()


@app.get("/api/network/topology")
async def get_network_topology_graph():
    """Returns global inter-service communication and dependency graph."""
    return await NetworkInspector.get_network_topology()


@app.get("/api/network/check-port/{port}")
async def check_port_in_use(port: int):
    """Checks if a given port is currently listening on localhost."""
    return {"port": port, "in_use": is_port_bound(port)}


class DirectExecRequest(BaseModel):
    container_id: str
    command: str
    user: Optional[str] = None


@app.post("/api/network/exec")
async def exec_in_network_container(req: DirectExecRequest):
    """Executes a command directly inside any active container."""
    if not req.container_id or not req.command.strip():
        raise HTTPException(status_code=400, detail="Container ID and command are required.")

    cmd_parts = ["docker", "exec", "-i"]
    if req.user:
        cmd_parts.extend(["-u", req.user])
    cmd_parts.extend([req.container_id, "/bin/sh", "-c", req.command.strip()])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


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



@app.get("/api/state/managed")
async def get_managed_state():
    """Returns currently tracked projects, uptimes, and interrupted projects after server restart."""
    return StateTracker.get_managed_state()


@app.get("/api/history")
async def get_action_history(project_id: Optional[str] = None, limit: int = 50):
    """Returns persistent chronological audit trail of all project operations."""
    return StateTracker.get_history(project_id=project_id, limit=limit)


@app.post("/api/state/restore-interrupted")
async def restore_interrupted_projects():
    """Restarts all projects that were active before server restart or crash."""
    managed_state = StateTracker.get_managed_state()
    interrupted = managed_state.get("interrupted_projects", [])
    restored = []
    failed = []

    for item in interrupted:
        pid = item["project_id"]
        path = item.get("path")
        if not path or not os.path.exists(path):
            proj = ProjectStore.get_project(pid)
            if proj:
                path = proj.path
        if path and os.path.exists(path):
            res = await DockerManager.start_project(path, project_id=pid, project_name=item.get("name"))
            if res.get("success"):
                restored.append(pid)
            else:
                failed.append({"project_id": pid, "error": res.get("stderr") or res.get("error")})

    # Trigger cache refresh after restoring
    asyncio.create_task(enrich_and_cache_projects())

    return {
        "restored": restored,
        "failed": failed,
        "total_attempted": len(interrupted)
    }


@app.get("/api/governance/summary")
async def get_governance_summary():
    """Returns governance summary with idle days, disk usage, and cleanup recommendations."""
    return await ProjectGovernance.get_governance_summary()


@app.post("/api/governance/{project_id}/cleanup")
async def cleanup_project_resources(project_id: str, remove_images: bool = True, remove_volumes: bool = False):
    """Cleans up Docker images and optionally volumes for a specific project."""
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    if proj.visual_status in ("green", "yellow"):
        raise HTTPException(status_code=400, detail="Não é possível limpar um projeto em execução. Pare-o primeiro.")
    
    res = await ProjectGovernance.cleanup_project(proj.path, remove_images=remove_images, remove_volumes=remove_volumes)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error") or res.get("stderr") or "Falha na limpeza")
    
    from studio.services.state_tracker import StateTracker
    StateTracker.record_action(
        project_id, "cleanup",
        status="success",
        details=f"Limpeza manual. Imagens: {'sim' if remove_images else 'não'}, Volumes: {'sim' if remove_volumes else 'não'}",
        project_name=proj.name,
        project_path=proj.path
    )
    return {"message": "Cleanup realizado com sucesso", "details": res}


@app.put("/api/governance/{project_id}/settings")
async def update_project_governance_settings(project_id: str, req: ProjectGovernanceRequest):
    """Updates governance settings for a specific project."""
    success = ProjectStore.update_project_governance(
        project_id,
        auto_cleanup_days=req.auto_cleanup_days,
        clean_images=req.clean_images_on_idle,
        clean_volumes=req.clean_volumes_on_idle
    )
    if not success:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"message": "Governance settings updated", "project_id": project_id}


@app.post("/api/governance/auto-cleanup")
async def run_auto_cleanup():
    """Runs automatic cleanup on all projects exceeding their idle threshold."""
    result = await ProjectGovernance.auto_cleanup_check()
    return result


# =============================================================================
# CREDENTIAL VAULT — encrypted local storage for generic & cloud credentials.
# Locked by default on every server start; unlocked in-memory only for the
# lifetime of this process once the master password is supplied.
# =============================================================================

@app.get("/api/vault/status")
async def get_vault_status():
    return CredentialVault.status()


@app.get("/api/vault/providers")
async def get_vault_providers():
    return CredentialVault.get_providers()


@app.post("/api/vault/setup")
async def setup_vault(req: VaultPasswordRequest):
    try:
        return CredentialVault.setup(req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/vault/unlock")
async def unlock_vault(req: VaultPasswordRequest):
    try:
        return CredentialVault.unlock(req.password)
    except VaultNotInitializedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidPasswordError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/vault/lock")
async def lock_vault():
    CredentialVault.lock()
    return CredentialVault.status()


@app.post("/api/vault/change-password")
async def change_vault_password(req: VaultChangePasswordRequest):
    try:
        return CredentialVault.change_password(req.old_password, req.new_password)
    except VaultNotInitializedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidPasswordError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/vault/credentials")
async def list_vault_credentials():
    return CredentialVault.list_credentials()


@app.post("/api/vault/credentials")
async def create_vault_credential(req: CredentialCreateRequest):
    try:
        return CredentialVault.create_credential(req.name, req.type, req.data, req.notes or "")
    except VaultLockedError as e:
        raise HTTPException(status_code=423, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/vault/credentials/{credential_id}")
async def update_vault_credential(credential_id: str, req: CredentialUpdateRequest):
    try:
        return CredentialVault.update_credential(credential_id, req.name, req.data, req.notes)
    except VaultLockedError as e:
        raise HTTPException(status_code=423, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/vault/credentials/{credential_id}")
async def delete_vault_credential(credential_id: str):
    try:
        deleted = CredentialVault.delete_credential(credential_id)
    except VaultLockedError as e:
        raise HTTPException(status_code=423, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Credencial não encontrada.")
    return {"message": "Credencial removida do cofre."}


@app.post("/api/vault/credentials/{credential_id}/reveal")
async def reveal_vault_credential(credential_id: str):
    """Decrypts and returns one credential's secret fields. Requires the vault to be unlocked."""
    try:
        return CredentialVault.reveal_credential(credential_id)
    except VaultLockedError as e:
        raise HTTPException(status_code=423, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/vault/credentials/{credential_id}/apply")
async def apply_vault_credential(credential_id: str, req: CredentialApplyRequest):
    """Decrypts a credential and writes it into the target project's .env (and, for
    blob-type secrets like a GCP service account or an SSH key, a gitignored .secrets/ file)."""
    proj = ProjectStore.get_project(req.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        result = CredentialVault.apply_to_project(credential_id, proj.path)
    except VaultLockedError as e:
        raise HTTPException(status_code=423, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"Credencial aplicada ao projeto '{proj.name}' com sucesso.", **result}


_ENRICH_LOCK = asyncio.Lock()
_LAST_ENRICH_TIMESTAMP: float = 0.0


async def enrich_and_cache_projects() -> List[ProjectInfo]:
    global _LAST_ENRICH_TIMESTAMP
    cached_existing = ProjectStore.load_cache()

    # If another enrichment task is already running, avoid queueing duplicate Docker CLI calls
    if _ENRICH_LOCK.locked():
        if cached_existing:
            return cached_existing
        async with _ENRICH_LOCK:
            return ProjectStore.load_cache() or ProjectStore.list_projects()

    async with _ENRICH_LOCK:
        now = time.time()
        # Throttle: if updated less than 1.5s ago, reuse memory/JSON cache
        if cached_existing and (now - _LAST_ENRICH_TIMESTAMP) < 1.5:
            return cached_existing

        projects = ProjectStore.list_projects()
        
        # 1. Ultra-fast single docker call batch inspection (< 1-2s for all projects)
        batch_status = await DockerManager.get_all_projects_status_batch(projects)
        
        # If Docker CLI timed out or had a transient glitch, NEVER wipe out existing online status!
        if batch_status is None:
            return cached_existing if cached_existing else projects

        from studio.services.project_governance import ProjectGovernance

        for proj in projects:
            st = batch_status.get(proj.id) or {"status": "stopped", "visual_status": "orange", "containers": []}
            proj.status = st["status"]
            proj.visual_status = st.get("visual_status", "orange")
            proj.containers = st["containers"]
            
            # Recalculate dynamic UI links with current compose & live ports
            proj.ui_links = ProjectStore.extract_ui_links(
                proj.path,
                tools=proj.tools,
                containers=proj.containers,
                is_merged=proj.is_merged_workspace
            )

            # Calculate idle days for governance
            try:
                proj.idle_days = ProjectGovernance.calculate_idle_days(proj.id)
                if proj.visual_status in ("green", "yellow"):
                    ProjectStore.touch_last_used(proj.id)
                    proj.idle_days = 0
            except Exception:
                proj.idle_days = 0

            # Detached auto-retry for crashed/unhealthy containers
            if proj.visual_status == "red":
                try:
                    asyncio.create_task(DockerManager.auto_retry_crashed_containers(proj.path))
                except Exception:
                    pass

        # Persist the full project list with live status to projects_cache.json
        ProjectStore.save_cache(projects)
        _LAST_ENRICH_TIMESTAMP = time.time()
        return projects


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


@app.get("/api/stats")
async def get_system_stats():
    projects = ProjectStore.load_cache() or ProjectStore.list_projects()
    total = len(projects)
    running = sum(1 for p in projects if p.status == "running")
    stopped = sum(1 for p in projects if p.status == "stopped")
    degraded = sum(1 for p in projects if p.status == "degraded")
    catalog = fetch_catalog()
    total_tools = sum(len(c.tools) for c in catalog)
    return {
        "total_projects": total,
        "running_projects": running,
        "stopped_projects": stopped,
        "degraded_projects": degraded,
        "total_catalog_tools": total_tools,
        "total_categories": len(catalog),
        "total_presets": len(PRESETS)
    }


@app.post("/api/projects/sync", response_model=List[ProjectInfo])
async def sync_projects_now():
    return await enrich_and_cache_projects()



@app.post("/api/projects", response_model=ProjectInfo)
async def create_project(request: ProjectCreateRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required.")
    if not request.tools:
        raise HTTPException(status_code=400, detail="At least one tool must be selected.")

    scaffolder = ProjectScaffolder(request)
    scaffolder.scaffold()
    project_dir = scaffolder.project_dir

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

    # Ensure all volume host folders declared in docker-compose.yml exist on disk
    try:
        FolderAnalyzer.ensure_volume_folders(target_path)
    except Exception:
        pass

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


@app.post("/api/projects/merge", response_model=ProjectInfo)
async def merge_projects(req: ProjectMergeRequest):
    """
    Combines multiple existing projects into a unified multi-root workspace stack.
    Generates workspace.code-workspace mounting all subproject folders,
    and a unified docker-compose file with connected bridge networking.
    """
    if len(req.project_ids) < 2:
        raise HTTPException(status_code=400, detail="Selecione pelo menos 2 projetos para unificar.")

    try:
        merged_info = ProjectMerger.merge_projects(
            name=req.name,
            project_ids=req.project_ids,
            description=req.description
        )
        asyncio.create_task(enrich_and_cache_projects())
        return merged_info
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao mesclar projetos: {str(e)}")


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

    res = await DockerManager.start_project(proj.path, project_id=proj.id, project_name=proj.name)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to start project")
    return {"message": "Project started successfully", "details": res}


@app.post("/api/projects/{project_id}/pause")
async def pause_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.pause_project(proj.path, project_id=proj.id)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to pause project")
    return {"message": "Project paused successfully", "details": res}


@app.post("/api/projects/{project_id}/resume")
async def resume_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.resume_project(proj.path, project_id=proj.id)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to resume project")
    return {"message": "Project resumed successfully", "details": res}


@app.post("/api/projects/{project_id}/stop")
async def stop_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.stop_project(proj.path, project_id=proj.id)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to stop project")
    return {"message": "Project stopped successfully", "details": res}


@app.post("/api/projects/{project_id}/restart")
async def restart_project(project_id: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    res = await DockerManager.restart_project(proj.path, project_id=proj.id)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to restart project")
    return {"message": "Project restarted successfully", "details": res}


@app.post("/api/projects/{project_id}/services/{service_name}/start")
async def start_single_service(project_id: str, service_name: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    res = await DockerManager.start_service(proj.path, service_name, project_id=proj.id)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to start service")
    return {"message": f"Service {service_name} started successfully", "details": res}


@app.post("/api/projects/{project_id}/services/{service_name}/stop")
async def stop_single_service(project_id: str, service_name: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    res = await DockerManager.stop_service(proj.path, service_name, project_id=proj.id)
    if not res["success"]:
        raise HTTPException(status_code=500, detail=res.get("stderr") or res.get("error") or "Failed to stop service")
    return {"message": f"Service {service_name} stopped successfully", "details": res}


@app.post("/api/projects/{project_id}/services/{service_name}/restart")
async def restart_single_service(project_id: str, service_name: str):
    proj = ProjectStore.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    res = await DockerManager.restart_service(proj.path, service_name, project_id=proj.id)
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
                if len(k8s_files) >= MAX_MANIFEST_FILES:
                    break
                if file.endswith((".yaml", ".yml")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, proj.path).replace("\\", "/")
                    try:
                        if os.path.getsize(full_path) > MAX_MANIFEST_FILE_BYTES:
                            k8s_files[rel_path] = f"# skipped: file exceeds {MAX_MANIFEST_FILE_BYTES} bytes"
                            continue
                        with open(full_path, "r", encoding="utf-8") as f:
                            k8s_files[rel_path] = f.read()
                    except Exception:
                        logger.warning("Failed to read manifest %s", full_path, exc_info=True)

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
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=TEST_SUBPROCESS_TIMEOUT_S)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        logger.warning("Project test run timed out project_id=%s timeout=%ss", project_id, TEST_SUBPROCESS_TIMEOUT_S)
        return {
            "success": False,
            "output": f"Test run timed out after {TEST_SUBPROCESS_TIMEOUT_S}s and was killed."
        }
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
