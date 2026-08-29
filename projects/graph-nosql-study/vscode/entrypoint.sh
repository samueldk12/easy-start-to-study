#!/bin/sh
set -e

echo "=== [StackStudio VS Code Web IDE] Inicializando Workspace ==="

if [ "$AUTO_INSTALL_EXTENSIONS" = "true" ] && [ -f /home/coder/project/.vscode/extensions.json ]; then
  echo "Instalando extensoes oficiais recomendadas do projeto..."
  for ext in redhat.vscode-yaml eamodio.gitlens ms-azuretools.vscode-docker; do
    echo " -> Instalando extensao: $ext"
    code-server --install-extension "$ext" --force || echo "  [AVISO] Nao foi possivel instalar $ext, continuando..."
  done
  echo "Extensoes oficiais configuradas com sucesso!"
fi

echo "Iniciando code-server..."
exec code-server --auth none --bind-addr 0.0.0.0:8080 /home/coder/project
