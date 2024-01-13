from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np
from pydantic import BaseModel
from pydantic_numpy import np_array_pydantic_annotated_typing as ndarray
from pygame import Surface
from plantsim.config import Config

from plantsim.plant import PlantCell


class PlantSim(BaseModel):
    ground_matrix: ndarray(
        np.bool_
    )  # boolean matrix indicating whether a cell is ground or not
    cells: dict[tuple[int, int], PlantCell]

    @classmethod
    def create(cls) -> PlantSim:
        """Create a new plant sim with a single seed"""

        ground_matrix = PlantSim._load_ground_matrix(Config.ground_mask_path)
        cells = {}

        return PlantSim(ground_matrix=ground_matrix, cells=cells)

    @staticmethod
    def _load_ground_matrix(ground_mask_path: Path) -> np.ndarray:
        """load a ground matrix from an image file"""

        im = cv2.imread(str(ground_mask_path), cv2.IMREAD_GRAYSCALE)
        ground_matrix = im[:, :] < 1  # black is ground
        return ground_matrix

    def get_background_array(self) -> Surface:
        """Return a PyGame Surface object to draw the air and ground"""

        image_data = np.array(
            [
                [(Config.ground_color if elem else Config.air_color) for elem in row]
                for row in self.ground_matrix.T
            ]
        )

        return image_data

    def update(self):
        pass

    def draw(self, image_data: np.ndarray):
        image_data[1, 1, :]  = (255, 0, 0)

        return image_data
