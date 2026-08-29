"""
StackStudio CLI - Unified Command Line Interface
Manage projects, view separated service logs, execute tests, deploy to Kubernetes, and configure credentials.

Usage:
  python studio_cli.py list
  python studio_cli.py start <project_id>
  python studio_cli.py stop <project_id>
  python studio_cli.py test <project_id>
  python studio_cli.py logs <project_id> [--service <svc>] [-f] [--tail 50]
  python studio_cli.py create --name <name> --tools <tools> [--user <user>] [--password <pass>] [--clean]
  python studio_cli.py k8s deploy <project_id>
  python studio_cli.py k8s status <project_id>
  python studio_cli.py plugins list
"""

import sys
import os
import argparse
import subprocess
import asyncio
from typing import Optional

# Ensure current working directory is in sys.path and UTF-8 encoding is enabled
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from studio.models import ProjectCreateRequest
from studio.services.project_store import ProjectStore
from studio.services.scaffolder import ProjectScaffolder
from studio.services.docker_manager import DockerManager
from studio.services.k8s_manager import K8sManager
from studio.services.plugin_manager import PluginManager
from studio.services.catalog import get_catalog, PRESETS


# Terminal Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"""{CYAN}{BOLD}
===================================================================
 🚀 StackStudio CLI: Data Engineering, MLOps, Backend & DevOps
