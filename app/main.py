"""
main.py  –  FastAPI micro-service that

1. exposes the server's public key (GET /public_key)
2. accepts a **signed, dill-pickled** CADET `Process` instance (POST /simulate)
3. verifies the sender with the client's public key stored in client_keys/
4. runs the CADET simulation
5. returns the results pickled + signed by the server's private key
"""

import base64
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from CADETProcess.simulator import Cadet

from .utils import (
    load_private_key,
    load_public_key,
    dill_deserialize,
    dill_serialize,
    verify_bytes,
)


load_dotenv()

PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "private_key.pem")
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "public_key.pem")
CLIENT_KEYS_DIR = Path(os.getenv("CLIENT_KEYS_DIR", "client_keys")).resolve()

CLIENT_KEYS_DIR.mkdir(exist_ok=True)

# server key-pair (auto-generated if missing)
_private_key = load_private_key(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)
with open(PUBLIC_KEY_PATH, "rb") as fh:
    SERVER_PUB_PEM = fh.read()

app = FastAPI()


@app.get("/public_key")
def public_key():
    """Return the server’s RSA-public key so callers can verify our signatures."""
    return {"public_key_pem": SERVER_PUB_PEM.decode()}

class SimulatePayload(BaseModel):
    client_id: str = Field(..., 
                           description="name of registered public key <client_id>-.pem"
    )
    process_serialized: str = Field(
        ...,
        description= "base64-encoded, serialized (dill) process instance from cadet_process."
    )
    signature: str = Field(
        ...,
        description = "base64-encoded RSA signature of the process class (signed with the private key matching to <client_id>-.pem)"
    )


@app.post("/simulate")
def simulate(body: SimulatePayload):
    # 1.  locate the client’s public key
    pub_path = CLIENT_KEYS_DIR / f"{body.client_id}.pem"
    if not pub_path.is_file():
        raise HTTPException(400, f"Unknown client_id '{body.client_id} in {pub_path}'")

    client_pub = load_public_key(pub_path)

    # 2.  verify the signature on the incoming pickle
    pickled = base64.b64decode(body.process_serialized)
    if not verify_bytes(pickled, body.signature, client_pub):
        raise HTTPException(400, "Signature verification failed")

    # 3.  unpickle the Process instance
    try:
        process = dill_deserialize(body.process_serialized)
    except Exception as exc:
        raise HTTPException(400, f"dill deserialization error: {exc}")

    # 4.  run the simulation
    results = Cadet().simulate(process)

    # 5.  pickle + sign the results
    results_b64, sig = dill_serialize(results, _private_key)

    return {
        "results_serialized": results_b64,
        "signature": sig,
    }
