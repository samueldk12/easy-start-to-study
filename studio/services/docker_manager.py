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

    @staticmethod
    async def get_project_status(project_dir: str) -> Dict[str, Any]:
        """Inspects containers status using docker compose ps --format json."""
        res = await DockerManager.run_command(project_dir, ["ps", "--format", "json"])
        if not res["success"]:
            return {"status": "stopped", "containers": []}

        output = res["stdout"].strip()
        if not output:
            return {"status": "stopped", "containers": []}

        containers: List[ContainerInfo] = []
        running_count = 0
        total_count = 0

        # Docker compose ps outputs each container as a JSON object per line or as a JSON array
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, list):
                    for item in data:
                        c_info = DockerManager._parse_container_item(item)
                        containers.append(c_info)
                        total_count += 1
                        if c_info.state.lower() in ("running", "healthy"):
                            running_count += 1
                else:
                    c_info = DockerManager._parse_container_item(data)
                    containers.append(c_info)
                    total_count += 1
                    if c_info.state.lower() in ("running", "healthy"):
                        running_count += 1
            except Exception:
                continue

        if total_count == 0:
            status = "stopped"
        elif running_count == total_count:
            status = "running"
        elif running_count > 0:
            status = "partial"
        else:
            status = "stopped"

        return {"status": status, "containers": containers}

    @staticmethod
    def _parse_container_item(item: Dict[str, Any]) -> ContainerInfo:
        return ContainerInfo(
            name=item.get("Name") or item.get("ID") or "unknown",
            service=item.get("Service") or item.get("Name") or "",
            state=item.get("State") or "",
            status=item.get("Status") or "",
            ports=item.get("Publishers") or item.get("Ports") or ""
        )

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
