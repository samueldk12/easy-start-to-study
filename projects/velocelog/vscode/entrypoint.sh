#!/bin/sh
set -e

echo "=== [StackStudio VS Code Web IDE] Inicializando Workspace ==="

if [ "$AUTO_INSTALL_EXTENSIONS" = "true" ] && [ -f /home/coder/project/.vscode/extensions.json ]; then
  (
    sleep 3
    echo "[StackStudio] Instalando extensoes recomendadas em background..."
    for ext in ms-azuretools.vscode-docker ms-python.python ms-python.vscode-pylance ms-toolsai.jupyter cweijan.vscode-database-client2 mtxr.sqltools mtxr.sqltools-driver-pg ckolkman.vscode-postgres redhat.vscode-yaml eamodio.gitlens formulahendry.vscode-kafka; do
      code-server --install-extension "$ext" --force 2>/dev/null || true
    done
    echo "[StackStudio] Extensoes configuradas!"
  ) &
fi

echo "Iniciando code-server..."
exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project
