from typing import Any, Dict, List

from BaseClasses import Item, ItemClassification, Location, LocationProgressType, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, Type, components, launch

from .data import BOSSES, ENEMIES, ITEMS, LOCATIONS
from .options import BlackSoulsOptions

GAME = "Black Souls"
BASE_ID = 7_710_000
MASTER_KEY = "Master Key"
INVITATION = "Invitation to Atlantica"
VICTORY = "Victory"
ENDING_LOCATION = "Reach the Chosen Ending"
BOOK_IDS = range(273, 305)
PRINCESS_AREAS = ["Tainted Bog", "Atlantica", "Gothel's Tower", "Garden of Snow"]

# area, parent area, item needed
CONNECTIONS = [
    ("Holy Forest", "Menu", None),
    ("Watched River", "Holy Forest", None),
    ("Red Hood's House", "Watched River", None),
    ("Forest of the Abandoned", "Holy Forest", None),
    ("Dust Sea", "Forest of the Abandoned", None),
    ("Forest of Sabbath", "Dust Sea", None),
    ("Sewers", "Forest of the Abandoned", MASTER_KEY),
    ("Rotten Burg", "Sewers", None),
    ("Rotten Burg Locked Rooms", "Rotten Burg", MASTER_KEY),
    ("Old Rotten Burg", "Rotten Burg", None),
    ("Fort Ivern", "Rotten Burg", None),
    ("Lost Empire", "Fort Ivern", "princesses"),
    ("Behemoth Ranch", "Holy Forest", None),
    ("Jacob's Disused Mine", "Behemoth Ranch", None),
    ("Valley Checkpoint", "Jacob's Disused Mine", None),
    ("Gothel's Tower", "Valley Checkpoint", None),
    ("Helsa Desert", "Behemoth Ranch", None),
    ("Garden of Snow", "Helsa Desert", None),
    ("Wonderland", "Garden of Snow", None),
    ("Alice's Library", "Wonderland", None),
    ("Graveyard Town Elixir", "Holy Forest", None),
    ("Elixir Locked House", "Graveyard Town Elixir", MASTER_KEY),
    ("Skeleton Maze", "Graveyard Town Elixir", None),
    ("Abandoned Beach", "Skeleton Maze", None),
    ("Atlantica", "Abandoned Beach", INVITATION),
    ("Atlantica Locked House", "Atlantica", MASTER_KEY),
    ("Hotel Poseidon", "Atlantica", None),
    ("Hotel Poseidon Locked Room", "Hotel Poseidon", MASTER_KEY),
    ("Wilhelm Bridge", "Graveyard Town Elixir", None),
    ("Secret Garden", "Wilhelm Bridge", None),
    ("Tainted Bog", "Wilhelm Bridge", None),
    ("Kun-Yan", "Tainted Bog", None),
]

PICKUPS = LOCATIONS
BOSS_CHECKS = BOSSES

location_ids: Dict[str, int] = {}
for i, loc in enumerate(PICKUPS):
    location_ids[loc["name"]] = BASE_ID + i
for i, boss in enumerate(BOSS_CHECKS):
    location_ids[boss["name"]] = BASE_ID + 5000 + i

item_ids: Dict[str, int] = {row["name"]: BASE_ID + i for i, row in enumerate(ITEMS)}
ITEM_ROWS = {row["name"]: row for row in ITEMS}
FILLER = [row["name"] for row in ITEMS
          if row["cls"] == "filler" and row["kind"] == "item" and row["id"] not in BOOK_IDS]


def run_client(*args: str) -> None:
    from .client import launch_client
    launch(launch_client, name="Black Souls Client", args=args)


components.append(Component("Black Souls Client", func=run_client, game_name=GAME, component_type=Type.CLIENT))


class BlackSoulsItem(Item):
    game = GAME


class BlackSoulsLocation(Location):
    game = GAME


class BlackSoulsWeb(WebWorld):
    theme = "stone"
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "How to set up BLACK SOULS for Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["kamin1ii"],
    )]


