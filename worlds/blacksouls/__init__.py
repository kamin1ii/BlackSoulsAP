from typing import Any, Dict, List, Set

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
# Little Match Girl, Demonbeast Hero and Lord of Corruption only show up once all four princesses are down
PRINCESS_GATED_BOSSES = {151, 201, 306}
# Lamia hangs on Elma's story, so she only holds filler
MISSABLE_BOSSES = {170}
# Dorothy's three targets never appear once she is locked up, filler only unless the player asks for them
DOROTHY_TARGETS = {167, 168, 169}
# in the order the game script uses, Frog, Rapunzel, Snow White, Little Mermaid
PRINCESS_ROOMS = [
    ("Tainted Bog", 82, 44, 156),
    ("Gothel's Tower", 66, 5, 157),
    ("Garden of Snow", 53, 5, 158),
    ("Atlantica", 76, 43, 159),
]
SKIP_AREAS = {
    "skip_kun_yan": {"Kun-Yan"},
    "skip_lost_empire": {"Lost Empire"},
    "skip_atlantica": {"Atlantica", "Atlantica Locked House", "Hotel Poseidon", "Hotel Poseidon Locked Room"},
}
# Master Key, Magical Mirror, Desert Rose, Anti-Fairy, Invitation, Jeanne's Ashes, Alice's Ribbon, Black Ash
UNIQUE_ITEM_IDS = {47, 23, 46, 51, 52, 55, 179, 181}

