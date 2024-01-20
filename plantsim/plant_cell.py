from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from typing import ClassVar
import numpy as np

from plantsim.cell_types import CellType
from plantsim.config import Config
from plantsim.coord import Coord
from plantsim.genome import Genome


@dataclass(kw_only=True)
class PlantCell(ABC):
    """Abstract base class for different cell types"""

    cell_type: ClassVar[CellType]
    coord: Coord
    genome: Genome
    parent: PlantCell
    cell_distance: int
    growth_cooldown: int = 0
    age: int = 0  # age in ticks
    water: float = 0.0
    energy: float = 0.0

    creation_cost_water: float = Config.default_creation_cost
    creation_cost_energy: float = Config.default_creation_cost
    constant_loss_water: float = Config.default_loss_per_tick
    constant_loss_energy: float = Config.default_loss_per_tick

    def update(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> list[PlantCell]:
        """Update the state of the plant cell."""

        self.age += 1
        self._apply_loss_per_tick()
        self._share_resources_with_parent()

    def _sample_growth(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> list[PlantCell]:
        """Determine whether a new cell will be created and in which direction"""

        if self.growth_cooldown > 0:
            self.growth_cooldown -= 1
            return

        new_cells = []

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
                            new_coord = self.coord + coord_offset
                            if not (
                                new_coord in occupied_coords
                                or new_coord.x < 0
                                or new_coord.x > Config.grid_size.x - 1
                                or new_coord.y < 0
                                or new_coord.y > Config.grid_size.y - 1
                            ):
                                if (cell_type is CellType.ROOT and ground_matrix[new_coord.x, new_coord.y]) or (
                                    not cell_type is CellType.ROOT and not ground_matrix[new_coord.x, new_coord.y]
                                ):
                                    self.energy -= cell_class.creation_cost_energy
                                    self.water -= cell_class.creation_cost_water

                                    new_plant_cell = cell_class(
                                        genome=self.genome,
                                        coord=new_coord,
                                        parent=self,
                                        cell_distance=self.cell_distance + 1,
                                    )
                                    new_cells.append(new_plant_cell)
                                    self.growth_cooldown = Config.growth_cooldown
        return new_cells

    def _share_resources_with_parent(self):
        """Share water and energy with parent plant cells"""

        total_energy = self.parent.energy + self.energy
        total_water = self.parent.water + self.water

        self.energy = total_energy / 2
        self.parent.energy = total_energy / 2
        self.water = total_water / 2
        self.parent.water = total_water / 2

    def _get_surrounding_soil_factor(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> float:
        """Get the factor of empty ground cells surrounding this cell"""

        surrounding_soil = 0
        for coord in Config.coords_for_directions:
            surrounding_soil += int(coord not in occupied_coords and ground_matrix[coord.x, coord.y])
        return surrounding_soil / 8

    def _get_surrounding_air_factor(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> float:
        """Get the factor of empty air cells surrounding this cell"""

        surrounding_air = 0
        for coord in Config.coords_for_directions:
            surrounding_air += int(coord not in occupied_coords and not ground_matrix[coord.x, coord.y])
        return surrounding_air / 8

    def _apply_loss_per_tick(self):
        self.water -= self.constant_loss_water
        self.energy -= self.constant_loss_energy


@dataclass(kw_only=True)
class Stem(PlantCell):
    cell_type = CellType.STEM

    def update(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> list[PlantCell]:
        """Update the state of the plant cell."""

        super().update(occupied_coords, ground_matrix)
        self._collect_resources(occupied_coords, ground_matrix)
        return self._sample_growth(occupied_coords, ground_matrix)

    def _collect_resources(self, occupied_coords: set[Coord], ground_matrix: np.ndarray):
        """Get the amount of energy the leaf cell generates per tick"""

        surrounding_air_factor = self._get_surrounding_air_factor(occupied_coords, ground_matrix)
        self.energy += Config.stem_energy_gain * surrounding_air_factor


@dataclass(kw_only=True)
class Root(PlantCell):
    cell_type = CellType.ROOT

    def update(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> list[PlantCell]:
        """Update the state of the plant cell."""

        super().update(occupied_coords, ground_matrix)
        self._collect_resources(occupied_coords, ground_matrix)
        return self._sample_growth(occupied_coords, ground_matrix)

    def _collect_resources(self, occupied_coords: set[Coord], ground_matrix: np.ndarray):
        """Get the amount of water the root cell generates per tick"""

        surrounding_soil_factor = self._get_surrounding_soil_factor(occupied_coords, ground_matrix)
        self.water += Config.root_water_gain * surrounding_soil_factor


@dataclass(kw_only=True)
class Leaf(PlantCell):
    cell_type = CellType.LEAF

    def update(self, occupied_coords: set[Coord], ground_matrix: np.ndarray):
        """Update the state of the plant cell."""

        super().update(occupied_coords, ground_matrix)
        self._collect_resources(occupied_coords, ground_matrix)

    def _collect_resources(self, occupied_coords: set[Coord], ground_matrix: np.ndarray):
        """Get the amount of energy the leaf cell generates per tick"""

        surrounding_air_factor = self._get_surrounding_air_factor(occupied_coords, ground_matrix)
        self.energy += Config.leaf_energy_gain * surrounding_air_factor


@dataclass(kw_only=True)
class Flower(PlantCell):
    cell_type = CellType.FLOWER

    seed_progress_water = 0.0
    seed_progress_energy = 0.0

    seed_completed = False

    def update(self, occupied_coords: set[Coord], ground_matrix: np.ndarray):
        """Grow the flower into a seed"""

        super().update(occupied_coords, ground_matrix)
        return self._grow_seed()

    def _grow_seed(self):
        """Consume resources and turn it into a seed once enough have been consumed"""

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
            self.seed_completed = True


@dataclass(kw_only=True)
class Seed(PlantCell):
    cell_type = CellType.SEED

    init_water_cost: float = Config.seed_creation_cost
    init_energy_cost: float = Config.seed_creation_cost
    energy: float = init_water_cost
    water: float = init_energy_cost

    parent: PlantCell = None
    cell_distance: int = 0

    def update(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> list[PlantCell]:
        """Update the state of the plant cell"""

        self.age += 1
        return self._sample_growth(occupied_coords, ground_matrix)
