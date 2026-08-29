import os
import json
import tempfile
import pytest
from pathlib import Path
from studio.models import ProjectCreateRequest
from studio.services.scaffolder import ProjectScaffolder


def test_vscode_default_extensions_present():
    with tempfile.TemporaryDirectory() as tmpdir:
        req = ProjectCreateRequest(
            name="test-vscode-defaults",
            path=tmpdir,
            tools=["postgres", "vscode"],
            auto_install_extensions=True
        )
        scaff = ProjectScaffolder(req)
        scaff.scaffold()

        extensions_path = Path(tmpdir) / ".vscode" / "extensions.json"
        assert extensions_path.exists()
        
        data = json.loads(extensions_path.read_text(encoding="utf-8"))
        recommendations = data.get("recommendations", [])
        
        # Check required default extensions
        assert "ms-azuretools.vscode-docker" in recommendations
        assert "ms-python.python" in recommendations
        assert "ms-python.vscode-pylance" in recommendations
        assert "cweijan.vscode-database-client2" in recommendations
        assert "mtxr.sqltools" in recommendations
        assert "mtxr.sqltools-driver-pg" in recommendations
        assert "ckolkman.vscode-postgres" in recommendations
        assert "redhat.vscode-yaml" in recommendations
        assert "eamodio.gitlens" in recommendations


def test_vscode_preconfigured_database_connections():
    with tempfile.TemporaryDirectory() as tmpdir:
        req = ProjectCreateRequest(
            name="ecommerce-db-stack",
            path=tmpdir,
            tools=["postgres", "redis", "clickhouse"],
            default_user="admin",
            default_password="secretpassword123",
            auto_install_extensions=True
        )
        scaff = ProjectScaffolder(req)
        scaff.scaffold()

        settings_path = Path(tmpdir) / ".vscode" / "settings.json"
        assert settings_path.exists()
        
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        
        # Check SQLTools connections
        assert "sqltools.connections" in settings
        sql_conns = settings["sqltools.connections"]
        assert len(sql_conns) > 0
        pg_sql_conn = next((c for c in sql_conns if c["driver"] == "PostgreSQL"), None)
        assert pg_sql_conn is not None
        assert pg_sql_conn["server"] == "postgres"
        assert pg_sql_conn["port"] == 5432
        assert pg_sql_conn["username"] == "admin"
        assert pg_sql_conn["password"] == "secretpassword123"

        # Check Database Client connections
        assert "database.connections" in settings
        db_conns = settings["database.connections"]
        assert len(db_conns) >= 2
        
        pg_db_conn = next((c for c in db_conns if c["dbType"] == "PostgreSQL"), None)
        assert pg_db_conn is not None
        assert pg_db_conn["host"] == "postgres"
        assert pg_db_conn["user"] == "admin"
        
        redis_conn = next((c for c in db_conns if c["dbType"] == "Redis"), None)
        assert redis_conn is not None
        assert redis_conn["host"] == "redis"
        assert redis_conn["port"] == 6379


def test_vscode_extracts_credentials_from_existing_compose():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("""
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: custom_user
      POSTGRES_PASSWORD: custom_pass
      POSTGRES_DB: custom_database
""", encoding="utf-8")

        req = ProjectCreateRequest(
            name="imported-custom-db",
            path=str(tmp_path),
            tools=["postgres"],
            auto_install_extensions=True
        )
        scaff = ProjectScaffolder(req)
        scaff._generate_vscode_files()

        settings_path = tmp_path / ".vscode" / "settings.json"
        assert settings_path.exists()
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        
        sql_conns = settings.get("sqltools.connections", [])
        pg_conn = next(c for c in sql_conns if c["driver"] == "PostgreSQL")
        assert pg_conn["username"] == "custom_user"
        assert pg_conn["password"] == "custom_pass"
        assert pg_conn["database"] == "custom_database"
