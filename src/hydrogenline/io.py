from pathlib import Path
import numpy as np
import json
from datetime import datetime
from typing import List, Tuple, Dict
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
    
def get_reference_folder() -> Path:
    path = Path.home() / ".hydrogenline" / "references"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_reference_path(fname: str) -> Path:
    return get_reference_folder() / fname

def load_reference_settings(fname: str) -> dict:
    with open(get_reference_folder() / f"{fname}.json", "rb") as f:
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

def load_data(folder: str) -> Tuple[List[datetime], Dict[str, NDArray[np.float64]]]:
    path = get_data_path(folder)
    files = [file for file in path.iterdir()]

    datetimes = [parse_datetime(file) for file in files]

    settings = load_settings(folder)
    bins = settings["bins"]
    num_meas = len(files)

    # Data with each file containing the PSD for several windowing functions
    PSD_orig = [np.load(file, allow_pickle=True).item() for file in files]

    # Group data per windowing function
    PSD = {}
    for window in settings["windows"]:
        PSD[window] = np.zeros((num_meas, bins))

        for i in range(num_meas):
            PSD[window][i,:] = PSD_orig[i][window]

    return datetimes, PSD

def load_reference(fname: str) -> Dict[str, NDArray[np.float64]]:
    path = get_reference_path(f"{fname}.npy")

    if not path.exists():
        return None

    return np.load(path, allow_pickle=True).item()