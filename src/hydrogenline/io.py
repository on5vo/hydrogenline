from pathlib import Path

def get_path(folder: str):
    path = Path.home() / ".hydrogenline" / folder
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_data_path(folder: str):
    path =  get_path(folder) / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path