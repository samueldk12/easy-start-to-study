import os
import shutil
import tempfile
import yaml
import pytest
from studio.models import ProjectCreateRequest
from studio.services.scaffolder import ProjectScaffolder

def test_airflow_spark_scaffolding_and_customization():
    test_dir = tempfile.mkdtemp(prefix="stackstudio_test_airflow_")
    try:
        req = ProjectCreateRequest(
            name="airflow-spark-lakehouse",
            path=test_dir,
            description="Test Airflow and Spark Project",
            tools=["airflow", "spark", "postgres", "minio", "trino", "kafka"],
            include_templates=True,
            airflow_providers=["apache-spark", "postgres", "amazon", "trino", "apache-kafka"],
            airflow_executor="LocalExecutor",
            custom_airflow_requirements=["polars>=1.0.0", "duckdb>=1.0.0"]
        )

        scaffolder = ProjectScaffolder(req)
        scaffolder.scaffold()

        # 1. Verify requirements.txt
        req_path = os.path.join(test_dir, "airflow", "requirements.txt")
        assert os.path.exists(req_path)
        with open(req_path, "r", encoding="utf-8") as f:
            req_content = f.read()

        assert "apache-airflow-providers-apache-spark" in req_content
        assert "pyspark" in req_content
        assert "apache-airflow-providers-postgres" in req_content
        assert "apache-airflow-providers-amazon" in req_content
        assert "apache-airflow-providers-trino" in req_content
        assert "apache-airflow-providers-apache-kafka" in req_content
        assert "polars>=1.0.0" in req_content
        assert "duckdb>=1.0.0" in req_content

        # 2. Verify Dockerfile
        df_path = os.path.join(test_dir, "airflow", "Dockerfile")
        assert os.path.exists(df_path)
        with open(df_path, "r", encoding="utf-8") as f:
            df_content = f.read()

        assert "openjdk-17-jre-headless" in df_content
        assert "JAVA_HOME" in df_content

        # 3. Verify DAGs
        dags_dir = os.path.join(test_dir, "airflow", "dags")
        assert os.path.exists(os.path.join(dags_dir, "spark_orchestration.py"))
        assert os.path.exists(os.path.join(dags_dir, "lakehouse_pipeline.py"))

        with open(os.path.join(dags_dir, "spark_orchestration.py"), "r", encoding="utf-8") as f:
            spark_dag_content = f.read()
        assert "spark_default" in spark_dag_content
        assert "spark_orchestration" in spark_dag_content

        # 4. Verify Compose connections
        compose_path = os.path.join(test_dir, "docker-compose.yml")
        assert os.path.exists(compose_path)
        with open(compose_path, "r", encoding="utf-8") as f:
            compose_data = yaml.safe_load(f)

        services = compose_data["services"]
        assert "airflow-db" in services
        assert "airflow-init" in services
        assert "airflow-webserver" in services
        assert "airflow-scheduler" in services

        init_cmd = services["airflow-init"]["command"]
        assert "spark_default" in init_cmd
        assert "postgres_default" in init_cmd
        assert "aws_default" in init_cmd
        assert "trino_default" in init_cmd

        print("All Airflow Spark Scaffolding and Customization assertions passed 100%!")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
