from __future__ import annotations
from abc import ABC
import copy
from dataclasses import dataclass
from typing import ClassVar
from typing_extensions import Self
import numpy as np

from plantsim.cell_types import CellType
from plantsim.cell_update import CellUpdate
from plantsim.config import Config


from plantsim.genome import Genome


@dataclass(kw_only=True)
class PlantCell(ABC):
    """Abstract base class for different cell types"""

    cell_type: ClassVar[CellType]
    is_alive = True
    genome: Genome
    coords: tuple[int, int]
    parent: PlantCell
    cell_distance: int
    age: int = 0  # age in ticks
    water: float = 0.0
    energy: float = 0.0

    creation_cost_water: float = Config.default_creation_cost
    creation_cost_energy: float = Config.default_creation_cost
    constant_loss_water: float = Config.default_loss_per_tick
    constant_loss_energy: float = Config.default_loss_per_tick

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

    def update(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> list[CellUpdate]:
        """Update the state of the plant cell."""

        self.age += 1
        if not self.parent.is_alive and self.is_alive:
            self.age = self.parent.age
            self.is_alive = False

        if not self.is_alive:
            if self.age >= Config.dead_cell_lifespan:
                return [CellUpdate(coords=self.coords, update_with=None)]

        if self.is_alive:
            self._share_resources_with_parent()

    def _sample_growth(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> list[CellUpdate]:
        """Determine whether a new cell will be created and in which direction"""
        cell_updates = []

        age = 1
        density = 1
        water = self.water / Config.cell_resource_capacity
        energy = self.energy / Config.cell_resource_capacity

        expressions = self.genome.test_expression(self.cell_type, age, density, self.cell_distance, water, energy)
        for cell_type, directional_expressions in expressions.items():
            cell_class = next((subclass for subclass in PlantCell.__subclasses__() if subclass.cell_type is cell_type))

            if self.energy >= cell_class.creation_cost_energy and self.water >= cell_class.creation_cost_water:
                if any(directional_expressions):
                    for directional_expression, coord_offset in zip(
                        directional_expressions, Config.coords_for_directions
                    ):
                        if directional_expression:
                            new_coords = (self.coords[0] + coord_offset[0], self.coords[1] + coord_offset[1])
                            if not new_coords in all_coords:
                                if (cell_type is CellType.ROOT and ground_matrix[new_coords[0], new_coords[1]]) or (
                                    not cell_type is CellType.ROOT and not ground_matrix[new_coords[0], new_coords[1]]
                                ):
                                    self.energy -= cell_class.creation_cost_energy
                                    self.water -= cell_class.creation_cost_water

                                    new_plant_cell = cell_class(
                                        genome=self.genome,
                                        coords=new_coords,
                                        parent=self,
                                        cell_distance=self.cell_distance + 1,
                                    )
                                    # TODO keep track of branching properly
                                    cell_updates.append(CellUpdate(coords=new_coords, update_with=new_plant_cell))
        return cell_updates

    def _share_resources_with_parent(self):
        """Share water and energy with parent plant cells"""

        total_energy = self.parent.energy + self.energy
        total_water = self.parent.water + self.water

        self.energy = total_energy / 2
        self.parent.energy = total_energy / 2
        self.water = total_water / 2
        self.parent.water = total_water / 2

    def _get_surrounding_soil_factor(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> float:
        """Get the factor of empty ground cells surrounding this cell"""

        surrounding_soil = 0
        for coord in Config.coords_for_directions:
            surrounding_soil += int(coord not in all_coords and ground_matrix[coord[0], coord[1]])
        return surrounding_soil / 8

    def _get_surrounding_air_factor(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> float:
        """Get the factor of empty air cells surrounding this cell"""

        surrounding_air = 0
        for coord in Config.coords_for_directions:
            surrounding_air += int(coord not in all_coords and not ground_matrix[coord[0], coord[1]])
        return surrounding_air / 8

    # def _apply_loss_per_tick(self):
    #     self.water -= self.constant_loss_water
    #     self.energy -= self.constant_loss_energy


@dataclass(kw_only=True)
class Stem(PlantCell):
    cell_type = CellType.STEM

    def update(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> list[CellUpdate]:
        """Update the state of the plant cell."""

        potential_result = super().update(all_coords, ground_matrix)
        if potential_result:
            return potential_result

        if self.is_alive:
            self._collect_resources(all_coords, ground_matrix)
            return self._sample_growth(all_coords, ground_matrix)

    def _collect_resources(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray):
        """Get the amount of energy the leaf cell generates per tick"""

        surrounding_air_factor = self._get_surrounding_air_factor(all_coords, ground_matrix)
        self.energy += Config.stem_energy_gain * surrounding_air_factor


@dataclass(kw_only=True)
class Root(PlantCell):
    cell_type = CellType.ROOT

    def update(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> list[CellUpdate]:
        """Update the state of the plant cell."""

        potential_result = super().update(all_coords, ground_matrix)
        if potential_result:
            return potential_result

        if self.is_alive:
            self._collect_resources(all_coords, ground_matrix)
            return self._sample_growth(all_coords, ground_matrix)

    def _collect_resources(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray):
        """Get the amount of water the root cell generates per tick"""

        surrounding_soil_factor = self._get_surrounding_soil_factor(all_coords, ground_matrix)
        self.water += Config.root_water_gain * surrounding_soil_factor


@dataclass(kw_only=True)
class Leaf(PlantCell):
    cell_type = CellType.LEAF

    def update(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> list[CellUpdate]:
        """Update the state of the plant cell."""

        potential_result = super().update(all_coords, ground_matrix)
        if potential_result:
            return potential_result

        if self.is_alive:
            self._collect_resources(all_coords, ground_matrix)

    def _collect_resources(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray):
        """Get the amount of energy the leaf cell generates per tick"""

        surrounding_air_factor = self._get_surrounding_air_factor(all_coords, ground_matrix)
        self.energy += Config.leaf_energy_gain * surrounding_air_factor


@dataclass(kw_only=True)
class Flower(PlantCell):
    cell_type = CellType.FLOWER

    seed_progress_water = 0.0
    seed_progress_energy = 0.0

    def update(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> list[CellUpdate]:
        """Grow the flower into a seed"""

        potential_result = super().update(all_coords, ground_matrix)
        if potential_result:
            return potential_result

        return self._grow_seed()

    def _grow_seed(self) -> list[CellUpdate]:
        if self.water > Config.flower_grow_rate and self.seed_progress_water < Config.seed_creation_cost:
            self.water -= Config.flower_grow_rate
            self.seed_progress_water += Config.flower_grow_rate * Config.flower_growth_efficiency
        if self.energy > Config.flower_grow_rate and self.seed_progress_energy < Config.seed_creation_cost:
            self.energy -= Config.flower_grow_rate
            self.seed_progress_energy += Config.flower_grow_rate * Config.flower_growth_efficiency

        if (
            self.seed_progress_energy >= Config.seed_creation_cost
            and self.seed_progress_water >= Config.seed_creation_cost
        ):
            copy_coords = copy.copy(self.coords)
            new_seed = Seed(genome=self.genome.mutate(), coords=copy_coords)
            return [
                CellUpdate(coords=self.coords, update_with=None),
                CellUpdate(coords=copy_coords, update_with=new_seed),
            ]


@dataclass(kw_only=True)
class Seed(PlantCell):
    cell_type = CellType.SEED

    init_water_cost: float = Config.seed_creation_cost
    init_energy_cost: float = Config.seed_creation_cost
    energy: float = init_water_cost
    water: float = init_energy_cost

    parent: PlantCell = None
    cell_distance: int = 0

    prev_water = water
    prev_energy = energy

    @classmethod
    def init_random(cls, coords: tuple[int, int]) -> Seed:
        """Create a randomly initialized seed"""
        genome = Genome.init_random()
        return Seed(genome=genome, coords=coords)

    def update(self, all_coords: set[tuple[int, int]], ground_matrix: np.ndarray) -> list[CellUpdate]:
        """Update the state of the plant cell"""

        # if in air, drop to the ground. Else, grow.
        if not ground_matrix[self.coords[0], self.coords[1]]:
            return self._fall_down()
        else:
            self.age += 1
            if self.is_alive and self.age >= Config.cell_lifespan:
                self.age = 0
                self.is_alive = False

            if not self.is_alive:
                if self.age >= Config.dead_cell_lifespan:
                    return [CellUpdate(coords=self.coords, update_with=None)]

            if self.is_alive:
                return self._sample_growth(all_coords, ground_matrix)


    def _fall_down(self) -> list[CellUpdate]:
        self_moved = self.copy()
        self_moved.coords = (self.coords[0], self.coords[1] + 1)

        return [
            CellUpdate(coords=self.coords, update_with=None),
            CellUpdate(coords=self_moved.coords, update_with=self_moved),
        ]
