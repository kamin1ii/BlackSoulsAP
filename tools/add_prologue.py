# Adds the prologue pickups as checks with a mirror spot in the main game dungeon
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rbmarshal import load, text

DATA = Path(sys.argv[1])
TABLE = Path(sys.argv[2])
# prologue map and the main game map it was copied from
MIRRORS = {98: 2, 99: 6}
DUNGEON_KEY = 50
KINDS = {126: "item", 127: "weapon", 128: "armor"}


def tiles(m):
    d = m["data"].data
    _, xs, ys, zs, n = struct.unpack_from("<5i", d, 0)
    vals = struct.unpack_from(f"<{n}h", d, 20)
    return lambda x, y: tuple(vals[x + y * xs + z * xs * ys] for z in range(zs)) if 0 <= x < xs and 0 <= y < ys else None


def free_spot(main, x, y):
    tile_at = tiles(main)
    taken = {(ev["x"], ev["y"]) for ev in main["events"].values()}
    want = tile_at(x, y)

    def floor(p):
        t = tile_at(*p)
        return t is not None and t[0] == want[0] and t[2] in (0, want[2])

    # walk outward over connected floor so the spot stays in the same room
    queue, seen = [(x, y)], {(x, y)}
    while queue:
        p = queue.pop(0)
        if p not in taken:
            return p
        for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
            if q not in seen and floor(q):
                seen.add(q)
                queue.append(q)
    raise ValueError(f"no free spot near {x},{y}")


def clean(name):
    name = text(name).replace("　", " ").replace("【", " [").replace("】", "]")
    return " ".join(name.split()).replace("[ ", "[")


tables = {126: load(DATA / "Items.rvdata2"), 127: load(DATA / "Weapons.rvdata2"), 128: load(DATA / "Armors.rvdata2")}
locations = json.loads(TABLE.read_text(encoding="utf-8"))
known = {l["key"] for l in locations}
names = {l["name"] for l in locations}
added = 0
for src, dst in MIRRORS.items():
    prologue, main = load(DATA / f"Map{src:03d}.rvdata2"), load(DATA / f"Map{dst:03d}.rvdata2")
    for eid, ev in sorted(prologue["events"].items()):
        page = ev["pages"][0]
        for i, cmd in enumerate(page["list"]):
            if cmd["code"] not in KINDS or cmd["parameters"][1] != 0 or cmd["parameters"][0] == DUNGEON_KEY:
                continue
            key = f"{src}:{eid}:0:{i}"
            if key in known:
                continue
            gid, amount = cmd["parameters"][0], cmd["parameters"][3]
            item = clean(tables[cmd["code"]][gid]["name"])
            name = f"Fort Ivern - Prologue {item}" + (f" x{amount}" if amount > 1 else "")
            n = 2
            while name in names:
                name = f"Fort Ivern - Prologue {item} {n}"
                n += 1
            names.add(name)
            x, y = free_spot(main, ev["x"], ev["y"])
            locations.append(dict(key=key, area="Fort Ivern", kind=KINDS[cmd["code"]], id=gid, amount=amount,
                                  item=item, quest=False, key_door=dst == 2, name=name,
                                  mirror=dict(map=dst, x=x, y=y, src_map=src, src_event=eid)))
            added += 1

TABLE.write_text(json.dumps(locations, ensure_ascii=False, indent=0), encoding="utf-8")
print(added, "prologue checks added")
