import yaml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@pytest.mark.unit
class TestConfigValidation:
    def test_docker_compose_exists_and_is_valid_yaml(self):
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml not found"
        with open(compose_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert "services" in data
        assert len(data["services"]) > 0

    def test_no_port_collisions_in_compose(self):
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        with open(compose_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        host_ports = []
        for service_name, svc in data.get("services", {}).items():
            for p in svc.get("ports", []):
                if isinstance(p, str) and ":" in p:
                    host_ports.append(p.split(":")[0])
        duplicates = [p for p in host_ports if host_ports.count(p) > 1]
        assert len(set(duplicates)) == 0, f"Host port collision detected: {duplicates}"
