"""
Pydantic Data Models for StackStudio with Custom Configuration & Template Choices
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
    custom_ports: Dict[str, int] = Field(default_factory=dict)
    custom_envs: Dict[str, str] = Field(default_factory=dict)
    custom_folders: Dict[str, str] = Field(default_factory=dict)


class ContainerInfo(BaseModel):
    name: str
    service: str
    state: str
    status: str
    ports: str


class ProjectInfo(BaseModel):
    id: str
    name: str
    path: str
    description: str
    tools: List[str]
    include_templates: bool = True
    created_at: str
    status: str = "stopped"  # "running", "stopped", "partial", "starting", "error"
    containers: List[ContainerInfo] = Field(default_factory=list)
    ui_links: List[Dict[str, str]] = Field(default_factory=list)
