import os
import shutil
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from studio.app import app
from studio.models import ProjectCreateRequest, ToolPlugin, ContainerExecRequest
from studio.services.catalog import get_catalog, PRESETS, CATEGORIES
from studio.services.plugin_manager import PluginManager
from studio.services.scaffolder import ProjectScaffolder
from studio.services.k8s_scaffolder import K8sScaffolder
from studio.services.project_store import ProjectStore

client = TestClient(app)
TEST_DIR = './projects/test-llm-os-stack'
TEST_OS_DIR = './projects/test-os-sandbox'

def setup_module():
    for d in [TEST_DIR, TEST_OS_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

def teardown_module():
    for d in [TEST_DIR, TEST_OS_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)


def test_catalog_llm_and_os_tools():
    catalog = get_catalog()
    all_tool_ids = [tool.id for cat in catalog for tool in cat.tools]
    
    # Check LLMs
    assert 'ollama' in all_tool_ids
    assert 'open_webui' in all_tool_ids
    assert 'localai' in all_tool_ids
    
    # Check OS Sandboxes
    assert 'ubuntu_sandbox' in all_tool_ids
    assert 'debian_sandbox' in all_tool_ids
    assert 'alpine_sandbox' in all_tool_ids
    assert 'arch_sandbox' in all_tool_ids
    
    # Check Presets
    preset_ids = [p.id for p in PRESETS]
    assert 'local_llm_ai_stack' in preset_ids
    assert 'linux_os_sandbox' in preset_ids


def test_scaffold_local_llm_stack():
    req = ProjectCreateRequest(
        name='test-llm-os-stack',
        path=TEST_DIR,
        description='Local LLM Stack Test',
        tools=['ollama', 'open_webui', 'localai', 'vscode'],
        custom_ports={'ollama': 11434, 'open_webui': 3000, 'localai': 8091, 'vscode': 8443}
    )
    scaffolder = ProjectScaffolder(req)
    proj_info = scaffolder.scaffold()
    
    assert os.path.exists(os.path.join(TEST_DIR, 'docker-compose.yml'))
    with open(os.path.join(TEST_DIR, 'docker-compose.yml'), 'r', encoding='utf-8') as f:
        compose_text = f.read()
        assert 'ollama/ollama' in compose_text
        assert 'ghcr.io/open-webui/open-webui' in compose_text
        assert 'localai/localai' in compose_text
        assert 'OLLAMA_BASE_URL' in compose_text

    # Verify K8s Scaffolding
    k8s = K8sScaffolder(request=req, tools=set(req.tools), project_dir=TEST_DIR)
    k8s.scaffold()
    assert os.path.exists(os.path.join(TEST_DIR, 'k8s', 'ollama.yaml'))
    assert os.path.exists(os.path.join(TEST_DIR, 'k8s', 'open-webui.yaml'))
    assert os.path.exists(os.path.join(TEST_DIR, 'k8s', 'localai.yaml'))


def test_scaffold_os_sandboxes():
    req = ProjectCreateRequest(
        name='test-os-sandbox',
        path=TEST_OS_DIR,
        description='OS Sandbox Test',
        tools=['ubuntu_sandbox', 'debian_sandbox', 'alpine_sandbox', 'arch_sandbox'],
        custom_ports={}
    )
    scaffolder = ProjectScaffolder(req)
    scaffolder.scaffold()
    
    assert os.path.exists(os.path.join(TEST_OS_DIR, 'docker-compose.yml'))
    with open(os.path.join(TEST_OS_DIR, 'docker-compose.yml'), 'r', encoding='utf-8') as f:
        compose_text = f.read()
        assert 'ubuntu:24.04' in compose_text
        assert 'debian:bookworm-slim' in compose_text
        assert 'alpine:latest' in compose_text
        assert 'archlinux:latest' in compose_text

    # Verify K8s Scaffolding
    k8s = K8sScaffolder(request=req, tools=set(req.tools), project_dir=TEST_OS_DIR)
    k8s.scaffold()
    assert os.path.exists(os.path.join(TEST_OS_DIR, 'k8s', 'ubuntu-sandbox.yaml'))
    assert os.path.exists(os.path.join(TEST_OS_DIR, 'k8s', 'alpine-sandbox.yaml'))


def test_custom_service_creation_docker_image():
    plugin = ToolPlugin(
        id='custom_redis_cache',
        name='Custom Redis Cache',
        category='backend',
        source_type='image',
        image='redis:7-alpine',
        default_port=6389,
        container_port=6379,
        badge='Cache'
    )
    response = client.post('/api/custom-services/create', json=plugin.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 'custom_redis_cache'
    assert 'custom-redis-cache' in data['compose_services']
    assert data['compose_services']['custom-redis-cache']['image'] == 'redis:7-alpine'
    assert any('6379' in p for p in data['compose_services']['custom-redis-cache']['ports'])


def test_custom_service_creation_dockerfile():
    plugin = ToolPlugin(
        id='custom_node_api',
        name='Custom Node API',
        category='backend',
        source_type='dockerfile',
        dockerfile_content='FROM node:20-alpine\nWORKDIR /app\nCMD [node, -e, console.log(\x27running\x27)]',
        default_port=3030,
        container_port=3000,
        badge='Node.js'
    )
    response = client.post('/api/custom-services/create', json=plugin.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 'custom_node_api'
    assert 'custom-node-api' in data['compose_services']
    assert 'build' in data['compose_services']['custom-node-api']


def test_custom_service_creation_github():
    plugin = ToolPlugin(
        id='custom_github_worker',
        name='Custom GitHub Worker',
        category='backend',
        source_type='github',
        git_url='https://github.com/example/worker.git',
        git_branch='main',
        default_port=9090,
        container_port=9090,
        badge='Worker'
    )
    response = client.post('/api/custom-services/create', json=plugin.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 'custom_github_worker'
    assert 'custom-github-worker' in data['compose_services']
    assert 'build' in data['compose_services']['custom-github-worker']
    assert data['compose_services']['custom-github-worker']['build']['context'] == 'https://github.com/example/worker.git#main'


def test_container_exec_api_mocked():
    "Test POST /api/projects/{id}/services/{service}/exec endpoint."
    projects = ProjectStore.list_projects()
    if projects:
        proj_id = projects[0].id
        with patch('studio.services.docker_manager.DockerManager.exec_in_container') as mock_exec:
            mock_exec.return_value = {
                'success': True,
                'returncode': 0,
                'stdout': 'Linux test 6.6.0 #1 SMP x86_64\n',
                'stderr': '',
                'latency_ms': 12.5
            }
            res = client.post(f'/api/projects/{proj_id}/services/postgres/exec', json={'command': 'uname -a'})
            assert res.status_code == 200
            data = res.json()
            assert data['success'] is True
            assert 'Linux' in data['stdout']
            assert data['latency_ms'] == 12.5


def test_api_catalog_endpoint():
    response = client.get('/api/catalog')
    assert response.status_code == 200
    categories = response.json()
    cat_ids = [c['id'] for c in categories]
    assert 'os_sandboxes' in cat_ids
    assert 'mlops' in cat_ids
    assert 'data_engineering' in cat_ids

