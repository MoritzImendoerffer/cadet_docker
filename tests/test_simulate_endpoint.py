import os
import signal
import subprocess
import time
import base64
import tempfile
from pathlib import Path
import shutil 
import pytest
import requests
import dill
import sys, pathlib
import socket
from cryptography.hazmat.primitives import serialization

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1])) 

from scripts.generate_server_keys import create_server_keys

from app.utils import (
    load_private_key,
    load_public_key,
    sign_bytes,
    verify_bytes,
    dill_serialize,
)

def _start_uvicorn(port: int):
    # Create a temporary directory for isolated keys
    tmpdir = tempfile.TemporaryDirectory()
    tmp_path = Path(tmpdir.name)

    # Prepare env vars for the subprocess
    env = os.environ.copy()

    # Create server keys (private/public + client_keys dir)
    create_server_keys(
        env_file=None,
        key_dir=tmp_path,
        overwrite=True
    )

    # Load PEM content into env variables
    priv_path = tmp_path / "private_key.pem"
    pub_path = tmp_path / "public_key.pem"
    client_keys_dir = tmp_path / "client_keys"
    
    client_keys_dir.mkdir(parents=True, exist_ok=True)
    env["PRIVATE_KEY_PEM"] = priv_path.read_text()
    env["PUBLIC_KEY_PEM"] = pub_path.read_text()
    env["CLIENT_KEYS_DIR"] = str(client_keys_dir)

    # Start Uvicorn server
    p = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start (max 15 seconds)
    for _ in range(30):
        try:
            r = requests.get(f"http://localhost:{port}/public_key", timeout=3)
            if r.ok:
                return p, env, tmpdir
        except Exception:
            time.sleep(0.5)

    # If server fails to start, capture logs and raise error
    out, err = p.communicate()
    raise RuntimeError(f"uvicorn failed to start:\nstdout:\n{out.decode()}\nstderr:\n{err.decode()}")


def _make_process():
    """
    The load wash elute example from cadet process
    """
    import numpy as np
    from CADETProcess.processModel import (
        ComponentSystem, StericMassAction,
        Inlet, GeneralRateModel, Outlet,
        FlowSheet, Process
    )

    cs = ComponentSystem()
    cs.add_component("Salt")
    cs.add_component("A")
    cs.add_component("B")
    cs.add_component("C")

    sma = StericMassAction(cs, name="SMA")
    sma.is_kinetic = True
    sma.adsorption_rate = [0.0, 35.5, 1.59, 7.7]
    sma.desorption_rate = [0.0, 1000, 1000, 1000]
    sma.characteristic_charge = [0.0, 4.7, 5.29, 3.7]
    sma.steric_factor = [0.0, 11.83, 10.6, 10.0]
    sma.capacity = 1200.0

    inlet = Inlet(cs, name="inlet")
    inlet.flow_rate = 6.683738370512285e-8

    column = GeneralRateModel(cs, name="column")
    column.binding_model = sma
    column.length = 0.014
    column.diameter = 0.02
    column.bed_porosity = 0.37
    column.particle_radius = 4.5e-5
    column.particle_porosity = 0.75
    column.axial_dispersion = 5.75e-8
    column.film_diffusion = column.n_comp * [6.9e-6]
    column.pore_diffusion = [7e-10, 6.07e-11, 6.07e-11, 6.07e-11]
    column.surface_diffusion = column.n_bound_states * [0.0]
    column.c = [50, 0, 0, 0]
    column.cp = [50, 0, 0, 0]
    column.q = [sma.capacity, 0, 0, 0]

    outlet = Outlet(cs, name="outlet")

    fs = FlowSheet(cs)
    fs.add_unit(inlet)
    fs.add_unit(column)
    fs.add_unit(outlet, product_outlet=True)
    fs.add_connection(inlet, column)
    fs.add_connection(column, outlet)

    process = Process(fs, name="lwe")
    process.cycle_time = 2000.0
    load_duration = 9.0
    t_gradient_start = 90.0
    gradient_duration = process.cycle_time - t_gradient_start

    c_load = np.array([50.0, 1.0, 1.0, 1.0])
    c_wash = np.array([50.0, 0.0, 0.0, 0.0])
    c_elute = np.array([500.0, 0.0, 0.0, 0.0])
    gradient_slope = (c_elute - c_wash) / gradient_duration
    c_gradient_poly = np.array(list(zip(c_wash, gradient_slope)))

    process.add_event("load", "flow_sheet.inlet.c", c_load)
    process.add_event("wash", "flow_sheet.inlet.c", c_wash, time=load_duration)
    process.add_event("grad_start", "flow_sheet.inlet.c", c_gradient_poly, time=t_gradient_start)

    return process

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Bind to a free port provided by the OS
        return s.getsockname()[1]  # Return the assigned port

