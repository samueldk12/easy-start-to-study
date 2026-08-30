import pytest
from unittest.mock import patch
import httpx
from studio.app import app
from studio.services.project_store import ProjectStore


@pytest.mark.asyncio
async def test_stream_project_logs_endpoint():
    projects = ProjectStore.list_projects()
    assert len(projects) > 0
    test_proj = projects[0]

    async def mock_logs(project_path, service=None, tail=150):
        yield "Starting container...\n"
        yield "Service is healthy and ready\n"

    with patch("studio.services.docker_manager.DockerManager.stream_logs", side_effect=mock_logs):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Test streaming for all services
            async with ac.stream("GET", f"/api/projects/{test_proj.id}/logs") as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
                lines = []
                async for chunk in response.aiter_lines():
                    if chunk:
                        lines.append(chunk)
                assert len(lines) >= 2
                assert any("StackStudio SSE" in l for l in lines)
                assert any("Starting container..." in l for l in lines)

            # 2. Test streaming for a specific service
            service_name = test_proj.tools[0] if test_proj.tools else "postgres"
            async with ac.stream("GET", f"/api/projects/{test_proj.id}/logs?service={service_name}") as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
                lines = []
                async for chunk in response.aiter_lines():
                    if chunk:
                        lines.append(chunk)
                assert len(lines) >= 2


@pytest.mark.asyncio
async def test_stream_project_logs_not_found():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/projects/non-existent-project-9999/logs")
        assert response.status_code == 404

