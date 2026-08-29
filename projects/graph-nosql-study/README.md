# 🚀 graph-nosql-study

> Projeto de Grafos e NoSQL com plugins customizados

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **MongoDB & Mongo Express** | `backend` | `27017` | http://localhost:8091 |
| **Neo4j Graph Database & Browser** | `data_engineering` | `7474` | http://localhost:7474 |

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