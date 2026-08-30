import asyncio
import os
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
        """Safely updates a conflicting host port mapping in the project compose file."""
        candidates = ["docker-compose.yml", "docker-compose.yaml", "compose.yaml"]
        replaced = False
        for fname in candidates:
            cpath = os.path.join(project_dir, fname)
            if os.path.exists(cpath):
                try:
                    with open(cpath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    # Replace patterns like "8443:8080", "8443:8443", "- 8443:8080", "- '8443:8080'"
                    new_content = re.sub(rf'(["\']?){old_port}(:[\d]+["\']?)', rf'\g<1>{new_port}\g<2>', content)
                    if new_content != content:
                        with open(cpath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        replaced = True
                except Exception:
                    pass
        return replaced

    @staticmethod
    async def run_command(project_dir: str, cmd: List[str], timeout: float = 30.0) -> Dict[str, Any]:
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
    async def start_project(project_dir: str) -> Dict[str, Any]:
        res = await DockerManager.run_command(project_dir, ["up", "-d", "--build"])
        
        # Automatic Port Conflict Detection and Auto-Recovery
        if not res.get("success", False):
            err_text = (res.get("stderr", "") + " " + res.get("stdout", "") + " " + str(res.get("error", ""))).lower()
            if "port is already allocated" in err_text or "address already in use" in err_text:
                raw_err = res.get("stderr", "") + " " + res.get("stdout", "")
                # Find conflicting port, e.g. "Bind for 0.0.0.0:8443 failed: port is already allocated"
                match = re.search(r"Bind for [^:]+:(\d+) failed", raw_err) or re.search(r":(\d+) failed: port is already allocated", raw_err)
                if match:
                    clash_port = int(match.group(1))
                    free_port = find_next_free_port(clash_port + 1)
                    if DockerManager._replace_port_in_compose(project_dir, clash_port, free_port):
                        # Retry starting the project with the reassigned free port
                        retry_res = await DockerManager.run_command(project_dir, ["up", "-d", "--build"])
                        if retry_res.get("success", False):
                            return retry_res
        return res

    @staticmethod
    async def pause_project(project_dir: str) -> Dict[str, Any]:
        return await DockerManager.run_command(project_dir, ["stop"])

    @staticmethod
    async def resume_project(project_dir: str) -> Dict[str, Any]:
        return await DockerManager.run_command(project_dir, ["start"])

    @staticmethod
    async def stop_project(project_dir: str) -> Dict[str, Any]:
        return await DockerManager.run_command(project_dir, ["down"])

    @staticmethod
    async def restart_project(project_dir: str) -> Dict[str, Any]:
        return await DockerManager.run_command(project_dir, ["restart"])

    @staticmethod
    async def start_service(project_dir: str, service: str) -> Dict[str, Any]:
        """Starts or recreates an individual service."""
        return await DockerManager.run_command(project_dir, ["up", "-d", service])

    @staticmethod
    async def stop_service(project_dir: str, service: str) -> Dict[str, Any]:
        """Stops an individual service container."""
        return await DockerManager.run_command(project_dir, ["stop", service])

    @staticmethod
    async def restart_service(project_dir: str, service: str) -> Dict[str, Any]:
        """Restarts an individual service container."""
        return await DockerManager.run_command(project_dir, ["restart", service])

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

    _RETRY_TRACKER: Dict[str, int] = {}
    _MAX_RETRIES: int = 5

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

        # Evaluate Visual Status:
        # 1. Paused containers are ALWAYS orange and paused (never red!)
        if state_raw == "paused" or "paused" in status_raw.lower():
            visual_status = "orange"
            state_raw = "paused"
        # 2. Intentionally stopped (exit code 0, 137 [SIGKILL], 143 [SIGTERM]) is orange
        elif state_raw in ("exited", "stopped") and exit_code in (0, 137, 143):
            visual_status = "orange"
        # 3. Crashed, Dead, non-graceful Exit, or Unhealthy running container
        elif state_raw in ("dead", "crashed", "error") or (state_raw in ("exited", "stopped") and exit_code not in (0, 137, 143)) or (state_raw == "running" and health_raw == "unhealthy"):
            visual_status = "red"
        # 4. Starting, Restarting, Created
        elif state_raw in ("starting", "restarting", "created") or health_raw == "starting" or "health: starting" in status_raw.lower():
            visual_status = "yellow"
        # 5. Running & Healthy
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

        return ContainerInfo(
            name=name,
            service=service,
            state=state_raw,
            status=status_raw,
            health=health_raw or None,
            exit_code=exit_code,
            ports=ports_str,
            retry_count=retry_count,
            visual_status=visual_status,
            last_changed=last_changed
        )

    @staticmethod
    async def get_project_status(project_dir: str) -> Dict[str, Any]:
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

        has_red = False
        has_yellow = False
        has_green = False
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
        elif has_green and not has_orange:
            status = "running"
            visual_status = "green"
        elif has_green and has_orange:
            status = "partial"
            visual_status = "yellow"
        else:
            status = "stopped"
            visual_status = "orange"

        # Sort containers by recent status change first, then status severity (red > yellow > green > orange), then name
        severity_map = {"red": 0, "yellow": 1, "green": 2, "orange": 3}
        containers.sort(key=lambda c: (-c.last_changed, severity_map.get(c.visual_status, 4), c.service))

        return {"status": status, "visual_status": visual_status, "containers": containers}

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
        """Streams real-time logs from docker compose logs, optionally filtered by service."""
        full_cmd = ["docker", "compose", "logs", "-f", f"--tail={tail}"]
        if service and service.strip() and service.lower() != "all":
            full_cmd.append(service.strip())

        process = await asyncio.create_subprocess_exec(
            *full_cmd,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                yield line.decode("utf-8", errors="replace")
        finally:
            try:
                process.kill()
            except Exception:
                pass
