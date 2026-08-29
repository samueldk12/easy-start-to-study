import os
import shutil
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from studio.app import app
from studio.services.folder_analyzer import FolderAnalyzer
from studio.services.project_store import ProjectStore

client = TestClient(app)


def test_analyze_existing_compose_folder():
    velocelog_path = Path("projects/velocelog").resolve()
    if velocelog_path.exists():
        analysis = FolderAnalyzer.analyze(str(velocelog_path))
        assert analysis["success"] is True
        assert analysis["has_compose"] is True
        assert analysis["launch_strategy"] == "docker-compose"
        assert analysis["start_command"] == "docker compose up -d"
        assert "postgres" in analysis["tools"]
        assert len(analysis["detected_services"]) > 0
        assert len(analysis["detected_techs"]) > 0


def test_analyze_synthetic_python_app():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create a Python FastAPI project structure
        reqs = tmp_path / "requirements.txt"
        reqs.write_text("fastapi==0.111.0\nuvicorn==0.30.1\npyspark==3.5.0\nconfluent-kafka==2.3.0", encoding="utf-8")
        
        main_py = tmp_path / "main.py"
        main_py.write_text("from fastapi import FastAPI\napp = FastAPI()", encoding="utf-8")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.10-slim\nWORKDIR /app\nCOPY . .\nCMD ['python', 'main.py']", encoding="utf-8")
        
        analysis = FolderAnalyzer.analyze(str(tmp_path))
        assert analysis["success"] is True
        assert analysis["has_dockerfile"] is True
        assert "spark" in analysis["tools"] or "kafka" in analysis["tools"]
        assert any("Python" in t["name"] for t in analysis["detected_techs"])
        assert "docker" in analysis["start_command"] or "python" in analysis["start_command"]


def test_analyze_and_import_api_endpoints():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create a sample project with compose
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("""
version: '3.8'
services:
  app:
    image: python:3.10-slim
    ports:
      - "8080:8080"
  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
  cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"
""", encoding="utf-8")
        
        # 1. Test POST /api/projects/analyze-folder
        analyze_res = client.post("/api/projects/analyze-folder", json={"path": str(tmp_path)})
        assert analyze_res.status_code == 200
        data = analyze_res.json()
        assert data["success"] is True
        assert data["has_compose"] is True
        assert "postgres" in data["tools"]
        assert "redis" in data["tools"]
        assert data["start_command"] == "docker compose up -d"

        # 2. Test POST /api/projects/import
        import_res = client.post("/api/projects/import", json={
            "name": "imported-test-stack",
            "path": str(tmp_path),
            "description": "Test imported stack",
            "tools": data["tools"],
            "auto_create_compose": False,
            "auto_install_extensions": True
        })
        assert import_res.status_code == 200
        proj_data = import_res.json()
        assert proj_data["name"] == "imported-test-stack"
        assert "postgres" in proj_data["tools"]

        # Clean up registered project
        ProjectStore.delete_project(proj_data["id"])
