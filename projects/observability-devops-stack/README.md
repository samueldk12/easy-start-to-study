# 🚀 observability-devops-stack

> Monitoramento e Metricas: ClickHouse OLAP + Prometheus + Grafana Dashboards + Portainer + pgAdmin

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **ClickHouse OLAP** | `data_engineering` | `8123` | http://localhost:8123/play |
| **Grafana Dashboards** | `devops` | `3005` | http://localhost:3005 |
| **pgAdmin 4** | `devops` | `5055` | http://localhost:5055 |
| **Portainer CE** | `devops` | `9443` | https://localhost:9443 |
| **PostgreSQL (OLTP + CDC)** | `data_engineering` | `5434` | - |
| **Prometheus** | `devops` | `9095` | http://localhost:9095 |

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