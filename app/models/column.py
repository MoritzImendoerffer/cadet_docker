from pydantic import BaseModel, Field
from typing import Literal, Union, List
from .binding import StericMassActionParams

class GeneralRateModelParams(BaseModel):
    """
    Parameters for the General Rate Model (GRM) chromatographic column.
    """
    unit_type: Literal["GeneralRateModel"] = Field("GeneralRateModel", description="Discriminator for unit operation")
    name: str = Field(..., description="Unique name for the unit operation")

    length: float = Field(..., description="Column length [m]")
    diameter: float = Field(..., description="Column diameter [m]")
    bed_porosity: float = Field(..., description="Porosity of packed bed [-]")
    particle_radius: float = Field(..., description="Radius of particles [m]")
    particle_porosity: float = Field(..., description="Particle porosity [-]")

    axial_dispersion: float = Field(..., description="Axial dispersion coefficient [m²/s]")
    film_diffusion: float = Field(..., description="Film mass transfer coefficient [m/s]")
    pore_diffusion: List[float] = Field(..., description="Intra-particle pore diffusivity per component [m²/s]")

    binding: StericMassActionParams = Field(..., description="Binding model configuration (e.g., SMA)")
