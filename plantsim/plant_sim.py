from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import cv2
import numpy as np
from pydantic import BaseModel
from pydantic_numpy import np_array_pydantic_annotated_typing as ndarray

import contextlib
from plantsim.cell_update import CellUpdate

with contextlib.redirect_stdout(None):
    from pygame import Surface
from plantsim.config import Config

from plantsim.plant import PlantCell, Seed


@dataclass(kw_only=True)
class PlantSim:
    ground_matrix: ndarray(
        np.bool_
    )  # boolean matrix indicating whether a cell is ground or not
    plant_cells: dict[tuple[int, int], PlantCell]

    @classmethod
    def create(cls) -> PlantSim:
        """Create a new plant sim with a single seed"""

        ground_matrix = PlantSim._load_ground_matrix(Config.ground_mask_path)
        initial_seed = Seed.init_random(coords=Config.initial_seed_coords)
        cells = {Config.initial_seed_coords: initial_seed}

        return PlantSim(ground_matrix=ground_matrix, plant_cells=cells)

    @staticmethod
    def _load_ground_matrix(ground_mask_path: Path) -> np.ndarray:
        """load a ground matrix from an image file"""

        im = cv2.imread(str(ground_mask_path), cv2.IMREAD_GRAYSCALE).T
        ground_matrix = im[:, :] < 1  # black is ground
        return ground_matrix

    def get_background_array(self) -> Surface:
        """Return a PyGame Surface object to draw the air and ground"""

        image_data = np.array(
            [
                [(Config.ground_color if elem else Config.air_color) for elem in row]
                for row in self.ground_matrix
            ]
        )

        return image_data

    def update(self):
        """Update all plant cells"""
        plant_cell_coords = set(self.plant_cells.keys())

        for coord in plant_cell_coords:
            plant_cell = self.plant_cells[coord]
            cell_updates = plant_cell.update(plant_cell_coords, self.ground_matrix)
            self.apply_cell_updates(cell_updates)

    def draw(self, image_data: np.ndarray):
        """Draw a colored pixel in the image data for each plat cell"""

        for coord, plant_cell in self.plant_cells.items():
            image_data[*coord, :] = Config.cell_type_colors[plant_cell.cell_type]
            
            # resource color visualisation
            # water_color = np.array([0, 162, 232])
            # energy_color = np.array([255, 255, 0])
            # water_max = max([e.water for e in self.plant_cells.values()]) * 2
            # energy_max = max([e.energy for e in self.plant_cells.values()]) *2
            # image_data[*coord, :] = np.clip((plant_cell.water / water_max) * water_color + (plant_cell.energy / energy_max) * energy_color, [0,0,0], [255,255,255])

        return image_data

    def apply_cell_updates(self, cell_updates: list[CellUpdate]):
        """Apply all the cell updates"""

        for cell_update in cell_updates:
            if cell_update.update_with is None:
                del self.plant_cells[*cell_update.coords]
            else:
                self.plant_cells[cell_update.coords] = cell_update.update_with