class BlackSoulsWorld(World):
    """
    BLACK SOULS is a dark fairy-tale RPG made in RPG Maker VX Ace. Items found in chests and on
    the ground are shuffled across the multiworld, every boss kill is a check, and bosses can be
    shuffled between arenas.
    """
    game = GAME
    web = BlackSoulsWeb()
    options_dataclass = BlackSoulsOptions
    options: BlackSoulsOptions
    location_name_to_id = location_ids
    item_name_to_id = item_ids
    item_name_groups = {"Key Items": {MASTER_KEY, INVITATION}}

    def generate_early(self) -> None:
        self.boss_swaps: List[List[Any]] = []
        self.enemy_swaps: List[List[Any]] = []
        if self.options.boss_shuffle:
            self.boss_swaps = self.shuffle_troops([b for b in BOSSES if b["shuffle"]], bool(self.options.boss_scaling))
        if self.options.enemy_shuffle:
            self.enemy_swaps = self.shuffle_troops(ENEMIES, True)

    def shuffle_troops(self, pool: List[Dict[str, Any]], scale: bool) -> List[List[Any]]:
        placed = pool[:]
        self.random.shuffle(placed)
        swaps = []
        for slot, troop in zip(pool, placed):
            if slot["troop"] == troop["troop"]:
                continue
            hp, atk = 1.0, 1.0
            if scale:
                hp = max(0.05, min(20.0, slot["hp"] / troop["hp"]))
                atk = max(0.1, min(10.0, slot["atk"] / troop["atk"]))
            swaps.append([slot["troop"], troop["troop"], round(hp, 4), round(atk, 4)])
        return swaps

    def create_regions(self) -> None:
        regions = {"Menu": Region("Menu", self.player, self.multiworld)}
        for area, _parent, _rule in CONNECTIONS:
            regions[area] = Region(area, self.player, self.multiworld)
        for area, parent, rule in CONNECTIONS:
            entrance = regions[parent].connect(regions[area], f"{parent} to {area}")
            if rule == "princesses":
                entrance.access_rule = lambda state: all(
                    state.can_reach_region(a, self.player) for a in PRINCESS_AREAS)
                for a in PRINCESS_AREAS:
                    self.multiworld.register_indirect_condition(regions[a], entrance)
            elif rule:
                entrance.access_rule = lambda state, item=rule: state.has(item, self.player)

        for loc in PICKUPS:
            region = regions[loc["area"]]
            location = BlackSoulsLocation(self.player, loc["name"], location_ids[loc["name"]], region)
            if loc["key_door"]:
                location.access_rule = lambda state: state.has(MASTER_KEY, self.player)
            if loc["quest"]:
                location.progress_type = LocationProgressType.EXCLUDED
            region.locations.append(location)
        for boss in BOSS_CHECKS:
            region = regions[boss["area"]]
            region.locations.append(BlackSoulsLocation(self.player, boss["name"], location_ids[boss["name"]], region))

        goal = self.options.goal.value
        if goal in (self.options.goal.option_ending_c, self.options.goal.option_ending_d):
            goal_region = regions["Menu"]
            ending = BlackSoulsLocation(self.player, ENDING_LOCATION, None, goal_region)
            ending.access_rule = lambda state: all(state.can_reach_region(r, self.player) for r in regions)
        else:
            goal_region = regions["Lost Empire"]
            ending = BlackSoulsLocation(self.player, ENDING_LOCATION, None, goal_region)
        ending.place_locked_item(BlackSoulsItem(VICTORY, ItemClassification.progression, None, self.player))
        goal_region.locations.append(ending)
        self.multiworld.regions += regions.values()

        if goal == self.options.goal.option_ending_c:
            for loc in PICKUPS:
                if loc["kind"] == "item" and loc["id"] in BOOK_IDS:
                    name = ITEM_ROWS_BY_KEY[(loc["kind"], loc["id"], loc["amount"])]
                    self.get_location(loc["name"]).place_locked_item(self.create_item(name))

    def create_item(self, name: str) -> BlackSoulsItem:
        row = ITEM_ROWS[name]
        cls = {"progression": ItemClassification.progression, "useful": ItemClassification.useful,
               "filler": ItemClassification.filler}[row["cls"]]
        return BlackSoulsItem(name, cls, item_ids[name], self.player)

    def create_items(self) -> None:
        pool: List[BlackSoulsItem] = []
        have_key = False
        for loc in PICKUPS:
            if self.get_location(loc["name"]).item:
                continue
            name = ITEM_ROWS_BY_KEY[(loc["kind"], loc["id"], loc["amount"])]
            item = self.create_item(name)
            if name == MASTER_KEY:
                if have_key:
                    item.classification = ItemClassification.filler
                have_key = True
            pool.append(item)
        for _ in BOSS_CHECKS:
            pool.append(self.create_item(self.get_filler_item_name()))
        self.multiworld.itempool += pool

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = lambda state: state.has(VICTORY, self.player)

    def get_filler_item_name(self) -> str:
        return self.random.choice(FILLER)

    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "goal": self.options.goal.value,
            "boss_swaps": self.boss_swaps,
            "enemy_swaps": self.enemy_swaps,
            "boss_shuffle": bool(self.options.boss_shuffle),
            "boss_scaling": bool(self.options.boss_scaling),
            "enemy_shuffle": bool(self.options.enemy_shuffle),
        }


ITEM_ROWS_BY_KEY = {(row["kind"], row["id"], row["amount"]): row["name"] for row in ITEMS}
