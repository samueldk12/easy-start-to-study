#!/bin/sh
set -e

echo "=== [StackStudio Multi-Root Workspace] Inicializando VS Code Web ==="

if [ "$AUTO_INSTALL_EXTENSIONS" = "true" ] && [ -f /home/coder/project/.vscode/extensions.json ]; then
  (
    sleep 3
    echo "[StackStudio] Instalando extensoes recomendadas em background..."
    for ext in ms-python.python cweijan.vscode-database-client2 redhat.vscode-yaml mtxr.sqltools-driver-pg ms-azuretools.vscode-docker ms-python.vscode-pylance ms-toolsai.jupyter eamodio.gitlens mtxr.sqltools ckolkman.vscode-postgres; do
      code-server --install-extension "$ext" --force 2>/dev/null || true
    done
    echo "[StackStudio] Extensoes configuradas!"
  ) &
fi

echo "Iniciando code-server com Multi-Root Workspace..."
if [ -f /home/coder/project/workspace.code-workspace ]; then
  exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project/workspace.code-workspace
else
  exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project
fi
