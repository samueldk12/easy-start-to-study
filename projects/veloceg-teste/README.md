# 🚀 veloceg-teste

> Projeto gerado via StackStudio

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **Apache Airflow 2.9** | `orchestration` | `8088` | http://localhost:8088 |
| **ClickHouse OLAP** | `data_engineering` | `8123` | http://localhost:8123/play |
| **Apache Doris (Real-Time MPP)** | `data_engineering` | `8030` | http://localhost:8030 |
| **Apache Flink (Stateful Stream)** | `data_engineering` | `8093` | http://localhost:8093 |
| **Apache Iceberg REST Catalog** | `data_engineering` | `8181` | http://localhost:8181/v1/config |
| **Apache Kafka (KRaft)** | `data_engineering` | `9092` | - |
| **Kafka Connect + Debezium** | `data_engineering` | `8083` | http://localhost:8083 |
| **Kafka UI (Provectus)** | `data_engineering` | `8087` | http://localhost:8087 |
| **MinIO Object Storage** | `data_engineering` | `9001` | http://localhost:9001 |
| **PostgreSQL 16 (OLTP)** | `data_engineering` | `5434` | - |
| **Redpanda (C++ Kafka Alternative)** | `backend` | `8099` | http://localhost:8099 |
| **Apache Spark 3.5 Cluster** | `data_engineering` | `8082` | http://localhost:8082 |
| **Apache Superset (BI & Data Viz)** | `data_engineering` | `8094` | http://localhost:8094 |

## ⚡ Como Iniciar o Projeto e Rodar os Testes

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