# Builds the PopTracker pack from the apworld tables and logic
import ast
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / "worlds" / "blacksouls"
OUT = ROOT / "tracker"
BASE_ID = 7_710_000
FONT = "C:/Windows/Fonts/arialbd.ttf"

# area pins on the game's own Map.png, each sits on the line under the area's name
POSITIONS = {
    "Lost Empire": (933, 173),
    "Fort Ivern": (925, 287),
    "Rotten Burg": (980, 400),
    "Rotten Burg Locked Rooms": (1087, 400),
    "Old Rotten Burg": (630, 420),
    "Sewers": (945, 500),
    "Forest of Sabbath": (1303, 482),
    "Forest of the Abandoned": (883, 620),
    "Dust Sea": (1292, 617),
    "Holy Forest": (958, 813),
    "Watched River": (533, 812),
    "Red Hood's House": (40, 820),
    "Behemoth Ranch": (1805, 753),
    "Jacob's Disused Mine": (1640, 617),
    "Valley Checkpoint": (1870, 483),
    "Gothel's Tower": (1747, 483),
    "Helsa Desert": (1783, 867),
    "Garden of Snow": (1780, 1005),
    "Wonderland": (1797, 1245),
    "Alice's Library": (1793, 1393),
    "Graveyard Town Elixir": (1000, 1007),
    "Elixir Locked House": (1133, 1005),
    "Skeleton Maze": (1430, 983),
    "Abandoned Beach": (1408, 1062),
    "Atlantica": (1433, 1242),
    "Atlantica Locked House": (1558, 1242),
    "Hotel Poseidon": (1417, 1380),
    "Hotel Poseidon Locked Room": (1550, 1383),
    "Wilhelm Bridge": (550, 1000),
    "Secret Garden": (150, 1008),
    "Tainted Bog": (525, 1222),
    "Kun-Yan": (542, 1430),
}
# tracked item, its code and its icon in the game's IconSet
ITEMS = {"Invitation to Atlantica": ("invitation", 238)}


