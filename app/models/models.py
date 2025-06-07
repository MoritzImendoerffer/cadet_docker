from __future__ import annotations
import math
from typing import List, Sequence, Dict, Set, Literal, Tuple

from pydantic import BaseModel, Field, validator, root_validator, PrivateAttr

from rate_model_registry import rate_models
from binding_model_registry import binding_models



class ComponentSystemParams(BaseModel):
    """Identifiers of the solutes (feed order)."""

    components: List[str] = Field(default_factory=lambda: ["A", "B", "C", "D"])

    @property
    def n(self) -> int:  # noqa: D401 – simple helper
        return len(self.components)


class RateModelParams(BaseModel):
    """Column geometry and mass‑transfer parameters (SI units)."""

    name: str = Field(
        "GeneralRateModel",
        description=f"Rate‑model class; choices: {', '.join(rate_models)}")

    # geometry (m)
    length: float = Field(0.014, gt=0, description="Packed‑bed length [m].")
    diameter: float = Field(0.02, gt=0, description="Inner column diameter [m].")

    bed_porosity: float = Field(0.37, ge=0, le=1, description="Interstitial porosity (0–1).")
    particle_porosity: float = Field(0.75, ge=0, le=1, description="Particle porosity (0–1).")
    particle_radius: float = Field(5.0e-5, gt=0, description="Mean particle radius [m].")

    # dispersion & diffusion
    axial_dispersion: float = Field(5.75e-8, description="Axial dispersion coefficient [m2/s].")
    film_diffusion: Sequence[float] = Field(
        default_factory=lambda: [6.9e-6] * 4,
        description="Liquid‑film mass‑transfer coefficients [m/s] (one per component).")
    
    pore_diffusion: Sequence[float] = Field(
        default_factory=lambda: [7e-10, 6.07e-11, 6.07e-11, 6.07e-11],
        description="Pore diffusion coefficients [m2/s] (one per component).")
    
    surface_diffusion: Sequence[float] = Field(
        default_factory=lambda: [0.0] * 4,
        description="Surface diffusion coefficients [m2/s] (one per component).")

    @property
    def column_volume(self) -> float:
        r = self.diameter / 2.0
        return math.pi * r ** 2 * self.length

class BindingParams(BaseModel):
    name: str = Field(
        "StericMassAction",
        description=f"Binding‑model family; choices: {', '.join(binding_models)}")

    is_kinetic: bool = True
    adsorption_rate: List[float] = Field(
        default_factory=lambda: [0.0, 35.5, 1.59, 7.7],
        description="Adsorption rate in [1/s]",
    )
    desorption_rate: List[float] = Field(
        default_factory=lambda: [0.0, 1000.0, 1000.0, 1000.0],
        description="Desorption rate in [1/s]"
    )
    characteristic_charge: List[float] = Field(
        default_factory=lambda: [0.0, 4.7, 5.29, 3.7],
        description="Characteristic charge for each component"
    )
    steric_factor: List[float] = Field(
        default_factory=lambda: [0.0, 11.83, 10.6, 10.0],
        description="Steric shielding factor for each component"
    )
    capacity: float = Field(
        1200.0, 
        description="Ionic capacity of the resin in [mol/m3]"
    )

class UnitParams(BaseModel):
    name: str

class ConnectionParams(BaseModel):
    connections: List[List] = Field(
        default_factory = [["inlet", "GeneralRateModel"],
                           ["GeneralRateModel", "outlet"]
        ],
        description = "List[List[Node1, Node2]] which defines the connections"
    )
    product_outlet: str = Field(
        "outlet",
        description = "Name of the unit listed in the connections, which is the product outlet."
    )
    
class FlowSheetParams(BaseModel):
    connections: ConnectionParams
    
    @property
    def units(self):
        return list(set([subitem for item in self.connections.connections for subitem in item]))

    @property
    def product_outlet(self):
        return self.connections.product_outlet

