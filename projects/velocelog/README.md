# 🚀 velocelog

> Projeto auto-detectado: velocelog

## 📦 Ferramentas Habilitadas

| Ferramenta | Categoria | Porta Host | Endpoint / UI |
| :--- | :--- | :--- | :--- |
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