==================================================================={RESET}""")


async def cmd_list(args):
    projects = ProjectStore.list_projects()
    if not projects:
        print(f"{YELLOW}Nenhum projeto registrado no StackStudio.{RESET}")
        return

    print(f"\n{BOLD}{'ID DO PROJETO':<28} {'STATUS':<12} {'TEMPLATES':<14} {'FERRAMENTAS':<35}{RESET}")
    print("-" * 90)

    for p in projects:
        try:
            status_data = await DockerManager.get_project_status(p.path)
            status = status_data["status"]
        except Exception:
            status = "stopped"

        color = GREEN if status == "running" else (YELLOW if status == "partial" else RESET)
        tpl_str = "✨ Sim" if p.include_templates else "🧹 Limpo"
        tools_str = ", ".join(p.tools[:4]) + (f" (+{len(p.tools)-4})" if len(p.tools) > 4 else "")

        print(f"{BOLD}{p.id:<28}{RESET} {color}{status.upper():<12}{RESET} {tpl_str:<14} {tools_str:<35}")


async def cmd_start(args):
    proj = ProjectStore.get_project(args.project_id)
    if not proj:
        print(f"{RED}Erro: Projeto '{args.project_id}' não encontrado.{RESET}")
        return

    print(f"{CYAN}Iniciando containers do projeto {BOLD}{proj.name}{RESET}...")
    res = await DockerManager.start_project(proj.path)
    if res["success"]:
        print(f"{GREEN}✓ Todos os containers iniciados com sucesso!{RESET}")
    else:
        print(f"{RED}Falha ao iniciar: {res.get('stderr') or res.get('error')}{RESET}")


async def cmd_stop(args):
    proj = ProjectStore.get_project(args.project_id)
    if not proj:
        print(f"{RED}Erro: Projeto '{args.project_id}' não encontrado.{RESET}")
        return

    print(f"{YELLOW}Parando containers do projeto {BOLD}{proj.name}{RESET}...")
    res = await DockerManager.stop_project(proj.path)
    if res["success"]:
        print(f"{GREEN}✓ Containers parados com sucesso!{RESET}")
    else:
        print(f"{RED}Falha ao parar: {res.get('stderr') or res.get('error')}{RESET}")


async def cmd_logs(args):
    proj = ProjectStore.get_project(args.project_id)
    if not proj:
        print(f"{RED}Erro: Projeto '{args.project_id}' não encontrado.{RESET}")
        return

    service_filter = args.service
    tail = args.tail or 50
    follow = args.follow

    cmd = ["docker", "compose", "logs", f"--tail={tail}"]
    if follow:
        cmd.append("-f")
    if service_filter and service_filter.lower() != "all":
        cmd.append(service_filter)

    svc_label = f"[{service_filter}]" if service_filter else "[TODOS OS SERVIÇOS]"
    print(f"{CYAN}Streaming logs de {BOLD}{proj.name}{RESET} {svc_label} (tail={tail})...\n{RESET}")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=proj.path,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    await proc.wait()


async def cmd_test(args):
    proj = ProjectStore.get_project(args.project_id)
    if not proj:
        print(f"{RED}Erro: Projeto '{args.project_id}' não encontrado.{RESET}")
        return

    test_file = os.path.join(proj.path, "tests", "test_services.py")
    print(f"{CYAN}Executando suíte de testes para {BOLD}{proj.name}{RESET}...\n")

    proc = subprocess.run([sys.executable, test_file])
    if proc.returncode == 0:
        print(f"\n{GREEN}✓ Todos os testes de serviços passaram com sucesso!{RESET}")
    else:
        print(f"\n{RED}✗ Falha na execução dos testes.{RESET}")


async def cmd_create(args):
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    if not tools:
        print(f"{RED}Erro: Especifique ao menos uma ferramenta via --tools (ex: postgres,kafka,minio){RESET}")
        return

    user = args.user or "admin"
    password = args.password or "admin123"
    include_templates = not args.clean

    req = ProjectCreateRequest(
        name=args.name,
        description=args.description or f"Projeto {args.name} criado via CLI",
        tools=tools,
        include_templates=include_templates,
        default_user=user,
        default_password=password
    )

    scaffolder = ProjectScaffolder(req)
    project_dir = scaffolder.scaffold()

    ProjectStore.register_project(
        project_id=scaffolder.project_name,
        name=req.name,
        path=project_dir,
        description=req.description,
        tools=list(scaffolder.tools),
        include_templates=include_templates
    )

    print(f"\n{GREEN}✓ Projeto '{req.name}' gerado com sucesso em:{RESET} {project_dir}")
    print(f"{CYAN}Credenciais Padrão:{RESET} Usuário={BOLD}{user}{RESET} | Senha={BOLD}{password}{RESET}")
    print(f"{CYAN}Para iniciar:{RESET} python studio_cli.py start {scaffolder.project_name}")


async def cmd_k8s(args):
    sub = args.k8s_action
    proj = ProjectStore.get_project(args.project_id)
    if not proj:
        print(f"{RED}Erro: Projeto '{args.project_id}' não encontrado.{RESET}")
        return

    if sub == "deploy":
        print(f"{CYAN}Aplicando manifests no Kubernetes (kubectl apply -k k8s/)...{RESET}")
        res = await K8sManager.deploy_project(proj.path)
        if res["success"]:
            print(f"{GREEN}✓ Deploy aplicado no cluster!{RESET}")
            if res.get("stdout"):
                print(res["stdout"])
        else:
            print(f"{RED}Falha no deploy K8s: {res.get('stderr') or res.get('error')}{RESET}")

    elif sub == "destroy":
        print(f"{YELLOW}Removendo recursos do Kubernetes...{RESET}")
        res = await K8sManager.destroy_project(proj.path)
        if res["success"]:
            print(f"{GREEN}✓ Recursos K8s removidos!{RESET}")
        else:
            print(f"{RED}Falha ao remover K8s: {res.get('stderr') or res.get('error')}{RESET}")

    elif sub == "status":
        pods = await K8sManager.get_project_pods(proj.name)
        namespace = f"stack-{proj.name}"
        print(f"\n{BOLD}KUBERNETES STATUS (Namespace: {namespace}){RESET}")
        print("-" * 65)
        if not pods:
            print(f"{YELLOW}Nenhum pod encontrado no namespace {namespace}.{RESET}")
        else:
            for p in pods:
                ready_mark = f"{GREEN}✓ Ready{RESET}" if p["ready"] else f"{YELLOW}⏳ Not Ready{RESET}"
                print(f"Pod: {BOLD}{p['name']:<35}{RESET} | Status: {p['phase']:<10} | {ready_mark} | Restarts: {p['restarts']}")


def cmd_plugins(args):
    plugins = PluginManager.list_plugins()
    print(f"\n{BOLD}{'ID':<15} {'NOME':<30} {'CATEGORIA':<20} {'PORTA':<8} {'BADGE':<15}{RESET}")
    print("-" * 90)
    for p in plugins:
        print(f"{BOLD}{p.id:<15}{RESET} {p.name:<30} {p.category:<20} {str(p.default_port or '-'):<8} {p.badge:<15}")


from studio.services.topology_graph import TopologyGraphEngine


async def cmd_edit(args):
    proj = ProjectStore.get_project(args.project_id)
    if not proj:
        print(f"{RED}Erro: Projeto '{args.project_id}' não encontrado.{RESET}")
        return

    current_tools = set(proj.tools)
    if args.add:
        for t in args.add.split(","):
            if t.strip():
                current_tools.add(t.strip())
    if args.remove:
        for t in args.remove.split(","):
            if t.strip():
                current_tools.discard(t.strip())

    if not current_tools:
        print(f"{RED}Erro: O projeto deve conter ao menos uma ferramenta ativa.{RESET}")
        return

    user = args.user or "admin"
    password = args.password or "admin123"

    req = ProjectCreateRequest(
        name=proj.name,
        path=proj.path,
        description=args.description or proj.description,
        tools=list(current_tools),
        include_templates=proj.include_templates,
        default_user=user,
        default_password=password
    )

    scaffolder = ProjectScaffolder(req)
    project_dir = scaffolder.scaffold()

    ProjectStore.register_project(
        project_id=proj.id,
        name=proj.name,
        path=project_dir,
        description=req.description,
        tools=list(scaffolder.tools),
        include_templates=proj.include_templates
    )

    print(f"\n{GREEN}✓ Projeto '{proj.name}' atualizado com sucesso!{RESET}")
    print(f"{CYAN}Ferramentas Ativas ({len(current_tools)}):{RESET} {', '.join(sorted(current_tools))}")


def cmd_graph(args):
    proj = ProjectStore.get_project(args.project_id)
    if not proj:
        print(f"{RED}Erro: Projeto '{args.project_id}' não encontrado.{RESET}")
        return

    if args.mermaid:
        print(f"\n```mermaid\n{TopologyGraphEngine.generate_mermaid(proj.tools)}\n```")
    else:
        print(f"\n{TopologyGraphEngine.generate_ascii_graph(proj.tools)}")


def main():
    parser = argparse.ArgumentParser(description="StackStudio CLI")
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="Lista todos os projetos e status")

    # start
    p_start = subparsers.add_parser("start", help="Inicia os containers do projeto")
    p_start.add_argument("project_id", help="ID do projeto")

    # stop
    p_stop = subparsers.add_parser("stop", help="Para os containers do projeto")
    p_stop.add_argument("project_id", help="ID do projeto")

    # logs
    p_logs = subparsers.add_parser("logs", help="Exibe ou transmite logs separados por serviço")
    p_logs.add_argument("project_id", help="ID do projeto")
    p_logs.add_argument("-s", "--service", help="Nome do serviço para filtrar (ex: postgres, kafka, spark)", default=None)
    p_logs.add_argument("-f", "--follow", help="Seguir logs em tempo real", action="store_true")
    p_logs.add_argument("-n", "--tail", help="Número de linhas iniciais", type=int, default=50)

    # test
    p_test = subparsers.add_parser("test", help="Executa a suíte de testes do projeto")
    p_test.add_argument("project_id", help="ID do projeto")

    # create
    p_create = subparsers.add_parser("create", help="Cria um novo projeto customizado")
    p_create.add_argument("--name", required=True, help="Nome do projeto")
    p_create.add_argument("--tools", required=True, help="Lista de ferramentas separadas por vírgula (ex: postgres,kafka,minio)")
    p_create.add_argument("--description", help="Descrição do projeto")
    p_create.add_argument("--user", help="Usuário administrador padrão (default: admin)", default="admin")
    p_create.add_argument("--password", help="Senha administradora padrão (default: admin123)", default="admin123")
    p_create.add_argument("--clean", help="Criar apenas estrutura limpa sem templates de código", action="store_true")

    # k8s
    p_k8s = subparsers.add_parser("k8s", help="Gerencia deploys no Kubernetes")
    p_k8s.add_argument("k8s_action", choices=["deploy", "destroy", "status"], help="Ação K8s")
    p_k8s.add_argument("project_id", help="ID do projeto")

    # edit
    p_edit = subparsers.add_parser("edit", help="Adiciona ou remove ferramentas de um projeto existente")
    p_edit.add_argument("project_id", help="ID do projeto")
    p_edit.add_argument("--add", help="Ferramentas a adicionar (separadas por vírgula)")
    p_edit.add_argument("--remove", help="Ferramentas a remover (separadas por vírgula)")
    p_edit.add_argument("--description", help="Nova descrição do projeto")
    p_edit.add_argument("--user", help="Novo usuário administrador padrão")
    p_edit.add_argument("--password", help="Nova senha administradora padrão")

    # graph
    p_graph = subparsers.add_parser("graph", help="Visualiza o grafo de dependências e arquitetura do projeto")
    p_graph.add_argument("project_id", help="ID do projeto")
    p_graph.add_argument("--mermaid", help="Exibe no formato Mermaid.js", action="store_true")

    args = parser.parse_args()
    if not args.command:
        print_banner()
        parser.print_help()
        return

    if args.command == "list":
        asyncio.run(cmd_list(args))
    elif args.command == "start":
        asyncio.run(cmd_start(args))
    elif args.command == "stop":
        asyncio.run(cmd_stop(args))
    elif args.command == "logs":
        asyncio.run(cmd_logs(args))
    elif args.command == "test":
        asyncio.run(cmd_test(args))
    elif args.command == "create":
        asyncio.run(cmd_create(args))
    elif args.command == "edit":
        asyncio.run(cmd_edit(args))
    elif args.command == "graph":
        cmd_graph(args)
    elif args.command == "k8s":
        asyncio.run(cmd_k8s(args))
    elif args.command == "plugins":
        cmd_plugins(args)


if __name__ == "__main__":
    main()
