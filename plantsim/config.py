from pathlib import Path

from plantsim.cell_types import CellType


class Config:
    app_title = "Plant Sim"

    # DATA
    root_dir_path = Path(__file__).parent.parent
    data_dir_path = root_dir_path / "data"
    ground_mask_path = data_dir_path / "groundmask.png"

    # VISUAL
    window_size = (1280, 720)
    grid_size = (window_size[0] / 4, window_size[0] / 4)
    air_color = (194, 234, 246)
    ground_color = (206, 163, 97)

    cell_type_colors = {
        CellType.SEED: (0, 0, 0),  # (255, 200, 140),
        CellType.ROOT: (145, 104, 45),
        CellType.STEM: (0, 100, 0),
        CellType.LEAF: (0, 255, 0),
        CellType.FLOWER: (0,0,0)#(255, 128, 255),  # TODO make hue variable from genome
    }

    # SIMULATION
    initial_seed_coords = (int(grid_size[0] / 2), int(grid_size[1] / 4))
    tick_rate = 20
    base_growth_p = 0.01
    leaf_energy_gain = 0.1
    root_water_gain = 0.1

    # PLANTS
    lifespan = 1000  # cell lifespan in ticks
    growable_types = {
        CellType.SEED: [CellType.STEM, CellType.ROOT],
        CellType.ROOT: [CellType.ROOT],
        CellType.STEM: [CellType.STEM, CellType.LEAF, CellType.FLOWER],
        CellType.LEAF: [],
        CellType.FLOWER: []
    }

    # MISC
    coords_for_directions = [(1,0), (1,-1), (0,-1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1,1)]