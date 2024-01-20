from pathlib import Path

from plantsim.cell_types import CellType
from plantsim.coord import Coord


class Config:
    app_title = "Plant Sim"

    # DATA
    root_dir_path = Path(__file__).parent.parent
    data_dir_path = root_dir_path / "data"
    ground_mask_path = data_dir_path / "groundmask.png"

    # VISUAL
    window_size = Coord(1280, 720)
    grid_size = Coord(window_size.x / 4, window_size.y / 4)
    air_color = (194, 234, 246)
    ground_color = (206, 163, 97)

    cell_type_colors = {
        CellType.SEED: (0, 0, 0),  # (255, 200, 140),
        CellType.ROOT: (145, 104, 45),
        CellType.STEM: (0, 100, 0),
        CellType.LEAF: (0, 255, 0),
        CellType.FLOWER: (255, 128, 255),  # TODO make hue variable from genome
    }
    dead_cell_color = (80, 49, 33)

    # SIMULATION
    initial_plant_coord = Coord(int(grid_size.x / 2), int(grid_size.y / 4))
    tick_rate = 0 # set to 0 for as fast as possible
    base_growth_p = 0.01
    flower_grow_rate = 0.1
    flower_growth_efficiency = 2 # 0.5
    growth_cooldown = 20

    # GENOME
    distance_factor_scale = 0.05
    direction_mutation_p = 1 / (6 * 8) # 6 sets of 8 directions per genome
    redetermination_p = 0.1
    mutation_sigma = 0.2

    # RESOURCES
    leaf_energy_gain = 0.1
    stem_energy_gain = 0.01
    root_water_gain = 0.1
    default_creation_cost = 0.5
    default_loss_per_tick = 0.01
    seed_creation_cost = 10
    cell_resource_capacity = 10

    # PLANTS
    plant_lifespan = 2000  # cell lifespan in ticks
    dead_cell_lifespan = 200

    growable_types = {
        CellType.SEED: [CellType.STEM, CellType.ROOT],
        CellType.ROOT: [CellType.ROOT],
        CellType.STEM: [CellType.STEM, CellType.LEAF, CellType.FLOWER],
        CellType.LEAF: [],
        CellType.FLOWER: [],
    }

    # MISC
    coords_for_directions = [
        Coord(1, 0),
        Coord(1, -1),
        Coord(0, -1),
        Coord(-1, -1),
        Coord(-1, 0),
        Coord(-1, 1),
        Coord(0, 1),
        Coord(1, 1),
    ]
