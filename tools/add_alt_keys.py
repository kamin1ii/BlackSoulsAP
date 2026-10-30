# Adds the event keys another game version uses for the same pickups
import json
import sys
from pathlib import Path

TABLE = Path(sys.argv[1])
OTHER = Path(sys.argv[2])

base = json.loads(TABLE.read_text(encoding="utf-8"))
other = json.loads(OTHER.read_text(encoding="utf-8"))
base_keys = {l["key"] for l in base}
other_keys = {l["key"] for l in other}
free = [l for l in other if l["key"] not in base_keys]


def event_of(loc):
    return loc["key"].rsplit(":", 1)[0]


def item_of(loc):
    return loc["kind"], loc["id"], loc["amount"]


used = set()
added = 0
for loc in base:
    if loc["key"] in other_keys:
        continue
    match = sorted((m for m in free if event_of(m) == event_of(loc) and item_of(m) == item_of(loc)
                    and m["key"] not in used), key=lambda m: int(m["key"].rsplit(":", 1)[1]))
    if not match:
        print("no match for", loc["name"])
        continue
    used.add(match[0]["key"])
    loc.setdefault("alt_keys", [])
    if match[0]["key"] not in loc["alt_keys"]:
        loc["alt_keys"].append(match[0]["key"])
        added += 1

TABLE.write_text(json.dumps(base, ensure_ascii=False, indent=0), encoding="utf-8")
print(added, "alt keys added")
