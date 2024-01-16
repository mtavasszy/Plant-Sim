from __future__ import annotations
from dataclasses import dataclass

from typing_extensions import TYPE_CHECKING
if TYPE_CHECKING:
    from plantsim.plant_cell import PlantCell

@dataclass(kw_only=True)
class CellUpdate:
    coords: tuple[int, int]
    update_with: PlantCell