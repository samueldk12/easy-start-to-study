# 🚀 ecommerce-mlops

> Stack Completa de MLOps: Rastreamento com MLflow, Vector DB Qdrant, JupyterLab e Feature Store Redis

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **JupyterLab Workspace** | `mlops` | `8888` | http://localhost:8888 |
| **MinIO Object Storage** | `data_engineering` | `9001` | http://localhost:9001 |
| **MLflow Tracking & Registry** | `mlops` | `5001` | http://localhost:5001 |
| **PostgreSQL (OLTP + CDC)** | `data_engineering` | `5434` | - |
| **Qdrant Vector DB** | `mlops` | `6333` | http://localhost:6333/dashboard |
| **Redis & Redis Commander** | `backend` | `6380` | http://localhost:8089 |

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