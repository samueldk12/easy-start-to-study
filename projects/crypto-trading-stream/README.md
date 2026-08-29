# 🚀 crypto-trading-stream

> Projeto crypto-trading-stream criado via CLI

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **PostgreSQL (OLTP + CDC)** | `data_engineering` | `5434` | - |
| **RabbitMQ + Management** | `backend` | `15672` | http://localhost:15672 |
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