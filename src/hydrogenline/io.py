from pathlib import Path
import numpy as np
import json
from datetime import datetime
from typing import List, Tuple
from numpy.typing import NDArray

def get_path(folder: str) -> Path:
    path = Path.home() / ".hydrogenline" / folder
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_data_path(folder: str) -> Path:
    path =  get_path(folder) / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_waterfall_path(folder: str) -> Path:
    path =  get_path(folder) / "waterfall"
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_settings(folder: str) -> dict:
    with open(get_path(folder) / "settings.json", "rb") as f:
        return json.loads(f.read())
    
def parse_datetime(file: Path) -> datetime:
    """
    Parses a datetime from the filename, trying two different formats.
    """
    try:
        dt = datetime.strptime(file.name.removesuffix(".npy"), "%Y%m%d_%H:%M:%S")
    except ValueError:
        dt = datetime.strptime(file.name.removesuffix(".npy"), "%Y%m%d_%H_%M_%S")
    return dt

def load_data(folder: str) -> Tuple[List[datetime], List[List[NDArray[np.float64]]]]:
    path = get_data_path(folder)
    files = [file for file in path.iterdir()]

    datetimes = [parse_datetime(file) for file in files]

    settings = load_settings(folder)
    num_windows = len(settings["windows"])
    bins = settings["bins"]
    num_meas = len(files)

    # Data with each file containing the PSD for several windowing functions
    PSD_orig = [np.load(file) for file in files]

    # Group data per windowing function
    PSD = [np.zeros((num_meas, bins)) for _ in range(num_windows)]
    for i in range(num_meas):
        for j in range(num_windows):
            PSD[j][i,:] = PSD_orig[i][j,:]

    return datetimes, PSD