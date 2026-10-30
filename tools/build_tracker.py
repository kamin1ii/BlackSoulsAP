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

# area pin positions on the overview map
POSITIONS = {
    "Holy Forest": (600, 420),
    "Watched River": (380, 420),
    "Red Hood's House": (160, 420),
    "Forest of the Abandoned": (600, 300),
    "Dust Sea": (380, 300),
    "Forest of Sabbath": (160, 300),
    "Sewers": (600, 190),
    "Rotten Burg": (600, 90),
    "Rotten Burg Locked Rooms": (380, 90),
    "Old Rotten Burg": (380, 190),
    "Fort Ivern": (820, 90),
    "Lost Empire": (1040, 90),
    "Behemoth Ranch": (820, 420),
    "Jacob's Disused Mine": (820, 300),
    "Valley Checkpoint": (1040, 300),
    "Gothel's Tower": (1040, 190),
    "Helsa Desert": (1040, 420),
    "Garden of Snow": (1040, 530),
    "Wonderland": (820, 530),
    "Alice's Library": (820, 640),
    "Graveyard Town Elixir": (600, 530),
    "Elixir Locked House": (600, 640),
    "Skeleton Maze": (380, 530),
    "Abandoned Beach": (160, 530),
    "Atlantica": (160, 640),
    "Atlantica Locked House": (160, 750),
    "Hotel Poseidon": (380, 750),
    "Hotel Poseidon Locked Room": (600, 750),
    "Wilhelm Bridge": (380, 640),
    "Secret Garden": (820, 750),
    "Tainted Bog": (1040, 640),
    "Kun-Yan": (1040, 750),
}
ITEMS = {"Master Key": ("masterkey", (70, 110, 160), "KEY"), "Invitation to Atlantica": ("invitation", (120, 70, 150), "INV")}


def world_constant(name):
    tree = ast.parse((WORLD / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == name:
            return node.value
    raise KeyError(name)


def area_rules():
    names = {"MASTER_KEY": "masterkey", "INVITATION": "invitation"}
    rows = []
    for elt in world_constant("CONNECTIONS").elts:
        area, parent, rule = elt.elts
        rule_code = names.get(getattr(rule, "id", None)) or ("princesses" if getattr(rule, "value", None) == "princesses" else None)
        rows.append((area.value, parent.value, rule_code))
    needs = {"Menu": set()}
    for area, parent, rule in rows:
        req = set(needs[parent])
        if rule == "princesses":
            req |= {"invitation"}
        elif rule:
            req.add(rule)
        needs[area] = req
    return needs


def icon(path, color, label, size=64):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, size - 3, size - 3), radius=10, fill=color + (255,), outline=(230, 230, 230, 255), width=2)
    font = ImageFont.truetype(FONT, 20)
    w = d.textlength(label, font=font)
    d.text(((size - w) / 2, size / 2 - 12), label, font=font, fill=(255, 255, 255, 255))
    img.save(path)


def overview(path):
    img = Image.new("RGB", (1200, 840), (24, 22, 28))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 15)
    for name, (x, y) in POSITIONS.items():
        d.rounded_rectangle((x - 95, y - 38, x + 95, y + 38), radius=8, fill=(48, 44, 56), outline=(110, 100, 120), width=2)
        words, lines, cur = name.split(), [], ""
        for word in words:
            if d.textlength((cur + " " + word).strip(), font=font) > 170:
                lines.append(cur)
                cur = word
            else:
                cur = (cur + " " + word).strip()
        lines.append(cur)
        for i, line in enumerate(lines):
            w = d.textlength(line, font=font)
            d.text((x - w / 2, y - 34 + i * 17), line, font=font, fill=(235, 235, 240))
    img.save(path)


def main():
    locations = json.loads((WORLD / "data" / "locations.json").read_text(encoding="utf-8"))
    bosses = json.loads((WORLD / "data" / "bosses.json").read_text(encoding="utf-8"))
    items = json.loads((WORLD / "data" / "items.json").read_text(encoding="utf-8"))
    needs = area_rules()

    for sub in ("images/items", "images/maps", "items", "locations", "layouts", "maps", "scripts"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    sections = {area: [] for area in POSITIONS}
    location_map = {}
    for i, loc in enumerate(locations):
        name = loc["name"].split(" - ", 1)[1]
        rule = sorted(needs[loc["area"]] | ({"masterkey"} if loc["key_door"] else set()))
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
    (OUT / "locations" / "locations.json").write_text(json.dumps(loc_json, indent=1), encoding="utf-8")

    item_json, item_map = [], {}
    for name, (code, color, label) in ITEMS.items():
        icon(OUT / "images" / "items" / f"{code}.png", color, label)
        item_json.append({"name": name, "type": "toggle", "img": f"images/items/{code}.png", "codes": code})
        item_map[BASE_ID + next(i for i, r in enumerate(items) if r["name"] == name)] = code
    (OUT / "items" / "items.json").write_text(json.dumps(item_json, indent=1), encoding="utf-8")

    overview(OUT / "images" / "maps" / "overview.png")
    (OUT / "maps" / "maps.json").write_text(json.dumps([{
        "name": "overview", "location_size": 30, "location_border_thickness": 3, "img": "images/maps/overview.png"}],
        indent=1), encoding="utf-8")

    (OUT / "layouts" / "tracker.json").write_text(json.dumps({
        "shared_item_grid": {"type": "itemgrid", "item_margin": "4", "item_size": 64,
                             "rows": [[code for code, _, _ in ITEMS.values()]]},
        "tracker_default": {"type": "container", "background": "#00000000", "content": {
            "type": "dock", "dropshadow": True, "content": [
                {"type": "group", "header": "Key Items", "dock": "top", "content": {"type": "layout", "key": "shared_item_grid"}},
                {"type": "map", "maps": ["overview"]}]}},
        "tracker_broadcast": {"type": "layout", "key": "shared_item_grid"},
    }, indent=1), encoding="utf-8")

    lines = ["LOCATION_MAPPING = {"] + [f'    [{k}] = "{v}",' for k, v in location_map.items()] + ["}", "",
             "ITEM_MAPPING = {"] + [f'    [{k}] = "{v}",' for k, v in item_map.items()] + ["}", ""]
    (OUT / "scripts" / "mapping.lua").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "scripts" / "init.lua").write_text((ROOT / "tools" / "tracker_init.lua").read_text(encoding="utf-8"),
                                               encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps({
        "name": "Black Souls Archipelago", "game_name": "Black Souls", "package_version": "0.1.0",
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
