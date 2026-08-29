# 🚀 clean-lakehouse

> Lakehouse limpo sem templates iniciais

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **Apache Airflow 2.9** | `orchestration` | `8088` | http://localhost:8088 |
| **Apache Iceberg REST Catalog** | `data_engineering` | `8181` | http://localhost:8181/v1/config |
| **Apache Kafka (KRaft)** | `data_engineering` | `9092` | - |
| **MinIO Object Storage** | `data_engineering` | `9001` | http://localhost:9001 |
| **PostgreSQL (OLTP + CDC)** | `data_engineering` | `5435` | - |
| **Apache Spark 3.5 Cluster** | `data_engineering` | `8084` | http://localhost:8082 |
| **Trino SQL Engine** | `data_engineering` | `8085` | http://localhost:8085 |

## ⚡ Como Iniciar o Projeto

```bash
docker compose up -d
```

Ou usando o Makefile:
```bash
make start
make status
make logs
make stop
```