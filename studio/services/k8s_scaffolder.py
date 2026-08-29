"""
Kubernetes (K8s) Manifest Scaffolding and Generation Engine
Generates Deployments, StatefulSets, Services, ConfigMaps, Secrets, and Kustomization files.
"""

import os
import json
import yaml
from typing import Dict, List, Any, Set, Optional
from studio.models import ProjectCreateRequest
from studio.services.catalog import get_tool_by_id


class K8sScaffolder:
    def __init__(self, request: ProjectCreateRequest, tools: Set[str], project_dir: str):
        self.request = request
        self.project_name = request.name.strip().replace(" ", "-").lower()
        self.namespace = f"stack-{self.project_name}"
        self.project_dir = project_dir
        self.k8s_dir = os.path.join(project_dir, "k8s")
        self.tools = tools

    def scaffold(self):
        """Generates all Kubernetes resources and kustomization.yaml."""
        os.makedirs(self.k8s_dir, exist_ok=True)

        resources: List[str] = ["namespace.yaml", "configmap.yaml", "secret.yaml"]

        # 1. Namespace
        self._generate_namespace()

        # 2. ConfigMap & Secret
        self._generate_config_and_secret()

        # 3. Tool Deployments & Services
        manifest_map = {
            "postgres": ("postgres.yaml", self._generate_postgres_manifest),
            "mysql": ("mysql.yaml", lambda: self._generate_generic_manifest("mysql", "mysql:8.0", 3306, {"MYSQL_ROOT_PASSWORD": "rootpassword", "MYSQL_DATABASE": "app_db"})),
            "clickhouse": ("clickhouse.yaml", lambda: self._generate_generic_manifest("clickhouse", "clickhouse/clickhouse-server:24.3-alpine", 8123)),
            "doris": ("doris.yaml", lambda: self._generate_generic_manifest("doris", "apache/doris:2.0.3-fe-x86_64", 8030)),
            "starrocks": ("starrocks.yaml", lambda: self._generate_generic_manifest("starrocks", "starrocks/fe-ubuntu:3.2.4", 8030)),
            "redis": ("redis.yaml", self._generate_redis_manifest),
            "rabbitmq": ("rabbitmq.yaml", self._generate_rabbitmq_manifest),
            "redpanda": ("redpanda.yaml", lambda: self._generate_generic_manifest("redpanda", "redpandadata/redpanda:v24.1.2", 9092)),
            "pulsar": ("pulsar.yaml", lambda: self._generate_generic_manifest("pulsar", "apachepulsar/pulsar:3.2.2", 6650)),
            "minio": ("minio.yaml", self._generate_minio_manifest),
            "kafka": ("kafka.yaml", self._generate_kafka_manifest),
            "spark": ("spark.yaml", self._generate_spark_manifest),
            "flink": ("flink.yaml", lambda: self._generate_generic_manifest("flink", "flink:1.19-scala_2.12-java11", 8081)),
            "superset": ("superset.yaml", lambda: self._generate_generic_manifest("superset", "apache/superset:4.0.1", 8088, {"SUPERSET_SECRET_KEY": "supersecretkey123"})),
            "metabase": ("metabase.yaml", lambda: self._generate_generic_manifest("metabase", "metabase/metabase:latest", 3000)),
            "datahub": ("datahub.yaml", lambda: self._generate_generic_manifest("datahub", "linkedin/datahub-frontend-react:latest", 9002)),
            "ranger": ("ranger.yaml", lambda: self._generate_generic_manifest("ranger", "apache/ranger:2.4.0", 6080)),
            "temporal": ("temporal.yaml", lambda: self._generate_generic_manifest("temporal", "temporalio/ui:2.26.2", 8080)),
            "n8n": ("n8n.yaml", lambda: self._generate_generic_manifest("n8n", "n8nio/n8n:latest", 5678)),
            "vault": ("vault.yaml", lambda: self._generate_generic_manifest("vault", "hashicorp/vault:1.16.2", 8200, {"VAULT_DEV_ROOT_TOKEN_ID": "root"})),
            "qdrant": ("qdrant.yaml", self._generate_qdrant_manifest),
            "milvus": ("milvus.yaml", lambda: self._generate_generic_manifest("milvus", "milvusdb/milvus:v2.4.0", 19530)),
            "weaviate": ("weaviate.yaml", lambda: self._generate_generic_manifest("weaviate", "semitechnologies/weaviate:1.24.10", 8080)),
            "evidently": ("evidently.yaml", lambda: self._generate_generic_manifest("evidently", "evidently/evidently-service:latest", 8000)),
            "prometheus": ("prometheus.yaml", self._generate_prometheus_manifest),
            "grafana": ("grafana.yaml", self._generate_grafana_manifest),
            "loki": ("loki.yaml", lambda: self._generate_generic_manifest("loki", "grafana/loki:3.0.0", 3100)),
            "jaeger": ("jaeger.yaml", lambda: self._generate_generic_manifest("jaeger", "jaegertracing/all-in-one:1.57", 16686)),
            "traefik": ("traefik.yaml", lambda: self._generate_generic_manifest("traefik", "traefik:v3.0", 80)),
            "argocd": ("argocd.yaml", lambda: self._generate_generic_manifest("argocd", "quay.io/argoproj/argocd:v2.11.0", 8080)),
            "wazuh": ("wazuh.yaml", lambda: self._generate_generic_manifest("wazuh", "wazuh/wazuh-dashboard:4.7.5", 5601)),
            "splunk": ("splunk.yaml", lambda: self._generate_generic_manifest("splunk", "splunk/splunk:9.2.1", 8000, {"SPLUNK_START_ARGS": "--accept-license", "SPLUNK_PASSWORD": "AdminPassword123!"})),
            "elastic_security": ("elastic-security.yaml", lambda: self._generate_generic_manifest("elastic-security", "docker.elastic.co/kibana/kibana:8.13.4", 5601)),
            "thehive": ("thehive.yaml", lambda: self._generate_generic_manifest("thehive", "strangebee/thehive:5.2", 9000, {"SECRET": "thehivesecret123"})),
            "misp": ("misp.yaml", lambda: self._generate_generic_manifest("misp", "coolacid/misp-docker:core-latest", 80)),
            "shuffle": ("shuffle.yaml", lambda: self._generate_generic_manifest("shuffle", "ghcr.io/shuffle/shuffle-frontend:latest", 80)),
            "suricata": ("suricata.yaml", lambda: self._generate_generic_manifest("suricata", "jasonish/suricata:latest", None, command=["-i", "eth0"])),
            "zeek": ("zeek.yaml", lambda: self._generate_generic_manifest("zeek", "zeek/zeek:latest", None, command=["sleep", "infinity"])),
            "openvas": ("openvas.yaml", lambda: self._generate_generic_manifest("openvas", "greenbone/openvas-scanner:latest", 9392)),
            "nmap": ("nmap.yaml", lambda: self._generate_generic_manifest("nmap", "instrumentisto/nmap:latest", None, command=["sleep", "infinity"])),
            "metasploit": ("metasploit.yaml", lambda: self._generate_generic_manifest("metasploit", "metasploitframework/metasploit-framework:latest", None, command=["sleep", "infinity"])),
            "sonarqube": ("sonarqube.yaml", lambda: self._generate_generic_manifest("sonarqube", "sonarqube:community", 9000)),
            "trivy": ("trivy.yaml", lambda: self._generate_generic_manifest("trivy", "aquasec/trivy:latest", 4954)),
            "defectdojo": ("defectdojo.yaml", lambda: self._generate_generic_manifest("defectdojo", "defectdojo/defectdojo-django:latest", 8080)),
            "zap": ("zap.yaml", lambda: self._generate_generic_manifest("zap", "zaproxy/zap-stable:latest", 8080)),
            "gitleaks": ("gitleaks.yaml", lambda: self._generate_generic_manifest("gitleaks", "zricethezav/gitleaks:latest", None, command=["sleep", "infinity"])),
            "trufflehog": ("trufflehog.yaml", lambda: self._generate_generic_manifest("trufflehog", "trufflesecurity/trufflehog:latest", None, command=["sleep", "infinity"])),
            "teleport": ("teleport.yaml", lambda: self._generate_generic_manifest("teleport", "quay.io/gravitational/teleport:15.2.0", 3080)),
            "authentik": ("authentik.yaml", lambda: self._generate_generic_manifest("authentik", "ghcr.io/goauthentik/server:2024.4.2", 9000, {"AUTHENTIK_SECRET_KEY": "authentiksecretkey123"})),
            "opentelemetry": ("opentelemetry.yaml", self._generate_opentelemetry_manifest),
            "openmetadata": ("openmetadata.yaml", self._generate_openmetadata_manifest),
            "nginx": ("nginx.yaml", self._generate_nginx_manifest),
            "apigateway": ("apigateway.yaml", self._generate_apigateway_manifest),
            "vscode": ("vscode.yaml", self._generate_vscode_manifest),
            "hdfs": ("hdfs.yaml", self._generate_hdfs_manifest),
            "yarn": ("yarn.yaml", self._generate_yarn_manifest),
            "hive": ("hive.yaml", self._generate_hive_manifest),
            "zeppelin": ("zeppelin.yaml", self._generate_zeppelin_manifest),
            "ollama": ("ollama.yaml", self._generate_ollama_manifest),
            "open_webui": ("open-webui.yaml", self._generate_open_webui_manifest),
            "localai": ("localai.yaml", self._generate_localai_manifest),
            "ubuntu_sandbox": ("ubuntu-sandbox.yaml", lambda: self._generate_sandbox_manifest("ubuntu", "ubuntu:24.04")),
            "debian_sandbox": ("debian-sandbox.yaml", lambda: self._generate_sandbox_manifest("debian", "debian:bookworm-slim")),
            "alpine_sandbox": ("alpine-sandbox.yaml", lambda: self._generate_sandbox_manifest("alpine", "alpine:latest")),
            "arch_sandbox": ("arch-sandbox.yaml", lambda: self._generate_sandbox_manifest("arch", "archlinux:latest")),
        }

        for tool, (filename, generator) in manifest_map.items():
            if tool in self.tools:
                generator()
                resources.append(filename)

        # 4. Kustomization
        self._generate_kustomization(resources)

        # 5. Automation Scripts (deploy, destroy, port-forward)
        self._generate_k8s_scripts()

    def _generate_namespace(self):
        ns_dict = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": self.namespace,
                "labels": {
                    "app.kubernetes.io/name": self.project_name,
                    "app.kubernetes.io/managed-by": "StackStudio"
                }
            }
        }
        with open(os.path.join(self.k8s_dir, "namespace.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(ns_dict, f, sort_keys=False)

    def _generate_config_and_secret(self):
        cm_dict = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": f"{self.project_name}-config", "namespace": self.namespace},
            "data": {
                "ENVIRONMENT": "development",
                "PROJECT_NAME": self.project_name
            }
        }
        with open(os.path.join(self.k8s_dir, "configmap.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(cm_dict, f, sort_keys=False)

        user = self.request.default_user or "admin"
        password = self.request.default_password or "admin123"

        secret_dict = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": f"{self.project_name}-secret", "namespace": self.namespace},
            "type": "Opaque",
            "stringData": {
                "DEFAULT_USER": user,
                "DEFAULT_PASSWORD": password
            }
        }
        with open(os.path.join(self.k8s_dir, "secret.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(secret_dict, f, sort_keys=False)

    def _generate_generic_manifest(self, name: str, image: str, port: Optional[int] = None, env_dict: Optional[Dict[str, str]] = None, command: Optional[List[str]] = None):
        env_lines = ""
        if env_dict:
            for k, v in env_dict.items():
                env_lines += f"""        - name: {k}
          value: "{v}"
"""

        ports_container = ""
        ports_service = ""
        if port:
            ports_container = f"""        ports:
        - containerPort: {port}
          name: {name[:15]}"""
            ports_service = f"""---
apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {self.namespace}
  labels:
    app: {name}
spec:
  type: ClusterIP
  ports:
  - port: {port}
    targetPort: {port}
    name: {name[:15]}
  selector:
    app: {name}"""

        cmd_lines = ""
        if command:
            cmd_lines = f"""        command: {json.dumps(command)}"""

        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {self.namespace}
  labels:
    app: {name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
      - name: {name}
        image: {image}
{cmd_lines}
{ports_container}
{env_lines}
{ports_service}
"""
        with open(os.path.join(self.k8s_dir, f"{name}.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest.strip() + "\n")

    def _generate_postgres_manifest(self):
        self._generate_generic_manifest("postgres", "postgres:16-alpine", 5432, {
            "POSTGRES_USER": "postgres", "POSTGRES_PASSWORD": "postgres_password", "POSTGRES_DB": "oltp_db"
        })

    def _generate_redis_manifest(self):
        self._generate_generic_manifest("redis", "redis:7-alpine", 6379)

    def _generate_rabbitmq_manifest(self):
        self._generate_generic_manifest("rabbitmq", "rabbitmq:3-management-alpine", 5672, {
            "RABBITMQ_DEFAULT_USER": "guest", "RABBITMQ_DEFAULT_PASS": "guest"
        })

    def _generate_minio_manifest(self):
        self._generate_generic_manifest("minio", "minio/minio:RELEASE.2024-05-10T01-41-38Z", 9000, {
            "MINIO_ROOT_USER": "admin", "MINIO_ROOT_PASSWORD": "admin123"
        }, command=["server", "/data", "--console-address", ":9001"])

    def _generate_kafka_manifest(self):
        self._generate_generic_manifest("kafka", "confluentinc/cp-kafka:7.6.0", 9092, {
            "KAFKA_NODE_ID": "1",
            "KAFKA_PROCESS_ROLES": "broker,controller",
            "KAFKA_LISTENERS": "PLAINTEXT://:9092,CONTROLLER://:9093",
            "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://kafka:9092",
            "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@kafka:9093",
            "CLUSTER_ID": "MkU3OEVBNTcwNTJENDM2Qk"
        })

    def _generate_spark_manifest(self):
        self._generate_generic_manifest("spark-master", "apache/spark:3.5.1", 7077)

    def _generate_qdrant_manifest(self):
        self._generate_generic_manifest("qdrant", "qdrant/qdrant:latest", 6333)

    def _generate_prometheus_manifest(self):
        self._generate_generic_manifest("prometheus", "prom/prometheus:v2.53.0", 9090)

    def _generate_grafana_manifest(self):
        self._generate_generic_manifest("grafana", "grafana/grafana:11.0.0", 3000, {
            "GF_SECURITY_ADMIN_USER": "admin", "GF_SECURITY_ADMIN_PASSWORD": "admin"
        })

    def _generate_opentelemetry_manifest(self):
        self._generate_generic_manifest("opentelemetry", "otel/opentelemetry-collector-contrib:0.100.0", 4318)

    def _generate_openmetadata_manifest(self):
        self._generate_generic_manifest("openmetadata", "openmetadata/server:1.4.1", 8585)

    def _generate_nginx_manifest(self):
        self._generate_generic_manifest("nginx", "nginx:alpine", 80)

    def _generate_apigateway_manifest(self):
        self._generate_generic_manifest("kong", "kong:3.6-alpine", 8000, {"KONG_DATABASE": "off"})

    def _generate_vscode_manifest(self):
        self._generate_generic_manifest("vscode", "codercom/code-server:latest", 8080)

    def _generate_hdfs_manifest(self):
        self._generate_generic_manifest("hdfs-namenode", "bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8", 9870)

    def _generate_yarn_manifest(self):
        self._generate_generic_manifest("yarn-resourcemanager", "bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8", 8088)

    def _generate_hive_manifest(self):
        self._generate_generic_manifest("hive-metastore", "bde2020/hive:2.3.2-postgresql-metastore", 9083)

    def _generate_zeppelin_manifest(self):
        self._generate_generic_manifest("zeppelin", "apache/zeppelin:0.10.1", 8080)

    def _generate_ollama_manifest(self):
        self._generate_generic_manifest("ollama", "ollama/ollama:latest", 11434)

    def _generate_open_webui_manifest(self):
        self._generate_generic_manifest("open-webui", "ghcr.io/open-webui/open-webui:main", 8080, {"OLLAMA_BASE_URL": "http://ollama:11434"})

    def _generate_localai_manifest(self):
        self._generate_generic_manifest("localai", "localai/localai:latest-cpu", 8080)

    def _generate_sandbox_manifest(self, name: str, image: str):
        self._generate_generic_manifest(f"{name}-sandbox", image, None, command=["tail", "-f", "/dev/null"])

    def _generate_kustomization(self, resources: List[str]):
        kust = {
            "apiVersion": "kustomize.config.k8s.io/v1beta1",
            "kind": "Kustomization",
            "namespace": self.namespace,
            "resources": resources
        }
        with open(os.path.join(self.k8s_dir, "kustomization.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(kust, f, sort_keys=False)

    def _generate_k8s_scripts(self):
        deploy_sh = f"""#!/bin/bash
echo "Deploying {self.project_name} to Kubernetes..."
kubectl apply -k .
echo "Deployment applied! Checking pods:"
kubectl get pods -n {self.namespace}
"""
        with open(os.path.join(self.k8s_dir, "deploy.sh"), "w", encoding="utf-8") as f:
            f.write(deploy_sh)

        destroy_sh = f"""#!/bin/bash
echo "Destroying {self.project_name} Kubernetes resources..."
kubectl delete -k .
"""
        with open(os.path.join(self.k8s_dir, "destroy.sh"), "w", encoding="utf-8") as f:
            f.write(destroy_sh)
