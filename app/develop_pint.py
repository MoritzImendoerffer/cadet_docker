from pydantic import BaseModel
from pydantic_pint import PydanticPintQuantity
from pint import Quantity
from typing import Annotated

class Box(BaseModel):
    length: Annotated[Quantity, PydanticPintQuantity("m")]
    width: Annotated[Quantity, PydanticPintQuantity("m")]

class Molar(BaseModel):
    cMol: Annotated[Quantity, PydanticPintQuantity("Mol")]
    cmMol: Annotated[Quantity, PydanticPintQuantity("m")]
    
box = Box(
    length="4cm",
    width="2m",
)