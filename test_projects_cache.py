import os
import json
import pytest
from fastapi.testclient import TestClient
from studio.app import app
from studio.models import ProjectInfo, ProjectCreateRequest, ContainerInfo
from studio.services.project_store import ProjectStore, CACHE_FILE, REGISTRY_FILE

client = TestClient(app)


def test_project_store_cache_lifecycle(tmp_path):
    # Register test project
    proj = ProjectStore.register_project(
        project_id="test-cache-proj",
        name="Test Cache Proj",
        path=str(tmp_path),
        description="Testing JSON Cache",
        tools=["postgres", "redis"]
    )

    assert os.path.exists(CACHE_FILE)
    cached = ProjectStore.load_cache()
    assert len(cached) > 0
    match = next((p for p in cached if p.id == "test-cache-proj"), None)
    assert match is not None
    assert match.name == "Test Cache Proj"

    # Mutate status and save cache
    match.status = "running"
    match.visual_status = "green"
    match.containers = [
        ContainerInfo(
            name="test-postgres",
            service="postgres",
            state="running",
            status="Up 2 hours",
            visual_status="green"
        )
    ]
    ProjectStore.save_cache([match])

    # Verify reload from JSON file
    reloaded = ProjectStore.load_cache()
    reloaded_proj = next((p for p in reloaded if p.id == "test-cache-proj"), None)
    assert reloaded_proj is not None
    assert reloaded_proj.status == "running"
    assert reloaded_proj.visual_status == "green"
    assert len(reloaded_proj.containers) == 1
    assert reloaded_proj.containers[0].name == "test-postgres"

    # Clean up test project
    ProjectStore.delete_project("test-cache-proj")


def test_api_projects_cached_and_refresh_endpoints():
    # 1. Test cached_only=true
    res_cache = client.get("/api/projects?cached_only=true")
    assert res_cache.status_code == 200
    data_cache = res_cache.json()
    assert isinstance(data_cache, list)

    # 2. Test refresh=true
    res_refresh = client.get("/api/projects?refresh=true")
    assert res_refresh.status_code == 200
    data_refresh = res_refresh.json()
    assert isinstance(data_refresh, list)

    # Verify that projects_cache.json was written/updated on disk
    assert os.path.exists(CACHE_FILE)
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        file_data = json.load(f)
    assert isinstance(file_data, list)
    assert len(file_data) == len(data_refresh)


def test_api_projects_sync_endpoint():
    res = client.post("/api/projects/sync")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
