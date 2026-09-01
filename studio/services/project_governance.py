"""
Project Governance & Auto-Cleanup Engine
Manages project lifecycle policies: idle detection, disk usage estimation,
and automatic Docker image/volume cleanup for inactive projects.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any


class ProjectGovernance:
    
    @staticmethod
    def calculate_idle_days(project_id: str) -> int:
        """Calculates how many days a project has been idle.
        Uses last_used_at from registry + last action from StateTracker history."""
        from studio.services.project_store import ProjectStore
        from studio.services.state_tracker import StateTracker
        
        proj = ProjectStore.get_project(project_id)
        if not proj:
            return -1
        
        now = datetime.now()
        latest_activity = None
        
        # Check last_used_at from project info
        if proj.last_used_at:
            try:
                latest_activity = datetime.fromisoformat(proj.last_used_at)
            except Exception:
                pass
        
        # Check StateTracker for last action
        history = StateTracker.get_history(project_id=project_id, limit=1)
        if history:
            try:
                action_dt = datetime.fromisoformat(history[0].get("timestamp", ""))
                if latest_activity is None or action_dt > latest_activity:
                    latest_activity = action_dt
            except Exception:
                pass
        
        # Fallback to created_at
        if latest_activity is None:
            try:
                latest_activity = datetime.fromisoformat(proj.created_at)
            except Exception:
                try:
                    latest_activity = datetime.strptime(proj.created_at, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return 0
        
        diff = (now - latest_activity).days
        return max(0, diff)
    
    @staticmethod
    async def estimate_disk_usage(project_dir: str) -> Dict[str, Any]:
        """Estimates disk usage for a project's Docker images and volumes."""
        result = {"images_mb": 0, "containers_mb": 0, "total_mb": 0, "human": "0 MB", "image_count": 0}
        
        try:
            # Get images used by this compose project
            proc = await asyncio.create_subprocess_exec(
                "docker", "compose", "images", "--format", "json",
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            
            if proc.returncode == 0:
                import json
                output = stdout.decode("utf-8", errors="replace").strip()
                if output:
                    images = []
                    for line in output.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if isinstance(data, list):
                                images.extend(data)
                            else:
                                images.append(data)
                        except Exception:
                            continue
                    
                    total_size = 0
                    for img in images:
                        size_str = str(img.get("Size", "0"))
                        # Parse size like "123MB", "1.2GB", "456KB"
                        try:
                            if "GB" in size_str.upper():
                                total_size += float(size_str.upper().replace("GB", "").strip()) * 1024
                            elif "MB" in size_str.upper():
                                total_size += float(size_str.upper().replace("MB", "").strip())
                            elif "KB" in size_str.upper():
                                total_size += float(size_str.upper().replace("KB", "").strip()) / 1024
                        except Exception:
                            pass
                    
                    result["images_mb"] = round(total_size, 1)
                    result["image_count"] = len(images)
        except Exception:
            pass
        
        result["total_mb"] = result["images_mb"] + result["containers_mb"]
        
        # Human-readable
        total = result["total_mb"]
        if total >= 1024:
            result["human"] = f"{total / 1024:.1f} GB"
        elif total > 0:
            result["human"] = f"{total:.0f} MB"
        else:
            result["human"] = "—"
        
        return result
    
    @staticmethod
    async def cleanup_project(project_dir: str, remove_images: bool = True, remove_volumes: bool = False) -> Dict[str, Any]:
        """Cleans up Docker resources for a project.
        remove_images=True: docker compose down --rmi all (removes images)
        remove_volumes=True: also adds -v (removes named volumes - DANGEROUS)
        """
        args = ["docker", "compose", "down"]
        if remove_images:
            args.append("--rmi")
            args.append("all")
        if remove_volumes:
            args.append("-v")
        args.append("--remove-orphans")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)
            
            success = proc.returncode == 0
            return {
                "success": success,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "removed_images": remove_images,
                "removed_volumes": remove_volumes
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Timeout após 120s durante cleanup"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_governance_summary() -> List[Dict[str, Any]]:
        """Returns governance summary for all projects with idle days, disk usage, and cleanup recommendations."""
        from studio.services.project_store import ProjectStore
        
        projects = ProjectStore.list_projects()
        summary = []
        
        for proj in projects:
            idle_days = ProjectGovernance.calculate_idle_days(proj.id)
            
            # Estimate disk usage (async)
            disk_usage = {"human": "—", "total_mb": 0, "image_count": 0}
            if os.path.exists(proj.path):
                try:
                    disk_usage = await ProjectGovernance.estimate_disk_usage(proj.path)
                except Exception:
                    pass
            
            # Determine recommendation
            auto_cleanup_days = proj.auto_cleanup_days or 15
            recommendation = "ok"
            if idle_days >= auto_cleanup_days and auto_cleanup_days > 0:
                recommendation = "auto_cleanup_eligible"
            elif idle_days >= 7:
                recommendation = "idle_warning"
            
            summary.append({
                "project_id": proj.id,
                "name": proj.name,
                "path": proj.path,
                "status": proj.status,
                "visual_status": proj.visual_status,
                "idle_days": idle_days,
                "last_used_at": proj.last_used_at,
                "created_at": proj.created_at,
                "auto_cleanup_days": auto_cleanup_days,
                "clean_images_on_idle": proj.clean_images_on_idle,
                "clean_volumes_on_idle": proj.clean_volumes_on_idle,
                "disk_usage": disk_usage,
                "recommendation": recommendation,
                "is_running": proj.visual_status in ("green", "yellow")
            })
        
        # Sort: idle_warning/auto_cleanup first, then by idle_days desc
        priority = {"auto_cleanup_eligible": 0, "idle_warning": 1, "ok": 2}
        summary.sort(key=lambda x: (priority.get(x["recommendation"], 2), -x["idle_days"]))
        
        return summary
    
    @staticmethod
    async def auto_cleanup_check() -> Dict[str, Any]:
        """Runs automatic cleanup on all projects that exceeded their idle threshold.
        Only cleans stopped projects (never cleans running ones)."""
        from studio.services.project_store import ProjectStore
        from studio.services.state_tracker import StateTracker
        
        projects = ProjectStore.list_projects()
        cleaned = []
        skipped = []
        errors = []
        
        for proj in projects:
            auto_days = proj.auto_cleanup_days
            if not auto_days or auto_days <= 0:
                continue  # Auto-cleanup disabled for this project
            
            # Never auto-clean running projects
            if proj.visual_status in ("green", "yellow"):
                skipped.append({"project_id": proj.id, "reason": "running"})
                continue
            
            idle_days = ProjectGovernance.calculate_idle_days(proj.id)
            if idle_days < auto_days:
                continue  # Not idle enough
            
            if not os.path.exists(proj.path):
                continue
            
            res = await ProjectGovernance.cleanup_project(
                proj.path,
                remove_images=proj.clean_images_on_idle,
                remove_volumes=proj.clean_volumes_on_idle
            )
            
            if res.get("success"):
                cleaned.append({
                    "project_id": proj.id,
                    "name": proj.name,
                    "idle_days": idle_days,
                    "removed_images": proj.clean_images_on_idle,
                    "removed_volumes": proj.clean_volumes_on_idle
                })
                StateTracker.record_action(
                    proj.id, "auto_cleanup",
                    status="success",
                    details=f"Auto-cleanup após {idle_days} dias inativo. Imagens: {'sim' if proj.clean_images_on_idle else 'não'}, Volumes: {'sim' if proj.clean_volumes_on_idle else 'não'}",
                    project_name=proj.name,
                    project_path=proj.path
                )
            else:
                errors.append({"project_id": proj.id, "error": res.get("error") or res.get("stderr", "")})
        
        return {
            "cleaned": cleaned,
            "skipped": skipped,
            "errors": errors,
            "total_cleaned": len(cleaned)
        }
