from __future__ import annotations
from abc import ABC, abstractmethod
import copy
from dataclasses import dataclass
import json
from pathlib import Path
from pprint import pprint
from typing import ClassVar, Self
import numpy as np

from plantsim.cell_types import CellType
from plantsim.cell_update import CellUpdate
from plantsim.config import Config


from plantsim.genome import Genome


@dataclass(kw_only=True)
class PlantCell(ABC):
    """Abstract base class for different cell types"""

    cell_type: ClassVar[CellType]
    genome: Genome
    coords: tuple[int, int]
    parent: PlantCell
    branch_n: int
    cell_distance: int
    age: int = 0  # age in ticks
    water: float = 0.0
    energy: float = 0.0
    
    water_cost: float = 1.0
    energy_cost: float = 1.0
    # water_per_tick_cost: float
    # sugar_per_tick_cost: float


    def copy(self) -> Self:
        """Return a copy of self"""

        return self.__class__(
            genome=self.genome,
            coords=copy.copy(self.coords),
            age=self.age,
            parent=self.parent,
            water=self.water,
            energy=self.energy,
        )

    # @abstractmethod
    def update(
        self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray
    ) -> list[CellUpdate]:
        """
        Update the state of the plant cell.
        - Test for expression of genomes (growth)
        - exchange water and suger with parent cells
        """
        self._collect_resources(all_coords=all_coords, ground_matrix=ground_matrix)
        self._share_resources_with_parent()
        return self._sample_growth(all_coords, ground_matrix)


    def _sample_growth(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> list[CellUpdate]:
        """Determine whether a new cell will be created and in which direction"""
        cell_updates = []

        expressions = self.genome.test_expression(self.cell_type, self.branch_n, self.cell_distance)
        for cell_type, directional_expressions in expressions.items():
            cell_class = next((subclass for subclass in PlantCell.__subclasses__() if subclass.cell_type is cell_type))

            if self.energy >= cell_class.energy_cost and self.water >= cell_class.water_cost:
                if any(directional_expressions):
                    for directional_expression, coord_offset in zip(directional_expressions, Config.coords_for_directions):
                        if directional_expression:
                            new_coords = (self.coords[0] + coord_offset[0], self.coords[1] + coord_offset[1])
                            if not new_coords in all_coords:
                                if (cell_type is CellType.ROOT and ground_matrix[*new_coords]) or (not cell_type is CellType.ROOT and not ground_matrix[*new_coords]):
                                    self.energy -= cell_class.energy_cost
                                    self.water -= cell_class.water_cost
                                    
                                    new_plant_cell = cell_class(genome=self.genome, coords=new_coords, parent=self, branch_n=0, cell_distance=self.cell_distance+1)
                                    # TODO keep track of branching properly
                                    cell_updates.append(CellUpdate(coords=new_coords, update_with=new_plant_cell))
        return cell_updates

    def _collect_resources(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray):
        pass

    def _share_resources_with_parent(self):
        """Share water and energy with parent plant cells"""

        total_energy = self.parent.energy + self.energy
        total_water = self.parent.water + self.water

        self.energy = total_energy / 2
        self.parent.energy = total_energy / 2
        self.water = total_water / 2
        self.parent.water = total_water / 2


@dataclass(kw_only=True)
class Stem(PlantCell):
    cell_type = CellType.STEM

@dataclass(kw_only=True)
class Root(PlantCell):
    cell_type = CellType.ROOT

    def _collect_resources(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray):
        surrounding_soil = 0
        for coord in Config.coords_for_directions:
            surrounding_soil += int(coord not in all_coords and ground_matrix[*coord])
        surrounding_soil_factor = surrounding_soil / 8

        self.water += Config.root_water_gain * surrounding_soil_factor

@dataclass(kw_only=True)
class Leaf(PlantCell):
    cell_type = CellType.LEAF

    def _collect_resources(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray):
        surrounding_air = 0
        for coord in Config.coords_for_directions:
            surrounding_air += int(coord not in all_coords and not ground_matrix[*coord])
        surrounding_air_factor = surrounding_air / 8

        self.energy += Config.leaf_energy_gain * surrounding_air_factor

@dataclass(kw_only=True)
class Flower(PlantCell):
    cell_type = CellType.FLOWER


@dataclass(kw_only=True)
class Seed(PlantCell):
    cell_type = CellType.SEED

    init_water_cost: float = 10
    init_energy_cost: float = 10
    energy: float = init_water_cost
    water: float = init_energy_cost

    parent: PlantCell = None
    branch_n: int = 0
    cell_distance: int = 0

    prev_water = water
    prev_energy = energy

    @classmethod
    def init_random(cls, coords: tuple[int, int]) -> Seed:
        """Create a randomly initialized seed"""
        genome = Genome.init_random()
        # print(genome.__dict__)
        # exit()
        # with (Path(__file__).parent.parent / "genome.json").open('w') as f:
        #     json.dump(genome.__dict__, f, skipkeys=True)
        # exit()
        return Seed(genome=genome, coords=coords)

    def update(
        self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray
    ) -> list[CellUpdate]:
        """
        Update the state of the plant cell.
        - Test for expression of genomes (growth)
        - exchange water and suger with parent cells
        - special case for seed: if in the air, fall down
        """

        if not ground_matrix[*self.coords]:
            self_moved = self.copy()
            self_moved.coords = (self.coords[0], self.coords[1] + 1)

            return [
                CellUpdate(coords=self.coords, update_with=None),
                CellUpdate(coords=self_moved.coords, update_with=self_moved),
            ]
        else:
            # if self.prev_water != self.water:
            #     print(f"water: {self.water}")
            #     self.prev_water = self.water
            # if self.prev_energy != self.energy:
            #     print(f"energy: {self.energy}")
            #     self.prev_energy = self.energy

            return self._sample_growth(all_coords, ground_matrix)