# Finds conditional branches on items and switches that wrap transfers
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rbmarshal import load, text

sys.stdout.reconfigure(encoding="utf-8")
DATA = Path(sys.argv[1])
items = {o["id"]: text(o["name"]) for o in load(DATA / "Items.rvdata2") if o}
mapinfo = load(DATA / "MapInfos.rvdata2")
sw = [text(s) if s else "" for s in load(DATA / "System.rvdata2")["switches"]]
item_conds = defaultdict(list)
for mid in sorted(mapinfo):
    m = load(DATA / f"Map{mid:03d}.rvdata2")
    for eid, ev in (m["events"] or {}).items():
        for pi, page in enumerate(ev["pages"]):
            c = page["condition"]
            cmds = page["list"]
            transfers = sorted({x["parameters"][1] for x in cmds if x["code"] == 201 and x["parameters"][0] == 0})
            if c["item_valid"]:
                item_conds[c["item_id"]].append(f"PAGECOND map{mid} ev{eid} p{pi} -> {transfers}")
            for i, cmd in enumerate(cmds):
                if cmd["code"] == 111 and cmd["parameters"][0] == 8:
                    iid = cmd["parameters"][1]
                    ind = cmd["indent"]
                    inner = []
                    for x in cmds[i + 1:]:
                        if x["indent"] <= ind:
                            break
                        if x["code"] == 201 and x["parameters"][0] == 0:
                            inner.append(x["parameters"][1])
                        if x["code"] == 121:
                            inner.append(f"sw{x['parameters'][0]}={x['parameters'][2] == 0}")
                    item_conds[iid].append(f"map{mid} ev{eid} p{pi} -> {inner}")
for iid in sorted(item_conds):
    print(iid, items.get(iid))
    for line in item_conds[iid][:12]:
        print("   ", line)
