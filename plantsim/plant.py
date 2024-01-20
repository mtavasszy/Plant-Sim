from __future__ import annotations
from dataclasses import dataclass
from random import random

import numpy as np
from plantsim.cell_types import CellType

from plantsim.config import Config
from plantsim.coord import Coord
from plantsim.genome import Genome
from plantsim.plant_cell import Flower, PlantCell, Seed


@dataclass(kw_only=True)
class Plant:
    plant_cells: dict[Coord, PlantCell]
    genome: Genome
    coord: Coord
    age: int = 0
    is_landed: bool = False

    @classmethod
    def init_random(cls) -> Plant:
        """Create a randomly initialized seed"""
        return Plant(plant_cells={}, genome=Genome.init_random(), coord=Coord(int(Config.grid_size.x * random()),Config.initial_plant_coord.y))

    def update(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> list[Plant]:
        """
        Update the cells in the plant.
        Also updates `occupied_coords` while cells are being added/removed.
        If a flower produces a new seed, this function returns a new plant instance.
        """

        self.age += 1
        if self.age < Config.plant_lifespan:
            if not self.is_landed:
                self._fall_down(occupied_coords, ground_matrix)
            else:
                return self._update_cells(occupied_coords, ground_matrix)

    def _fall_down(self, occupied_coords: set[Coord], ground_matrix: np.ndarray):
        """Let the seed fall until it hits the ground"""

        if ground_matrix[self.coord.x, self.coord.y]:
            self.is_landed = True
            if not self.coord in occupied_coords:
                self.plant_cells[self.coord] = Seed(coord=self.coord, genome=self.genome)
                occupied_coords.add(self.coord)
        else:
            self.coord += Coord(0, 1)

    def _update_cells(self, occupied_coords: set[Coord], ground_matrix: np.ndarray) -> list[Plant]:
        """
        Update the cells of the plant.
        If a flower produces a new seed, this function returns a new plant instance.
        """

        new_plants = []

        for coord in set(self.plant_cells.keys()):
            plant_cell = self.plant_cells[coord]
            new_plant_cells = plant_cell.update(occupied_coords, ground_matrix)

            if isinstance(plant_cell, Flower) and plant_cell.seed_completed:
                new_plants.append(Plant(plant_cells={}, genome=self.genome.get_mutation(), coord=coord.copy()))
                del self.plant_cells[plant_cell.coord]
                occupied_coords.remove(plant_cell.coord)

            if new_plant_cells:
                self._add_new_cells(new_plant_cells, occupied_coords)

        return new_plants

    def _add_new_cells(self, new_plant_cells: list[PlantCell], occupied_coords: set[Coord]):
        """Apply all the cell updates"""

        for new_plant_cell in new_plant_cells:
            self.plant_cells[new_plant_cell.coord] = new_plant_cell
            occupied_coords.add(new_plant_cell.coord)

    def draw(self, image_data: np.ndarray):
        """Draw the plant cells into the image data"""

        if not self.plant_cells:
            image_data[self.coord.x, self.coord.y, :] = Config.cell_type_colors[CellType.SEED]
        else:
            for plant_cell in self.plant_cells.values():
                color = Config.cell_type_colors[plant_cell.cell_type] if self.age < Config.plant_lifespan else Config.dead_cell_color
                image_data[plant_cell.coord.x, plant_cell.coord.y, :] = color

    def clear_coords(self, occupied_coords: set[Coord]):
        for coord in self.plant_cells.keys():
            occupied_coords.remove(coord)