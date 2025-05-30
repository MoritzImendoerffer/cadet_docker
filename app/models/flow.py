from pydantic import BaseModel, Field
from typing import Literal, Union
from .column import GeneralRateModelParams

class InletParams(BaseModel):
    """
    Configuration for the Inlet unit.
    """
    unit_type: Literal["Inlet"] = Field("Inlet")
    name: str = Field("inlet", description="Unit name")
    flow_rate: float = Field(..., description="Inlet flow rate [m³/s]")

class OutletParams(BaseModel):
    """
    Configuration for the Outlet unit.
    """
    unit_type: Literal["Outlet"] = Field("Outlet")
    name: str = Field("outlet", description="Unit name")

# Union of all supported unit types
UnitOperationParams = Union[InletParams, GeneralRateModelParams, OutletParams]
