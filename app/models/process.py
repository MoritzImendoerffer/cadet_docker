from pydantic import BaseModel, Field
from typing import List

class ProcessParams(BaseModel):
    name: str
    cycle_time: float
    inlet_concentration: List[float]
    c_wash: List[float]
    c_elute: List[float]

    load_duration: float
    t_gradient_start: float
    