from __future__ import annotations
from random import random

from typing import ClassVar, Type
import numpy as np
from pydantic import BaseModel

from plantsim.plant import PlantCell
from plantsim.config import Config

class Genome(BaseModel):
    max_branching: ClassVar[int] = 3

    directional_growth: dict[Type[PlantCell], CellTypeGrowthInfo]
    flower_color: tuple[int]

    # cumulative probabilities for number of branches
    stems_per_stem_probabilities: list[float]
    leaves_per_stem_probabilities: list[float]
    roots_per_root_probabilities: list[float]

    @classmethod
    def init_random(cls) -> Genome:
        """Initialize a random genome"""

        flower_color = tuple(np.random.uniform(0, 255, 3).astype(np.unit8))

        # random probabilities for number of branches
        stems_per_stem_probabilities = np.random.uniform(0, 1, Genome.max_branching)
        stems_per_stem_probabilities /= stems_per_stem_probabilities.sum()
        leaves_per_stem_probabilities = np.random.uniform(0, 1, Genome.max_branching)
        leaves_per_stem_probabilities /= leaves_per_stem_probabilities.sum()
        roots_per_root_probabilities = np.random.uniform(0, 1, Genome.max_branching)
        roots_per_root_probabilities /= roots_per_root_probabilities.sum()


class CellTypeGrowthInfo(BaseModel):
    """
    Probabilities for a specific plant cell to grow another
    plant cell, for all directions, starting at the right cell
    and rotating counter-clockwise.
    """

    growth_genome_for_celltype: dict[Type[PlantCell], list[DirectionalGrowthGenes]]

class DirectionalGrowthGenes(BaseModel):
    """
    Growth info for a specific direction.
    """

    growth_p: float
    cell_branch_factor: float
    cell_distance_factor: float

    @classmethod
    def init_random(cls) -> DirectionalGrowthGenes:

        return DirectionalGrowthGenes(
            growth_p=random() * Config.base_growth_p, cell_branch_factor=random(), cell_distance_factor=random()
        )
