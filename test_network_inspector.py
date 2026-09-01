import pytest
from fastapi.testclient import TestClient
from studio.app import app
from studio.services.network_inspector import NetworkInspector, is_port_bound

client = TestClient(app)


def test_network_html_pages_served():
    """Verify HTML pages /network, /containers, /topology are properly served."""
    for path in ["/network", "/containers", "/topology"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "StackStudio - Visão Global de Containers, Portas & Topologia" in res.text
        assert "Quem se Liga a Quem" in res.text


def test_api_network_overview():
    """Verify /api/network/overview endpoint returns valid schema."""
    res = client.get("/api/network/overview")
    assert res.status_code == 200
    data = res.json()
    assert "stats" in data
    assert "containers" in data
    assert "ports" in data
    assert "topology" in data
    assert isinstance(data["containers"], list)
    assert isinstance(data["ports"], list)
    assert "nodes" in data["topology"]
    assert "edges" in data["topology"]


def test_api_network_containers():
    """Verify /api/network/containers returns list of containers."""
    res = client.get("/api/network/containers")
    assert res.status_code == 200
    containers = res.json()
    assert isinstance(containers, list)
    if containers:
        c = containers[0]
        assert "id" in c
        assert "name" in c
        assert "service" in c
        assert "project" in c
        assert "visual_status" in c


def test_api_network_ports():
    """Verify /api/network/ports returns mapped ports."""
    res = client.get("/api/network/ports")
    assert res.status_code == 200
    ports = res.json()
    assert isinstance(ports, list)
    if ports:
        p = ports[0]
        assert "host_port" in p
        assert "protocol" in p
        assert "container_name" in p


def test_api_network_topology():
    """Verify /api/network/topology returns graph nodes and edges."""
    res = client.get("/api/network/topology")
    assert res.status_code == 200
    topology = res.json()
    assert "nodes" in topology
    assert "edges" in topology
    assert "total_nodes" in topology
    assert "total_edges" in topology


def test_api_network_check_port():
    """Verify /api/network/check-port/{port} checks port availability."""
    res = client.get("/api/network/check-port/65530")
    assert res.status_code == 200
    data = res.json()
    assert data["port"] == 65530
    assert "in_use" in data
    assert isinstance(data["in_use"], bool)


def test_network_inspector_parse_ports():
    """Unit test port parser helper."""
    raw = "0.0.0.0:8090->8081/tcp, [::]:8090->8081/tcp, 9000/tcp"
    parsed = NetworkInspector._parse_ports(raw)
    assert len(parsed) >= 2
    assert parsed[0]["host_port"] == 8090
    assert parsed[0]["container_port"] == 8081
    assert parsed[0]["protocol"] == "tcp"
