# Builds the apworld location and item tables from the unpacked game data
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rbmarshal import load, text

DATA = Path(sys.argv[1])
OUT = Path(sys.argv[2])

AREAS = {
    "Holy Forest": [10, 11, 13, 14, 15, 114],
    "Watched River": [85, 86],
    "Red Hood's House": [1, 3, 5, 89],
    "Forest of the Abandoned": [18, 19, 20, 16, 21, 22],
    "Dust Sea": [115, 116, 117, 118],
    "Forest of Sabbath": [136, 137],
    "Sewers": [23, 24, 25, 26],
    "Rotten Burg": [27, 28, 30, 31, 33, 131, 144, 149, 150],
    "Rotten Burg Locked Rooms": [32, 111],
    "Old Rotten Burg": [134, 135],
    "Fort Ivern": [9, 6, 2, 34],
    "Lost Empire": [88, 95, 96, 87, 90, 91, 92, 93],
    "Behemoth Ranch": [35, 36, 37, 38, 50, 51, 102],
    "Jacob's Disused Mine": [39, 40, 41, 42, 43, 108],
    "Valley Checkpoint": [45, 46, 103],
    "Gothel's Tower": [60, 62, 63, 64, 65, 66],
    "Helsa Desert": [49, 47],
    "Garden of Snow": [52, 48, 54, 55, 53],
    "Wonderland": [56, 83, 107, 138],
    "Alice's Library": [101, 104],
    "Graveyard Town Elixir": [67, 68],
    "Elixir Locked House": [57],
    "Skeleton Maze": [69, 70, 73, 75, 110, 113, 119, 142],
    "Abandoned Beach": [71],
    "Atlantica": [72, 78, 76, 74],
    "Atlantica Locked House": [143],
    "Hotel Poseidon": [77],
    "Hotel Poseidon Locked Room": [84],
    "Wilhelm Bridge": [79],
    "Secret Garden": [81, 80, 94],
    "Tainted Bog": [82],
    "Kun-Yan": [4, 8, 12, 17, 130, 132, 133],
}
MAP_AREA = {m: a for a, ms in AREAS.items() for m in ms}
# maps with a master key door somewhere inside
KEY_DOOR_MAPS = {2, 5, 14, 27, 28}

# troop id, boss name, area
BOSSES = [
    (137, "Hyena of Hunger", "Behemoth Ranch"),
    (138, "Monster Behemoth", "Jacob's Disused Mine"),
    (139, "Iron King", "Rotten Burg"),
    (140, "Pied Piper", "Sewers"),
    (141, "Musicians of Bremen", "Behemoth Ranch"),
    (142, "Knight in Boots", "Fort Ivern"),
    (143, "Ugly Duckling", "Fort Ivern"),
    (144, "Beanstalk Jack", "Forest of the Abandoned"),
    (145, "Peter Pan", "Gothel's Tower"),
    (146, "King Sinbad", "Hotel Poseidon"),
    (147, "Mage Aladdin", "Helsa Desert"),
    (148, "Donkey King", "Garden of Snow"),
    (149, "Iron Hans", "Skeleton Maze"),
    (150, "Beauty and the Beast", "Lost Empire"),
    (151, "Little Match Girl", "Rotten Burg"),
    (152, "Devourer Patrasche", "Graveyard Town Elixir"),
    (153, "Singing Bone", "Skeleton Maze"),
    (155, "Undead Drake Helkaiser", "Tainted Bog"),
    (156, "Princess Frog", "Tainted Bog"),
    (157, "Rapunzel", "Gothel's Tower"),
    (158, "Snow White", "Garden of Snow"),
    (160, "Pumpkin Carriage", "Lost Empire"),
    (162, "Monster Behemoth Second Fight", "Gothel's Tower"),
    (163, "Knights of Sun and North Wind", "Lost Empire"),
    (164, "Torture Queen Elisabeth Bathory", "Forest of the Abandoned"),
    (167, "Heartless Tin Man", "Behemoth Ranch"),
    (168, "Cowardly Lion", "Sewers"),
    (169, "Moronic Scarecrow", "Forest of the Abandoned"),
    (170, "Lamia", "Rotten Burg Locked Rooms"),
    (178, "Snow White's Prince", "Garden of Snow"),
    (192, "Black Condemner Miranda", "Tainted Bog"),
    (194, "Marionette Boy Pinocchio", "Hotel Poseidon Locked Room"),
    (195, "Saint's Guardian Ox", "Skeleton Maze"),
    (196, "Saint's Guardian Belior", "Skeleton Maze"),
    (201, "Demonbeast Hero", "Rotten Burg"),
    (220, "Trashlord Kraken", "Dust Sea"),
    (226, "Golden Goose", "Behemoth Ranch"),
    (227, "Holy Beast Jeanne d'Arc", "Lost Empire"),
    (255, "Black Drake Caramille", "Kun-Yan"),
    (256, "Shadowmoon Knight Oentius", "Kun-Yan"),
    (259, "Clock Crok", "Atlantica"),
    (263, "Nameless Demon", "Forest of Sabbath"),
    (289, "Divine Mistake Lilith", "Old Rotten Burg"),
    (304, "Beloved White Dragon Shirasu", "Secret Garden"),
    (305, "Foolish Prince", "Skeleton Maze"),
    (306, "Lord of Corruption", "Forest of the Abandoned"),
    (307, "Jabberwock", "Wonderland"),
    (309, "Vampire", "Rotten Burg"),
    (314, "Lust Demon Satyr", "Tainted Bog"),
]
# bosses that stay in place but still count as checks
FIXED_BOSSES = [
    (135, "Drake Helkaiser", "Fort Ivern"),
    (136, "Hansel and Gretel", "Forest of the Abandoned"),
    (154, "Rotting Drake Helkaiser", "Wilhelm Bridge"),
    (159, "Little Mermaid", "Atlantica"),
    (180, "One Who Observes", "Watched River"),
    (200, "Guardian Chameleon", "Gothel's Tower"),
    (161, "Cinderella", "Lost Empire"),
]

