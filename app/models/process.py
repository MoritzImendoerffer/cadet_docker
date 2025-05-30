from pydantic import BaseModel, Field
from .component import ComponentSystemParams
from .flowsheet import FlowSheetParams
from typing import List

class ProcessParams(BaseModel):
    """
    Defines a complete single-column process configuration including the flowsheet, components, and inlet profile.
    """
    name: str = Field(..., description="Name of the process")
    cycle_time: float = Field(..., description="Total cycle time [s]")

    system: ComponentSystemParams
    flow_sheet: FlowSheetParams

    inlet_concentration: List[float] = Field(..., description="Concentration vector during load [mol/m³]")
    c_wash: List[float] = Field(..., description="Wash buffer composition [mol/m³]")
    c_elute: List[float] = Field(..., description="Elution buffer composition [mol/m³]")

    load_duration: float = Field(..., description="Duration of load phase [s]")
    t_gradient_start: float = Field(..., description="Time at which gradient starts [s]")
