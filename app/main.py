from fastapi import FastAPI, Request
from dotenv import load_dotenv
from app.models.models import (
    ComponentSystemParams,
    BindingParams,
    RateModelParams,
    InletParams,
    OutletParams,
    FlowSheetParams,
    ProcessParams
)
from .builder import build_process

load_dotenv()
app = FastAPI()

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
    ProcessParams: ProcessParams
):
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
    # process.simulate()  # Optional simulation step
    return {"message": "Process built successfully", "units": list(process.flowSheet.units.keys())}
