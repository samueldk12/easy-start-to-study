import asyncio
import os
import sys
import subprocess
import json
import time
import socket
import re
from typing import List, Dict, Any, AsyncGenerator, Optional, Tuple
from studio.models import ContainerInfo


def is_port_in_use(port: int) -> bool:
    """Checks if a TCP port is currently bound on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False


def find_next_free_port(start_port: int, max_attempts: int = 100) -> int:
    """Finds the next available free TCP port on localhost."""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    return start_port


class DockerManager:
    _RETRY_TRACKER: Dict[str, int] = {}
    _MAX_RETRIES: int = 5
    _LAST_KNOWN_STATE: Dict[str, Tuple[str, str, str]] = {}
    _STATUS_CHANGE_TIMES: Dict[str, float] = {}

    @staticmethod
    def _replace_port_in_compose(project_dir: str, old_port: int, new_port: int) -> bool:
        """Safely updates a conflicting host port mapping and external host env references in the project compose file."""
        candidates = ["docker-compose.yml", "docker-compose.yaml", "compose.yaml"]
        replaced = False
        for fname in candidates:
            cpath = os.path.join(project_dir, fname)
            if os.path.exists(cpath):
                try:
                    with open(cpath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    # 1. Replace only host port in port mappings like "- 8080:80", "- '8080:80'", "- "8080:80""
                    new_content = re.sub(
                        rf'(-\s*["\']?){old_port}(:[\d]+["\']?)',
                        rf'\g<1>{new_port}\g<2>',
                        content
                    )

                    # 2. Replace Kafka / Service specific advertised host ports
                    new_content = re.sub(
                        rf'(PLAINTEXT_HOST://(?:localhost|127\.0\.0\.1|0\.0\.0\.0):){old_port}\b',
                        rf'\g<1>{new_port}',
                        new_content
                    )

                    if new_content != content:
                        with open(cpath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        replaced = True
                except Exception:
                    pass
        return replaced

    @staticmethod
    async def run_command(project_dir: str, cmd: List[str], timeout: float = 180.0) -> Dict[str, Any]:
        """Runs a docker compose command in the project directory with a safety timeout."""
        if not os.path.exists(project_dir):
            return {"success": False, "error": f"Directory not found: {project_dir}"}

        full_cmd = ["docker", "compose"] + cmd
        try:
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                try:
                    if sys.platform == "win32":
                        subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, capture_output=True)
                    else:
                        process.kill()
                except Exception:
                    pass
                return {"success": False, "error": f"Command timed out after {timeout}s: {' '.join(full_cmd)}"}

            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def start_project(project_dir: str, project_id: Optional[str] = None, project_name: Optional[str] = None) -> Dict[str, Any]:
        pid = project_id or os.path.basename(project_dir)
        pname = project_name or pid
        from studio.services.state_tracker import StateTracker

        res = await DockerManager.run_command(project_dir, ["up", "-d", "--build"], timeout=180.0)
        
        # Automatic Port Conflict Detection and Auto-Recovery (up to 5 consecutive collisions)
        max_conflict_retries = 5
        while not res.get("success", False) and max_conflict_retries > 0:
            err_text = (res.get("stderr", "") + " " + res.get("stdout", "") + " " + str(res.get("error", ""))).lower()
            if "port is already allocated" in err_text or "address already in use" in err_text:
                raw_err = res.get("stderr", "") + " " + res.get("stdout", "")
                # Find conflicting port, e.g. "Bind for 0.0.0.0:8443 failed: port is already allocated"
                match = re.search(r"Bind for [^:]+:(\d+) failed", raw_err) or re.search(r":(\d+) failed: port is already allocated", raw_err)
                if match:
                    clash_port = int(match.group(1))
                    free_port = find_next_free_port(clash_port + 1)
                    if DockerManager._replace_port_in_compose(project_dir, clash_port, free_port):
                        max_conflict_retries -= 1
                        res = await DockerManager.run_command(project_dir, ["up", "-d", "--build"], timeout=180.0)
                        continue
            break

        status = "success" if res.get("success") else "failed"
        details = "Containers iniciados com sucesso" if res.get("success") else (res.get("stderr") or res.get("error") or "Falha ao iniciar")
        StateTracker.record_action(pid, "start", status=status, details=details, project_name=pname, project_path=project_dir)
        return res

    @staticmethod
    async def pause_project(project_dir: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        pid = project_id or os.path.basename(project_dir)
        from studio.services.state_tracker import StateTracker
        res = await DockerManager.run_command(project_dir, ["stop"])
        status = "success" if res.get("success") else "failed"
        StateTracker.record_action(pid, "pause", status=status, details="Containers pausados", project_path=project_dir)
        return res

    @staticmethod
    async def resume_project(project_dir: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        pid = project_id or os.path.basename(project_dir)
        from studio.services.state_tracker import StateTracker
        res = await DockerManager.run_command(project_dir, ["start"])
        status = "success" if res.get("success") else "failed"
        StateTracker.record_action(pid, "resume", status=status, details="Containers retomados", project_path=project_dir)
        return res

    @staticmethod
    async def stop_project(project_dir: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        pid = project_id or os.path.basename(project_dir)
        from studio.services.state_tracker import StateTracker
        res = await DockerManager.run_command(project_dir, ["down"], timeout=60.0)
        status = "success" if res.get("success") else "failed"
        StateTracker.record_action(pid, "stop", status=status, details="Containers parados e rede liberada", project_path=project_dir)
        return res

    @staticmethod
    async def restart_project(project_dir: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        pid = project_id or os.path.basename(project_dir)
        from studio.services.state_tracker import StateTracker
        res = await DockerManager.run_command(project_dir, ["restart"], timeout=120.0)
        status = "success" if res.get("success") else "failed"
        StateTracker.record_action(pid, "restart", status=status, details="Containers reiniciados", project_path=project_dir)
        return res

    @staticmethod
    async def start_service(project_dir: str, service: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Starts or recreates an individual service with automatic port collision recovery."""
        pid = project_id or os.path.basename(project_dir)
        from studio.services.state_tracker import StateTracker
        res = await DockerManager.run_command(project_dir, ["up", "-d", service], timeout=120.0)

        # Automatic Port Conflict Detection and Auto-Recovery
        max_conflict_retries = 5
        while not res.get("success", False) and max_conflict_retries > 0:
            err_text = (res.get("stderr", "") + " " + res.get("stdout", "") + " " + str(res.get("error", ""))).lower()
            if "port is already allocated" in err_text or "address already in use" in err_text:
                raw_err = res.get("stderr", "") + " " + res.get("stdout", "")
                match = re.search(r"Bind for [^:]+:(\d+) failed", raw_err) or re.search(r":(\d+) failed: port is already allocated", raw_err)
                if match:
                    clash_port = int(match.group(1))
                    free_port = find_next_free_port(clash_port + 1)
                    if DockerManager._replace_port_in_compose(project_dir, clash_port, free_port):
                        max_conflict_retries -= 1
                        res = await DockerManager.run_command(project_dir, ["up", "-d", service], timeout=120.0)
                        continue
            break

        status = "success" if res.get("success") else "failed"
        details = f"Serviço {service} iniciado" if res.get("success") else (res.get("stderr") or res.get("error") or f"Falha ao iniciar {service}")
        StateTracker.record_action(pid, f"start_service_{service}", status=status, details=details, project_path=project_dir)
        return res

    @staticmethod
    async def stop_service(project_dir: str, service: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Stops an individual service container."""
        pid = project_id or os.path.basename(project_dir)
        from studio.services.state_tracker import StateTracker
        res = await DockerManager.run_command(project_dir, ["stop", service])
        status = "success" if res.get("success") else "failed"
        StateTracker.record_action(pid, f"stop_service_{service}", status=status, details=f"Serviço {service} parado", project_path=project_dir)
        return res

    @staticmethod
    async def restart_service(project_dir: str, service: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Restarts an individual service container."""
        pid = project_id or os.path.basename(project_dir)
        from studio.services.state_tracker import StateTracker
        res = await DockerManager.run_command(project_dir, ["restart", service])
        status = "success" if res.get("success") else "failed"
        StateTracker.record_action(pid, f"restart_service_{service}", status=status, details=f"Serviço {service} reiniciado", project_path=project_dir)
        return res

    @staticmethod
    async def get_service_logs(project_dir: str, service: str, tail: int = 150) -> Dict[str, Any]:
        """Retrieves non-blocking tail logs for a specific service."""
        return await DockerManager.run_command(project_dir, ["logs", f"--tail={tail}", service])

    @staticmethod
    async def exec_in_container(project_dir: str, service: str, cmd: str, user: Optional[str] = None, workdir: Optional[str] = None) -> Dict[str, Any]:
        """Executes a command inside a specific running container via docker compose exec (or fallback to docker exec)."""
        start_time = time.time()
        
        # 1. Try via docker compose exec
        args = ["docker", "compose", "exec", "-T"]
        if user:
            args.extend(["-u", user])
        if workdir:
            args.extend(["-w", workdir])
        args.append(service)
        args.extend(["/bin/sh", "-c", cmd])

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            latency = (time.time() - start_time) * 1000
            
            # If sh failed because container doesn't have /bin/sh (e.g. scratch) or service name mismatch, try /bin/bash or direct container name
            if process.returncode != 0 and "no such service" in stderr.decode("utf-8", errors="replace").lower():
                # Fallback directly to docker exec
                direct_args = ["docker", "exec", "-i"]
                if user: direct_args.extend(["-u", user])
                if workdir: direct_args.extend(["-w", workdir])
                direct_args.extend([service, "/bin/sh", "-c", cmd])
                
                direct_proc = await asyncio.create_subprocess_exec(
                    *direct_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                d_stdout, d_stderr = await direct_proc.communicate()
                latency = (time.time() - start_time) * 1000
                return {
                    "success": direct_proc.returncode == 0,
                    "returncode": direct_proc.returncode,
                    "stdout": d_stdout.decode("utf-8", errors="replace"),
                    "stderr": d_stderr.decode("utf-8", errors="replace"),
                    "latency_ms": round(latency, 2)
                }

            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }



    @staticmethod
    def _parse_container_item(item: Dict[str, Any]) -> ContainerInfo:
        name = item.get("Name") or item.get("ID") or "unknown"
        service = item.get("Service") or item.get("Name") or ""
        state_raw = (item.get("State") or "").lower()
        status_raw = item.get("Status") or ""
        health_raw = (item.get("Health") or "").lower()
        exit_code = item.get("ExitCode") if item.get("ExitCode") is not None else 0

        # Parse Ports (handles list of dicts from Publishers or string from Ports)
        ports_str = ""
        publishers = item.get("Publishers")
        if isinstance(publishers, list) and publishers:
            ports_list = []
            for p in publishers:
                if isinstance(p, dict):
                    pub = p.get("PublishedPort")
                    tgt = p.get("TargetPort")
                    proto = p.get("Protocol", "tcp")
                    if pub and tgt:
                        ports_list.append(f"{pub}->{tgt}/{proto}")
                    elif tgt:
                        ports_list.append(f"{tgt}/{proto}")
            ports_str = ", ".join(ports_list)
        elif isinstance(item.get("Ports"), str):
            ports_str = item.get("Ports")
        elif publishers is not None:
            ports_str = str(publishers)

        # Check if container is an initialization / migration / oneshot task
        oneshot_keywords = ("init", "migrate", "migration", "seed", "setup", "bootstrap", "oneshot", "job")
        is_oneshot = any(k in service.lower() or k in name.lower() for k in oneshot_keywords)

        # Evaluate Visual Status:
        # 1. Paused containers are ALWAYS orange and paused (never red!)
        if state_raw == "paused" or "paused" in status_raw.lower():
            visual_status = "orange"
            state_raw = "paused"
        # 2. Oneshot / Init container that executed and exited with code 0 is GREEN and CREATED
        elif state_raw in ("exited", "stopped") and exit_code == 0 and is_oneshot:
            visual_status = "green"
            state_raw = "created"
            if "exited (0)" in status_raw.lower() or status_raw.lower() in ("exited", "stopped", ""):
                status_raw = "Created (0)"
        # 3. Intentionally stopped regular service (exit code 0, 137 [SIGKILL], 143 [SIGTERM]) is orange
        elif state_raw in ("exited", "stopped") and exit_code in (0, 137, 143):
            visual_status = "orange"
        # 4. Crashed, Dead, non-graceful Exit, or Unhealthy running container
        elif state_raw in ("dead", "crashed", "error") or (state_raw in ("exited", "stopped") and exit_code not in (0, 137, 143)) or (state_raw == "running" and health_raw == "unhealthy"):
            visual_status = "red"
        # 5. Starting, Restarting, Created (or oneshot task currently executing)
        elif state_raw in ("starting", "restarting", "created") or health_raw == "starting" or "health: starting" in status_raw.lower() or (is_oneshot and state_raw == "running"):
            visual_status = "yellow"
        # 6. Running & Healthy regular service
        elif state_raw == "running":
            visual_status = "green"
        else:
            visual_status = "orange"

        # Track state transition timestamp for real-time sorting
        current_signature = (state_raw, status_raw, visual_status)
        last_signature = DockerManager._LAST_KNOWN_STATE.get(name)
        if last_signature is None or last_signature != current_signature:
            DockerManager._LAST_KNOWN_STATE[name] = current_signature
            DockerManager._STATUS_CHANGE_TIMES[name] = time.time()

        last_changed = DockerManager._STATUS_CHANGE_TIMES.get(name, 0.0)
        retry_count = DockerManager._RETRY_TRACKER.get(name, 0)

        cid = item.get("ID") or item.get("Id")
        return ContainerInfo(
            id=cid,
            name=name,
            service=service,
            state=state_raw,
            status=status_raw,
            health=health_raw or None,
            exit_code=exit_code,
            ports=ports_str,
            retry_count=retry_count,
            is_oneshot=is_oneshot,
            visual_status=visual_status,
            last_changed=last_changed
        )

    @staticmethod
    async def get_project_status(project_dir: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Inspects containers status using docker compose ps -a --format json."""
        res = await DockerManager.run_command(project_dir, ["ps", "-a", "--format", "json"], timeout=6.0)
        if not res["success"]:
            return {"status": "stopped", "visual_status": "orange", "containers": []}

        output = res["stdout"].strip()
        if not output:
            return {"status": "stopped", "visual_status": "orange", "containers": []}

        containers: List[ContainerInfo] = []
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, list):
                    for item in data:
                        containers.append(DockerManager._parse_container_item(item))
                else:
                    containers.append(DockerManager._parse_container_item(data))
            except Exception:
                continue

        # Record container IDs in persistent StateTracker
        if containers:
            cids = [c.id for c in containers if c.id]
            if cids:
                pid = project_id or os.path.basename(project_dir)
                try:
                    from studio.services.state_tracker import StateTracker
                    StateTracker.record_containers_for_project(pid, cids)
                except Exception:
                    pass

        has_red = False
        has_yellow = False
        has_green = False
        has_blue = False
        has_orange = False
        has_paused = False

        for c in containers:
            if c.state == "paused" or "paused" in c.status.lower():
                has_paused = True
            if c.visual_status == "red":
                has_red = True
            elif c.visual_status == "yellow":
                has_yellow = True
            elif c.visual_status == "green":
                has_green = True
            elif c.visual_status == "blue":
                has_blue = True
            elif c.visual_status == "orange":
                has_orange = True

        if not containers:
            status = "stopped"
            visual_status = "orange"
        elif has_paused:
            status = "paused"
            visual_status = "orange"
        elif has_red:
            status = "error"
            visual_status = "red"
        elif has_yellow:
            status = "starting"
            visual_status = "yellow"
        elif (has_green or has_blue) and not has_orange:
            status = "running"
            visual_status = "green"
        elif has_green and has_orange:
            status = "partial"
            visual_status = "yellow"
        else:
            status = "stopped"
            visual_status = "orange"

        # Sort containers: red (errors) > yellow (starting) > green (running) > blue (concluído) > orange (stopped)
        severity_map = {"red": 0, "yellow": 1, "green": 2, "blue": 3, "orange": 4}
        containers.sort(key=lambda c: (-c.last_changed, severity_map.get(c.visual_status, 4), c.service))

        return {"status": status, "visual_status": visual_status, "containers": containers}

    @staticmethod
    async def get_all_projects_status_batch(projects: List[Any]) -> Dict[str, Dict[str, Any]]:
        """
        Executes a single ultra-fast docker ps -a call across the entire system (1-2s)
        and resolves status, containers, and visual status for all managed projects in memory.
        """
        result: Dict[str, Dict[str, Any]] = {}
        for p in projects:
            pid = getattr(p, "id", None) or (p.get("id") if isinstance(p, dict) else "")
            result[pid] = {"status": "stopped", "visual_status": "orange", "containers": []}

        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "ps", "-a", "--format", "{{json .}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30.0)
            if process.returncode != 0:
                return None

            output = stdout.decode("utf-8", errors="replace").strip()
            if not output:
                return result

            lines = output.splitlines()
            project_containers_map: Dict[str, List[ContainerInfo]] = {}

            proj_by_dir: Dict[str, str] = {}
            proj_by_id: Dict[str, str] = {}
            proj_by_name: Dict[str, str] = {}
            for p in projects:
                pid = getattr(p, "id", None) or (p.get("id") if isinstance(p, dict) else "")
                pdir = getattr(p, "path", None) or (p.get("path") if isinstance(p, dict) else "")
                pname = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else "")
                if pid:
                    proj_by_id[str(pid).lower()] = pid
                    proj_by_id[str(pid).lower().replace("-", "_")] = pid
                    proj_by_id[str(pid).lower().replace("_", "-")] = pid
                if pdir:
                    proj_by_dir[os.path.abspath(str(pdir)).lower()] = pid
                    proj_by_dir[os.path.normpath(str(pdir)).lower()] = pid
                    proj_by_dir[os.path.basename(str(pdir)).lower()] = pid
                if pname:
                    proj_by_name[str(pname).lower()] = pid
                    proj_by_name[str(pname).lower().replace("-", "_")] = pid
                    proj_by_name[str(pname).lower().replace("_", "-")] = pid

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    c_name = raw.get("Names", "")
                    c_labels = raw.get("Labels", "")
                    
                    matched_pid = None
                    m_proj = re.search(r"com\.docker\.compose\.project=([^,]+)", c_labels)
                    m_dir = re.search(r"com\.docker\.compose\.project\.working_dir=([^,]+)", c_labels)
                    m_svc = re.search(r"com\.docker\.compose\.service=([^,]+)", c_labels)

                    compose_proj = m_proj.group(1).strip() if m_proj else None
                    compose_workdir = m_dir.group(1).strip() if m_dir else None
                    compose_svc = m_svc.group(1).strip() if m_svc else c_name

                    # 1. Match by compose working dir (most exact)
                    if compose_workdir:
                        norm_workdir = os.path.normpath(compose_workdir).lower()
                        abs_workdir = os.path.abspath(compose_workdir).lower()
                        if abs_workdir in proj_by_dir:
                            matched_pid = proj_by_dir[abs_workdir]
                        elif norm_workdir in proj_by_dir:
                            matched_pid = proj_by_dir[norm_workdir]

                    # 2. Match by compose project label
                    if not matched_pid and compose_proj:
                        c_proj_low = compose_proj.lower()
                        if c_proj_low in proj_by_id:
                            matched_pid = proj_by_id[c_proj_low]
                        elif c_proj_low in proj_by_dir:
                            matched_pid = proj_by_dir[c_proj_low]
                        elif c_proj_low in proj_by_name:
                            matched_pid = proj_by_name[c_proj_low]

                    # 3. Fallback match by container name prefix
                    if not matched_pid:
                        c_low = c_name.lower()
                        for p_key, pid in proj_by_id.items():
                            if c_low.startswith(p_key + "-") or c_low.startswith(p_key + "_"):
                                matched_pid = pid
                                break

                    if matched_pid:
                        item_formatted = {
                            "ID": raw.get("ID"),
                            "Name": c_name,
                            "Service": compose_svc,
                            "State": raw.get("State"),
                            "Status": raw.get("Status"),
                            "Health": "healthy" if "(healthy)" in raw.get("Status", "").lower() else ("unhealthy" if "(unhealthy)" in raw.get("Status", "").lower() else ("starting" if "starting" in raw.get("Status", "").lower() else "")),
                            "Ports": raw.get("Ports", ""),
                            "ExitCode": 0 if "exited (0)" in raw.get("Status", "").lower() else (1 if "exited (" in raw.get("Status", "").lower() else 0)
                        }
                        c_info = DockerManager._parse_container_item(item_formatted)
                        project_containers_map.setdefault(matched_pid, []).append(c_info)
                except Exception:
                    continue

            severity_map = {"red": 0, "yellow": 1, "green": 2, "blue": 3, "orange": 4}

            for p in projects:
                pid = getattr(p, "id", None) or (p.get("id") if isinstance(p, dict) else "")
                containers = project_containers_map.get(pid, [])
                
                has_red = False
                has_yellow = False
                has_green = False
                has_blue = False
                has_orange = False
                has_paused = False

                for c in containers:
                    if c.state == "paused" or "paused" in c.status.lower():
                        has_paused = True
                    if c.visual_status == "red":
                        has_red = True
                    elif c.visual_status == "yellow":
                        has_yellow = True
                    elif c.visual_status == "green":
                        has_green = True
                    elif c.visual_status == "blue":
                        has_blue = True
                    elif c.visual_status == "orange":
                        has_orange = True

                if not containers:
                    status = "stopped"
                    visual_status = "orange"
                elif has_paused:
                    status = "paused"
                    visual_status = "orange"
                elif has_red:
                    status = "error"
                    visual_status = "red"
                elif has_yellow:
                    status = "starting"
                    visual_status = "yellow"
                elif (has_green or has_blue) and not has_orange:
                    status = "running"
                    visual_status = "green"
                elif has_green and has_orange:
                    status = "partial"
                    visual_status = "yellow"
                else:
                    status = "stopped"
                    visual_status = "orange"

                containers.sort(key=lambda c: (-c.last_changed, severity_map.get(c.visual_status, 4), c.service))
                result[pid] = {
                    "status": status,
                    "visual_status": visual_status,
                    "containers": containers
                }

            return result
        except asyncio.TimeoutError:
            try:
                if sys.platform == "win32":
                    subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, capture_output=True)
                else:
                    process.kill()
            except Exception:
                pass
            return None
        except Exception:
            return None

    @staticmethod
    async def auto_retry_crashed_containers(project_dir: str) -> List[str]:
        """Automatically detects and retries/restarts crashed or unhealthy containers.
        NEVER restarts paused or intentionally stopped containers!
        """
        status_data = await DockerManager.get_project_status(project_dir)
        # If the project as a whole is paused or stopped, do not auto-retry!
        if status_data.get("status") in ("paused", "stopped"):
            return []

        restarted = []
        for c in status_data["containers"]:
            # NEVER restart paused containers
            if c.state == "paused" or "paused" in c.status.lower():
                continue
            if c.visual_status == "red":
                current_retries = DockerManager._RETRY_TRACKER.get(c.name, 0)
                if current_retries < DockerManager._MAX_RETRIES:
                    DockerManager._RETRY_TRACKER[c.name] = current_retries + 1
                    await DockerManager.run_command(project_dir, ["restart", c.service])
                    restarted.append(c.service)
        return restarted

    @staticmethod
    async def stream_logs(project_dir: str, service: Optional[str] = None, tail: int = 100) -> AsyncGenerator[str, None]:
        """Streams real-time logs from docker compose logs, retrying gracefully if containers are currently building or starting."""
        full_cmd = ["docker", "compose", "logs", "-f", f"--tail={tail}"]
        if service and service.strip() and service.lower() != "all":
            full_cmd.append(service.strip())

        retry_count = 0
        max_retries = 60  # Allow streaming to stay open while building/downloading

        while retry_count < max_retries:
            process = None
            try:
                process = await asyncio.create_subprocess_exec(
                    *full_cmd,
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )

                had_output = False
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    had_output = True
                    retry_count = 0
                    yield line.decode("utf-8", errors="replace")

                # If the process exited without output (e.g. containers not yet created or starting)
                if not had_output:
                    retry_count += 1
                    if retry_count == 1:
                        yield "[StackStudio] ⏳ Containers em fase de build / download ou aguardando inicialização...\n"
                    await asyncio.sleep(2.0)
                else:
                    # If containers stopped, wait a moment and poll in case they restart
                    await asyncio.sleep(2.0)
                    retry_count += 1

            except (asyncio.CancelledError, GeneratorExit):
                break
            except Exception as e:
                yield f"[StackStudio] ⚠️ {str(e)}\n"
                await asyncio.sleep(2.0)
                retry_count += 1
            finally:
                if process:
                    try:
                        process.terminate()
                    except Exception:
                        pass
                    try:
                        await asyncio.wait_for(process.wait(), timeout=0.5)
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass
