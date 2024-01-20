from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np
from pydantic_numpy import np_array_pydantic_annotated_typing as ndarray

from plantsim.coord import Coord
from plantsim.genome import Genome
from plantsim.plant import Plant
from plantsim.config import Config

import contextlib

with contextlib.redirect_stdout(None):
    from pygame import Surface


@dataclass(kw_only=True)
class PlantSim:
    ground_matrix: ndarray(np.bool_)  # boolean matrix indicating whether a cell is ground or not
    occupied_coords: set[Coord]
    plants: list[Plant]

    @classmethod
    def create(cls) -> PlantSim:
        """Create a new plant sim with a single randomly initialized plant"""

        ground_matrix = PlantSim._load_ground_matrix(Config.ground_mask_path)
        occupied_coords = set()
        n_plants = 10
        first_plants = [Plant(plant_cells={}, genome=Genome.init_random(), coord=Coord(x + int(Config.grid_size.x / n_plants / 2), Config.initial_plant_coord.y)) for x in range(0, Config.grid_size.x, int(Config.grid_size.x / n_plants))]
        return PlantSim(ground_matrix=ground_matrix, occupied_coords=occupied_coords, plants=first_plants)

    @staticmethod
    def _load_ground_matrix(ground_mask_path: Path) -> np.ndarray:
        """load a ground matrix from an image file"""

        im = cv2.imread(str(ground_mask_path), cv2.IMREAD_GRAYSCALE).T
        ground_matrix = im[:, :] < 1  # black is ground
        return ground_matrix

    def get_background_array(self) -> np.ndarray:
        """Return a PyGame Surface object to draw the air and ground"""

        image_data = np.array(
            [[(Config.ground_color if elem else Config.air_color) for elem in row] for row in self.ground_matrix]
        )

        return image_data

    def update(self):
        """Update all plant cells"""

        new_plants: list[list[Plant]] = []
        remove_plants = False

        for plant in self.plants:
            new_plants.append(plant.update(self.occupied_coords, self.ground_matrix))
            if plant.age > Config.plant_lifespan + Config.dead_cell_lifespan:
                plant.clear_coords(self.occupied_coords)
                remove_plants = True

        if remove_plants:
            self.plants = [plant for plant in self.plants if plant.age <= Config.plant_lifespan + Config.dead_cell_lifespan]

        for new_plant_list in new_plants:
            if new_plant_list:
                for new_plant in new_plant_list:
                    self.plants.append(new_plant)

    def draw(self, image_data: np.ndarray):
        """Draw a colored pixel in the image data for each plant cell"""

        for plant in self.plants:
            plant.draw(image_data)

            # resource color visualisation
            # water_color = np.array([0, 162, 232])
            # energy_color = np.array([255, 255, 0])
            # water_max = max([e.water for e in self.plant_cells.values()]) * 2
            # energy_max = max([e.energy for e in self.plant_cells.values()]) *2
            # image_data[*coord, :] = np.clip((plant_cell.water / water_max) * water_color + (plant_cell.energy / energy_max) * energy_color, [0,0,0], [255,255,255])

        return image_data
