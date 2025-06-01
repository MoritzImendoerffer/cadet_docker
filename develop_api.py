import json
from pydantic import BaseModel
from typing import Dict, Type

# Import all schema classes
from app.models.component import ComponentSystemParams
from app.models.column import GeneralRateModelParams
from app.models.binding import StericMassActionParams
from app.models.flow import InletParams, OutletParams
from app.models.flowsheet import FlowSheetParams
from app.models.process import ProcessParams

# Import CADet Process objects
from CADETProcess.processModel import (
    ComponentSystem, StericMassAction,
    Inlet, GeneralRateModel, Outlet,
    FlowSheet, Process
)

with open("lwe_1.json", "r") as f:
    parsed = json.load(f)


binding_models = {
    "SMA": StericMassAction
}

rate_models = {
    "GeneralRateModel": GeneralRateModel
}


comps = parsed["ComponentSystemParams"]
cs = ComponentSystem()
for comp in comps["components"]:
    cs.add_component(comp)

bp = parsed["BindingParams"]
binding_model = binding_models.get(bp["type"])
if binding_model:
    bm = binding_model(cs, name = bp["name"])
    if all([p in bp.keys() for p in bm.required_parameters]):
        bm.parameters = {key: bp[key] for key in bm.required_parameters}
    else:
        raise ValueError("Check your binding model parameters")       
else:
    raise NotImplementedError("Binding model not supported")


inlet = Inlet(cs, **parsed["InletParams"])
outlet = Outlet(cs, **parsed["OutletParams"])

rp = parsed["RateModelParams"]
rate_model = rate_models.get(rp["type"])
if rate_model:
    column = rate_model(cs, name=rp["name"])
    if all([p in rp.keys() for p in column.required_parameters]):
        column.parameters = {key: rp[key] for key in column.required_parameters}
else:
    raise NotImplementedError("Rate model not supported")


# Assemble flowsheet
fs = FlowSheet(cs)
# .... STUCK HERE ... 
# How to achieve following code in a generic way from the jso
#fs.add_unit(inlet)
#fs.add_unit(column)
#fs.add_unit(outlet, product_outlet=True)
#fs.add_connection(inlet, column)
#fs.add_connection(column, outlet)
print("Done")