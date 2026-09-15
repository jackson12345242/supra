import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _path(name):
    return os.path.join(DATA_DIR, f"{name}.json")


def read_json(name, fallback):
    path = _path(name)
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            return json.loads(content) if content else fallback
    except (json.JSONDecodeError, OSError) as err:
        print(f"Failed to read {name}.json: {err}")
        return fallback


def write_json(name, data):
    path = _path(name)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