def test_simulate():
    """
    Runs the server, creates a private and public key for user 'acme',
    saves the keys to a temp directory and the app folder
    """
    port = get_free_port()
    server_proc, env, tmpdir = _start_uvicorn(port)

    try:
        priv_path = str(Path(env["CLIENT_KEYS_DIR"], "acme_priv.pem"))
        pub_path  = str(Path(env["CLIENT_KEYS_DIR"], "acme_pub.pem"))
        client_priv = load_private_key(priv_path, pub_path)
        shutil.copyfile(pub_path, os.path.join(env["CLIENT_KEYS_DIR"], "acme.pem"))
        proc = _make_process()
        proc_pickle = dill.dumps(proc)
        proc_b64 = base64.b64encode(proc_pickle).decode()
        signature = sign_bytes(proc_pickle, client_priv)

        resp = requests.post(f"http://localhost:{port}/simulate", json={
            "client_id": "acme",
            "process_serialized": proc_b64,
            "signature": signature,
        }, timeout=300)
        assert resp.ok, resp.text

        data = resp.json()
        server_pub = serialization.load_pem_public_key(env["PUBLIC_KEY_PEM"].encode())
        assert verify_bytes(base64.b64decode(data["results_serialized"]),
                            data["signature"], server_pub)

        results = dill.loads(base64.b64decode(data["results_serialized"]))
        assert hasattr(results, "solution")

    finally:
        server_proc.send_signal(signal.SIGINT)
        server_proc.wait(timeout=10)
        tmpdir.cleanup() 

def test_invalid_signature_rejected():
    port = get_free_port()
    server_proc, env, tmpdir = _start_uvicorn(port)
    try:
        priv_path = str(Path(env["CLIENT_KEYS_DIR"], "acme_priv.pem"))
        pub_path = str(Path(env["CLIENT_KEYS_DIR"], "acme_pub.pem"))
        client_priv = load_private_key(priv_path, pub_path)
        shutil.copyfile(pub_path, os.path.join(env["CLIENT_KEYS_DIR"], "acme.pem"))

        proc = _make_process()
        proc_pickle = dill.dumps(proc)
        proc_b64 = base64.b64encode(proc_pickle).decode()
        bad_signature = base64.b64encode(b"garbage").decode()

        resp = requests.post(f"http://localhost:{port}/simulate", json={
            "client_id": "acme",
            "process_serialized": proc_b64,
            "signature": bad_signature,
        })
        assert resp.status_code == 400
        assert "Signature verification failed" in resp.text
    finally:
        server_proc.send_signal(signal.SIGINT)
        server_proc.wait(timeout=10)
        tmpdir.cleanup()
 
def test_deserialization_error():
    port = get_free_port()
    server_proc, env, tmpdir = _start_uvicorn(port)
    try:
        priv_path = str(Path(env["CLIENT_KEYS_DIR"], "acme_priv.pem"))
        pub_path  = str(Path(env["CLIENT_KEYS_DIR"], "acme_pub.pem"))
        client_priv = load_private_key(priv_path, pub_path)
        shutil.copyfile(pub_path, os.path.join(env["CLIENT_KEYS_DIR"], "acme.pem"))

        bad_b64 = base64.b64encode(b"not a dill object").decode()
        signature = sign_bytes(b"not a dill object", client_priv)

        resp = requests.post(f"http://localhost:{port}/simulate", json={
            "client_id": "acme",
            "process_serialized": bad_b64,
            "signature": signature,
        })
        assert resp.status_code == 400
        assert "dill deserialization error" in resp.text
    finally:
        server_proc.send_signal(signal.SIGINT)
        server_proc.wait(timeout=10)
        tmpdir.cleanup()
        
if __name__ == "__main__":
    test_simulate()