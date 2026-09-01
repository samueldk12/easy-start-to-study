"""
StateTracker & Crash Recovery Engine
Persistently records all projects, container IDs and operations started by StackStudio.
Survives server reboots/crashes, detects running containers, tracks uptime and enables 1-click session restoration.
"""

import os
import json
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(_PROJECT_ROOT, "projects", ".state_history.json")


class StateTracker:
    _state: Dict[str, Any] = {
        "managed_projects": {},   # project_id -> { name, path, expected_state, started_at, last_action, last_action_at, container_ids, was_running_before_restart }
        "action_history": [],     # list of action records
        "server_sessions": []     # list of { started_at, pid, last_heartbeat }
    }
    _initialized: bool = False

    @classmethod
    def _load_from_disk(cls):
        if not os.path.exists(STATE_FILE):
            cls._state = {
                "managed_projects": {},
                "action_history": [],
                "server_sessions": []
            }
            return

        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                cls._state = json.load(f)
                if not isinstance(cls._state, dict):
                    cls._state = {"managed_projects": {}, "action_history": [], "server_sessions": []}
                cls._state.setdefault("managed_projects", {})
                cls._state.setdefault("action_history", [])
                cls._state.setdefault("server_sessions", [])
        except Exception as e:
            print(f"[StateTracker] Error loading state file: {e}")
            cls._state = {"managed_projects": {}, "action_history": [], "server_sessions": []}

    @classmethod
    def _save_to_disk(cls):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        try:
            temp_file = STATE_FILE + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(cls._state, f, indent=2, ensure_ascii=False)
            if os.path.exists(STATE_FILE):
                os.replace(temp_file, STATE_FILE)
            else:
                os.rename(temp_file, STATE_FILE)
        except Exception as e:
            print(f"[StateTracker] Error saving state to disk: {e}")

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            cls._load_from_disk()
            cls._initialized = True

    @classmethod
    def record_action(
        cls,
        project_id: str,
        action: str,
        status: str = "success",
        details: str = "",
        container_ids: Optional[List[str]] = None,
        project_name: Optional[str] = None,
        project_path: Optional[str] = None
    ):
        """Records an action in both the project's managed state and the persistent audit history."""
        cls.initialize()
        now_iso = datetime.now().isoformat()
        
        proj_entry = cls._state["managed_projects"].get(project_id, {
            "project_id": project_id,
            "name": project_name or project_id,
            "path": project_path or "",
            "expected_state": "stopped",
            "started_at": None,
            "last_action": action,
            "last_action_at": now_iso,
            "container_ids": [],
            "was_running_before_restart": False
        })

        if project_name:
            proj_entry["name"] = project_name
        if project_path:
            proj_entry["path"] = project_path

        proj_entry["last_action"] = action
        proj_entry["last_action_at"] = now_iso

        # Update expected state based on action
        if action in ("start", "resume", "restart", "merge_start"):
            if status == "success":
                proj_entry["expected_state"] = "running"
                if not proj_entry.get("started_at") or action in ("start", "restart"):
                    proj_entry["started_at"] = now_iso
                proj_entry["was_running_before_restart"] = False
        elif action == "pause":
            if status == "success":
                proj_entry["expected_state"] = "paused"
        elif action in ("stop", "delete"):
            if status == "success":
                proj_entry["expected_state"] = "stopped"
                proj_entry["started_at"] = None
                proj_entry["container_ids"] = []
                proj_entry["was_running_before_restart"] = False

        if container_ids:
            # Merge container IDs
            current_ids = set(proj_entry.get("container_ids", []))
            current_ids.update(container_ids)
            proj_entry["container_ids"] = list(current_ids)

        cls._state["managed_projects"][project_id] = proj_entry

        # Add to chronological action history (capped at 200 events)
        action_item = {
            "timestamp": now_iso,
            "project_id": project_id,
            "project_name": proj_entry.get("name", project_id),
            "action": action,
            "status": status,
            "details": details,
            "container_ids": container_ids or []
        }
        cls._state["action_history"].insert(0, action_item)
        if len(cls._state["action_history"]) > 200:
            cls._state["action_history"] = cls._state["action_history"][:200]

        cls._save_to_disk()

    @classmethod
    def record_containers_for_project(cls, project_id: str, container_ids: List[str], project_name: Optional[str] = None):
        cls.initialize()
        if project_id in cls._state["managed_projects"]:
            cls._state["managed_projects"][project_id]["container_ids"] = list(set(container_ids))
            if project_name:
                cls._state["managed_projects"][project_id]["name"] = project_name
            cls._save_to_disk()

    @classmethod
    async def reconcile_on_startup(cls) -> Dict[str, Any]:
        """
        Reconciles in-memory/disk state with real Docker daemon state.
        Identifies which containers are currently running, which were interrupted by a crash/server shutdown,
        and prepares recovery metrics.
        """
        cls.initialize()
        now_iso = datetime.now().isoformat()
        pid = os.getpid()

        cls._state["server_sessions"].insert(0, {
            "started_at": now_iso,
            "pid": pid,
            "last_heartbeat": now_iso
        })
        if len(cls._state["server_sessions"]) > 20:
            cls._state["server_sessions"] = cls._state["server_sessions"][:20]

        # Get list of all currently running Docker container IDs and names
        running_container_ids = set()
        running_container_names = set()
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                lines = stdout.decode("utf-8", errors="replace").strip().splitlines()
                for line in lines:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        cid = parts[0].strip()
                        cname = parts[1].strip()
                        running_container_ids.add(cid)
                        running_container_names.add(cname)
        except Exception as e:
            print(f"[StateTracker] Error querying Docker daemon on reconcile: {e}")

        active_projects = []
        interrupted_projects = []

        for pid, pdata in cls._state["managed_projects"].items():
            expected = pdata.get("expected_state", "stopped")
            tracked_cids = pdata.get("container_ids", [])
            p_name = pdata.get("name", pid)

            # Check if any tracked containers are actively running in Docker
            has_running_containers = False
            for cid in tracked_cids:
                if cid in running_container_ids or any(cid.startswith(rc) or rc.startswith(cid) for rc in running_container_ids):
                    has_running_containers = True
                    break

            if expected == "running":
                if has_running_containers:
                    pdata["was_running_before_restart"] = False
                    active_projects.append(pid)
                else:
                    # It was expected to be running, but no containers are up (e.g. system reboot or docker restart)
                    pdata["was_running_before_restart"] = True
                    interrupted_projects.append(pid)
            elif expected == "paused":
                pdata["was_running_before_restart"] = False
            else:
                pdata["was_running_before_restart"] = False

        cls._save_to_disk()

        return {
            "active_projects": active_projects,
            "interrupted_projects": interrupted_projects,
            "total_managed": len(cls._state["managed_projects"]),
            "running_containers_found": len(running_container_ids)
        }

    @classmethod
    def get_managed_state(cls) -> Dict[str, Any]:
        cls.initialize()
        now = datetime.now()
        
        # Calculate live uptimes
        projects_with_uptime = {}
        for pid, data in cls._state["managed_projects"].items():
            item = dict(data)
            started_at = item.get("started_at")
            if started_at and item.get("expected_state") == "running":
                try:
                    start_dt = datetime.fromisoformat(started_at)
                    diff = (now - start_dt).total_seconds()
                    item["uptime_seconds"] = max(0, int(diff))
                    item["uptime_human"] = cls._format_uptime(diff)
                except Exception:
                    item["uptime_seconds"] = None
                    item["uptime_human"] = None
            else:
                item["uptime_seconds"] = None
                item["uptime_human"] = None
            projects_with_uptime[pid] = item

        interrupted = [p for p in projects_with_uptime.values() if p.get("was_running_before_restart")]

        return {
            "managed_projects": projects_with_uptime,
            "interrupted_projects": interrupted,
            "total_managed": len(projects_with_uptime),
            "interrupted_count": len(interrupted)
        }

    @classmethod
    def get_history(cls, project_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        cls.initialize()
        history = cls._state.get("action_history", [])
        if project_id:
            history = [h for h in history if h.get("project_id") == project_id]
        return history[:limit]

    @classmethod
    def _format_uptime(cls, seconds: float) -> str:
        s = int(seconds)
        if s < 60:
            return f"{s}s"
        m = s // 60
        if m < 60:
            return f"{m}m {s % 60}s"
        h = m // 60
        if h < 24:
            return f"{h}h {m % 60}m"
        d = h // 24
        return f"{d}d {h % 24}h"
