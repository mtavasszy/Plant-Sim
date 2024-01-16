from __future__ import annotations
from dataclasses import dataclass
from random import random

from plantsim.cell_types import CellType
from plantsim.config import Config
import numpy as np


@dataclass(kw_only=True)
class Genome:
    directional_growth: dict[CellType, CellTypeGrowthInfo]

    @classmethod
    def init_random(cls) -> Genome:
        """Initialize a random genome"""

        directional_growth = {
            cell_type: CellTypeGrowthInfo(
                growth_genome_for_celltype={
                    growable_cell_type: [
                        DirectionalGrowthGenes.init_zero()
                        if cell_type is CellType.SEED
                        else DirectionalGrowthGenes.init_random()
                        for _ in range(8)
                    ]
                    for growable_cell_type in Config.growable_types[cell_type]
                }
            )
            for cell_type in CellType
        }

        # stem goes up, root goes down. fosho.
        directional_growth[CellType.SEED].growth_genome_for_celltype[CellType.STEM][2].growth_p = 1
        directional_growth[CellType.SEED].growth_genome_for_celltype[CellType.ROOT][6].growth_p = 1

        return Genome(directional_growth=directional_growth)

    def mutate(self) -> Genome:  # TODO
        """Return a mutated copy of the genome"""

        return self

    def test_expression(
        self, cell_type: CellType, age: float, density: float, distance: int, water: float, energy: float
    ) -> dict[CellType, list[bool]]:
        return self.directional_growth[cell_type].test_expression(age, density, distance, water, energy)

    @property
    def flower_color(self) -> tuple[int, int, int]:
        """Determine color hue based on genome, and return RGB value"""

        return (0, 0, 0)


@dataclass(kw_only=True)
class CellTypeGrowthInfo:
    """
    Probabilities for a specific plant cell to grow another
    plant cell, for all directions, starting at the right cell
    and rotating counter-clockwise.
    """

    growth_genome_for_celltype: dict[CellType, list[DirectionalGrowthGenes]]

    def test_expression(
        self, age: float, density: float, distance: int, water: float, energy: float
    ) -> dict[CellType, list[bool]]:
        return {
            cell_type: [genes.test_expression(age, density, distance, water, energy) for genes in genes_list]
            for cell_type, genes_list in self.growth_genome_for_celltype.items()
        }


@dataclass(kw_only=True)
class DirectionalGrowthGenes:
    """
    Growth info for a specific direction.
    """

    growth_p: float
    factors: np.ndarray
    n_factors = 5  # age, local density, cell distance, water, energy

    @classmethod
    def init_random(cls) -> DirectionalGrowthGenes:
        return DirectionalGrowthGenes(
            growth_p=Config.base_growth_p,
            factors=np.random.uniform(size=DirectionalGrowthGenes.n_factors) * Config.base_growth_p,
        )

    @classmethod
    def init_zero(cls) -> DirectionalGrowthGenes:
        return DirectionalGrowthGenes(
            growth_p=0,
            factors=np.zeros(DirectionalGrowthGenes.n_factors),
        )

    def test_expression(self, age: float, density: float, distance: int, water: float, energy: float) -> bool:
        """Test whether the gene is randomly expressed or not"""

        factor_array = np.array(
            [age, density, distance * Config.distance_factor_scale, water, energy]
        )  # TODO add inverse factors too ?
        combined_factors = factor_array.dot(self.factors) * Config.base_growth_p

        expression_p = self.growth_p + combined_factors

        draw = random()
        # print(f"testing p={self.growth_p} + {combined_factors} against random draw {draw}")

        return draw < expression_p

    def copy(self) -> DirectionalGrowthGenes:
        """Return a deep copy of the object"""

        return DirectionalGrowthGenes(
            growth_p=self.growth_p,
        )

    def mutate(self) -> DirectionalGrowthGenes:
        """Return a mutated copy of the directional growth genes"""
