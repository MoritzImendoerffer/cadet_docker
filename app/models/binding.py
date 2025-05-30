from pydantic import BaseModel, Field

class StericMassActionParams(BaseModel):
    """
    Parameters for the Steric Mass Action (SMA) binding model.
    See: https://cadet.github.io/master/interface/binding/index.html#steric-mass-action
    """
    model_type: str = Field("SMA", description="Discriminator for binding model type")

    is_kinetic: bool = Field(True, description="Use kinetic (True) or quasi-stationary (False) binding")
    adsorption_rate: list[float] = Field(description="Adsorption rate constants [1/s]")
    desorption_rate: list[float] = Field(description="Desorption rate constants [1/s]")
    characteristic_charge: list[float] = Field(description="Characteristic charge of each component")
    steric_factor: list[float] = Field(description="Steric shielding factor per component")
    capacity: float = Field(description="Total binding site capacity [mol/m³]")
