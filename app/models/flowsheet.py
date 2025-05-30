from pydantic import BaseModel, Field
from typing import List
from .flow import UnitOperationParams

class ConnectionParams(BaseModel):
    """
    Connects two units in the flowsheet in order of flow.
    """
    from_unit: str = Field(..., description="Name of the upstream unit")
    to_unit: str = Field(..., description="Name of the downstream unit")

class FlowSheetParams(BaseModel):
    """
    Describes the network of unit operations and their connections.
    """
    units: List[UnitOperationParams] = Field(..., description="List of all unit operations (inlet, column, outlet, etc.)")
    connections: List[ConnectionParams] = Field(..., description="List of connections (edges) between units")
    product_outlet: str = Field(..., description="Name of the outlet where product is collected")
