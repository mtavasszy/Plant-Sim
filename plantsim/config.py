from pathlib import Path


class Config:
    app_title = "Plant Sim"

    root_dir_path = Path(__file__).parent.parent
    data_dir_path = root_dir_path / "data"
    ground_mask_path = data_dir_path / "groundmask.png"

    window_size = (1280, 720)
    grid_size= (320, 180)
    air_color = (194,234,246)
    ground_color = (206,163,97)