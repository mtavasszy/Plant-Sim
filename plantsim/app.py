from __future__ import annotations


import numpy as np

from plantsim.plant_sim import PlantSim

import contextlib

with contextlib.redirect_stdout(None):
    import pygame
    from pygame import DOUBLEBUF, HWSURFACE, Surface

from pydantic import BaseModel, ConfigDict
from pydantic_numpy import np_array_pydantic_annotated_typing as ndarray

from plantsim.config import Config


class App(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    plant_sim: PlantSim
    background_array: ndarray(np.uint8)
    display: Surface

    @classmethod
    def create(cls) -> App:
        """Initialize a plant simulation application"""

        # create plantsim
        plant_sim = PlantSim.create()
        background_array = plant_sim.get_background_array()

        # init pygame and create a display
        pygame.init()
        display = pygame.display.set_mode(
            size=Config.window_size, flags=HWSURFACE | DOUBLEBUF
        )
        pygame.display.set_caption(Config.app_title)

        # create app
        return App(
            plant_sim=plant_sim, display=display, background_array=background_array
        )

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    running = False

            self._update()
            self._draw()

        pygame.quit()

    def _update(self):
        self.plant_sim.update()

    def _draw(self):
        # draw pixel data
        image_data = self.background_array.copy()
        image_data = self.plant_sim.draw(image_data)

        # create and scale surface for big pixels
        surface = pygame.surfarray.make_surface(image_data)
        scaled_surface = pygame.transform.scale(surface, Config.window_size)
        self.display.blit(scaled_surface, (0, 0))
        pygame.display.update()