class ProcessParams(BaseModel):
    name: str = "lwe_1"
    load_volume: float = Field(1e-6, gt=0, description="Load volume in m3")
    flow_rate_load: float = Field(2.5e-7, gt=0, description="Flow rate during load [m3/s]")
    flow_rate_elution: float = Field(2.5e-7, gt=0, description="Flow rate during elution [m3/s]")
    flow_rate_wash: float = Field(2.5e-7, gt=0, description="Flow rate during wash in [m3/s]")
    flow_rate_equilibration: float = Field(4.17e-7, gt=0, description="Flow rate during equilibration [m3/s]")

    equilibration_duration: float = Field(3, description="Duration of the equilibration step [cv]")
    wash_duration: float = Field(3, description="Duration of the wash step [cv]")
    gradient_duration: float = Field(3, description="Duration of the gradient [cv]")
    elution_duration: float = Field(1, description="Duration of the elution after gradient is completed [cv]")

    equilibration_conc: Sequence[float] = Field(
        default_factory=lambda: [5.0, 0.0, 0.0, 0.0],
        description = "Inlet concentration for each component during equilibration [mol/L]"
    )
    load_conc: Sequence[float] = Field(
        default_factory=lambda: [15.0, 1.0, 1.0, 1.0],
        description = "Inlet concentration for each component during the load step [mol/L]"
    )
    wash_conc: Sequence[float] = Field(
        default_factory=lambda: [50.0, 0.0, 0.0, 0.0],
        description = "Inlet concentration for each component during the wash step [mol/L]"
    )
    elute_conc: Sequence[float] = Field(
        default_factory=lambda: [500.0, 0.0, 0.0, 0.0],
        description = "Inlet concentration for each component during the elution step [mol/L]"
    )
    
    # Will be filled by SimulationPayload
    equilibration_start: float = Field(0, description="Start of the equilibration step [s]")
    load_start: float = Field(0, description="Start of the load step [s]")
    wash_start: float = Field(0, description="Start of the wash step [s]")
    gradient_start: float = Field(0, description="Start of the gradient [s]")
    elution_start: float = Field(0, description="Start of the elution step after gradient is completed [s]")
    cycle_time: float = Field(0, description="Total time of one cycle [s]")
    
class SimulationPayload(BaseModel):
    ComponentSystemParams: ComponentSystemParams = Field(default_factory=ComponentSystemParams)
    BindingParams: BindingParams = Field(default_factory=BindingParams)
    RateModelParams: RateModelParams = Field(default_factory=RateModelParams)
    FlowSheetParams: FlowSheetParams = Field(default_factory=FlowSheetParams)
    ProcessParams: ProcessParams = Field(default_factory=ProcessParams)

    # Array-length and CV→time injection ----------------------------------
    @root_validator
    def _length_checks_and_compute_timings(cls, values):
        n = values["ComponentSystemParams"].n
        rmp: RateModelParams = values["RateModelParams"]
        bp: BindingParams = values["BindingParams"]
        pp: ProcessParams = values["ProcessParams"]

        def _len_ok(seq):
            return len(seq) == n

        if not all(_len_ok(seq) for seq in (rmp.film_diffusion, rmp.pore_diffusion, rmp.surface_diffusion)):
            raise ValueError("RateModel diffusion arrays length mismatch")
        if not all(_len_ok(seq) for seq in (bp.adsorption_rate, bp.desorption_rate, bp.characteristic_charge, bp.steric_factor)):
            raise ValueError("BindingParams arrays length mismatch")
        if not all(_len_ok(seq) for seq in (pp.equilibration_conc, pp.load_conc, pp.wash_conc, pp.elute_conc)):
            raise ValueError("ProcessParams concentration arrays length mismatch")


        # Conversion from CV (duration) to seconds (start)
        col_vol = rmp.column_volume

        pp.equilibration_start = 0

        # Load starts after equilibration
        equilibration_duration_s = pp.equilibration_duration * col_vol / pp.flow_rate_equilibration
        pp.load_start = pp.equilibration_start + equilibration_duration_s

        # Wash starts after load
        load_duration_s = pp.load_volume / pp.flow_rate_load
        pp.wash_start = pp.load_start + load_duration_s

        # Gradient starts after wash
        wash_duration_s = pp.wash_duration * col_vol / pp.flow_rate_wash
        pp.gradient_start = pp.wash_start + wash_duration_s

        # Elution starts after gradient
        gradient_duration_s = pp.gradient_duration * col_vol / pp.flow_rate_elution
        pp.elution_start = pp.gradient_start + gradient_duration_s
        
        elution_duration_s = pp.elution_duration * col_vol / pp.flow_rate_elution
        pp.cycle_time = pp.elution_start + elution_duration_s

        return values
