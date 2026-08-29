# 🚀 StackStudio: Easy Start to Study

> **Plataforma Plugável em Python com Web UI para Scaffolding, Orquestração e Testes Automatizados de Ambientes de Engenharia de Dados, MLOps, Backend e DevOps.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Pytest](https://img.shields.io/badge/Pytest-Unit%20%26%20Integration-0A9EDC.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 Visão Geral

O **StackStudio (Easy Start to Study)** resolve o desafio de configurar ambientes de estudo e produção locais para arquiteturas complexas. 

Com uma **Interface Web interativa (Dark Mode)** e uma **API Python totalmente plugável**, você pode criar em segundos projetos completos contendo desde **Lakehouses orientados a eventos (CDC + Iceberg + Spark + Trino + Airflow)** até stacks completas de **MLOps**, **Microsserviços/Mensageria** e **Observabilidade DevOps**.

Cada projeto gerado já vem acompanhado de:
- 🐳 **`docker-compose.yml`** modular com resolução automática de dependências e sem conflito de portas no Host.
- 🧹 **Opção de Estrutura**: Escolha entre **✨ Com Templates de Código/Exemplos** ou **🧹 Estrutura Limpa (Clean Slate)** para codificar do zero.
- 🧪 **Suíte de Testes Automatizados**: Testes de unidade (`pytest.mark.unit`) e testes de integração com os containers (`pytest.mark.integration`).
- ⚡ **Automação Completa**: Scripts de inicialização (`start.ps1`, `start.sh`, `stop.ps1`, `stop.sh`) e `Makefile` integrado.
- 📊 **Streaming de Logs ao Vivo & Health Checks**: Acompanhe a inicialização dos containers diretamente pela UI.

---

## 🖥️ Web UI Dashboard

O StackStudio oferece um painel visual moderno em **Dark Mode** para gerenciar múltiplos projetos:

```bash
# Iniciar o painel do StackStudio
python run_studio.py
```
Acesse no seu navegador: **[http://localhost:5050](http://localhost:5050)**

### Funcionalidades do Painel:
1. **Criar Novos Projetos**: Escolha o nome, selecione as ferramentas ou aplique **Presets de 1-Clique**.
2. **🧩 Sistema de Plugins Extensível**: Adicione qualquer nova ferramenta via arquivo YAML ou diretamente pela Web UI sem alterar o código-fonte.
3. **Controle de Templates & Pastas**: Alterne entre estrutura limpa ou com código starter; customize portas e nomes de pastas montadas nos volumes.
4. **Orquestração com 1-Clique**: Botões **Start**, **Pausar**, **Parar** e **Reiniciar** por projeto.
5. **Testes Automatizados com 1-Clique**: O botão **"Testar"** roda a bateria de testes do projeto e exibe o relatório de conformidade no terminal integrado.
6. **Acesso Direto às Web UIs**: Links automáticos para o Airflow, Kafka UI, Spark Master, MinIO Console, Trino, RabbitMQ, Redis Commander, Grafana, MLflow, etc.

---

## 🧩 Como Adicionar Novas Ferramentas via Plugins

O StackStudio é **100% extensível**. Você pode plugar qualquer banco de dados, broker ou ferramenta adicionando uma pasta em `plugins/` com um arquivo `plugin.yaml`:

### Exemplo: `plugins/mongodb/plugin.yaml`
```yaml
id: mongodb
name: MongoDB & Mongo Express
category: backend
description: Banco de dados NoSQL orientado a documentos com UI visual.
badge: NoSQL / Doc DB
default_port: 27017
ui_url: http://localhost:8091
compose_services:
  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
  mongo-express:
    image: mongo-express:latest
    ports:
      - "8091:8081"
    depends_on:
      - mongodb
volumes:
  - mongodb_data
```

*(Você também pode instalar plugins com 1 clique pela interface web no botão **"Plugins"** no topo da página).*

---

## 📦 4 Projetos de Estudo Pré-Configurados

O repositório já vem com **4 projetos prontos** cobrindo os cenários mais procurados no mercado:

```text
projects/
├── velocelog-lakehouse/          # 🌟 Lakehouse CDC (Kafka + Iceberg + Spark + Trino + Airflow)
├── ecommerce-mlops/              # 🤖 MLOps & Vector Search (MLflow + Qdrant + Jupyter + Redis)
├── fintech-backend-queue/        # 💳 Backend & Mensageria (Postgres + RabbitMQ + Hasura + Keycloak)
└── observability-devops-stack/   # 📊 Observabilidade (ClickHouse + Prometheus + Grafana + Portainer)
```

---

### 1. 🌟 `velocelog-lakehouse` (Data Engineering Lakehouse)
*Arquitetura moderna de Lakehouse orientada a eventos para capturar mutações transacionais (CDC) em tempo real.*

- **Stack Tecnológica**: PostgreSQL 16 (Logical Decoding) ➔ Debezium Connector ➔ Apache Kafka (KRaft) ➔ Apache Iceberg REST Catalog + MinIO S3 ➔ Apache Spark 3.5 (Structured Streaming Bronze/Silver) ➔ Trino Distributed SQL Engine ➔ Apache Airflow 2.9 (Orquestração Gold & Governança).
- **Código Incluído**:
  - `spark/apps/bronze_ingestion.py`: Ingestão contínua em streaming CDC para tabelas Iceberg particionadas.
  - `spark/apps/silver_sync.py`: Sincronização e upserts (`MERGE INTO`).
  - `airflow/dags/gold_aggregations.py`: DAG analítica para geração de Data Marts.
  - `airflow/dags/iceberg_maintenance.py`: DAG de compactação de pequenos arquivos e expiração de snapshots.
  - `postgres/init.sql`: DDL de e-commerce e replicação lógica (`dbz_publication`).
- **Como Iniciar e Testar**:
  ```bash
  cd projects/velocelog-lakehouse
  docker compose up -d
  make test
  ```

---

### 2. 🤖 `ecommerce-mlops` (MLOps & Semantic Vector Search)
*Stack completa para ciclo de vida de Machine Learning, Feature Store em tempo real e busca semântica vetorial.*

- **Stack Tecnológica**: PostgreSQL + Redis (Feature Store de baixa latência) + MinIO (S3 Artifact Store) + MLflow 2.13 (Rastreamento e Registro de Modelos) + Qdrant (Vector Database) + JupyterLab (PySpark & ML Environment).
- **Código Incluído**:
  - `ml/feature_engineering.py`: Pipeline de transformação e cálculo de escores de recência/monetário para churn.
  - `tests/unit/test_feature_engineering.py`: Testes unitários para regras de feature store.
- **Como Iniciar e Testar**:
  ```bash
  cd projects/ecommerce-mlops
  docker compose up -d
  make test-unit
  ```

---

### 3. 💳 `fintech-backend-queue` (Microserviços & Mensageria)
*Infraestrutura resiliente para transações financeiras, mensageria assíncrona, GraphQL e autenticação IAM.*

- **Stack Tecnológica**: PostgreSQL + Redis (Cache & Idempotency) + RabbitMQ (Filas & Dead Letter Exchange) + Hasura (GraphQL Engine instantânea) + Keycloak (IAM / OAuth2 / OIDC).
- **Código Incluído**:
  - `services/payment_processor.py`: Motor de validação de transações, cálculo de taxas e análise antifraude.
  - `tests/unit/test_payment_processor.py`: Testes unitários de regras de negócio financeiro.
- **Como Iniciar e Testar**:
  ```bash
  cd projects/fintech-backend-queue
  docker compose up -d
  make test-unit
  ```

---

### 4. 📊 `observability-devops-stack` (DevOps & Observabilidade)
*Monitoramento de telemetria em tempo real, dashboards unificados e banco de logs colunar analítico.*

- **Stack Tecnológica**: ClickHouse 24 (OLAP de altíssima performance para logs) + Prometheus (Scraping de métricas) + Grafana 11 (Dashboards) + Portainer CE (Gerenciamento visual Docker) + pgAdmin 4 + PostgreSQL.
- **Código Incluído**:
  - `monitoring/metrics_collector.py`: Agregador de percentis de latência (P50, P99) e formatador de métricas Prometheus.
  - `tests/unit/test_metrics_collector.py`: Testes unitários de agregação de métricas.
- **Como Iniciar e Testar**:
  ```bash
  cd projects/observability-devops-stack
  docker compose up -d
  make test-unit
  ```

---

## ☸️ Suporte Nativo ao Kubernetes (K8s)

Além de rodar localmente via Docker Compose, **todos os projetos gerados no StackStudio criam automaticamente manifests Kubernetes prontos para produção**:

```text
k8s/
├── namespace.yaml                    # Namespace isolado (ex: stack-fintech-backend-queue)
├── configmap.yaml                    # Variáveis de ambiente centralizadas
├── secret.yaml                       # Credenciais e senhas criptografadas
├── postgres.yaml                     # Deployment + ClusterIP Service
├── redis.yaml                        # Deployment + ClusterIP Service
├── rabbitmq.yaml                     # Deployment + ClusterIP Service (AMQP 5672 + UI 15672)
├── minio.yaml / kafka.yaml / spark.yaml
└── kustomization.yaml                # Orquestração Kustomize declarativa
```

### Como Fazer Deploy e Testar no Kubernetes:

```bash
# 1. Aplicar todos os manifests no cluster K8s:
kubectl apply -k k8s/

# 2. Verificar os pods e serviços em tempo real:
kubectl get pods -n stack-fintech-backend-queue
kubectl get svc -n stack-fintech-backend-queue

# 3. Rodar os testes automatizados do Kubernetes:
python -m pytest tests/integration/test_kubernetes_deployment.py

# 4. Destruir os recursos no cluster:
kubectl delete -k k8s/
```

*(Você também pode fazer o deploy no Kubernetes com 1 clique usando o botão **"K8s"** na Web UI).*

---

## 🧪 Suíte de Testes Automatizados

Todos os projetos gerados contam com uma estrutura padronizada com `pytest`:

```text
tests/
├── conftest.py                       # Fixtures compartilhadas (Postgres, MinIO S3, Redis, HTTP)
├── pytest.ini                        # Configurações do Pytest e markers (unit, integration)
├── run_all_tests.py                  # Runner CLI unificado
├── test_services.py                  # Health check & verificação de portas TCP/HTTP
├── unit/                             # Testes unitários (rápidos, sem dependência de containers)
└── integration/                      # Testes de integração (testam containers ativos e dados reais)
```

### Comandos de Teste:
```bash
# Rodar todos os testes (Unitários + Integração):
make test

# Rodar apenas os testes unitários (execução em ~0.3s):
make test-unit

# Rodar apenas os testes de integração:
make test-integration
```

---

## 🔌 Uso como Módulo Python Plugável

O motor do StackStudio pode ser importado diretamente em qualquer outro script Python para automatizar a criação e o ciclo de vida de projetos:

```python
from studio.models import ProjectCreateRequest
from studio.services.scaffolder import ProjectScaffolder
from studio.services.docker_manager import DockerManager

# 1. Definir o projeto
request = ProjectCreateRequest(
    name="meu-novo-lakehouse",
    description="Ambiente customizado de Engenharia de Dados",
    include_templates=False,  # <--- Estrutura limpa sem templates
    tools=["postgres", "kafka", "minio", "iceberg_rest", "spark", "trino", "airflow"],
    custom_ports={"postgres": 5439, "spark": 8092},
    custom_folders={"spark_apps": "meus_scripts_spark"}
)

# 2. Gerar a estrutura de arquivos e docker-compose
scaffolder = ProjectScaffolder(request)
project_path = scaffolder.scaffold()
print(f"Projeto gerado em: {project_path}")

# 3. Iniciar containers de forma assíncrona
# await DockerManager.start_project(project_path)
```

---

## 🛠️ Catálogo Completo de Ferramentas (24+)

| Categoria | Ferramentas Suportadas |
| :--- | :--- |
| **Engenharia de Dados** | PostgreSQL (CDC), MySQL 8, ClickHouse OLAP, Apache Kafka (KRaft), Confluent Schema Registry, Kafka Connect (Debezium), Kafka UI, MinIO S3, Apache Iceberg REST, Apache Spark 3.5, Trino SQL, dbt Core. |
| **MLOps** | MLflow, JupyterLab, Qdrant Vector DB, Redis Feature Store. |
| **Orquestração** | Apache Airflow 2.9, Mage.ai, Prefect. |
| **Backend & Mensageria** | Redis & Redis Commander, RabbitMQ, Hasura GraphQL Engine, Keycloak IAM. |
| **DevOps & Monitoramento** | Grafana, Prometheus, Portainer CE, pgAdmin 4. |

---

## ⚙️ Instalação & Pré-requisitos

1. **Docker & Docker Compose**: Certifique-se de que o [Docker Desktop](https://www.docker.com/) está instalado e em execução.
2. **Python 3.10+**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Iniciar o StackStudio**:
   ```bash
   python run_studio.py
   ```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte `LICENSE` para mais informações.
