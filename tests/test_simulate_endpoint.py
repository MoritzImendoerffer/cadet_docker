# tests/test_simulate_endpoint.py
import base64
import os
import signal
import socket
import subprocess
import time
import dill
import sys
from pathlib import Path
import pytest
import requests

# make repo root importable
sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.serialization import loads_b64
from tests.cadet_utils import make_process


def _start_uvicorn(port: int):
    env = os.environ.copy()

    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    for _ in range(30):
        try:
            if requests.get(f"http://localhost:{port}/get_status", timeout=3).ok:
                return proc
        except Exception:
            time.sleep(0.5)

    out, err = proc.communicate()
    raise RuntimeError(f"uvicorn start-up failed:\n{out.decode()}\n{err.decode()}")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def test_simulate():
    port = _free_port()
    proc = _start_uvicorn(port)
    try:
    
        # Create and simulate process
        proc_obj = make_process()
        blob = dill.dumps(proc_obj)
        resp = requests.post(
            f"http://localhost:{port}/simulate",
            json={
                "process_serialized": base64.b64encode(blob).decode(),
            },
            timeout=300,
        )
        assert resp.ok, resp.text
    finally:
        proc.send_signal(signal.SIGINT)
        proc.wait(10)


if __name__ == "__main__":
    test_simulate()