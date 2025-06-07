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
from .utils import serialize, load_public_key
import os, base64
load_dotenv()

PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "private_key.pem")
PUBLIC_KEY_PATH  = os.getenv("PUBLIC_KEY_PATH",  "public_key.pem")


app = FastAPI()

@app.get("/public_key")
def public_key():
    """Provide the RSA‑public key so that clients can verify signatures."""
    pub_key = load_public_key(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)
    return {"public_key_pem": pub_key.decode()}


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

    res, sig = serialize(results, PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)

    return {
        "results_serialized": res,
        "signature": sig,
    }
