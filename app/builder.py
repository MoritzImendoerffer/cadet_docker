from fastapi import FastAPI
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

# FastAPI app
app = FastAPI()

# Mapping schema keys to schema classes and CADet model constructors
schema_map: Dict[str, Type[BaseModel]] = {
    "ComponentSystemParams": ComponentSystemParams,
    "StericMassActionParams": StericMassActionParams,
    "GeneralRateModelParams": GeneralRateModelParams,
    "InletParams": InletParams,
    "OutletParams": OutletParams,
    "FlowSheetParams": FlowSheetParams,
    "ProcessParams": ProcessParams
}


class CadetBuilder:
    @staticmethod
    def build(parsed: dict) -> Process:
        # Instantiate components from parsed dict
        system = ComponentSystem(**parsed["ComponentSystemParams"])
        binding = StericMassAction(**parsed["StericMassActionParams"])

        # Build units
        inlet = Inlet(**parsed["InletParams"])
        column = GeneralRateModel(binding=binding, **parsed["GeneralRateModelParams"])
        outlet = Outlet(**parsed["OutletParams"])

        # Assemble flowsheet
        flowsheet_data = parsed["FlowSheetParams"]
        units = {u.name: u for u in [inlet, column, outlet]}
        flowsheet = FlowSheet(units=units, **flowsheet_data)
        
        # Final process
        return Process(
            system=system,
            flowSheet=flowsheet,
            **parsed["ProcessParams"]
        )

