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
            CellType.SEED: CellTypeGrowthInfo({
                CellType.STEM: [DirectionalGrowthGenes.init_zero() for _ in range(8)],
                 CellType.ROOT: [DirectionalGrowthGenes.init_zero() for _ in range(8)],
                 }
            ),
            CellType.ROOT: CellTypeGrowthInfo({
                 CellType.ROOT: [DirectionalGrowthGenes.init_zero(), DirectionalGrowthGenes.init_zero(),DirectionalGrowthGenes.init_zero(),DirectionalGrowthGenes.init_zero(),DirectionalGrowthGenes.init_zero(),DirectionalGrowthGenes.init_random(),DirectionalGrowthGenes.init_random(),DirectionalGrowthGenes.init_random()],
                 }
            ),
            CellType.STEM: CellTypeGrowthInfo({
                 CellType.STEM: [DirectionalGrowthGenes.init_zero(), DirectionalGrowthGenes.init_random(),DirectionalGrowthGenes.init_random(),DirectionalGrowthGenes.init_random(),DirectionalGrowthGenes.init_zero(),DirectionalGrowthGenes.init_zero(),DirectionalGrowthGenes.init_zero(),DirectionalGrowthGenes.init_zero()],
                 CellType.LEAF: [DirectionalGrowthGenes.init_random() for _ in range(8)],
                 CellType.FLOWER: [DirectionalGrowthGenes.init_random() for _ in range(8)],
                 }
            ),
            CellType.LEAF: CellTypeGrowthInfo({}),
            CellType.FLOWER: CellTypeGrowthInfo({}),
        }

        #     cell_type: CellTypeGrowthInfo(
        #         growth_genome_for_celltype={
        #             growable_cell_type: [
        #                 DirectionalGrowthGenes.init_zero()
        #                 if cell_type is CellType.SEED or cell_type is CellType.ROOT
        #                 else DirectionalGrowthGenes.init_random()
        #                 for _ in range(8)
        #             ]
        #             for growable_cell_type in Config.growable_types[cell_type]
        #         }
        #     )
        #     for cell_type in CellType
        # }

        # stem goes up, root goes down. fosho.
        directional_growth[CellType.SEED].growth_genome_for_celltype[CellType.STEM][2].growth_p = 1
        directional_growth[CellType.SEED].growth_genome_for_celltype[CellType.ROOT][6].growth_p = 1

        return Genome(directional_growth=directional_growth)

    def get_mutation(self) -> Genome:  # TODO
        """Return a mutated copy of the genome"""

        mutated_directional_growth = {
            cell_type: growth_info.get_mutation() for cell_type, growth_info in self.directional_growth.items()
        }

        return Genome(directional_growth=mutated_directional_growth)

    def test_expression(
        self, cell_type: CellType, age: float, density: float, distance: int, water: float, energy: float
    ) -> dict[CellType, list[bool]]:
        return self.directional_growth[cell_type].test_expression(age, density, distance, water, energy)

    @property
    def flower_color(self) -> tuple[int, int, int]:
        """Determine color hue based on genome, and return RGB value"""

        return (0, 0, 0)


@dataclass
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

    def get_mutation(self) -> CellTypeGrowthInfo:  # TODO
        """Return a mutated copy of the growth info"""

        growth_genome_for_celltype = {
            cell_type: [directional_genes.get_mutation() for directional_genes in directional_genes_list]
            for cell_type, directional_genes_list in self.growth_genome_for_celltype.items()
        }

        return CellTypeGrowthInfo(growth_genome_for_celltype=growth_genome_for_celltype)


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

        return random() < expression_p

    def copy(self) -> DirectionalGrowthGenes:
        """Return a deep copy of the object"""

        return DirectionalGrowthGenes(
            growth_p=self.growth_p,
            factors=self.factors.copy()
        )

    def get_mutation(self) -> DirectionalGrowthGenes:
        """Return a potentially mutated copy of the directional growth genes"""

        n_factors_plus_growth = self.n_factors + 1

        if random() < Config.direction_mutation_p:
            is_mutated = np.random.uniform(size=n_factors_plus_growth) < (1 / n_factors_plus_growth)
            is_redetermination = np.random.uniform(size=n_factors_plus_growth) < Config.redetermination_p

            factors_offset = np.random.normal(0, Config.mutation_sigma, size=n_factors_plus_growth) * Config.base_growth_p
            factors_redetermination = np.random.uniform(size=n_factors_plus_growth) * Config.base_growth_p

            all_factors = np.array(self.factors.tolist() + [self.growth_p])
            mutated_factors = factors_redetermination * is_redetermination +  (all_factors + factors_offset) * np.invert(is_redetermination)

            new_factors = mutated_factors * is_mutated + all_factors * np.invert(is_mutated)

            return DirectionalGrowthGenes(factors=new_factors[0:self.n_factors], growth_p=new_factors[-1])

        return self.copy()
