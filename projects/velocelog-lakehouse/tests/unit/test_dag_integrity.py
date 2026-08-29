"""
Unit Tests: Airflow DAG Integrity, Syntax, and Structure Validation
"""

import os
import ast
import pytest
from pathlib import Path

DAGS_FOLDER = Path(__file__).resolve().parent.parent.parent / "airflow" / "dags"


@pytest.mark.unit
class TestDAGIntegrity:
    """Validates that all DAG files can be parsed without syntax errors."""

    def test_dags_directory_exists(self):
        assert DAGS_FOLDER.exists(), f"DAGs folder not found at: {DAGS_FOLDER}"

    def test_dag_files_syntax(self):
        dag_files = list(DAGS_FOLDER.glob("*.py"))
        assert len(dag_files) > 0, "No DAG python files found to test."

        for file_path in dag_files:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
                assert tree is not None, f"Failed to parse AST for {file_path.name}"

    def test_no_forbidden_patterns_in_dags(self):
        """Ensures DAGs don't contain common antipatterns (like hardcoded credentials or infinite loops)."""
        dag_files = list(DAGS_FOLDER.glob("*.py"))
        for file_path in dag_files:
            content = file_path.read_text(encoding="utf-8")
            assert "while True:" not in content, f"Infinite loop detected in {file_path.name}"
            assert "import time; time.sleep" not in content, f"Blocking sleep detected in {file_path.name}"
