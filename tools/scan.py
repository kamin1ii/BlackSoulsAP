# Scans maps and common events for item gains, battles, shops and transfers
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rbmarshal import load, text

DATA = Path(sys.argv[1])
OUT = Path(sys.argv[2])


def names(fname):
    return {o["id"]: text(o["name"]) for o in load(DATA / fname) if o}


items, weapons, armors = names("Items.rvdata2"), names("Weapons.rvdata2"), names("Armors.rvdata2")
troops = names("Troops.rvdata2")
kinds = {126: ("item", items), 127: ("weapon", weapons), 128: ("armor", armors)}
mapinfo = load(DATA / "MapInfos.rvdata2")
rows = []


def scan_list(where, cmds, page_cond=None):
    for idx, c in enumerate(cmds or []):
        code, p = c["code"], c["parameters"]
        base = dict(where, index=idx, indent=c["indent"])
        if code in kinds and p[1] == 0:
            kind, table = kinds[code]
            amount = p[3] if p[2] == 0 else f"var{p[3]}"
            rows.append(dict(base, type=kind, id=p[0], name=table.get(p[0]), amount=amount))
        elif code == 125 and p[0] == 0:
            rows.append(dict(base, type="gold", amount=p[2] if p[1] == 0 else f"var{p[2]}"))
        elif code == 301:
            rows.append(dict(base, type="battle", designation=p[0], id=p[1], name=troops.get(p[1]) if p[0] == 0 else None,
                             escape=p[2], lose=p[3]))
        elif code == 302:
            goods = [p[:2]]
            j = idx + 1
            while j < len(cmds) and cmds[j]["code"] == 605:
                goods.append(cmds[j]["parameters"][:2])
                j += 1
            rows.append(dict(base, type="shop", goods=goods))
        elif code == 201:
            rows.append(dict(base, type="transfer", direct=p[0] == 0, to_map=p[1], x=p[2], y=p[3]))
        elif code in (355, 655):
            s = text(p[0])
            if any(k in s for k in ("gain_item", "gain_gold", "battle", "BattleManager")):
                rows.append(dict(base, type="script", text=s))


for mid in sorted(mapinfo):
    m = load(DATA / f"Map{mid:03d}.rvdata2")
    mname = text(mapinfo[mid]["name"])
    for eid, ev in sorted((m["events"] or {}).items()):
        for pi, page in enumerate(ev["pages"]):
            scan_list(dict(map=mid, map_name=mname, event=eid, event_name=text(ev["name"]), page=pi,
                           ex=ev["x"], ey=ev["y"]), page["list"])
for ce in load(DATA / "CommonEvents.rvdata2"):
    if ce:
        scan_list(dict(map=0, map_name="common", event=ce["id"], event_name=text(ce["name"]), page=0), ce["list"])

OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
from collections import Counter
print(Counter(r["type"] for r in rows))
