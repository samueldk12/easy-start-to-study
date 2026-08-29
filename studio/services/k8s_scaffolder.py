"""
Kubernetes (K8s) Manifest Scaffolding and Generation Engine
Generates Deployments, StatefulSets, Services, ConfigMaps, Secrets, and Kustomization files.
"""

import os
import yaml
from typing import Dict, List, Any, Set
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
        if "postgres" in self.tools:
            self._generate_postgres_manifest()
            resources.append("postgres.yaml")

        if "redis" in self.tools:
            self._generate_redis_manifest()
            resources.append("redis.yaml")

        if "rabbitmq" in self.tools:
            self._generate_rabbitmq_manifest()
            resources.append("rabbitmq.yaml")

        if "minio" in self.tools:
            self._generate_minio_manifest()
            resources.append("minio.yaml")

        if "kafka" in self.tools:
            self._generate_kafka_manifest()
            resources.append("kafka.yaml")

        if "spark" in self.tools:
            self._generate_spark_manifest()
            resources.append("spark.yaml")

        if "qdrant" in self.tools:
            self._generate_qdrant_manifest()
            resources.append("qdrant.yaml")

        if "clickhouse" in self.tools:
            self._generate_clickhouse_manifest()
            resources.append("clickhouse.yaml")

        if "prometheus" in self.tools:
            self._generate_prometheus_manifest()
            resources.append("prometheus.yaml")

        if "grafana" in self.tools:
            self._generate_grafana_manifest()
            resources.append("grafana.yaml")

        if "opentelemetry" in self.tools:
            self._generate_opentelemetry_manifest()
            resources.append("opentelemetry.yaml")

        if "openmetadata" in self.tools:
            self._generate_openmetadata_manifest()
            resources.append("openmetadata.yaml")

        if "nginx" in self.tools:
            self._generate_nginx_manifest()
            resources.append("nginx.yaml")

        if "apigateway" in self.tools:
            self._generate_apigateway_manifest()
            resources.append("apigateway.yaml")

        if "vscode" in self.tools:
            self._generate_vscode_manifest()
            resources.append("vscode.yaml")

        if "hdfs" in self.tools:
            self._generate_hdfs_manifest()
            resources.append("hdfs.yaml")

        if "yarn" in self.tools:
            self._generate_yarn_manifest()
            resources.append("yarn.yaml")

        if "hive" in self.tools:
            self._generate_hive_manifest()
            resources.append("hive.yaml")

        if "zeppelin" in self.tools:
            self._generate_zeppelin_manifest()
            resources.append("zeppelin.yaml")

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
                "DEFAULT_PASSWORD": password,
                "POSTGRES_PASSWORD": password,
                "MINIO_ROOT_PASSWORD": password,
                "RABBITMQ_DEFAULT_PASS": password
            }
        }
        with open(os.path.join(self.k8s_dir, "secret.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(secret_dict, f, sort_keys=False)

    def _generate_postgres_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: {self.namespace}
  labels:
    app: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          value: "postgres"
        - name: POSTGRES_DB
          value: "oltp_db"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: {self.namespace}
  labels:
    app: postgres
spec:
  type: ClusterIP
  ports:
  - port: 5432
    targetPort: 5432
    name: postgres
  selector:
    app: postgres
"""
        with open(os.path.join(self.k8s_dir, "postgres.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_redis_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: {self.namespace}
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
          name: redis
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: {self.namespace}
  labels:
    app: redis
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
  selector:
    app: redis
"""
        with open(os.path.join(self.k8s_dir, "redis.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_rabbitmq_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: rabbitmq
  namespace: {self.namespace}
  labels:
    app: rabbitmq
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
      - name: rabbitmq
        image: rabbitmq:3-management-alpine
        ports:
        - containerPort: 5672
          name: amqp
        - containerPort: 15672
          name: management
        env:
        - name: RABBITMQ_DEFAULT_USER
          value: "guest"
        - name: RABBITMQ_DEFAULT_PASS
          value: "guest"
---
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq
  namespace: {self.namespace}
  labels:
    app: rabbitmq
spec:
  type: ClusterIP
  ports:
  - port: 5672
    targetPort: 5672
    name: amqp
  - port: 15672
    targetPort: 15672
    name: management
  selector:
    app: rabbitmq
"""
        with open(os.path.join(self.k8s_dir, "rabbitmq.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_minio_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: {self.namespace}
  labels:
    app: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: minio/minio:RELEASE.2024-05-10T01-41-38Z
        command: ["minio", "server", "/data", "--console-address", ":9001"]
        ports:
        - containerPort: 9000
          name: s3-api
        - containerPort: 9001
          name: console
        env:
        - name: MINIO_ROOT_USER
          value: "admin"
        - name: MINIO_ROOT_PASSWORD
          value: "password123"
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: {self.namespace}
  labels:
    app: minio
spec:
  type: ClusterIP
  ports:
  - port: 9000
    targetPort: 9000
    name: s3-api
  - port: 9001
    targetPort: 9001
    name: console
  selector:
    app: minio
"""
        with open(os.path.join(self.k8s_dir, "minio.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_kafka_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka
  namespace: {self.namespace}
  labels:
    app: kafka
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:7.6.0
        ports:
        - containerPort: 9092
          name: plaintext
        env:
        - name: KAFKA_NODE_ID
          value: "1"
        - name: KAFKA_PROCESS_ROLES
          value: "broker,controller"
        - name: KAFKA_LISTENERS
          value: "PLAINTEXT://0.0.0.0:29092,CONTROLLER://0.0.0.0:29093,EXTERNAL://0.0.0.0:9092"
        - name: KAFKA_ADVERTISED_LISTENERS
          value: "PLAINTEXT://kafka:29092,EXTERNAL://localhost:9092"
        - name: KAFKA_LISTENER_SECURITY_PROTOCOL_MAP
          value: "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT"
        - name: KAFKA_CONTROLLER_QUORUM_VOTERS
          value: "1@kafka:29093"
        - name: KAFKA_CONTROLLER_LISTENER_NAMES
          value: "CONTROLLER"
        - name: CLUSTER_ID
          value: "MkU3OEVBNTcwNTJENDM2Qk"
        - name: KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR
          value: "1"
---
apiVersion: v1
kind: Service
metadata:
  name: kafka
  namespace: {self.namespace}
  labels:
    app: kafka
spec:
  type: ClusterIP
  ports:
  - port: 9092
    targetPort: 9092
    name: plaintext
  - port: 29092
    targetPort: 29092
    name: internal
  selector:
    app: kafka
"""
        with open(os.path.join(self.k8s_dir, "kafka.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_spark_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: spark-master
  namespace: {self.namespace}
  labels:
    app: spark-master
spec:
  replicas: 1
  selector:
    matchLabels:
      app: spark-master
  template:
    metadata:
      labels:
        app: spark-master
    spec:
      containers:
      - name: spark-master
        image: apache/spark:3.5.1-python3
        command: ["/opt/spark/bin/spark-class", "org.apache.spark.deploy.master.Master"]
        ports:
        - containerPort: 7077
          name: spark-rpc
        - containerPort: 8080
          name: master-ui
        env:
        - name: SPARK_NO_DAEMONIZE
          value: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: spark-master
  namespace: {self.namespace}
  labels:
    app: spark-master
spec:
  type: ClusterIP
  ports:
  - port: 7077
    targetPort: 7077
    name: spark-rpc
  - port: 8080
    targetPort: 8080
    name: master-ui
  selector:
    app: spark-master
"""
        with open(os.path.join(self.k8s_dir, "spark.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_qdrant_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: {self.namespace}
  labels:
    app: qdrant
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
          name: http
        - containerPort: 6334
          name: grpc
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: {self.namespace}
  labels:
    app: qdrant
spec:
  type: ClusterIP
  ports:
  - port: 6333
    targetPort: 6333
    name: http
  selector:
    app: qdrant
"""
        with open(os.path.join(self.k8s_dir, "qdrant.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_clickhouse_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: clickhouse
  namespace: {self.namespace}
  labels:
    app: clickhouse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: clickhouse
  template:
    metadata:
      labels:
        app: clickhouse
    spec:
      containers:
      - name: clickhouse
        image: clickhouse/clickhouse-server:24.3
        ports:
        - containerPort: 8123
          name: http
        - containerPort: 9000
          name: native
---
apiVersion: v1
kind: Service
metadata:
  name: clickhouse
  namespace: {self.namespace}
  labels:
    app: clickhouse
spec:
  type: ClusterIP
  ports:
  - port: 8123
    targetPort: 8123
    name: http
  selector:
    app: clickhouse
"""
        with open(os.path.join(self.k8s_dir, "clickhouse.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_prometheus_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: {self.namespace}
  labels:
    app: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.53.0
        ports:
        - containerPort: 9090
          name: http
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: {self.namespace}
  labels:
    app: prometheus
spec:
  type: ClusterIP
  ports:
  - port: 9090
    targetPort: 9090
    name: http
  selector:
    app: prometheus
"""
        with open(os.path.join(self.k8s_dir, "prometheus.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_grafana_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: {self.namespace}
  labels:
    app: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:11.0.0
        ports:
        - containerPort: 3000
          name: http
        env:
        - name: GF_SECURITY_ADMIN_USER
          value: "admin"
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: {self.namespace}
  labels:
    app: grafana
spec:
  type: ClusterIP
  ports:
  - port: 3000
    targetPort: 3000
    name: http
  selector:
    app: grafana
"""
        with open(os.path.join(self.k8s_dir, "grafana.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_opentelemetry_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: opentelemetry
  namespace: {self.namespace}
  labels:
    app: opentelemetry
spec:
  replicas: 1
  selector:
    matchLabels:
      app: opentelemetry
  template:
    metadata:
      labels:
        app: opentelemetry
    spec:
      containers:
      - name: opentelemetry
        image: otel/opentelemetry-collector-contrib:0.102.0
        ports:
        - containerPort: 4317
          name: otlp-grpc
        - containerPort: 4318
          name: otlp-http
        - containerPort: 13133
          name: health
---
apiVersion: v1
kind: Service
metadata:
  name: opentelemetry
  namespace: {self.namespace}
  labels:
    app: opentelemetry
spec:
  type: ClusterIP
  ports:
  - port: 4317
    targetPort: 4317
    name: otlp-grpc
  - port: 4318
    targetPort: 4318
    name: otlp-http
  - port: 13133
    targetPort: 13133
    name: health
  selector:
    app: opentelemetry
"""
        with open(os.path.join(self.k8s_dir, "opentelemetry.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_openmetadata_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: openmetadata
  namespace: {self.namespace}
  labels:
    app: openmetadata
spec:
  replicas: 1
  selector:
    matchLabels:
      app: openmetadata
  template:
    metadata:
      labels:
        app: openmetadata
    spec:
      containers:
      - name: openmetadata
        image: docker.getcollate.io/openmetadata/server:1.4.2
        ports:
        - containerPort: 8585
          name: http
        env:
        - name: DB_HOST
          value: "postgres"
        - name: DB_PORT
          value: "5432"
        - name: DB_USER
          value: "postgres"
        - name: DB_USER_PASSWORD
          value: "postgres"
---
apiVersion: v1
kind: Service
metadata:
  name: openmetadata
  namespace: {self.namespace}
  labels:
    app: openmetadata
spec:
  type: ClusterIP
  ports:
  - port: 8585
    targetPort: 8585
    name: http
  selector:
    app: openmetadata
"""
        with open(os.path.join(self.k8s_dir, "openmetadata.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_nginx_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  namespace: {self.namespace}
  labels:
    app: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
          name: http
---
apiVersion: v1
kind: Service
metadata:
  name: nginx
  namespace: {self.namespace}
  labels:
    app: nginx
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 80
    name: http
  selector:
    app: nginx
"""
        with open(os.path.join(self.k8s_dir, "nginx.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_apigateway_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: kong
  namespace: {self.namespace}
  labels:
    app: kong
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kong
  template:
    metadata:
      labels:
        app: kong
    spec:
      containers:
      - name: kong
        image: kong:3.6
        ports:
        - containerPort: 8000
          name: proxy
        - containerPort: 8001
          name: admin
        - containerPort: 8002
          name: gui
        env:
        - name: KONG_DATABASE
          value: "off"
        - name: KONG_PROXY_ACCESS_LOG
          value: "/dev/stdout"
        - name: KONG_ADMIN_ACCESS_LOG
          value: "/dev/stdout"
---
apiVersion: v1
kind: Service
metadata:
  name: kong
  namespace: {self.namespace}
  labels:
    app: kong
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    name: proxy
  - port: 8001
    targetPort: 8001
    name: admin
  - port: 8002
    targetPort: 8002
    name: gui
  selector:
    app: kong
"""
        with open(os.path.join(self.k8s_dir, "apigateway.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_vscode_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: vscode
  namespace: {self.namespace}
  labels:
    app: vscode
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vscode
  template:
    metadata:
      labels:
        app: vscode
    spec:
      containers:
      - name: vscode
        image: codercom/code-server:latest
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: PASSWORD
          value: "admin"
        - name: DEFAULT_WORKSPACE
          value: "/home/coder/project"
---
apiVersion: v1
kind: Service
metadata:
  name: vscode
  namespace: {self.namespace}
  labels:
    app: vscode
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  selector:
    app: vscode
"""
        with open(os.path.join(self.k8s_dir, "vscode.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_hdfs_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: namenode
  namespace: {self.namespace}
  labels:
    app: namenode
spec:
  replicas: 1
  selector:
    matchLabels:
      app: namenode
  template:
    metadata:
      labels:
        app: namenode
    spec:
      containers:
      - name: namenode
        image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
        ports:
        - containerPort: 9870
          name: http
        - containerPort: 9000
          name: ipc
        env:
        - name: CLUSTER_NAME
          value: "hadoop-cluster"
        - name: CORE_CONF_fs_defaultFS
          value: "hdfs://namenode:9000"
---
apiVersion: v1
kind: Service
metadata:
  name: namenode
  namespace: {self.namespace}
  labels:
    app: namenode
spec:
  type: ClusterIP
  ports:
  - port: 9870
    targetPort: 9870
    name: http
  - port: 9000
    targetPort: 9000
    name: ipc
  selector:
    app: namenode
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datanode
  namespace: {self.namespace}
  labels:
    app: datanode
spec:
  replicas: 1
  selector:
    matchLabels:
      app: datanode
  template:
    metadata:
      labels:
        app: datanode
    spec:
      containers:
      - name: datanode
        image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
        ports:
        - containerPort: 9864
          name: http
        env:
        - name: CORE_CONF_fs_defaultFS
          value: "hdfs://namenode:9000"
---
apiVersion: v1
kind: Service
metadata:
  name: datanode
  namespace: {self.namespace}
  labels:
    app: datanode
spec:
  type: ClusterIP
  ports:
  - port: 9864
    targetPort: 9864
    name: http
  selector:
    app: datanode
"""
        with open(os.path.join(self.k8s_dir, "hdfs.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_yarn_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: resourcemanager
  namespace: {self.namespace}
  labels:
    app: resourcemanager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: resourcemanager
  template:
    metadata:
      labels:
        app: resourcemanager
    spec:
      containers:
      - name: resourcemanager
        image: bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8
        ports:
        - containerPort: 8088
          name: http
        env:
        - name: CORE_CONF_fs_defaultFS
          value: "hdfs://namenode:9000"
        - name: YARN_CONF_yarn_resourcemanager_hostname
          value: "resourcemanager"
---
apiVersion: v1
kind: Service
metadata:
  name: resourcemanager
  namespace: {self.namespace}
  labels:
    app: resourcemanager
spec:
  type: ClusterIP
  ports:
  - port: 8088
    targetPort: 8088
    name: http
  selector:
    app: resourcemanager
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodemanager
  namespace: {self.namespace}
  labels:
    app: nodemanager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nodemanager
  template:
    metadata:
      labels:
        app: nodemanager
    spec:
      containers:
      - name: nodemanager
        image: bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8
        ports:
        - containerPort: 8042
          name: http
        env:
        - name: CORE_CONF_fs_defaultFS
          value: "hdfs://namenode:9000"
        - name: YARN_CONF_yarn_resourcemanager_hostname
          value: "resourcemanager"
---
apiVersion: v1
kind: Service
metadata:
  name: nodemanager
  namespace: {self.namespace}
  labels:
    app: nodemanager
spec:
  type: ClusterIP
  ports:
  - port: 8042
    targetPort: 8042
    name: http
  selector:
    app: nodemanager
"""
        with open(os.path.join(self.k8s_dir, "yarn.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_hive_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: hive-metastore
  namespace: {self.namespace}
  labels:
    app: hive-metastore
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hive-metastore
  template:
    metadata:
      labels:
        app: hive-metastore
    spec:
      containers:
      - name: hive-metastore
        image: bde2020/hive:2.3.2-postgresql-metastore
        ports:
        - containerPort: 9083
          name: thrift
        env:
        - name: HIVE_CORE_CONF_javax_jdo_option_ConnectionURL
          value: "jdbc:postgresql://postgres:5432/metastore_db"
        - name: HIVE_CORE_CONF_javax_jdo_option_ConnectionDriverName
          value: "org.postgresql.Driver"
        - name: HIVE_CORE_CONF_javax_jdo_option_ConnectionUserName
          value: "postgres"
        - name: HIVE_CORE_CONF_javax_jdo_option_ConnectionPassword
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: POSTGRES_PASSWORD
        - name: CORE_CONF_fs_defaultFS
          value: "hdfs://namenode:9000"
---
apiVersion: v1
kind: Service
metadata:
  name: hive-metastore
  namespace: {self.namespace}
  labels:
    app: hive-metastore
spec:
  type: ClusterIP
  ports:
  - port: 9083
    targetPort: 9083
    name: thrift
  selector:
    app: hive-metastore
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hive-server
  namespace: {self.namespace}
  labels:
    app: hive-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hive-server
  template:
    metadata:
      labels:
        app: hive-server
    spec:
      containers:
      - name: hive-server
        image: bde2020/hive:2.3.2-postgresql-metastore
        command: ["/opt/hive/bin/hive", "--service", "hiveserver2"]
        ports:
        - containerPort: 10002
          name: http
        - containerPort: 10000
          name: thrift
        env:
        - name: HIVE_CORE_CONF_javax_jdo_option_ConnectionURL
          value: "jdbc:postgresql://postgres:5432/metastore_db"
        - name: HIVE_CORE_CONF_javax_jdo_option_ConnectionDriverName
          value: "org.postgresql.Driver"
        - name: HIVE_CORE_CONF_javax_jdo_option_ConnectionUserName
          value: "postgres"
        - name: HIVE_CORE_CONF_javax_jdo_option_ConnectionPassword
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: POSTGRES_PASSWORD
        - name: CORE_CONF_fs_defaultFS
          value: "hdfs://namenode:9000"
---
apiVersion: v1
kind: Service
metadata:
  name: hive-server
  namespace: {self.namespace}
  labels:
    app: hive-server
spec:
  type: ClusterIP
  ports:
  - port: 10002
    targetPort: 10002
    name: http
  - port: 10000
    targetPort: 10000
    name: thrift
  selector:
    app: hive-server
"""
        with open(os.path.join(self.k8s_dir, "hive.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

    def _generate_zeppelin_manifest(self):
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: zeppelin
  namespace: {self.namespace}
  labels:
    app: zeppelin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zeppelin
  template:
    metadata:
      labels:
        app: zeppelin
    spec:
      containers:
      - name: zeppelin
        image: apache/zeppelin:0.10.1
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: ZEPPELIN_PORT
          value: "8080"
        - name: ZEPPELIN_ANONYMOUS
          value: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: zeppelin
  namespace: {self.namespace}
  labels:
    app: zeppelin
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  selector:
    app: zeppelin
"""
        with open(os.path.join(self.k8s_dir, "zeppelin.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest)

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
        scripts_dir = os.path.join(self.project_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)

        deploy_ps1 = f"""Write-Host "Deploying {self.project_name} to Kubernetes ({self.namespace})..." -ForegroundColor Cyan
kubectl apply -k k8s/
Write-Host "Checking pod rollout status..." -ForegroundColor Yellow
kubectl get pods -n {self.namespace} -w
"""
        with open(os.path.join(scripts_dir, "k8s-deploy.ps1"), "w", encoding="utf-8") as f:
            f.write(deploy_ps1)

        deploy_sh = f"""#!/bin/bash
echo "Deploying {self.project_name} to Kubernetes ({self.namespace})..."
kubectl apply -k k8s/
echo "Checking pod rollout status..."
kubectl get pods -n {self.namespace} -w
"""
        with open(os.path.join(scripts_dir, "k8s-deploy.sh"), "w", encoding="utf-8") as f:
            f.write(deploy_sh)

        destroy_ps1 = f"""Write-Host "Deleting {self.project_name} from Kubernetes ({self.namespace})..." -ForegroundColor Yellow
kubectl delete -k k8s/
"""
        with open(os.path.join(scripts_dir, "k8s-destroy.ps1"), "w", encoding="utf-8") as f:
            f.write(destroy_ps1)

        destroy_sh = f"""#!/bin/bash
echo "Deleting {self.project_name} from Kubernetes ({self.namespace})..."
kubectl delete -k k8s/
"""
        with open(os.path.join(scripts_dir, "k8s-destroy.sh"), "w", encoding="utf-8") as f:
            f.write(destroy_sh)

        port_forward_ps1 = f"""Write-Host "Port-forwarding Kubernetes services for {self.project_name} ({self.namespace})..." -ForegroundColor Cyan
Write-Host "Forwarding Postgres (5434:5432), Redis (6380:6379), RabbitMQ (15672:15672)..."
kubectl port-forward -n {self.namespace} svc/postgres 5434:5432 &
kubectl port-forward -n {self.namespace} svc/redis 6380:6379 &
kubectl port-forward -n {self.namespace} svc/rabbitmq 15672:15672 &
"""
        with open(os.path.join(scripts_dir, "k8s-port-forward.ps1"), "w", encoding="utf-8") as f:
            f.write(port_forward_ps1)
