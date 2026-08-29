"""
Pydantic Data Models for StackStudio with Plugin Support, Custom Configuration & Template Choices
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


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
    category: str = "backend"  # data_engineering, mlops, backend, devops, orchestration
    description: str
    icon: str = "box"
    badge: str = "Plugin"
    default_port: Optional[int] = None
    ui_url: Optional[str] = None
    env_vars: Dict[str, str] = Field(default_factory=dict)
    default_folders: Dict[str, str] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    compose_services: Dict[str, Any] = Field(default_factory=dict)
    volumes: List[str] = Field(default_factory=list)
    test_type: str = "http"  # "http", "tcp"
    test_path: str = "/"
    author: Optional[str] = "Community"
    version: Optional[str] = "1.0.0"


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


class ProjectUpdateRequest(BaseModel):
    tools: List[str]
    description: Optional[str] = None
    default_user: Optional[str] = None
    default_password: Optional[str] = None
    custom_ports: Dict[str, int] = Field(default_factory=dict)
    custom_envs: Dict[str, str] = Field(default_factory=dict)
    custom_folders: Dict[str, str] = Field(default_factory=dict)


class ContainerInfo(BaseModel):
    name: str
    service: str
    state: str
    status: str
    health: Optional[str] = None
    exit_code: Optional[int] = 0
    ports: str = ""
    retry_count: int = 0
    visual_status: str = "green"  # "green" (running/healthy), "yellow" (starting), "orange" (stopped/paused), "red" (crashed/unhealthy/error)


class ProjectInfo(BaseModel):
    id: str
    name: str
    path: str
    description: str
    tools: List[str]
    include_templates: bool = True
    created_at: str
    status: str = "stopped"  # "running", "starting", "stopped", "paused", "error", "partial"
    visual_status: str = "orange"  # "green", "yellow", "orange", "red"
    retry_count: int = 0
    containers: List[ContainerInfo] = Field(default_factory=list)
    ui_links: List[Dict[str, str]] = Field(default_factory=list)
