from pydantic import BaseModel, Field

class InletParams(BaseModel):
    #unit_type: str = Field("Inlet")
    name: str
    flow_rate: float

class OutletParams(BaseModel):
    #unit_type: str = Field("Outlet")
    name: str
