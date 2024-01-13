from __future__ import annotations
from typing import ClassVar, Type

from pydantic import BaseModel

class PlantCell(BaseModel):
    """Abstract class"""
    growable_types: ClassVar[list[Type[PlantCell]]]

class Stem(PlantCell):
    max_new_stems: int # branching factor

class Root(PlantCell):
    max_new_roots: int # branching factor

class Leaf(PlantCell):
    growable_types = []

class Flower(PlantCell):
    growable_types = []

class Seed(PlantCell):
    growable_types = [Stem, Root]
