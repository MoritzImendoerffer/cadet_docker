# tests/test_simulation_endpoints.py
import base64, os, signal, socket, subprocess, time, dill, sys
from pathlib import Path
import pytest
import requests
from cryptography.hazmat.primitives import serialization

# make repo root importable
sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.crypto import generate_rsa_keypair, sign_bytes, verify_bytes
from app.settings import (
    PRIVATE_KEY_SERVER_ENV,
    PUBLIC_KEY_SERVER_ENV,
    PUBLIC_KEY_CLIENT_ENV_PREFIX,
)
from app.serialization import loads_b64
from tests.cadet_utils import make_process

def _start_uvicorn(port: int, extra_env: dict[str, str]):
    env = os.environ.copy()

    pub_pem, priv_pem, _ = generate_rsa_keypair()
    env[PRIVATE_KEY_SERVER_ENV] = priv_pem
    env[PUBLIC_KEY_SERVER_ENV]  = pub_pem
    env.update(extra_env)

    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--port", str(port)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    for _ in range(30):
        try:
            if requests.get(f"http://localhost:{port}/public_key", timeout=3).ok:
                return proc, env
        except Exception:
            time.sleep(0.5)

    out, err = proc.communicate()
    raise RuntimeError(f"uvicorn start-up failed:\n{out.decode()}\n{err.decode()}")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _gen_client_env():
    pub, priv, _ = generate_rsa_keypair()
    return {f"{PUBLIC_KEY_CLIENT_ENV_PREFIX}acme": pub}, priv


def test_simulate():
    port = _free_port()
    extra_env, client_priv_pem = _gen_client_env()
    client_priv = serialization.load_pem_private_key(client_priv_pem.encode(), None)

    proc, env = _start_uvicorn(port, extra_env)
    try:
        proc_obj = make_process()
        blob = dill.dumps(proc_obj)
        resp = requests.post(
            f"http://localhost:{port}/simulate",
            json={
                "client_id": "acme",
                "process_serialized": base64.b64encode(blob).decode(),
                "signature": sign_bytes(blob, client_priv),
            }, timeout=300,
        )
        assert resp.ok, resp.text
        data = resp.json()

        server_pub = serialization.load_pem_public_key(env[PUBLIC_KEY_SERVER_ENV].encode())
        assert verify_bytes(base64.b64decode(data["results_serialized"]),
                            data["signature"], server_pub)
    finally:
        proc.send_signal(signal.SIGINT); proc.wait(10)
        
def test_invalid_signature_rejected():
    port = _free_port()
    extra_env, client_priv_pem = _gen_client_env()
    proc, env = _start_uvicorn(port, extra_env)

    try:
        process = make_process()
        proc_pickle = dill.dumps(process)
        proc_b64 = base64.b64encode(proc_pickle).decode()
        bad_signature = base64.b64encode(b"not a real signature").decode()

        resp = requests.post(
            f"http://localhost:{port}/simulate",
            json={
                "client_id": "acme",
                "process_serialized": proc_b64,
                "signature": bad_signature,
            },
        )

        assert resp.status_code == 400
        assert "Invalid signature" in resp.text

    finally:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=10)


def test_deserialization_error():
    port = _free_port()
    extra_env, client_priv_pem = _gen_client_env()
    client_priv = serialization.load_pem_private_key(client_priv_pem.encode(), None)

    proc, env = _start_uvicorn(port, extra_env)

    try:
        bad_data = b"this is not a dill object"
        bad_b64 = base64.b64encode(bad_data).decode()
        signature = sign_bytes(bad_data, client_priv)

        resp = requests.post(
            f"http://localhost:{port}/simulate",
            json={
                "client_id": "acme",
                "process_serialized": bad_b64,
                "signature": signature,
            },
        )

        assert resp.status_code == 400
        assert "Deserialization failed" in resp.text

    finally:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=10)

if __name__ == "__main__":
    test_simulate()
    test_invalid_signature_rejected()
    test_deserialization_error()