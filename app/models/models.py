from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ComponentSystemParams(BaseModel):
    components: List[str] = Field(..., description="List of component names")


class BindingParams(BaseModel):
    type: str = Field(..., description="Type of binding model (e.g., 'SMA')")
    name: str = Field(..., description="Name of the binding model instance")
    is_kinetic: bool
    adsorption_rate: List[float]
    desorption_rate: List[float]
    characteristic_charge: List[float]
    steric_factor: List[float]
    capacity: float


class RateModelParams(BaseModel):
    name: str = Field(..., description="Name of the rate model instance (used as unit name)")
    length: float
    diameter: float
    bed_porosity: float
    particle_radius: float
    particle_porosity: float
    axial_dispersion: float
    film_diffusion: List[float]
    pore_diffusion: List[float]
    surface_diffusion: List[float]


class InletParams(BaseModel):
    name: str = Field(..., description="Unit name of the inlet")


class OutletParams(BaseModel):
    name: str = Field(..., description="Unit name of the outlet")


class ConnectionParams(BaseModel):
    from_unit: str = Field(..., description="Name of upstream unit")
    to_unit: str = Field(..., description="Name of downstream unit")


class UnitParams(BaseModel):
    name: str = Field(..., description="Unit name")


class FlowSheetParams(BaseModel):
    units: List[UnitParams] = Field(..., description="List of unit definitions by name")
    connections: List[ConnectionParams] = Field(..., description="Unit-to-unit connections")
    product_outlet: str = Field(..., description="Name of the product outlet unit")


class ProcessParams(BaseModel):
    name: str
    cycle_time_cv: float
    load_volume_mL: float
    flow_rate_ml_min: float
    wash_duration_cv: float
    gradient_duration_cv: float
    c_load: List[float]
    c_wash: List[float]
    c_elute: List[float]
