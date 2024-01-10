from __future__ import annotations
from typing import ClassVar, Type

from pydantic import BaseModel

class PlantCell(BaseModel):
    """Abstract class"""
    growable_types: ClassVar[list[Type[PlantCell]]]