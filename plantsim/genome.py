from __future__ import annotations
from dataclasses import dataclass
from random import random

from typing import ClassVar, Self, Type
import numpy as np

# from pydantic import BaseModel

from plantsim.cell_types import CellType
from plantsim.config import Config


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
        directional_growth[CellType.SEED].growth_genome_for_celltype[CellType.STEM][
            2
        ].growth_p = 1
        directional_growth[CellType.SEED].growth_genome_for_celltype[CellType.ROOT][
            6
        ].growth_p = 1

        return Genome(directional_growth=directional_growth)

    def copy(self) -> Self:  # TODO
        return Genome()

    def test_expression(
        self, cell_type: CellType, branch_n: int, distance: int
    ) -> dict[CellType, list[bool]]:
        return self.directional_growth[cell_type].test_expression(branch_n, distance)

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
        self, branch_n: int, distance: int
    ) -> dict[CellType, list[bool]]:
        return {
            cell_type: [
                genes.test_expression(branch_n, distance) for genes in genes_list
            ]
            for cell_type, genes_list in self.growth_genome_for_celltype.items()
        }


@dataclass(kw_only=True)
class DirectionalGrowthGenes:
    """
    Growth info for a specific direction.
    """

    growth_p: float
    branch_factor: float
    distance_factor: float

    @classmethod
    def init_random(cls) -> DirectionalGrowthGenes:
        return DirectionalGrowthGenes(
            growth_p=Config.base_growth_p,
            branch_factor=random()*Config.base_growth_p,
            distance_factor=random()*Config.base_growth_p,
        )

    @classmethod
    def init_zero(cls) -> DirectionalGrowthGenes:
        return DirectionalGrowthGenes(
            growth_p=0,
            branch_factor=0,
            distance_factor=0,
        )

    def test_expression(self, branch_n: int, distance: int) -> bool:
        """Test whether the gene is randomly expressed or not"""
        combined_factors = (
            self.branch_factor * branch_n + self.distance_factor * distance
        )
        expression_p = self.growth_p + combined_factors

        draw = random()
        # print(f"testing p={self.growth_p} + {combined_factors} against random draw {draw}")

        return draw < expression_p
