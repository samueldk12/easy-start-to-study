#!/bin/sh
set -e

echo "=== [StackStudio VS Code Web IDE] Inicializando Workspace ==="

if [ "$AUTO_INSTALL_EXTENSIONS" = "true" ] && [ -f /home/coder/project/.vscode/extensions.json ]; then
  echo "Instalando extensoes oficiais recomendadas do projeto (Docker, Python, SQL/Database, etc)..."
  for ext in ms-azuretools.vscode-docker ms-python.python ms-python.vscode-pylance ms-toolsai.jupyter cweijan.vscode-database-client2 mtxr.sqltools mtxr.sqltools-driver-pg ckolkman.vscode-postgres redhat.vscode-yaml eamodio.gitlens formulahendry.vscode-kafka vscjava.vscode-java-pack; do
    echo " -> Instalando extensao: $ext"
    code-server --install-extension "$ext" --force || echo "  [AVISO] Nao foi possivel instalar $ext, continuando..."
  done
  echo "Extensoes oficiais configuradas com sucesso!"
fi

echo "Iniciando code-server..."
exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project
