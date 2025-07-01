# app/main.py
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.serialization import dumps, loads_b64
from CADETProcess.simulator import Cadet

app = FastAPI()


class SimulateRequest(BaseModel):
    process_serialized: str  # base64-encoded dill payload


@app.get("/get_status")
def get_public_key():
    return {"status": "ok"}


@app.post("/simulate")
def simulate(req: SimulateRequest):
    payload_bytes = base64.b64decode(req.process_serialized)

    try:
        process = loads_b64(req.process_serialized)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Deserialization failed: {exc}")

    results = Cadet().simulate(process)

    pickled = dumps(results)
    return {
        "results_serialized": base64.b64encode(pickled).decode(),
    }
