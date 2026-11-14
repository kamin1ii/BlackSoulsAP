"""Copies the standalone randomizer engine into the world, without its title screen and option menu.
The stream overlay, controller support and window resizing come along with their files."""
import shutil
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\Projects\BlackSoulsRandomizer\game")
GAME = Path(__file__).resolve().parent.parent / "worlds" / "blacksouls" / "game"
CUT = "# --- title screen"
NOTE = "# Copied from the standalone BLACK SOULS randomizer by tools/sync_rando.py, change it there and sync again\n"
SCRIPTS = ["rando_data.rb", "rando_pad.rb", "rando_overlay.rb", "rando_window.rb"]
FOLDERS = ["overlay", "sharp", "upscale"]

core = (SOURCE / "rando.rb").read_text(encoding="utf-8")
if CUT not in core:
    raise SystemExit("title screen marker not found in rando.rb")
core = NOTE + core[:core.index(CUT)].rstrip() + "\n"
(GAME / "rando_core.rb").write_text(core, encoding="utf-8", newline="\n")
print("rando_core.rb", len(core))

for name in SCRIPTS:
    text = NOTE + (SOURCE / name).read_text(encoding="utf-8")
    (GAME / name).write_text(text, encoding="utf-8", newline="\n")
    print(name, len(text))

for name in FOLDERS:
    shutil.rmtree(GAME / name, ignore_errors=True)
    shutil.copytree(SOURCE / name, GAME / name)
    print(name, len(list((GAME / name).rglob("*"))), "files")
