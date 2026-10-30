# Lists fixed battles with troop stats and troop event side effects
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rbmarshal import load, text

sys.stdout.reconfigure(encoding="utf-8")
DATA = Path(sys.argv[1])
troops = load(DATA / "Troops.rvdata2")
enemies = load(DATA / "Enemies.rvdata2")
mapinfo = load(DATA / "MapInfos.rvdata2")
rows = [json.loads(l) for l in open(sys.argv[2], encoding="utf-8")]
seen = {}
for r in rows:
    if r["type"] == "battle" and r["designation"] == 0 and r["map"] not in (0, 29):
        seen.setdefault(r["id"], []).append(f"m{r['map']}e{r['event']}p{r['page']}i{r['index']}")
for tid in sorted(seen):
    t = troops[tid]
    mem = [enemies[m["enemy_id"]] for m in t["members"]]
    effects = []
    for pg in t["pages"]:
        for c in pg["list"]:
            k = c["code"]
            if k == 121:
                effects.append(f"sw{c['parameters'][0]}={'ON' if c['parameters'][2] == 0 else 'OFF'}")
            elif k in (201, 301, 340, 353, 117, 126, 127, 128, 336, 129):
                effects.append(f"c{k}")
    mhp = sum(e["params"][0] for e in mem)
    atk = max(e["params"][2] for e in mem)
    exp = sum(e["exp"] for e in mem)
    print(tid, text(t["name"]), "| hp", mhp, "atk", atk, "exp", exp, "|", seen[tid][:5], "|", sorted(set(effects)))
