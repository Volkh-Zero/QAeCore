import json
from importlib import resources


def display_name(import_safe: str) -> str:
    try:
        with resources.files(__package__).joinpath("myth_map.json").open("r", encoding="utf-8") as f:
            mp = json.load(f)
        return mp.get(import_safe, import_safe)
    except Exception:
        return import_safe
