#!/bin/sh
set -e

echo "=== [StackStudio Multi-Root Workspace] Inicializando VS Code Web ==="

if [ "$AUTO_INSTALL_EXTENSIONS" = "true" ] && [ -f /home/coder/project/.vscode/extensions.json ]; then
  echo "Instalando extensoes oficiais recomendadas do Workspace Unificado..."
  for ext in redhat.vscode-yaml ms-azuretools.vscode-docker ms-python.python eamodio.gitlens mtxr.sqltools-driver-pg ms-python.vscode-pylance mtxr.sqltools ms-toolsai.jupyter cweijan.vscode-database-client2 ckolkman.vscode-postgres; do
    echo " -> Instalando extensao: $ext"
    code-server --install-extension "$ext" --force || echo "  [AVISO] Nao foi possivel instalar $ext, continuando..."
  done
  echo "Extensoes oficiais configuradas com sucesso!"
fi

echo "Iniciando code-server com Multi-Root Workspace..."
if [ -f /home/coder/project/workspace.code-workspace ]; then
  exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project/workspace.code-workspace
else
  exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project
fi
