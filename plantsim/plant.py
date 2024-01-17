from __future__ import annotations
from dataclasses import dataclass


from plantsim.plant_cell import PlantCell

@dataclass(kw_only=True)
class Plant:
    