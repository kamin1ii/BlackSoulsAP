# Prints the command list of one map event
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rbmarshal import load, text

sys.stdout.reconfigure(encoding="utf-8")
data = Path(sys.argv[1])
mid, eid = int(sys.argv[2]), int(sys.argv[3])
m = load(data / f"Map{mid:03d}.rvdata2")
ev = m["events"][eid]
print("event", eid, text(ev["name"]), ev["x"], ev["y"])
for pi, page in enumerate(ev["pages"]):
    c = page["condition"]
    conds = {k[1:]: v for k, v in c.attrs.items()}
    g = page["graphic"]
    print(f"-- page {pi} trigger={page['trigger']} cond={conds} graphic={text(g['character_name'])}:{g['character_index']}")
    for i, cmd in enumerate(page["list"]):
        params = [text(p) if isinstance(p, bytes) else p for p in cmd["parameters"]]
        print(f"{i:3d} {'  ' * cmd['indent']}{cmd['code']} {params}")