def world_constant(name):
    tree = ast.parse((WORLD / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == name:
            return node.value
    raise KeyError(name)


def area_order():
    """Areas in the order the world's CONNECTIONS walks them, the Holy Forest first."""
    return [elt.elts[0].value for elt in world_constant("CONNECTIONS").elts]


def area_rules():
    names = {"INVITATION": "invitation"}
    rows = []
    for elt in world_constant("CONNECTIONS").elts:
        area, parent, rule = elt.elts
        value = getattr(rule, "value", None)
        rule_code = names.get(getattr(rule, "id", None)) or (value if value in ("princesses", "ivern") else None)
        rows.append((area.value, parent.value, rule_code))
    needs = {"Menu": set()}
    for area, parent, rule in rows:
        req = set(needs[parent])
        if rule == "princesses":
            req |= {"invitation"}
        elif rule == "ivern":
            # the way in opens once Fort Ivern can be reached
            req |= needs["Fort Ivern"]
        elif rule:
            req.add(rule)
        needs[area] = req
    return needs


def icon(path, game, index):
    """Cuts one 24 pixel icon out of the game's IconSet and doubles it so it stays sharp."""
    sys.path.insert(0, str(ROOT / "tools"))
    from render_maps import Archive
    import io
    sheet = Image.open(io.BytesIO(Archive(Path(game) / "Game.rgss3a").read("Graphics/System/Iconset.png"))).convert("RGBA")
    x, y = index % 16 * 24, index // 16 * 24
    sheet.crop((x, y, x + 24, y + 24)).resize((48, 48), Image.NEAREST).save(path)


def overview(path, game):
    """Copies the map the game ships with, its Map.png sits next to Game.exe."""
    source = Path(game) / "Map.png"
    if not source.is_file():
        raise SystemExit(f"No Map.png in {game}, pass the BLACK SOULS folder that holds Game.exe")
    Image.open(source).convert("RGB").save(path)


AREA_SCALE = 0.5
AREA_GAP = 24


def find_rtp():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Enterbrain\RGSS3\RTP") as key:
            return Path(winreg.QueryValueEx(key, "RPGVXAce")[0]) / "Graphics"
    except OSError:
        default = Path(r"C:\Program Files (x86)\Common Files\Enterbrain\RGSS3\RPGVXAce\Graphics")
        return default if default.is_dir() else None


def slug(name):
    return "".join(c if c.isalnum() else "_" for c in name).strip("_").lower()


def area_lists():
    """The maps that make up each area, as tools/build_data.py lists them."""
    tree = ast.parse((ROOT / "tools" / "build_data.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "AREAS":
            return ast.literal_eval(node.value)
    raise KeyError("AREAS")


def squeeze_empty(img, unit):
    """Shrinks long empty black stretches inside a map down to one tile, so a map of a few scattered rooms stays
    small. Returns the picture and, for each old column and row, where it ended up."""
    lit = img.convert("L").point(lambda v: 255 if v > 8 else 0)
    w, h = lit.size

    def plan(filled):
        keep, where, run, new = [], [], 0, 0
        for i, full in enumerate(filled):
            run = 0 if full else run + 1
            where.append(new)
            if full or run <= unit:
                keep.append(i)
                new += 1
        return keep, where

    cols, fx = plan([lit.crop((x, 0, x + 1, h)).getbbox() is not None for x in range(w)])
    rows, fy = plan([lit.crop((0, y, w, y + 1)).getbbox() is not None for y in range(h)])
    # glue the kept runs of columns, then of rows, back together
    def runs(keep):
        out, start = [], None
        for i, k in enumerate(keep):
            if start is None:
                start = k
            if i + 1 == len(keep) or keep[i + 1] != k + 1:
                out.append((start, k + 1))
                start = None
        return out
    narrow = Image.new(img.mode, (len(cols), h))
    x = 0
    for a, b in runs(cols):
        narrow.paste(img.crop((a, 0, b, h)), (x, 0))
        x += b - a
    out = Image.new(img.mode, (len(cols), len(rows)))
    y = 0
    for a, b in runs(rows):
        out.paste(narrow.crop((0, a, len(cols), b)), (0, y))
        y += b - a
    return out, (fx, fy)


def door_side(x, y, w, h):
    """Which way a door inside a map leads, judged by where in the map it sits."""
    rx, ry = x / max(w, 1), y / max(h, 1)
    if ry < 0.34:
        return "north"
    if ry > 0.66:
        return "south"
    return "west" if rx < 0.5 else "east"


def lay_group(root, ids, sizes, links, doors=False):
    """Places root and every map joined to it through an exit at a map's edge, the way they join in game. links
    are (from, to, side, from x, from y, to x, to y) in pixels, side is where the exit sits on the first map."""
    step = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    spot = {root: (0, 0)}

    def clash(m, x, y):
        w, h = sizes[m]
        return any(x < ox + sizes[o][0] + AREA_GAP and ox < x + w + AREA_GAP and
                   y < oy + sizes[o][1] + AREA_GAP and oy < y + h + AREA_GAP for o, (ox, oy) in spot.items())

    grew = True
    while grew:
        grew = False
        for a, b, side, ax, ay, bx, by in links:
            if a not in ids or b not in ids:
                continue
            if not side:
                if not doors:
                    continue
                side = door_side(ax, ay, *sizes[a])
            if a in spot and b not in spot:
                known, new, flip = a, b, False
            elif b in spot and a not in spot:
                known, new, flip = b, a, True
            else:
                continue
            kx, ky = spot[known]
            dx, dy = step[side]
            if flip:
                dx, dy = -dx, -dy
                ax, ay, bx, by = bx, by, ax, ay
            w, h = sizes[new]
            kw, kh = sizes[known]
            # line the two ends of the exit up, then step clear of the map it leaves
            x = kx + ax - bx if dx == 0 else (kx + kw + AREA_GAP if dx > 0 else kx - w - AREA_GAP)
            y = ky + ay - by if dy == 0 else (ky + kh + AREA_GAP if dy > 0 else ky - h - AREA_GAP)
            tries = 0
            while clash(new, x, y) and tries < 400:
                x, y, tries = x + dx * 16, y + dy * 16, tries + 1
            spot[new] = (x, y)
            grew = True
    left = min(x for x, _ in spot.values())
    top = min(y for _, y in spot.values())
    return {m: (x - left, y - top) for m, (x, y) in spot.items()}


def place_maps(ids, sizes, links):
    """The biggest joined group of maps goes on the left. Every other group, like a house and its basement reached
    through a door, is laid out the same way and stacked down a column on the right."""
    degree = {m: sum(1 for l in links if l[2] and m in l[:2]) for m in ids}
    pick = lambda pool: max(pool, key=lambda m: (degree[m], sizes[m][0] * sizes[m][1], -m))
    spot = lay_group(pick(ids), set(ids), sizes, links)
    col_x = max(x + sizes[m][0] for m, (x, _) in spot.items()) + AREA_GAP * 3
    col_y = 0
    while len(spot) < len(ids):
        rest = [m for m in ids if m not in spot]
        # rooms behind a door are joined to each other through their doors as well
        group = lay_group(pick(rest), set(rest), sizes, links, doors=True)
        for m, (x, y) in group.items():
            spot[m] = (col_x + x, col_y + y)
        col_y += max(y + sizes[m][1] for m, (_, y) in group.items()) + AREA_GAP * 2
    return spot


def area_maps(game, locations, bosses, kept):
    """Renders every map that holds a check, packs each area's maps into one picture and pins each check on its tile."""
    sys.path.insert(0, str(ROOT / "tools"))
    from render_maps import TILE, Renderer
    archive = Path(game) / "Game.rgss3a"
    rtp = find_rtp()
    renderer = Renderer(archive, [archive] + ([rtp] if rtp else []))
    maps_of = {}
    spots = {}
    for loc in locations:
        if loc["name"] not in kept:
            continue
        map_id, event_id = (int(v) for v in loc["key"].split(":")[:2])
        maps_of.setdefault(loc["area"], []).append(map_id)
        spots.setdefault((loc["area"], map_id, event_id), []).append(loc["name"].split(" - ", 1)[1])
    events = {}

    def map_events(map_id):
        if map_id not in events:
            events[map_id] = renderer.load(f"Map{map_id:03d}.rvdata2")["events"] or {}
        return events[map_id]

    # a boss is pinned on the event that starts its fight, looked for in its own area's maps first
    all_maps = sorted(renderer.load("MapInfos.rvdata2"))
    for boss in bosses:
        own = list(dict.fromkeys(maps_of.get(boss["area"], [])))
        for map_id in own + [m for m in all_maps if m not in own]:
            hit = next((eid for eid, ev in map_events(map_id).items() for pg in ev["pages"] for c in pg["list"]
                        if c["code"] == 301 and c["parameters"][0] == 0 and c["parameters"][1] == boss["troop"]), None)
            if hit:
                maps_of.setdefault(boss["area"], []).append(map_id)
                spots.setdefault((boss["area"], map_id, hit), []).append(boss["name"])
                break

    entries, pins, tabs = [], [], []
    full_lists = area_lists()
    for area in area_order():
        ids = sorted(set(maps_of.get(area, [])) | set(full_lists.get(area, [])))
        if not maps_of.get(area):
            continue
        unit = int(TILE * AREA_SCALE)
        pictures, origin, squeeze = {}, {}, {}
        for map_id in ids:
            full = renderer.render(map_id)
            small = full.resize((int(full.width * AREA_SCALE), int(full.height * AREA_SCALE)), Image.BOX)
            # trim the empty black around a map, but never past one of its pins
            box = list(small.convert("L").point(lambda v: 255 if v > 8 else 0).getbbox() or (0, 0, unit, unit))
            for (spot_area, spot_map, event_id) in spots:
                ev = map_events(spot_map).get(event_id) if spot_area == area and spot_map == map_id else None
                if ev:
                    box = [min(box[0], ev["x"] * unit), min(box[1], ev["y"] * unit),
                           max(box[2], ev["x"] * unit + unit), max(box[3], ev["y"] * unit + unit)]
            box = [max(0, box[0] - unit), max(0, box[1] - unit), min(small.width, box[2] + unit), min(small.height, box[3] + unit)]
            pictures[map_id], squeeze[map_id] = squeeze_empty(small.crop(box), unit)
            origin[map_id] = (box[0], box[1])
        sizes = {m: pictures[m].size for m in ids}

        def at(map_id, x, y):
            fx, fy = squeeze[map_id]
            x, y = x - origin[map_id][0], y - origin[map_id][1]
            return fx[min(max(int(x), 0), len(fx) - 1)], fy[min(max(int(y), 0), len(fy) - 1)]
        links = []
        for a in ids:
            data = renderer.load(f"Map{a:03d}.rvdata2")
            for ev in (data["events"] or {}).values():
                for pg in ev["pages"]:
                    for c in pg["list"]:
                        prm = c["parameters"]
                        if c["code"] != 201 or prm[0] != 0 or prm[1] not in ids or prm[1] == a:
                            continue
                        ex, ey = ev["x"], ev["y"]
                        side = ("north" if ey <= 1 else "south" if ey >= data["height"] - 2 else
                                "west" if ex <= 1 else "east" if ex >= data["width"] - 2 else None)
                        links.append((a, prm[1], side) + at(a, ex * unit, ey * unit) + at(prm[1], prm[2] * unit, prm[3] * unit))
        # a map stays when it has a check or joins the others through an exit, story only rooms drop out
        pinned = {m for (spot_area, m, _e) in spots if spot_area == area}
        joined = {m for l in links if l[2] for m in l[:2]}
        ids = [m for m in ids if m in pinned or m in joined]
        links = [l for l in links if l[0] in ids and l[1] in ids]
        offsets = place_maps(ids, sizes, links)
        width = max(x + sizes[m][0] for m, (x, _) in offsets.items())
        height = max(y + sizes[m][1] for m, (_, y) in offsets.items())
        sheet = Image.new("RGB", (width, height), (0, 0, 0))
        for map_id, (ox, oy) in offsets.items():
            sheet.paste(pictures[map_id], (ox, oy))
        name = slug(area)
        # 256 colours look the same on these maps and keep the pack small
        sheet.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(
            OUT / "images" / "maps" / f"{name}.png", optimize=True)
        entries.append({"name": name, "location_size": 18, "location_border_thickness": 3,
                        "img": f"images/maps/{name}.png"})
        tabs.append({"title": area, "content": {"type": "map", "maps": [name]}})
        for (spot_area, map_id, event_id), names in spots.items():
            if spot_area != area:
                continue
            ev = map_events(map_id).get(event_id)
            if not ev:
                continue
            sx, sy = at(map_id, (ev["x"] * TILE + TILE / 2) * AREA_SCALE, (ev["y"] * TILE + TILE / 2) * AREA_SCALE)
            px, py = offsets[map_id][0] + sx, offsets[map_id][1] + sy
            title = names[0] if len(names) == 1 else f"{names[0]} and {len(names) - 1} more"
            pins.append({"name": f"{area} - {title}", "sections": [{"ref": f"{area}/{n}"} for n in names],
                         "map_locations": [{"map": name, "x": px, "y": py}]})
    if renderer.missing:
        print("tilesets not found", sorted(renderer.missing))
    return entries, pins, tabs


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage python tools/build_tracker.py <BLACK SOULS folder>")
    locations = json.loads((WORLD / "data" / "locations.json").read_text(encoding="utf-8"))
    bosses = json.loads((WORLD / "data" / "bosses.json").read_text(encoding="utf-8"))
    items = json.loads((WORLD / "data" / "items.json").read_text(encoding="utf-8"))
    needs = area_rules()

    for sub in ("images/items", "images/maps", "items", "locations", "layouts", "maps", "scripts"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    sections = {area: [] for area in POSITIONS}
    location_map = {}
    kept = set()
    for i, loc in enumerate(locations):
        if loc["kind"] == "item" and 273 <= loc["id"] <= 304:
            continue
        kept.add(loc["name"])
        name = loc["name"].split(" - ", 1)[1]
        rule = sorted(needs[loc["area"]])
        sections[loc["area"]].append({"name": name, "item_count": 1, "access_rules": [",".join(rule)] if rule else []})
        location_map[BASE_ID + i] = f"@{loc['area']}/{name}"
    for i, boss in enumerate(bosses):
        rule = sorted(needs[boss["area"]])
        sections[boss["area"]].append({"name": boss["name"], "item_count": 1, "access_rules": [",".join(rule)] if rule else []})
        location_map[BASE_ID + 5000 + i] = f"@{boss['area']}/{boss['name']}"

    loc_json = []
    for area, (x, y) in POSITIONS.items():
        rule = sorted(needs[area])
        loc_json.append({"name": area, "access_rules": [",".join(rule)] if rule else [],
                         "sections": sections[area], "map_locations": [{"map": "overview", "x": x, "y": y}]})
    entries, pins, tabs = area_maps(sys.argv[1], locations, bosses, kept)
    (OUT / "locations" / "locations.json").write_text(json.dumps(loc_json + pins, indent=1), encoding="utf-8")

    item_json, item_map = [], {}
    for name, (code, index) in ITEMS.items():
        icon(OUT / "images" / "items" / f"{code}.png", sys.argv[1], index)
        item_json.append({"name": name, "type": "toggle", "img": f"images/items/{code}.png", "codes": code})
        item_map[BASE_ID + next(i for i, r in enumerate(items) if r["name"] == name)] = code
    (OUT / "items" / "items.json").write_text(json.dumps(item_json, indent=1), encoding="utf-8")

    overview(OUT / "images" / "maps" / "overview.png", sys.argv[1])
    (OUT / "maps" / "maps.json").write_text(json.dumps([{
        "name": "overview", "location_size": 32, "location_border_thickness": 3, "img": "images/maps/overview.png"}]
        + entries, indent=1), encoding="utf-8")

    (OUT / "layouts" / "tracker.json").write_text(json.dumps({
        "shared_item_grid": {"type": "itemgrid", "item_margin": "4", "item_size": 40,
                             "rows": [[code] for code, _ in ITEMS.values()]},
        "tracker_default": {"type": "container", "background": "#00000000", "content": {
            "type": "dock", "dropshadow": True, "content": [
                {"type": "group", "header": "Items", "dock": "left", "content": {"type": "layout", "key": "shared_item_grid"}},
                {"type": "tabbed", "tabs": [{"title": "Overview", "content": {"type": "map", "maps": ["overview"]}}]
                 + tabs}]}},
        "tracker_broadcast": {"type": "layout", "key": "shared_item_grid"},
    }, indent=1), encoding="utf-8")

    lines = ["LOCATION_MAPPING = {"] + [f'    [{k}] = "{v}",' for k, v in location_map.items()] + ["}", "",
             "ITEM_MAPPING = {"] + [f'    [{k}] = "{v}",' for k, v in item_map.items()] + ["}", ""]
    (OUT / "scripts" / "mapping.lua").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "scripts" / "init.lua").write_text((ROOT / "tools" / "tracker_init.lua").read_text(encoding="utf-8"),
                                               encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps({
        "name": "Black Souls Archipelago", "game_name": "Black Souls", "package_version": "0.3.0",
        "package_uid": "black_souls_ap", "author": "kamin1ii", "min_poptracker_version": "0.25.0",
        "variants": {"standard": {"display_name": "Standard", "flags": ["ap"]}}}, indent=1), encoding="utf-8")

    zip_path = ROOT / "build" / "blacksouls_tracker.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(OUT))
    print(sum(len(s) for s in sections.values()), "sections", len(item_map), "items", zip_path)


if __name__ == "__main__":
    sys.exit(main())
