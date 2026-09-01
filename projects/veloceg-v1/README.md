# veloceg-v1

> Projeto gerado via StackStudio

## Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **Apache Airflow 2.9** | `orchestration` | `8088` | http://localhost:8088 |
| **dbt Core** | `data_engineering` | `-` | - |
| **Apache Iceberg REST Catalog** | `data_engineering` | `8181` | http://localhost:8181/v1/config |
| **JupyterLab Workspace** | `mlops` | `8888` | http://localhost:8888 |
| **Apache Kafka (KRaft)** | `data_engineering` | `9092` | - |
| **Kafka Connect + Debezium** | `data_engineering` | `8083` | http://localhost:8083 |
| **Kafka UI (Provectus)** | `data_engineering` | `8087` | http://localhost:8087 |
| **MinIO Object Storage** | `data_engineering` | `9001` | http://localhost:9001 |
| **PostgreSQL 16 (OLTP)** | `data_engineering` | `5434` | - |
| **Schema Registry** | `data_engineering` | `8086` | http://localhost:8086 |
| **Apache Spark 3.5 Cluster** | `data_engineering` | `8082` | http://localhost:8082 |
| **Trino SQL Engine** | `data_engineering` | `8085` | http://localhost:8085 |
| **VS Code Web (IDE)** | `devops` | `8443` | http://localhost:8443/?folder=/home/coder/project |

## Como Iniciar o Projeto e Rodar os Testes

```bash
docker compose up -d
python tests/test_services.py
```

Ou usando o Makefile:
```bash
make start
make test
make status
make logs
make stop
```