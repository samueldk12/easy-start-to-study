# 🚀 devops-edge-stack

> Projeto devops-edge-stack criado via CLI

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
| **Ansible Automation** | `devops` | `-` | - |
| **Kong API Gateway** | `backend` | `8000` | http://localhost:8002 |
| **NGINX Proxy & Web Server** | `backend` | `8088` | http://localhost:8088 |
| **PostgreSQL (OLTP + CDC)** | `data_engineering` | `5434` | - |
| **Redis & Redis Commander** | `backend` | `6380` | http://localhost:8089 |
| **Terraform (IaC)** | `devops` | `-` | - |
| **VS Code Web (IDE)** | `devops` | `8443` | http://localhost:8443/?folder=/home/coder/project |

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