items = {o["id"]: o for o in load(DATA / "Items.rvdata2") if o}
weapons = {o["id"]: o for o in load(DATA / "Weapons.rvdata2") if o}
armors = {o["id"]: o for o in load(DATA / "Armors.rvdata2") if o}
troops = load(DATA / "Troops.rvdata2")
enemies = load(DATA / "Enemies.rvdata2")
TABLES = {126: ("item", items), 127: ("weapon", weapons), 128: ("armor", armors)}

PROGRESSION = {("item", 47), ("item", 52)}
USEFUL_ITEMS = {8, 17, 45, 46, 50, 53, 54, 55, 56, 181, 182, 183, 185, 186, 187}

def clean(name):
    name = text(name).replace("　", " ").replace("【", " [").replace("】", "]")
    return " ".join(name.split()).replace("[ ", "[")


locations = []
for mid in sorted(MAP_AREA):
    m = load(DATA / f"Map{mid:03d}.rvdata2")
    for eid, ev in sorted((m["events"] or {}).items()):
        for pi, pg in enumerate(ev["pages"]):
            cmds = pg["list"]
            codes = [c["code"] for c in cmds]
            gains = [(i, c) for i, c in enumerate(cmds)
                     if c["code"] in TABLES and c["parameters"][1] == 0 and c["parameters"][2] == 0]
            if not gains or len(gains) > 10:
                continue
            guard = (any(c["code"] == 123 and c["parameters"][1] == 0 for c in cmds)
                     or any(c["code"] == 121 and c["parameters"][2] == 0 for c in cmds) or 214 in codes)
            if not guard:
                continue
            c = pg["condition"]
            cond = c["switch1_valid"] or c["switch2_valid"] or c["variable_valid"] or c["item_valid"] or c["actor_valid"]
            quest = cond or 102 in codes or any(x["code"] == 111 and x["parameters"][0] in (8, 9, 10) for x in cmds)
            for i, cmd in gains:
                kind, table = TABLES[cmd["code"]]
                gid, amount = cmd["parameters"][0], cmd["parameters"][3]
                obj = table.get(gid)
                if not obj or not clean(obj["name"]):
                    continue
                locations.append(dict(key=f"{mid}:{eid}:{pi}:{i}", area=MAP_AREA[mid], kind=kind, id=gid,
                                      amount=amount, item=clean(obj["name"]), quest=bool(quest),
                                      key_door=mid in KEY_DOOR_MAPS))

names = Counter()
for loc in locations:
    base = f"{loc['area']} - {loc['item']}" + (f" x{loc['amount']}" if loc["amount"] > 1 else "")
    names[base] += 1
    loc["name"] = base if names[base] == 1 else f"{base} {names[base]}"


def troop_stats(tid):
    mem = [enemies[x["enemy_id"]] for x in troops[tid]["members"]]
    return dict(hp=sum(e["params"][0] for e in mem), atk=max(max(e["params"][2], e["params"][4]) for e in mem))


bosses = []
for entry in BOSSES + FIXED_BOSSES:
    tid, name, area = entry
    bosses.append(dict(troop=tid, name=f"Defeat {name}", area=area, shuffle=entry in BOSSES,
                       goal=tid == 161, **troop_stats(tid)))

pool = Counter()
for loc in locations:
    pool[(loc["kind"], loc["id"], loc["amount"])] += 1
kinds = ["item", "weapon", "armor"]
lookup = {"item": items, "weapon": weapons, "armor": armors}
item_rows = []
for kind, gid, amount in sorted(pool, key=lambda k: (kinds.index(k[0]), k[1], k[2])):
    name = clean(lookup[kind][gid]["name"]) + (f" x{amount}" if amount > 1 else "")
    if (kind, gid) in PROGRESSION:
        cls = "progression"
    elif kind != "item" or gid in USEFUL_ITEMS:
        cls = "useful"
    else:
        cls = "filler"
    item_rows.append(dict(name=name, kind=kind, id=gid, amount=amount, cls=cls))
seen = Counter(r["name"] for r in item_rows)
for r in item_rows:
    if seen[r["name"]] > 1:
        r["name"] = f"{r['name']} ({r['kind']})"

# prologue only groups, the hare knight miniboss and centaur groups that flip switches
SKIP_ENEMY_TROOPS = {1, 2, 3, 4, 5, 47, 48, 73}
encounter_troops = set()
for mid in MAP_AREA:
    for enc in load(DATA / f"Map{mid:03d}.rvdata2")["encounter_list"] or []:
        encounter_troops.add(enc["troop_id"])
enemy_rows = [dict(troop=tid, **troop_stats(tid)) for tid in sorted(encounter_troops - SKIP_ENEMY_TROOPS)]

OUT.mkdir(parents=True, exist_ok=True)
for fname, rows in (("locations.json", locations), ("bosses.json", bosses), ("items.json", item_rows),
                    ("enemies.json", enemy_rows)):
    (OUT / fname).write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
print(len(locations), "pickups", sum(l["quest"] for l in locations), "quest", len(bosses), "bosses",
      len(item_rows), "item types")
print(Counter(l["area"] for l in locations))
