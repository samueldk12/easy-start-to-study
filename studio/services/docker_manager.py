"""
Docker Compose Lifecycle Manager
"""

import asyncio
import os
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
from studio.models import ContainerInfo


class DockerManager:
    @staticmethod
    async def run_command(project_dir: str, cmd: List[str]) -> Dict[str, Any]:
        """Runs a docker compose command in the project directory."""
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
            stdout, stderr = await process.communicate()
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
        return await DockerManager.run_command(project_dir, ["up", "-d", "--build"])

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
            visual_status=visual_status
        )

    @staticmethod
    async def get_project_status(project_dir: str) -> Dict[str, Any]:
        """Inspects containers status using docker compose ps -a --format json."""
        res = await DockerManager.run_command(project_dir, ["ps", "-a", "--format", "json"])
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
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line.decode("utf-8", errors="replace")
