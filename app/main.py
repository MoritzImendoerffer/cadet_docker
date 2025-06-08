"""
main.py – FastAPI micro-service that:

1. Exposes the server's public key (GET /public_key)
2. Accepts a signed, dill-pickled CADET `Process` instance (POST /simulate)
3. Verifies the sender using the client's public key stored in CLIENT_KEYS_DIR
4. Runs the CADET simulation
5. Returns the results pickled + signed by the server's private key
"""

import base64
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from CADETProcess.simulator import Cadet
from .utils import (
    dill_deserialize,
    dill_serialize,
    verify_bytes,
    load_public_key,
)

# === Load environment variables
load_dotenv()

PRIVATE_KEY_PEM = os.getenv("PRIVATE_KEY_PEM")
PUBLIC_KEY_PEM = os.getenv("PUBLIC_KEY_PEM")
CLIENT_KEYS_DIR = Path(os.getenv("CLIENT_KEYS_DIR", "client_keys")).resolve()

if not PRIVATE_KEY_PEM or not PUBLIC_KEY_PEM:
    raise RuntimeError("Missing PRIVATE_KEY_PEM or PUBLIC_KEY_PEM environment variable")

# Load private key from PEM string
try:
    _private_key = serialization.load_pem_private_key(
        PRIVATE_KEY_PEM.encode(), password=None
    )
except Exception as e:
    raise RuntimeError(f"Failed to parse PRIVATE_KEY_PEM: {e}")

SERVER_PUB_PEM = PUBLIC_KEY_PEM

# Ensure client keys directory exists
if not CLIENT_KEYS_DIR.exists():
    raise RuntimeError(f"Client keys directory not found: {CLIENT_KEYS_DIR}")

# Create FastAPI app
app = FastAPI()

@app.get("/public_key")
def public_key():
    """Returns the server's public key (PEM format)."""
    return {"public_key_pem": SERVER_PUB_PEM}


class SimulatePayload(BaseModel):
    client_id: str = Field(..., description="Name of the client (client_id.pem must exist in client_keys/)")
    process_serialized: str = Field(..., description="Base64-encoded, dill-serialized CADET Process instance")
    signature: str = Field(..., description="Base64-encoded RSA signature of the serialized process")


@app.post("/simulate")
def simulate(body: SimulatePayload):
    # Locate the client’s public key
    pub_path = CLIENT_KEYS_DIR / f"{body.client_id}.pem"
    if not pub_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Unknown client_id '{body.client_id}'. Expected key file: {pub_path}"
        )

    try:
        client_pub = load_public_key(str(pub_path))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load public key for client '{body.client_id}': {e}"
        )

    # Decode and verify the signature
    try:
        pickled = base64.b64decode(body.process_serialized)
    except Exception:
        raise HTTPException(400, "Invalid base64 encoding in 'process_serialized'")

    if not verify_bytes(pickled, body.signature, client_pub):
        raise HTTPException(400, "Signature verification failed")

    # Deserialize the Process instance
    try:
        process = dill_deserialize(body.process_serialized)
    except Exception as exc:
        raise HTTPException(400, f"dill deserialization error: {exc}")

    # Run the simulation
    results = Cadet().simulate(process)

    # Serialize + sign the results
    results_b64, sig = dill_serialize(results, _private_key)

    return {
        "results_serialized": results_b64,
        "signature": sig,
    }
