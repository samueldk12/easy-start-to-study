"""
Folder Analyzer & Tech Detector for StackStudio
Walks directory trees, inspects configuration/manifest files, detects technologies,
and determines the optimal startup strategy (docker-compose, Dockerfile, k8s, CLI).
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import yaml

# Known tool mapping signatures for images and service names
IMAGE_TOOL_MAP = {
    "postgres": "postgres",
    "postgresql": "postgres",
    "debezium/postgres": "postgres",
    "kafka": "kafka",
    "cp-kafka": "kafka",
    "confluentinc/cp-kafka": "kafka",
    "bitnami/kafka": "kafka",
    "apache/kafka": "kafka",
    "zookeeper": "kafka",
    "cp-zookeeper": "kafka",
    "confluentinc/cp-zookeeper": "kafka",
    "debezium/connect": "kafka",
    "cp-kafka-connect": "kafka",
    "minio": "minio",
    "minio/minio": "minio",
    "minio/mc": "minio",
    "spark": "spark",
    "apache/spark": "spark",
    "bitnami/spark": "spark",
    "iceberg": "iceberg",
    "tabulario/iceberg-rest": "iceberg",
    "apache/iceberg-rest-catalog": "iceberg",
    "trino": "trino",
    "trinodb/trino": "trino",
    "airflow": "airflow",
    "apache/airflow": "airflow",
    "puckel/docker-airflow": "airflow",
    "redis": "redis",
    "bitnami/redis": "redis",
    "rabbitmq": "rabbitmq",
    "bitnami/rabbitmq": "rabbitmq",
    "elasticsearch": "elasticsearch",
    "docker.elastic.co/elasticsearch/elasticsearch": "elasticsearch",
    "kibana": "kibana",
    "docker.elastic.co/kibana/kibana": "kibana",
    "grafana": "grafana",
    "grafana/grafana": "grafana",
    "prometheus": "prometheus",
    "prom/prometheus": "prometheus",
    "loki": "loki",
    "grafana/loki": "loki",
    "promtail": "loki",
    "jaeger": "jaeger",
    "jaegertracing/all-in-one": "jaeger",
    "zipkin": "zipkin",
    "openzipkin/zipkin": "zipkin",
    "traefik": "traefik",
    "argocd": "argocd",
    "argoproj/argocd": "argocd",
    "flink": "flink",
    "apache/flink": "flink",
    "superset": "superset",
    "apache/superset": "superset",
    "metabase": "metabase",
    "metabase/metabase": "metabase",
    "dbt": "dbt",
    "clickhouse": "clickhouse",
    "clickhouse/clickhouse-server": "clickhouse",
    "milvus": "milvus",
    "milvusdb/milvus": "milvus",
    "qdrant": "qdrant",
    "qdrant/qdrant": "qdrant",
    "chroma": "chroma",
    "chromadb/chroma": "chroma",
    "weaviate": "weaviate",
    "semitechnologies/weaviate": "weaviate",
    "ollama": "ollama",
    "ollama/ollama": "ollama",
    "vllm": "vllm",
    "vllm/vllm": "vllm",
    "localstack": "localstack",
    "localstack/localstack": "localstack",
    "wazuh": "wazuh",
    "wazuh/wazuh-manager": "wazuh",
    "sonarqube": "sonarqube",
    "aquasec/trivy": "trivy",
    "shuffle": "shuffle",
    "frikky/shuffle": "shuffle",
    "suricata": "suricata",
    "jasonish/suricata": "suricata",
    "nmap": "nmap",
    "metasploit": "metasploit",
    "metasploitframework/metasploit-framework": "metasploit",
    "openvas": "openvas",
    "greenbone/openvas-scanner": "openvas",
    "code-server": "vscode_web",
    "codercom/code-server": "vscode_web"
}

IGNORED_DIRS = {
    ".git", ".svn", ".hg", "node_modules", ".venv", "venv", "env",
    "__pycache__", ".pytest_cache", ".idea", ".vscode", "dist", "build",
    "target", ".next", ".nuxt", ".output", ".terraform", "vendor"
}


class FolderAnalyzer:
    """Intelligent scanner that inspects folder contents, detects tech stack and start mechanisms."""

    @staticmethod
    def analyze(folder_path: str) -> Dict[str, Any]:
        path = Path(folder_path).resolve()
        if not path.exists():
            return {
                "success": False,
                "error": f"O diretório '{folder_path}' não foi encontrado."
            }
        if not path.is_dir():
            return {
                "success": False,
                "error": f"O caminho '{folder_path}' não é um diretório válido."
            }

        folder_name = path.name
        detected_tools: Set[str] = set()
        detected_techs: List[Dict[str, Any]] = []
        detected_services: List[Dict[str, Any]] = []
        detected_files: List[str] = []
        
        has_compose = False
        compose_file_path: Optional[Path] = None
        compose_content = ""
        has_dockerfile = False
        dockerfile_path: Optional[Path] = None
        has_k8s = False
        k8s_manifests: List[str] = []

        # Walk directory up to depth 3
        for root, dirs, files in os.walk(path):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]
            rel_root = Path(root).relative_to(path)
            depth = len(rel_root.parts)
            if depth > 3:
                continue

            for file in files:
                rel_file = str(rel_root / file) if str(rel_root) != '.' else file
                lower_file = file.lower()

                # 1. Docker Compose Detection
                if lower_file in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
                    if not has_compose:
                        has_compose = True
                        compose_file_path = Path(root) / file
                        detected_files.append(rel_file)

                # 2. Dockerfile Detection
                elif lower_file in ["dockerfile", "containerfile"] or lower_file.endswith(".dockerfile"):
                    has_dockerfile = True
                    if not dockerfile_path:
                        dockerfile_path = Path(root) / file
                    detected_files.append(rel_file)

                # 3. Kubernetes manifests
                elif (str(rel_root).startswith("k8s") or str(rel_root).startswith("kubernetes") or "k8s" in lower_file) and lower_file.endswith((".yml", ".yaml")):
                    has_k8s = True
                    k8s_manifests.append(rel_file)
                    detected_files.append(rel_file)

                # 4. Dependency & Manifest files
                elif lower_file in [
                    "package.json", "requirements.txt", "pyproject.toml", "pipfile", "setup.py",
                    "pom.xml", "build.gradle", "build.gradle.kts", "go.mod", "cargo.toml",
                    "gemfile", "composer.json", "dbt_project.yml"
                ]:
                    detected_files.append(rel_file)

        # Parse Docker Compose if present
        if has_compose and compose_file_path and compose_file_path.exists():
            try:
                with open(compose_file_path, "r", encoding="utf-8", errors="replace") as f:
                    compose_content = f.read()
                    data = yaml.safe_load(compose_content) or {}

                services = data.get("services", {})
                detected_techs.append({
                    "name": "Docker Compose",
                    "category": "orchestration",
                    "badge": "Docker Compose",
                    "confidence": "high"
                })

                for svc_name, svc_conf in services.items():
                    if not isinstance(svc_conf, dict):
                        continue
                    img = svc_conf.get("image", "")
                    ports = svc_conf.get("ports", [])
                    formatted_ports = []
                    for p in ports:
                        if isinstance(p, str):
                            formatted_ports.append(p)
                        elif isinstance(p, (int, float)):
                            formatted_ports.append(str(int(p)))
                        elif isinstance(p, dict):
                            published = p.get("published", "")
                            target = p.get("target", "")
                            if published and target:
                                formatted_ports.append(f"{published}:{target}")

                    # Match with known tools
                    matched_tool = None
                    # First check image string
                    if img:
                        clean_img = img.split(":")[0].lower()
                        for pattern, tool_id in IMAGE_TOOL_MAP.items():
                            if pattern in clean_img:
                                matched_tool = tool_id
                                break

                    # Second check service name
                    if not matched_tool:
                        clean_svc = svc_name.lower()
                        for pattern, tool_id in IMAGE_TOOL_MAP.items():
                            if pattern in clean_svc or clean_svc.startswith(pattern):
                                matched_tool = tool_id
                                break

                    if matched_tool:
                        detected_tools.add(matched_tool)
                    else:
                        detected_tools.add(svc_name.lower())

                    detected_services.append({
                        "service": svc_name,
                        "image": img or (svc_conf.get("build", "Dockerfile") if svc_conf.get("build") else "custom"),
                        "ports": formatted_ports,
                        "matched_tool": matched_tool or svc_name
                    })

            except Exception as e:
                pass

        # Parse Languages & Frameworks from files
        # Parse Languages & Frameworks from all detected files across the tree
        # A. Python
        python_manifests = [path / f for f in detected_files if f.lower().endswith("requirements.txt") or f.lower().endswith("pyproject.toml")]
        if python_manifests or any(f.lower().endswith(".py") for f in detected_files):
            tech_names = []
            for pm in python_manifests:
                if pm.exists():
                    try:
                        with open(pm, "r", encoding="utf-8", errors="replace") as rf:
                            req_text = rf.read().lower()
                            if "fastapi" in req_text and "FastAPI" not in tech_names: tech_names.append("FastAPI")
                            if "flask" in req_text and "Flask" not in tech_names: tech_names.append("Flask")
                            if "django" in req_text and "Django" not in tech_names: tech_names.append("Django")
                            if "pyspark" in req_text:
                                if "PySpark" not in tech_names: tech_names.append("PySpark")
                                detected_tools.add("spark")
                            if "pyiceberg" in req_text or "iceberg" in req_text:
                                if "Apache Iceberg" not in tech_names: tech_names.append("Apache Iceberg")
                                detected_tools.add("iceberg")
                            if "confluent-kafka" in req_text or "kafka-python" in req_text:
                                if "Kafka Client" not in tech_names: tech_names.append("Kafka Client")
                                detected_tools.add("kafka")
                            if "airflow" in req_text or "apache-airflow" in req_text:
                                if "Airflow" not in tech_names: tech_names.append("Airflow")
                                detected_tools.add("airflow")
                            if "google-generativeai" in req_text or "gemini" in req_text:
                                if "Gemini AI" not in tech_names: tech_names.append("Gemini AI")
                            if "pandas" in req_text and "Pandas" not in tech_names: tech_names.append("Pandas")
                            if "streamlit" in req_text and "Streamlit" not in tech_names: tech_names.append("Streamlit")
                            if ("torch" in req_text or "pytorch" in req_text) and "PyTorch" not in tech_names: tech_names.append("PyTorch")
                            if "langchain" in req_text and "LangChain" not in tech_names: tech_names.append("LangChain")
                    except Exception:
                        pass

            badge = "Python"
            if tech_names:
                badge += f" ({', '.join(tech_names[:4])})"
            detected_techs.append({
                "name": "Python",
                "category": "language",
                "badge": badge,
                "confidence": "high"
            })

        # B. Node.js / TypeScript
        node_manifests = [path / f for f in detected_files if f.lower().endswith("package.json")]
        if node_manifests:
            for pkg_file in node_manifests:
                if pkg_file.exists():
                    try:
                        with open(pkg_file, "r", encoding="utf-8", errors="replace") as pf:
                            pkg_data = json.load(pf)
                            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                            frameworks = []
                            if "next" in deps and "Next.js" not in frameworks: frameworks.append("Next.js")
                            elif "react" in deps and "React" not in frameworks: frameworks.append("React")
                            if "vue" in deps and "Vue" not in frameworks: frameworks.append("Vue")
                            if "express" in deps and "Express" not in frameworks: frameworks.append("Express")
                            if ("nest" in deps or "@nestjs/core" in deps) and "NestJS" not in frameworks: frameworks.append("NestJS")
                            if ("prisma" in deps or "@prisma/client" in deps) and "Prisma ORM" not in frameworks: frameworks.append("Prisma ORM")
                            if "tailwindcss" in deps and "Tailwind CSS" not in frameworks: frameworks.append("Tailwind CSS")
                            if "typescript" in deps and "TypeScript" not in frameworks: frameworks.append("TypeScript")

                            rel_loc = str(pkg_file.relative_to(path).parent)
                            loc_label = f" [{rel_loc}]" if rel_loc != "." else ""
                            badge = f"Node.js{loc_label}"
                            if frameworks:
                                badge += f" ({', '.join(frameworks[:4])})"
                            detected_techs.append({
                                "name": f"Node.js{loc_label}",
                                "category": "language",
                                "badge": badge,
                                "confidence": "high"
                            })
                    except Exception:
                        pass

        # C. Java / JVM
        if any(f.lower().endswith("pom.xml") or "build.gradle" in f.lower() for f in detected_files):
            detected_techs.append({
                "name": "Java / JVM",
                "category": "language",
                "badge": "Java / Maven / Gradle",
                "confidence": "high"
            })

        # D. Go
        if any(f.lower().endswith("go.mod") for f in detected_files):
            detected_techs.append({
                "name": "Go",
                "category": "language",
                "badge": "Golang",
                "confidence": "high"
            })

        # E. Rust
        if any(f.lower().endswith("cargo.toml") for f in detected_files):
            detected_techs.append({
                "name": "Rust",
                "category": "language",
                "badge": "Rust / Cargo",
                "confidence": "high"
            })

        # F. dbt Data Build Tool
        if any(f.lower().endswith("dbt_project.yml") for f in detected_files):
            detected_tools.add("dbt")
            detected_techs.append({
                "name": "dbt",
                "category": "data_engineering",
                "badge": "dbt (Data Build Tool)",
                "confidence": "high"
            })

        # G. Airflow DAGs folder or files
        has_airflow_files = any("dags" in f.lower() or f.lower().endswith("_dag.py") for f in detected_files)
        if has_airflow_files or (path / "dags").exists() or (path / "data" / "dags").exists():
            detected_tools.add("airflow")
            if not any(t["name"] == "Apache Airflow" for t in detected_techs):
                detected_techs.append({
                    "name": "Apache Airflow",
                    "category": "orchestration",
                    "badge": "Apache Airflow (DAGs)",
                    "confidence": "high"
                })

        # H. Kubernetes manifests
        if has_k8s:
            detected_techs.append({
                "name": "Kubernetes",
                "category": "orchestration",
                "badge": "Kubernetes (k8s/)",
                "confidence": "high"
            })

        # Add tech badges for matched catalog tools
        for tool_id in sorted(detected_tools):
            if not any(t["name"].lower() == tool_id for t in detected_techs):
                detected_techs.append({
                    "name": tool_id.capitalize(),
                    "category": "tool",
                    "badge": f"{tool_id.capitalize()}",
                    "confidence": "high"
                })

        # Determine Launch Strategy & Commands
        launch_strategy = "docker-compose"
        start_command = "docker compose up -d"
        stop_command = "docker compose down"
        restart_command = "docker compose restart"
        logs_command = "docker compose logs -f"

        if has_compose:
            launch_strategy = "docker-compose"
            start_command = "docker compose up -d"
            stop_command = "docker compose down"
            restart_command = "docker compose restart"
            logs_command = "docker compose logs -f"
        elif has_k8s:
            launch_strategy = "kubernetes"
            start_command = "kubectl apply -k k8s/"
            stop_command = "kubectl delete -k k8s/"
            restart_command = "kubectl rollout restart deployment"
            logs_command = "kubectl logs -f"
        elif has_dockerfile:
            launch_strategy = "dockerfile"
            start_command = f"docker build -t {folder_name.lower()} . && docker run -d --name {folder_name.lower()} {folder_name.lower()}"
            stop_command = f"docker stop {folder_name.lower()}"
            restart_command = f"docker restart {folder_name.lower()}"
            logs_command = f"docker logs -f {folder_name.lower()}"
        elif (path / "package.json").exists():
            launch_strategy = "node_cli"
            start_command = "npm run dev"
            stop_command = "kill $(lsof -t -i:3000)"
            restart_command = "npm run dev"
            logs_command = "npm run dev"
        elif (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
            launch_strategy = "python_cli"
            start_command = "python main.py"
            stop_command = "kill"
            restart_command = "python main.py"
            logs_command = "python main.py"

        # Generate a fallback/suggested compose file if missing
        suggested_compose = compose_content
        if not has_compose:
            suggested_compose = FolderAnalyzer._generate_compose_template(folder_name, detected_tools, has_dockerfile)

        # Build nice description
        tech_summary = [t["name"] for t in detected_techs if t["category"] in ["language", "tool", "data_engineering"]][:4]
        desc = f"Projeto importado de {folder_name}"
        if tech_summary:
            desc += f" com {', '.join(tech_summary)}"

        return {
            "success": True,
            "path": str(path),
            "name": folder_name,
            "description": desc,
            "tools": sorted(list(detected_tools)),
            "detected_techs": detected_techs,
            "detected_services": detected_services,
            "detected_files": detected_files[:20],
            "launch_strategy": launch_strategy,
            "start_command": start_command,
            "stop_command": stop_command,
            "restart_command": restart_command,
            "logs_command": logs_command,
            "has_compose": has_compose,
            "has_dockerfile": has_dockerfile,
            "has_k8s": has_k8s,
            "suggested_compose": suggested_compose
        }

    @staticmethod
    def _generate_compose_template(project_name: str, tools: Set[str], has_dockerfile: bool) -> str:
        """Generates a clean docker-compose.yml tailored for the detected project."""
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', project_name.lower())
        services = {}

        if has_dockerfile:
            services["app"] = {
                "build": ".",
                "container_name": f"{clean_name}-app",
                "ports": ["8000:8000"],
                "restart": "unless-stopped",
                "environment": ["PORT=8000"]
            }

        if "postgres" in tools:
            services["postgres"] = {
                "image": "postgres:16-alpine",
                "container_name": f"{clean_name}-postgres",
                "environment": {
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_PASSWORD": "password123",
                    "POSTGRES_DB": "app_db"
                },
                "ports": ["5432:5432"],
                "volumes": [f"{clean_name}_pgdata:/var/lib/postgresql/data"]
            }

        if "redis" in tools:
            services["redis"] = {
                "image": "redis:7-alpine",
                "container_name": f"{clean_name}-redis",
                "ports": ["6379:6379"]
            }

        compose_dict = {
            "version": "3.8",
            "services": services or {
                "app": {
                    "image": "alpine:latest",
                    "command": "tail -f /dev/null",
                    "container_name": f"{clean_name}-app"
                }
            }
        }
        return yaml.dump(compose_dict, sort_keys=False)

    @staticmethod
    def ensure_volume_folders(project_path: Path) -> List[str]:
        """Inspects docker-compose.yml in project_path and guarantees that all host volume paths exist on disk."""
        created_paths: List[str] = []
        compose_files = [
            project_path / "docker-compose.yml",
            project_path / "docker-compose.yaml",
            project_path / "compose.yml",
            project_path / "compose.yaml"
        ]
        for cf in compose_files:
            if cf.exists():
                try:
                    with open(cf, "r", encoding="utf-8", errors="replace") as f:
                        data = yaml.safe_load(f)
                    if isinstance(data, dict) and "services" in data:
                        for svc_name, svc_conf in data.get("services", {}).items():
                            if isinstance(svc_conf, dict):
                                for vol in svc_conf.get("volumes", []):
                                    if isinstance(vol, str) and ":" in vol:
                                        host_part = vol.split(":")[0].strip()
                                        if host_part.startswith("/") or host_part.startswith("\\"):
                                            continue
                                        clean_rel = host_part.lstrip("./\\").replace("\\", "/")
                                        if not clean_rel or clean_rel.endswith("_data"):
                                            continue
                                        target_full = project_path / clean_rel
                                        _, ext = os.path.splitext(clean_rel)
                                        if ext:
                                            target_full.parent.mkdir(parents=True, exist_ok=True)
                                            if not target_full.exists():
                                                target_full.write_text(f"# Initial configuration stub for {clean_rel}\n", encoding="utf-8")
                                                created_paths.append(str(target_full))
                                        else:
                                            if not target_full.exists():
                                                target_full.mkdir(parents=True, exist_ok=True)
                                                created_paths.append(str(target_full))
                except Exception:
                    pass
        return created_paths