# area, parent area, what the way in needs
CONNECTIONS = [
    ("Holy Forest", "Menu", None),
    ("Watched River", "Holy Forest", None),
    ("Red Hood's House", "Watched River", None),
    ("Forest of the Abandoned", "Holy Forest", None),
    ("Dust Sea", "Forest of the Abandoned", None),
    ("Forest of Sabbath", "Dust Sea", None),
    ("Sewers", "Forest of the Abandoned", None),
    ("Rotten Burg", "Sewers", None),
    ("Rotten Burg Locked Rooms", "Rotten Burg", None),
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
    ("Elixir Locked House", "Graveyard Town Elixir", None),
    ("Skeleton Maze", "Graveyard Town Elixir", None),
    ("Abandoned Beach", "Skeleton Maze", None),
    ("Atlantica", "Abandoned Beach", INVITATION),
    ("Atlantica Locked House", "Atlantica", None),
    ("Hotel Poseidon", "Atlantica", None),
    ("Hotel Poseidon Locked Room", "Hotel Poseidon", None),
    ("Wilhelm Bridge", "Graveyard Town Elixir", None),
    ("Secret Garden", "Wilhelm Bridge", None),
    ("Tainted Bog", "Wilhelm Bridge", "ivern"),
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
ITEM_ROWS_BY_KEY = {(row["kind"], row["id"], row["amount"]): row["name"] for row in ITEMS}
BOOK_NAMES = [row["name"] for row in ITEMS if row["kind"] == "item" and row["id"] in BOOK_IDS]
FILLER = [row["name"] for row in ITEMS
          if row["cls"] == "filler" and row["kind"] == "item" and row["id"] not in BOOK_IDS]


def is_book(loc: Dict[str, Any]) -> bool:
    return loc["kind"] == "item" and loc["id"] in BOOK_IDS


def is_unique(loc: Dict[str, Any]) -> bool:
    if loc["kind"] != "item":
        return True
    return loc["id"] in UNIQUE_ITEM_IDS or loc["id"] in BOOK_IDS or loc["item"].startswith(("Sorcery", "Miracle"))


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
    BLACK SOULS is a dark fairytale RPG made in RPG Maker VX Ace. Items found in chests and on
    the ground are shuffled across the multiworld, every boss kill is a check, and bosses, princesses
    and companions can be shuffled the way the standalone randomizer does it.
    """
    game = GAME
    web = BlackSoulsWeb()
    options_dataclass = BlackSoulsOptions
    options: BlackSoulsOptions
    location_name_to_id = location_ids
    item_name_to_id = item_ids
    item_name_groups = {"Key Items": {MASTER_KEY, INVITATION}, "Fairytale Books": set(BOOK_NAMES)}

    def generate_early(self) -> None:
        self.books_shuffled = bool(self.options.randomize_fairy_tale_books) or \
            self.options.goal == self.options.goal.option_ending_c
        self.rando_seed = self.random.randrange(100_000_000)
        self.rooms = [0, 1, 2, 3]
        if self.options.shuffle_princesses:
            self.random.shuffle(self.rooms)
        self.skipped: Set[str] = set()
        for option, areas in SKIP_AREAS.items():
            if getattr(self.options, option):
                self.skipped |= areas
        self.real_pickups = self.pick_pickups()
        self.real_bosses = [b for b in BOSS_CHECKS if self.boss_area(b) not in self.skipped]

    def princess_room_area(self, princess: int) -> str:
        return PRINCESS_ROOMS[self.rooms.index(princess)][0]

    # a pickup inside a princess event moves with her
    def pickup_area(self, loc: Dict[str, Any]) -> str:
        map_id, event_id = (int(x) for x in loc["key"].split(":")[:2])
        for i, (_area, home_map, home_event, _troop) in enumerate(PRINCESS_ROOMS):
            if (map_id, event_id) == (home_map, home_event):
                return self.princess_room_area(i)
        return loc["area"]

    def boss_area(self, boss: Dict[str, Any]) -> str:
        for i, room in enumerate(PRINCESS_ROOMS):
            if boss["troop"] == room[3]:
                return self.princess_room_area(i)
        return boss["area"]

    def pick_pickups(self) -> List[Dict[str, Any]]:
        open_spots = [loc for loc in PICKUPS
                      if self.pickup_area(loc) not in self.skipped and (self.books_shuffled or not is_book(loc))]
        if not self.options.unique_checks_only:
            return open_spots
        chosen: Dict[Any, Dict[str, Any]] = {}
        for loc in open_spots:
            if not is_unique(loc):
                continue
            item = (loc["kind"], loc["id"])
            # a spot without a story choice in front of it wins over one with
            if item not in chosen or (chosen[item]["quest"] and not loc["quest"]):
                chosen[item] = loc
        picked = {id(loc) for loc in chosen.values()}
        return [loc for loc in open_spots if id(loc) in picked]

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
            elif rule == "ivern":
                entrance.access_rule = lambda state: state.can_reach_region("Fort Ivern", self.player)
                self.multiworld.register_indirect_condition(regions["Fort Ivern"], entrance)
            elif rule:
                entrance.access_rule = lambda state, item=rule: state.has(item, self.player)

        for loc in self.real_pickups:
            region = regions[self.pickup_area(loc)]
            location = BlackSoulsLocation(self.player, loc["name"], location_ids[loc["name"]], region)
            if loc["quest"]:
                location.progress_type = LocationProgressType.EXCLUDED
            region.locations.append(location)
        for boss in self.real_bosses:
            region = regions[self.boss_area(boss)]
            location = BlackSoulsLocation(self.player, boss["name"], location_ids[boss["name"]], region)
            if boss["troop"] in PRINCESS_GATED_BOSSES:
                location.access_rule = lambda state: all(
                    state.can_reach_region(a, self.player) for a in PRINCESS_AREAS)
            if boss["troop"] in MISSABLE_BOSSES:
                location.progress_type = LocationProgressType.EXCLUDED
            if boss["troop"] in DOROTHY_TARGETS and not self.options.dorothy_targets_in_logic:
                location.progress_type = LocationProgressType.EXCLUDED
            region.locations.append(location)

        goal = self.options.goal.value
        if goal == self.options.goal.option_ending_c:
            goal_region = regions["Alice's Library"]
            ending = BlackSoulsLocation(self.player, ENDING_LOCATION, None, goal_region)
            needed = self.options.fairy_tale_books_needed.value
            ending.access_rule = lambda state: state.has_from_list(BOOK_NAMES, self.player, needed)
        elif goal == self.options.goal.option_ending_d:
            goal_region = regions["Menu"]
            ending = BlackSoulsLocation(self.player, ENDING_LOCATION, None, goal_region)
            ending.access_rule = lambda state: all(state.can_reach_region(r, self.player) for r in regions)
        else:
            goal_region = regions["Lost Empire"]
            ending = BlackSoulsLocation(self.player, ENDING_LOCATION, None, goal_region)
        ending.place_locked_item(BlackSoulsItem(VICTORY, ItemClassification.progression, None, self.player))
        goal_region.locations.append(ending)
        self.multiworld.regions += regions.values()

    def create_item(self, name: str) -> BlackSoulsItem:
        row = ITEM_ROWS[name]
        cls = {"progression": ItemClassification.progression, "useful": ItemClassification.useful,
               "filler": ItemClassification.filler}[row["cls"]]
        if row["kind"] == "item" and row["id"] in BOOK_IDS and self.options.goal == self.options.goal.option_ending_c:
            cls = ItemClassification.progression
        return BlackSoulsItem(name, cls, item_ids[name], self.player)

    def create_items(self) -> None:
        pool: List[BlackSoulsItem] = []
        for loc in self.real_pickups:
            if is_book(loc):
                continue
            pool.append(self.create_item(ITEM_ROWS_BY_KEY[(loc["kind"], loc["id"], loc["amount"])]))
        # every book goes in once, wherever its normal spot ended up
        if self.books_shuffled:
            pool += [self.create_item(name) for name in BOOK_NAMES]
        total = len(self.real_pickups) + len(self.real_bosses)
        while len(pool) < total:
            pool.append(self.create_item(self.get_filler_item_name()))
        spare = [i for i, item in enumerate(pool) if item.classification == ItemClassification.filler
                 and item.name not in BOOK_NAMES]
        self.random.shuffle(spare)
        drop = set(spare[:len(pool) - total])
        pool = [item for i, item in enumerate(pool) if i not in drop]
        self.multiworld.itempool += pool

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = lambda state: state.has(VICTORY, self.player)

    def get_filler_item_name(self) -> str:
        return self.random.choice(FILLER)

    def fill_slot_data(self) -> Dict[str, Any]:
        is_c = self.options.goal == self.options.goal.option_ending_c
        return {
            "goal": self.options.goal.value,
            "books_shuffled": self.books_shuffled,
            "books_needed": self.options.fairy_tale_books_needed.value if is_c else 32,
            "rando_seed": self.rando_seed,
            "rooms": self.rooms,
            "shuffle_princesses": bool(self.options.shuffle_princesses),
            "shuffle_companions": bool(self.options.shuffle_companions),
            "boss_shuffle": bool(self.options.boss_shuffle),
            "special_boss_shuffle": bool(self.options.shuffle_special_bosses),
            "boss_scaling": bool(self.options.boss_scaling),
            "enemy_shuffle": bool(self.options.enemy_shuffle),
            "shuffle_prologue": bool(self.options.shuffle_prologue),
            "pause_menu_checklist": bool(self.options.pause_menu_checklist),
        }
