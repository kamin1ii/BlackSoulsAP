import asyncio
import os
import pkgutil
from pathlib import Path
from typing import Dict, Optional

import Utils
from CommonClient import ClientCommandProcessor, CommonContext, get_base_parser, gui_enabled, logger, server_loop
from MultiServer import mark_raw
from NetUtils import ClientStatus, NetworkItem

from . import BOSS_CHECKS, GAME, ITEMS, PICKUPS, location_ids
from .patcher import game_version, patch_game

STORE_KEY = "black_souls"
KNOWN_VERSIONS = {88934994, 12204037}
ENDING_GOALS = {0: None, 1: "A", 2: "B", 3: "C", 4: "D"}
ITEM_BY_ID = {7_710_000 + i: row for i, row in enumerate(ITEMS)}
KEY_TO_ID = {key: location_ids[loc["name"]] for loc in PICKUPS for key in [loc["key"], *loc.get("alt_keys", [])]}
KEY_TO_ID.update({f"boss:{b['troop']}": location_ids[b["name"]] for b in BOSS_CHECKS})
ALL_LOCATION_IDS = sorted(set(KEY_TO_ID.values()))


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def clean(text: str) -> str:
    return text.replace("\t", " ").replace("\n", " ")


class BlackSoulsCommandProcessor(ClientCommandProcessor):
    @mark_raw
    def _cmd_install(self, folder: str = "") -> bool:
        """Make an Archipelago copy of your BLACK SOULS folder. Usage /install <path to BLACK SOULS folder>"""
        if not folder:
            self.output("Usage /install <path to your BLACK SOULS folder>")
            return False
        source = Path(folder.strip().strip('"'))
        target = source.parent / (source.name + " Archipelago")
        try:
            if game_version(source) not in KNOWN_VERSIONS:
                self.output("Warning, this game version is untested and some checks may not line up")
            self.output(f"Copying the game to {target}, this can take a minute")
            mod = pkgutil.get_data(__package__, "game/ap.rb").decode("utf-8")
            target = patch_game(source, target, mod)
        except Exception as e:
            self.output(f"Install failed {e}")
            return False
        self.ctx.set_game_dir(target)
        self.output(f"Done. Play the game from {target / 'Game.exe'}")
        return True

    @mark_raw
    def _cmd_game(self, folder: str = "") -> bool:
        """Show or set the patched game folder. Usage /game <path>"""
        if folder:
            self.ctx.set_game_dir(Path(folder.strip().strip('"')))
        self.output(f"Game folder is {self.ctx.game_dir or 'not set, use /install first'}")
        return True


