# 🚀 telemetry-governance-stack

> Projeto telemetry-governance-stack criado via CLI

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **Grafana Dashboards** | `devops` | `3005` | http://localhost:3005 |
| **OpenMetadata & Governança** | `data_engineering` | `8585` | http://localhost:8585 |
| **OpenTelemetry Collector** | `devops` | `4318` | http://localhost:13133 |
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