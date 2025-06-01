from pydantic import BaseModel, Field
from typing import List

class ConnectionParams(BaseModel):
    from_unit: str
    to_unit: str

class FlowSheetParams(BaseModel):
    units: List[BaseModel]  # Builder must interpret Inlet, Column, Outlet, etc.
    connections: List[ConnectionParams]
    product_outlet: str