class BlackSoulsContext(CommonContext):
    command_processor = BlackSoulsCommandProcessor
    game = GAME
    items_handling = 0b111
    want_slot_data = True

    def __init__(self, server_address: Optional[str], password: Optional[str]):
        super().__init__(server_address, password)
        stored = Utils.persistent_load().get(STORE_KEY, {}).get("game_dir")
        self.game_dir: Optional[Path] = Path(stored) if stored else None
        self.slot_data: Dict = {}
        self.scouts: Dict[int, str] = {}
        self.checks_mtime = None
        self.inbox_count = -1

    def set_game_dir(self, folder: Path) -> None:
        self.game_dir = folder
        Utils.persistent_store(STORE_KEY, "game_dir", str(folder))
        self.inbox_count = -1
        if self.slot is not None:
            self.write_session()

    @property
    def bridge(self) -> Optional[Path]:
        if not self.game_dir:
            return None
        path = self.game_dir / "Archipelago"
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        if cmd == "Connected":
            self.slot_data = args.get("slot_data", {})
            self.inbox_count = -1
            if not self.game_dir:
                logger.info("Run /install <path to your BLACK SOULS folder> to make the Archipelago copy of the game")
            asyncio.create_task(self.send_msgs([{"cmd": "LocationScouts", "locations": ALL_LOCATION_IDS, "create_as_hint": 0}]))
            self.write_session()
        elif cmd == "LocationInfo":
            for item in (NetworkItem(*i) for i in args["locations"]):
                name = self.item_names.lookup_in_slot(item.item, item.player)
                if item.player == self.slot:
                    text = f"Found your {name}"
                else:
                    text = f"Found {name} for {self.player_names[item.player]}"
                self.scouts[item.location] = clean(text)
            self.write_session()

    def write_session(self) -> None:
        bridge = self.bridge
        if not bridge or self.slot is None:
            return
        lines = [f"seed\t{self.seed_name or 'local'}\t{self.slot}"]
        for key, loc_id in KEY_TO_ID.items():
            if key.startswith("boss:"):
                lines.append(f"boss\t{key[5:]}")
            else:
                lines.append(f"loc\t{key}")
            if loc_id in self.scouts:
                lines.append(f"scout\t{key}\t{self.scouts[loc_id]}")
        for arena, boss, hp, atk in self.slot_data.get("boss_swaps", []):
            lines.append(f"swap\t{arena}\t{boss}\t{hp}\t{atk}")
        for loc in PICKUPS:
            m = loc.get("mirror")
            if m:
                lines.append(f"mirror\t{m['map']}\t{m['x']}\t{m['y']}\t{m['src_map']}\t{m['src_event']}\t{loc['key']}")
        for slot, troop, hp, atk in self.slot_data.get("enemy_swaps", []):
            lines.append(f"eswap\t{slot}\t{troop}\t{hp}\t{atk}")
        lines.append("end")
        write_atomic(bridge / "session.txt", "\n".join(lines) + "\n")

    def write_inbox(self) -> None:
        bridge = self.bridge
        if not bridge or len(self.items_received) == self.inbox_count:
            return
        lines = []
        for i, item in enumerate(self.items_received):
            row = ITEM_BY_ID.get(item.item)
            if not row:
                continue
            sender = clean(self.player_names.get(item.player, "Archipelago"))
            lines.append(f"{i}\t{row['kind']}\t{row['id']}\t{row['amount']}\t{sender}")
        lines.append("end")
        write_atomic(bridge / "inbox.txt", "\n".join(lines) + "\n")
        self.inbox_count = len(self.items_received)

    async def read_checks(self) -> None:
        bridge = self.bridge
        if not bridge:
            return
        path = bridge / "checks.txt"
        if not path.exists():
            return
        mtime = path.stat().st_mtime
        if mtime == self.checks_mtime:
            return
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines or lines[-1] != "end":
            return
        self.checks_mtime = mtime
        found = {KEY_TO_ID[k] for k in lines if k in KEY_TO_ID}
        new = found - self.checked_locations
        if new:
            await self.check_locations(new)
        goal = ENDING_GOALS.get(self.slot_data.get("goal", 0))
        reached = {line[7:] for line in lines if line.startswith("ending:")}
        if reached and (goal is None or goal in reached) and not self.finished_game:
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            self.finished_game = True

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Archipelago Black Souls Client"
        return ui


async def game_loop(ctx: BlackSoulsContext) -> None:
    while not ctx.exit_event.is_set():
        try:
            if ctx.slot is not None:
                ctx.write_inbox()
                await ctx.read_checks()
        except Exception as e:
            logger.warning(f"Bridge error {e}")
        await asyncio.sleep(0.5)


def launch_client(*args: str) -> None:
    import colorama

    async def main(parsed):
        ctx = BlackSoulsContext(parsed.connect, parsed.password)
        ctx.auth = parsed.name
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        loop_task = asyncio.create_task(game_loop(ctx), name="Black Souls bridge")
        await ctx.exit_event.wait()
        ctx.server_address = None
        await loop_task
        await ctx.shutdown()

    parser = get_base_parser(description="Black Souls Archipelago Client")
    parser.add_argument("--name", default=None, help="Slot name to connect as")
    parser.add_argument("url", nargs="?", help="Archipelago connection url")
    parsed = parser.parse_args(args)
    if parsed.url:
        from CommonClient import handle_url_arg
        parsed = handle_url_arg(parsed, parser=parser)
    colorama.just_fix_windows_console()
    asyncio.run(main(parsed))
    colorama.deinit()
