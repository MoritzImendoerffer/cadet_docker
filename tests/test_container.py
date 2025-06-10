# tests/test_container.py
"""
End-to-end test that spins up the *built* Docker container.
"""

import base64
import socket
import tempfile
import time
import pathlib
import sys
import dill
import pytest
import requests
from cryptography.hazmat.primitives import serialization
from docker import from_env as docker_from_env
from docker.errors import DockerException

# required to import app.crypto
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from app.crypto import generate_rsa_keypair, sign_bytes, verify_bytes
from docker_utils import build_cadet_image, DEFAULT_TAG as IMAGE_TAG

from cadet_utils import make_process

try:
    _docker = docker_from_env()
    _docker.ping()
except DockerException:
    pytest.skip("Docker daemon not available – skipping container test", allow_module_level=True)


@pytest.fixture(scope="session")
def docker_image():
    """Build the image once per test session (or reuse if it exists)."""
    return build_cadet_image()

def _host_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def test_container(docker_image):

    tmp = tempfile.TemporaryDirectory()
    secrets_dir = pathlib.Path(tmp.name)

    pub_pem, priv_pem, _ = generate_rsa_keypair()
    secrets_dir.joinpath("public_key.pem").write_text(pub_pem)
    secrets_dir.joinpath("private_key.pem").write_text(priv_pem)
    

    client_pub, client_priv_pem, _ = generate_rsa_keypair()
    secrets_dir.joinpath("client_key_acme").write_text(client_pub)
    client_priv = serialization.load_pem_private_key(client_priv_pem.encode(), password=None)

    # Run container
    port = _host_port()
    container = _docker.containers.run(
        IMAGE_TAG,
        detach=True,
        ports={"8001/tcp": port},
        volumes={secrets_dir.as_posix(): {"bind": "/run/secrets", "mode": "ro"}},
    )

    try:
        for _ in range(30):
            try:
                if requests.get(f"http://localhost:{port}/public_key", timeout=3).ok:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            pytest.fail("Container never answered /public_key")

        proc = make_process()
        proc_blob = dill.dumps(proc)
        resp = requests.post(
            f"http://localhost:{port}/simulate",
            json={
                "client_id": "acme",
                "process_serialized": base64.b64encode(proc_blob).decode(),
                "signature": sign_bytes(proc_blob, client_priv),
            },
            timeout=300,
        )
        assert resp.ok, resp.text
        data = resp.json()

        server_pub = serialization.load_pem_public_key(pub_pem.encode())
        assert verify_bytes(
            base64.b64decode(data["results_serialized"]),
            data["signature"],
            server_pub,
        )
        results = dill.loads(base64.b64decode(data["results_serialized"]))
        assert hasattr(results, "solution")

    finally:
        container.remove(force=True, v=True)
        tmp.cleanup()

if __name__ == "__main__":
    test_container(build_cadet_image())