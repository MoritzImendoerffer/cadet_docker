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


# Registry of constructors
binding_models = {
    "SMA": StericMassAction
}

rate_models = {
    "GeneralRateModel": GeneralRateModel
}

unit_classes = {
    "Inlet": Inlet,
    "Outlet": Outlet,
    **rate_models  # include all column models under their types
}

# Create component system
cs = ComponentSystem()
for comp in parsed["ComponentSystemParams"]["components"]:
    cs.add_component(comp)

# Build binding model
bp = parsed["BindingParams"]
binding_model_cls = binding_models.get(bp["type"])
if not binding_model_cls:
    raise NotImplementedError(f"Binding model '{bp['type']}' is not supported.")
binding = binding_model_cls(cs, name=bp["name"])
binding.parameters = {k: bp[k] for k in binding.required_parameters}

# Build column (rate model)
rp = parsed["RateModelParams"]
rate_model_cls = rate_models.get(rp["name"])
if not rate_model_cls:
    raise NotImplementedError(f"Rate model '{rp['name']}' is not supported.")
column = rate_model_cls(cs, name=rp["name"])
column_params = {k: rp[k] for k in column.required_parameters}
column.parameters = column_params
column.binding = binding

# Create other units (Inlet, Outlet)
inlet = Inlet(cs, **parsed["InletParams"])
outlet = Outlet(cs, **parsed["OutletParams"])

# Build flowsheet
fs = FlowSheet(cs)
unit_data = parsed["FlowSheetParams"]["units"]
unit_instances = {}

for u in unit_data:
    name = u["name"]
    utype = u["type"]

    if utype not in unit_classes:
        raise NotImplementedError(f"Unit type '{utype}' is not supported.")
    
    if utype == rp["type"]:  # Matches the one in RateModelParams
        unit = column
    elif utype == "Inlet":
        unit = inlet
    elif utype == "Outlet":
        unit = outlet
    else:
        unit = unit_classes[utype](cs, name=name)

    is_product = name == parsed["FlowSheetParams"].get("product_outlet")
    fs.add_unit(unit, product_outlet=is_product)
    unit_instances[name] = unit

# Connect units
for conn in parsed["FlowSheetParams"]["connections"]:
    fs.add_connection(unit_instances[conn["from_unit"]], unit_instances[conn["to_unit"]])
