# app/main.py
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cryptography.hazmat.primitives import serialization

from app.config import load_private_key, load_public_key, load_client_keys
from app.crypto import sign_bytes, verify_bytes
from app.serialization import dumps, loads_b64
from CADETProcess.simulator import Cadet

app = FastAPI()

private_key = load_private_key()
public_key  = load_public_key()
CLIENT_KEYS = load_client_keys()


class SimulateRequest(BaseModel):
    client_id: str
    process_serialized: str  # base64-encoded dill payload
    signature: str           # base64-encoded RSA-PSS signature


@app.get("/public_key")
def get_public_key():
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return {"public_key": pem}


@app.post("/simulate")
def simulate(req: SimulateRequest):
    client_key = CLIENT_KEYS.get(req.client_id)
    if client_key is None:
        raise HTTPException(status_code=400, detail="Unknown client_id")

    payload_bytes = base64.b64decode(req.process_serialized)
    if not verify_bytes(payload_bytes, req.signature, client_key):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        process = loads_b64(req.process_serialized)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Deserialization failed: {exc}")

    results = Cadet().simulate(process)

    pickled = dumps(results)
    sig = sign_bytes(pickled, private_key)
    return {
        "results_serialized": base64.b64encode(pickled).decode(),
        "signature": sig,
    }
