# 🚀 fintech-backend-queue

> Microservicos Financeiros: Postgres + Redis Cache + RabbitMQ Filas + Hasura GraphQL + Keycloak IAM

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **Hasura GraphQL Engine** | `backend` | `8095` | http://localhost:8095 |
| **Keycloak IAM** | `backend` | `8090` | http://localhost:8090 |
| **PostgreSQL (OLTP + CDC)** | `data_engineering` | `5437` | - |
| **RabbitMQ + Management** | `backend` | `15673` | http://localhost:15672 |
| **Redis & Redis Commander** | `backend` | `6382` | http://localhost:8089 |

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