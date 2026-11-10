"""Copies the standalone randomizer engine into the world, without its title screen and option menu."""
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\Projects\BlackSoulsRandomizer\game")
GAME = Path(__file__).resolve().parent.parent / "worlds" / "blacksouls" / "game"
CUT = "# --- title screen"

core = (SOURCE / "rando.rb").read_text(encoding="utf-8")
if CUT not in core:
    raise SystemExit("title screen marker not found in rando.rb")
NOTE = "# Copied from the standalone BLACK SOULS randomizer by tools/sync_rando.py, change it there and sync again\n"
core = NOTE + core[:core.index(CUT)].rstrip() + "\n"
(GAME / "rando_core.rb").write_text(core, encoding="utf-8", newline="\n")
data = NOTE + (SOURCE / "rando_data.rb").read_text(encoding="utf-8")
(GAME / "rando_data.rb").write_text(data, encoding="utf-8", newline="\n")
print("rando_core.rb", len(core), "rando_data.rb", len(data))
