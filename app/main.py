from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from app.models.models import (
    ComponentSystemParams,
    BindingParams,
    RateModelParams,
    InletParams,
    OutletParams,
    FlowSheetParams,
    ProcessParams,
)
from CADETProcess.simulator import Cadet
from .builder import build_process

import os, base64, dill
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

load_dotenv()

PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "private_key.pem")
PUBLIC_KEY_PATH  = os.getenv("PUBLIC_KEY_PATH",  "public_key.pem")


def _generate_keypair(path_priv: str, path_pub: str) -> rsa.RSAPrivateKey:
    """Create a fresh RSA‑2048 key‑pair (if none exist) and save both PEMs."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048,
                                   backend=default_backend())

    with open(path_priv, "wb") as fh:
        fh.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(path_pub, "wb") as fh:
        fh.write(
            key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return key


def _load_private_key(path: str) -> rsa.RSAPrivateKey:
    if not os.path.exists(path):
        # First run – generate keys
        return _generate_keypair(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)
    with open(path, "rb") as fh:
        return serialization.load_pem_private_key(
            fh.read(), password=None, backend=default_backend()
        )


# singletons --------------------------------------------------------
_private_key: rsa.RSAPrivateKey = _load_private_key(PRIVATE_KEY_PATH)
with open(PUBLIC_KEY_PATH, "rb") as fh:
    _public_key_pem: bytes = fh.read()

app = FastAPI()

@app.get("/public_key")
def public_key():
    """Provide the RSA‑public key so that clients can verify signatures."""
    return {"public_key_pem": _public_key_pem.decode()}


@app.post("/test")
async def test(request: Request):
    return {"result": "Hurra"}

@app.post("/simulate")
def simulate(
    ComponentSystemParams: ComponentSystemParams,
    BindingParams: BindingParams,
    RateModelParams: RateModelParams,
    InletParams: InletParams,
    OutletParams: OutletParams,
    FlowSheetParams: FlowSheetParams,
    ProcessParams: ProcessParams,
):
    """Build a CADET‑Process, simulate it, and return a signed pickle."""

    parsed = {
        "ComponentSystemParams": ComponentSystemParams.dict(),
        "BindingParams": BindingParams.dict(),
        "RateModelParams": RateModelParams.dict(),
        "InletParams": InletParams.dict(),
        "OutletParams": OutletParams.dict(),
        "FlowSheetParams": FlowSheetParams.dict(),
        "ProcessParams": ProcessParams.dict(),
    }

    process = build_process(parsed)
    sim = Cadet()
    results = sim.simulate(process)
    pickled = dill.dumps(results)
    signature = _private_key.sign(
        pickled,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    return {
        "pickle": base64.b64encode(pickled).decode(),
        "signature": base64.b64encode(signature).decode(),
    }
