from __future__ import annotations

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame import DOUBLEBUF, HWSURFACE, Surface

from pathlib import Path
import cv2

import numpy as np
from pydantic import BaseModel, ConfigDict
import pygame
from plant import PlantCell
from pydantic_numpy import np_array_pydantic_annotated_typing as ndarray

from config import Config

class App(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    grid: list[list[None | PlantCell]]
    ground_matrix: ndarray(np.bool_) # boolean matrix indicating whether a cell is ground or not
    background_surface: Surface
    display: Surface


    @classmethod
    def create(cls) -> App:
        """Initialize a plant simulation application"""

        # create grid
        grid = [[None for _ in range(Config.grid_size[1])] for _ in range(Config.grid_size[0])]
        ground_matrix = App._load_ground_matrix(Config.ground_mask_path)
        background_surface = App._get_background_surface(ground_matrix)

        # init pygame and create a display 
        pygame.init()
        display = pygame.display.set_mode(size=Config.window_size, flags=HWSURFACE|DOUBLEBUF)
        pygame.display.set_caption(Config.app_title)

        return App(grid=grid, ground_matrix=ground_matrix, display=display, background_surface=background_surface)

    @staticmethod
    def _load_ground_matrix(ground_mask_path: Path) -> np.ndarray:
        """load a ground matrix from an image file"""

        im = cv2.imread(str(ground_mask_path), cv2.IMREAD_GRAYSCALE)
        ground_matrix = im[:,:] < 1 # black is ground
        return ground_matrix

    @staticmethod
    def _get_background_surface(ground_matrix: np.ndarray) -> Surface:
        """Return a PyGame Surface object to draw the air and ground"""

        image_data = np.array([[(Config.ground_color if elem else Config.air_color) for elem in row] for row in ground_matrix.T])

        surface = pygame.surfarray.make_surface(image_data)
        scaled_surface = pygame.transform.scale(surface, Config.window_size)
        return scaled_surface
    
    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self._update()
            self._draw()

        pygame.quit()


    def _update(self):
        pass

    def _draw(self):
        self.display.blit(self.background_surface, (0, 0))
        pygame.display.update()
