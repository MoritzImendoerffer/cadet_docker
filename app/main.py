# app/main.py
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.serialization import dumps, loads_b64
from CADETProcess.simulator import Cadet
import socket
import logging
import time
import datetime

app = FastAPI()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(hostname)s - %(message)s'
)

# Add hostname to all log messages
class HostnameFilter(logging.Filter):
    hostname = socket.gethostname()
    def filter(self, record):
        record.hostname = HostnameFilter.hostname
        return True

logger = logging.getLogger()
logger.addFilter(HostnameFilter())

class SimulateRequest(BaseModel):
    process_serialized: str  # base64-encoded dill payload


@app.get("/get_status")
def get_status():
    return {"status": "ok"}


@app.post("/simulate")
def simulate(req: SimulateRequest):

    logger.info(f"Started simulation request at {datetime.datetime.now()}")
    started = time.time()
    try:
        process = loads_b64(req.process_serialized)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Deserialization failed: {exc}")

    try:
        results = Cadet().simulate(process)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Deserialization failed: {exc}")
    
    stopped = time.time()
    logger.info(f"Finished simulation request in : {started-stopped} seconds")
    
    pickled = dumps(results)
    return {
        "results_serialized": base64.b64encode(pickled).decode(),
    }
