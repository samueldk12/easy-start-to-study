"""
Kubernetes Runtime and Cluster Lifecycle Manager
Executes kubectl commands, manages namespaces, deployments, and live pod statuses.
"""

import os
import json
import asyncio
import subprocess
from typing import Dict, List, Any, Optional


class K8sManager:
    @staticmethod
    async def is_cluster_available() -> bool:
        try:
            process = await asyncio.create_subprocess_exec(
                "kubectl", "cluster-info", "--request-timeout=3s",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    @staticmethod
    async def deploy_project(project_path: str) -> Dict[str, Any]:
        k8s_dir = os.path.join(project_path, "k8s")
        if not os.path.exists(k8s_dir):
            return {"success": False, "error": "k8s directory not found in project."}

        try:
            process = await asyncio.create_subprocess_exec(
                "kubectl", "apply", "-k", k8s_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def destroy_project(project_path: str) -> Dict[str, Any]:
        k8s_dir = os.path.join(project_path, "k8s")
        if not os.path.exists(k8s_dir):
            return {"success": False, "error": "k8s directory not found."}

        try:
            process = await asyncio.create_subprocess_exec(
                "kubectl", "delete", "-k", k8s_dir, "--timeout=30s",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_project_pods(project_name: str) -> List[Dict[str, Any]]:
        namespace = f"stack-{project_name}"
        try:
            process = await asyncio.create_subprocess_exec(
                "kubectl", "get", "pods", "-n", namespace, "-o", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode != 0:
                return []

            data = json.loads(stdout.decode("utf-8", errors="replace"))
            pods = []
            for item in data.get("items", []):
                name = item.get("metadata", {}).get("name", "")
                status_obj = item.get("status", {})
                phase = status_obj.get("phase", "Unknown")
                container_statuses = status_obj.get("containerStatuses", [])
                ready = all(cs.get("ready", False) for cs in container_statuses) if container_statuses else False
                restarts = sum(cs.get("restartCount", 0) for cs in container_statuses)

                pods.append({
                    "name": name,
                    "phase": phase,
                    "ready": ready,
                    "restarts": restarts
                })
            return pods
        except Exception:
            return []
