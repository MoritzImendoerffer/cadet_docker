# tests/test_simulate_compose.py
"""
End-to-end test that starts the Cadet API stack with *docker compose up*
(using the repo’s docker-compose.yml) and checks /simulate.
"""

from __future__ import annotations

import base64
import subprocess
import sys
import time
from pathlib import Path

import dill
import pytest
import requests
from cryptography.hazmat.primitives import serialization

# add repo root to PYTHONPATH for `app.crypto` & helpers
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.crypto import sign_bytes, verify_bytes
from tests.cadet_utils import make_process


# --------------------------------------------------------------------------- #
# Configuration – adjust only if your file names differ
# --------------------------------------------------------------------------- #
REPO_ROOT          = Path(__file__).resolve().parents[1]
COMPOSE_FILE       = REPO_ROOT / "docker-compose.yml"
SERVER_PUB_KEY     = REPO_ROOT / "run" / "secrets" / "public_key_server.pem"
CLIENT_PRIV_KEY    = REPO_ROOT / "run" / "secrets" / "private_key_client_acme.pem"
HOST_PORT          = 8001               # docker-compose.yml maps 8001:8001

# --------------------------------------------------------------------------- #
# Skip if docker compose is missing
# --------------------------------------------------------------------------- #
try:
    subprocess.run(["docker", "compose", "version"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except (FileNotFoundError, subprocess.CalledProcessError):
    pytest.skip("docker compose not available – skipping compose test",
                allow_module_level=True)


# --------------------------------------------------------------------------- #
def _compose(cmd: list[str]) -> None:
    """Run a docker-compose command and raise on error."""
    subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE), *cmd],
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


@pytest.fixture(scope="module")
def stack():
    """Bring the stack up for a single test module, tear it down afterwards."""
    _compose(["up", "-d", "--quiet-pull"])
    try:
        yield
    finally:
        # down even if the test failed
        _compose(["down", "-v", "--remove-orphans"])


# --------------------------------------------------------------------------- #
def test_simulate_compose(stack):
    # -------------------------------------------------------------------- #
    # Wait until /public_key answers (max ≈15 s)
    # -------------------------------------------------------------------- #
    for _ in range(30):
        try:
            resp = requests.get(f"http:///0.0.0.0:{HOST_PORT}/public_key", timeout=2)
            if resp.ok:
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            pass
        time.sleep(0.5)
    else:
        pytest.fail("Container never answered /public_key")

    # -------------------------------------------------------------------- #
    # Prepare keys
    # -------------------------------------------------------------------- #
    server_pub = serialization.load_pem_public_key(SERVER_PUB_KEY.read_bytes())
    client_priv = serialization.load_pem_private_key(
        CLIENT_PRIV_KEY.read_bytes(), password=None
    )

    # -------------------------------------------------------------------- #
    # Build a dummy process & hit /simulate
    # -------------------------------------------------------------------- #
    proc_obj = make_process()
    blob = dill.dumps(proc_obj)

    response = requests.post(
        f"http://0.0.0.0:{HOST_PORT}/simulate",
        json={
            "client_id": "acme",
            "process_serialized": base64.b64encode(blob).decode(),
            "signature": sign_bytes(blob, client_priv),
        },
        timeout=300,
    )
    assert response.ok, response.text
    payload = response.json()

    # verify server signature
    assert verify_bytes(
        base64.b64decode(payload["results_serialized"]),
        payload["signature"],
        server_pub,
    )

    # unpickle results & quick sanity check
    results = dill.loads(base64.b64decode(payload["results_serialized"]))
    assert hasattr(results, "solution")

if __name__ == "__main__":
    test_simulate_compose(None)