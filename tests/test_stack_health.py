# mypy: ignore-errors
import os
import socket
import shutil
import pytest
import requests


def is_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(pytestconfig.rootdir, "docker-compose.staging.yml")


docker_available = shutil.which("docker") is not None


@pytest.mark.skipif(not docker_available, reason="docker not available")
@pytest.mark.asyncio
def test_stack_health(docker_ip, docker_services):
    prom_port = docker_services.port_for("prometheus", 9090)
    docker_services.wait_until_responsive(
        check=lambda: is_open(docker_ip, prom_port), timeout=60.0, pause=5.0
    )
    resp = requests.get(f"http://{docker_ip}:{prom_port}/metrics")
    assert resp.status_code == 200
    for svc, port in [("redis", 6379), ("postgres", 5432)]:
        host_port = docker_services.port_for(svc, port)
        assert is_open(docker_ip, host_port)
