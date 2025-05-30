from pydantic import BaseModel, Field
from typing import List

class ComponentSystemParams(BaseModel):
    """
    Defines the list of components in the chromatographic system.
    These typically include salts and product-related species.
    """
    components: List[str] = Field(..., description="List of component names (e.g., ['Salt', 'A', 'B'])")
