# Builds the map transfer graph with the switch and item conditions on each edge
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rbmarshal import load, text

sys.stdout.reconfigure(encoding="utf-8")
DATA = Path(sys.argv[1])
mapinfo = load(DATA / "MapInfos.rvdata2")
edges = []


def cond_stack(cmds, i):
    stack = []
    ind = cmds[i]["indent"]
    for j in range(i - 1, -1, -1):
        c = cmds[j]
        if c["indent"] < ind:
            if c["code"] == 111:
                stack.append(("branch", c["parameters"][:4]))
            elif c["code"] == 402:
                stack.append(("choice", c["parameters"][0]))
            elif c["code"] == 411:
                stack.append(("else", None))
            ind = c["indent"]
    return stack


for mid in sorted(mapinfo):
    m = load(DATA / f"Map{mid:03d}.rvdata2")
    for eid, ev in (m["events"] or {}).items():
        for pi, page in enumerate(ev["pages"]):
            c = page["condition"]
            pc = {}
            if c["switch1_valid"]:
                pc["sw1"] = c["switch1_id"]
            if c["switch2_valid"]:
                pc["sw2"] = c["switch2_id"]
            if c["variable_valid"]:
                pc["var"] = [c["variable_id"], c["variable_value"]]
            if c["self_switch_valid"]:
                pc["self"] = text(c["self_switch_ch"])
            if c["item_valid"]:
                pc["item"] = c["item_id"]
            for i, cmd in enumerate(page["list"]):
                if cmd["code"] == 201 and cmd["parameters"][0] == 0:
                    p = cmd["parameters"]
                    edges.append(dict(src=mid, dst=p[1], x=p[2], y=p[3], ev=eid, page=pi, trigger=page["trigger"],
                                      page_cond=pc, branches=cond_stack(page["list"], i), ex=ev["x"], ey=ev["y"]))
Path(sys.argv[2]).write_text("\n".join(json.dumps(e) for e in edges), encoding="utf-8")
print(len(edges))
