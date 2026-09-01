"""
Pydantic Data Models for StackStudio with Plugin Support, Custom Configuration & Template Choices
"""

import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# Project names become directory names under PROJECTS_DIR (see scaffolder.py). Reject
# path separators, '..' and leading dots so a crafted name can't escape that directory.
_SAFE_NAME_RE = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9 ._-]{0,62}[A-Za-z0-9])?$')


def _validate_safe_name(name: str) -> str:
    name = name.strip()
    if not name or not _SAFE_NAME_RE.match(name) or ".." in name:
        raise ValueError(
            "name must be 2-64 chars, start/end alphanumeric, and contain only "
            "letters, numbers, spaces, '.', '_' or '-' (no path separators or '..')"
        )
    return name


class ToolOption(BaseModel):
    id: str
    name: str
    category: str
    description: str
    icon: str
    badge: str
    default_port: Optional[int] = None
    ui_url: Optional[str] = None
    env_vars: Dict[str, str] = Field(default_factory=dict)
    default_folders: Dict[str, str] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    is_plugin: bool = False


class ToolPlugin(BaseModel):
    id: str
    name: str
    category: str = "backend"  # data_engineering, mlops, backend, devops, orchestration, os_sandboxes, ai_llms
    description: str = ""
    icon: str = "box"
    badge: str = "Custom / Plugin"
    default_port: Optional[int] = None
    ui_url: Optional[str] = None
    env_vars: Dict[str, str] = Field(default_factory=dict)
    default_folders: Dict[str, str] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    compose_services: Dict[str, Any] = Field(default_factory=dict)
    volumes: List[str] = Field(default_factory=list)
    test_type: str = "http"  # "http", "tcp"
    test_path: str = "/"
    author: Optional[str] = "User"
    version: Optional[str] = "1.0.0"
    # Custom Service Source options: "image", "dockerfile", "github"
    source_type: str = "image"
    image: Optional[str] = None
    dockerfile_content: Optional[str] = None
    git_url: Optional[str] = None
    git_branch: Optional[str] = "main"
    git_dockerfile_path: Optional[str] = "Dockerfile"
    git_compose_path: Optional[str] = "docker-compose.yml"
    command: Optional[str] = None
    container_port: Optional[int] = None


class ContainerExecRequest(BaseModel):
    command: str
    user: Optional[str] = None
    workdir: Optional[str] = None


class ToolCategory(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    tools: List[ToolOption]


class ProjectPreset(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    tools: List[str]


class ProjectCreateRequest(BaseModel):
    name: str
    path: Optional[str] = None
    description: Optional[str] = "Projeto gerado via StackStudio"
    tools: List[str]
    include_templates: bool = True  # True = com código/boilerplates; False = estrutura limpa
    default_user: Optional[str] = "admin"
    default_password: Optional[str] = "admin123"
    custom_ports: Dict[str, int] = Field(default_factory=dict)
    custom_envs: Dict[str, str] = Field(default_factory=dict)
    custom_folders: Dict[str, str] = Field(default_factory=dict)
    auto_install_extensions: bool = True
    custom_vscode_extensions: List[str] = Field(default_factory=list)
    airflow_providers: List[str] = Field(default_factory=list)
    airflow_executor: Optional[str] = "LocalExecutor"
    custom_airflow_requirements: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        return _validate_safe_name(v)


class ProjectUpdateRequest(BaseModel):
    tools: List[str]
    description: Optional[str] = None
    default_user: Optional[str] = None
    default_password: Optional[str] = None
    custom_ports: Dict[str, int] = Field(default_factory=dict)
    custom_envs: Dict[str, str] = Field(default_factory=dict)
    custom_folders: Dict[str, str] = Field(default_factory=dict)
    auto_install_extensions: Optional[bool] = True
    custom_vscode_extensions: Optional[List[str]] = None
    airflow_providers: Optional[List[str]] = None
    airflow_executor: Optional[str] = None
    custom_airflow_requirements: Optional[List[str]] = None


class ContainerInfo(BaseModel):
    id: Optional[str] = None
    name: str
    service: str
    state: str
    status: str
    health: Optional[str] = None
    exit_code: Optional[int] = 0
    ports: str = ""
    retry_count: int = 0
    is_oneshot: bool = False
    visual_status: str = "green"  # "green" (running/healthy), "blue" (concluído/oneshot sucesso), "yellow" (starting), "orange" (stopped/paused), "red" (crashed/unhealthy/error)
    last_changed: float = 0.0


class FolderAnalyzeRequest(BaseModel):
    path: str


class ProjectImportRequest(BaseModel):
    name: str
    path: str
    description: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    include_templates: bool = False
    auto_create_compose: bool = False
    compose_content: Optional[str] = None
    auto_install_extensions: bool = True
    custom_vscode_extensions: List[str] = Field(default_factory=list)


class ProjectMergeRequest(BaseModel):
    name: str
    project_ids: List[str]
    description: Optional[str] = "Workspace unificado gerado via StackStudio"

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        return _validate_safe_name(v)


class VaultPasswordRequest(BaseModel):
    password: str


class VaultChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class CredentialCreateRequest(BaseModel):
    name: str
    type: str = "generic"
    data: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = ""


class CredentialUpdateRequest(BaseModel):
    name: Optional[str] = None
    data: Optional[Dict[str, str]] = None
    notes: Optional[str] = None


class CredentialApplyRequest(BaseModel):
    project_id: str


class ProjectGovernanceRequest(BaseModel):
    auto_cleanup_days: int = 15  # Days of inactivity before auto-pruning Docker images, 0 = disabled
    clean_images_on_idle: bool = True
    clean_volumes_on_idle: bool = False


class ProjectInfo(BaseModel):
    id: str
    name: str
    path: str
    description: str
    tools: List[str]
    include_templates: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_used_at: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
    auto_cleanup_days: Optional[int] = 15
    clean_images_on_idle: bool = True
    clean_volumes_on_idle: bool = False
    idle_days: Optional[int] = 0
    disk_usage_estimate: Optional[str] = None
    status: str = "stopped"  # "running", "starting", "stopped", "paused", "error", "partial"
    visual_status: str = "orange"  # "green", "yellow", "orange", "red"
    retry_count: int = 0
    auto_install_extensions: bool = True
    custom_vscode_extensions: List[str] = Field(default_factory=list)
    containers: List[ContainerInfo] = Field(default_factory=list)
    ui_links: List[Dict[str, str]] = Field(default_factory=list)
    launch_strategy: Optional[str] = "docker-compose"
    start_command: Optional[str] = "docker compose up -d"
    is_merged_workspace: bool = False
    merged_projects: List[str] = Field(default_factory=list)
