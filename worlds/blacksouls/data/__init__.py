import json
import pkgutil


def _load(name: str):
    return json.loads(pkgutil.get_data(__name__, name).decode("utf-8"))


LOCATIONS = _load("locations.json")
BOSSES = _load("bosses.json")
ITEMS = _load("items.json")
ENEMIES = _load("enemies.json")
