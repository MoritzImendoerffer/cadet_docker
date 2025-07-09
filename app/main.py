# app/main.py
import base64
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional

from app.serialization import dumps, loads_b64
from CADETProcess.simulator import Cadet
import socket
import logging
import time
import datetime
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import functools

app = FastAPI()
# Simple busy flag
is_busy = threading.Lock()

# Create executor for running simulations
executor = ThreadPoolExecutor(max_workers=1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    """Request model for CADET process simulation.
    
    This endpoint accepts a serialized CADET process object and returns
    the simulation results. The process object should be serialized using
    dill and then base64-encoded.
    """
    process_serialized: str = Field(
        ...,
        description="Base64-encoded dill-serialized CADET Process object. "
                    "The process should be created using CADET-Process and "
                    "serialized with dill.dumps() then base64-encoded."
    )
    timeout: Optional[float] = Field(
        None,
        description="Optional timeout in seconds for the simulation. "
                    "If not provided, the simulation runs without a timeout. "
                    "If the simulation exceeds this time, a 504 Gateway Timeout "
                    "error is returned. Recommended: 300 seconds (5 minutes).",
        ge=1.0,  # Greater than or equal to 1 second
        le=3600.0,  # Less than or equal to 1 hour
        example=300
    )
    
    class Config:
        schema_extra = {
            "example": {
                "process_serialized": "gASVcgAAAAAAAACMF2NhZGV0X3Byb2Nlc3MucHJvY2Vzc5SMB1Byb2Nlc3...",
                "timeout": 300.0
            }
        }


@app.get("/get_status")
def get_status():
    return {"status": "ok"}


@app.get("/health")
async def health_check(response: Response):
    """Health endpoint for HAProxy."""
    if is_busy.locked():
        response.status_code = 503
        return {"healthy": False, "ready": False}
    else:
        return {"healthy": True, "ready": True}

@app.post("/simulate", 
          summary="Run CADET simulation",
          description="Execute a CADET process simulation with optional timeout control.",
          response_description="The simulation results, serialized with dill and base64-encoded")
async def simulate(req: SimulateRequest):
    logger.info(f"Started simulation request at {datetime.datetime.now()}")
    
    if not is_busy.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="Server busy")
    
    started = time.time()
    try:
        process = loads_b64(req.process_serialized)
    except Exception as exc:
        is_busy.release()
        raise HTTPException(status_code=400, detail=f"Deserialization failed: {exc}")

    try:
        # Run simulation with optional timeout
        loop = asyncio.get_event_loop()
        
        # Determine timeout value
        timeout_value = req.timeout if req.timeout is not None else 600.0  # Default 10 minutes
        
        logger.info(f"Running simulation with timeout of {timeout_value} seconds")
        results = await asyncio.wait_for(
            loop.run_in_executor(
                executor,
                functools.partial(Cadet().simulate, process)
            ),
            timeout=timeout_value
        )
        
        stopped = time.time()
        logger.info(f"Finished simulation request in : {stopped-started} seconds")
        
        pickled = dumps(results)
        return {
            "results_serialized": base64.b64encode(pickled).decode(),
        }
    except asyncio.TimeoutError:
        logger.error(f"Simulation timeout after {timeout_value} seconds")
        raise HTTPException(status_code=504, detail="Simulation timeout")
    except Exception as exc:
        logger.error(f"Simulation failed: {exc}")
        raise HTTPException(status_code=400, detail=f"Simulation failed: {exc}")
    finally:
        is_busy.release()