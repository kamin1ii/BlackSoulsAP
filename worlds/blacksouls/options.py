from dataclasses import dataclass

from Options import Choice, DefaultOnToggle, Range, Toggle, PerGameCommonOptions, StartInventoryPool


class Goal(Choice):
    """Which ending finishes your game.
    Any Ending counts whichever ending you reach first.
    Ending A and Ending B are reached by defeating Cinderella in the Lost Empire.
    Ending C is the fairytale book route through Alice's Library. Picking it always shuffles the fairytale books
    into the item pool and you need Fairytale Books Needed of them on Alice's shelves to pull the lever.
    Ending D is the route through Kun-Yan."""
    display_name = "Goal"
    option_any_ending = 0
    option_ending_a = 1
    option_ending_b = 2
    option_ending_c = 3
    option_ending_d = 4
    default = 0


class RandomizeFairyTaleBooks(Toggle):
    """Shuffle all 32 fairytale books into the item pool, so they can turn up in other worlds and other players can
    send them to you. Bosses stop dropping their books and every book spot becomes a check.
    When off, every book stays where the normal game gives it. Ending C turns this on by itself."""
    display_name = "Randomize Fairytale Books"


class FairyTaleBooksNeeded(Range):
    """How many fairytale books Alice's Library wants before the lever to Ending C works. The normal game wants all 32.
    The inner library room opens once you have shelved this many minus the 8 books that belong in there.
    Only matters when the goal is Ending C."""
    display_name = "Fairytale Books Needed"
    range_start = 1
    range_end = 32
    default = 32


class UniqueChecksOnly(Toggle):
    """Only make a check for each unique item, the way BLACK SOULS II does it. Weapons, rings, spells, key items and
    fairytale books get one check each and every consumable spot gives its normal item.
    This cuts the world from 600+ checks to around 100, plus the boss kills."""
    display_name = "Unique Checks Only"


class SkipKunYan(Toggle):
    """Kun-Yan is the Ending D dungeon, the underground world past the Tainted Bog that leads into the Ending D route.
    With this on it has no checks and its pickups and bosses give their normal items."""
    display_name = "Skip Kun-Yan Checks"


class SkipLostEmpire(Toggle):
    """The Lost Empire has no checks. Its pickups and bosses give their normal items."""
    display_name = "Skip Lost Empire Checks"


class SkipAtlantica(Toggle):
    """Sunken Atlantica, where the Little Mermaid lives, has no checks, Hotel Poseidon and the locked houses included.
    Its pickups and bosses give their normal items."""
    display_name = "Skip Atlantica Checks"


class ShufflePrincesses(Toggle):
    """The four demonic princesses swap rooms. Each one keeps her own fight, covenant and book, so her checks move
    with her and the logic follows."""
    display_name = "Shuffle Demonic Princesses"


class ShuffleCompanions(Toggle):
    """Where you would meet one companion you get another instead. The scene keeps its place and dialogue but shows
    her walking sprite, and she then waits at her usual spot in the Holy Forest. All ten companions are in it, Leaf,
    Dorothy, Elma, Victoria, Goose, Jeanne, Miranda, Red Hood, Catherine and Elisabeth."""
    display_name = "Shuffle Companions"


class BossShuffle(DefaultOnToggle):
    """Shuffle which boss you fight in each boss arena. Fairytale bosses, the ones that drop a fairytale book, trade
    arenas only with each other and bring their book along, the rest trade among themselves. The Tortoise and Hare
    knights count as one boss. Story progress and the boss check stay tied to the arena, not the boss."""
    display_name = "Boss Shuffle"


class ShuffleSpecialBosses(Toggle):
    """Cinderella, Mary Sue, Baphomet (the Black Trial at the bottom of Kun-Yan), the Black Goat (the last fight of the
    Ending D route) and mimics trade arenas with the fairytale bosses. Every fairytale book then drops in the same
    place as in the normal game to prevent Ending C softlocks, so leave this off for a more random game. Needs Boss
    Shuffle."""
    display_name = "Shuffle Final Bosses"


class BossScaling(DefaultOnToggle):
    """Scale a shuffled boss so its HP and damage match the boss that normally lives in that arena."""
    display_name = "Boss Scaling"


class EnemyShuffle(DefaultOnToggle):
    """Shuffle the regular enemy groups you meet on maps. Their HP and damage are scaled to the group they replace."""
    display_name = "Enemy Shuffle"


class PauseMenuChecklist(DefaultOnToggle):
    """Adds a Checklist entry to the in-game pause menu, the one you open with the menu button while walking around.
    It lists every check in your slot by area and ticks off the ones you have done. Off leaves the pause menu as the
    normal game has it."""
    display_name = "Pause Menu Checklist"


class DorothyTargetsInLogic(Toggle):
    """Dorothy's training sends you after the Scarecrow, the Tin Man and the Lion, and they only show up once you have
    taken it. Locking Dorothy up before that keeps them away until new game plus brings her back. Off they only ever
    hold filler. On they are normal checks that can hold anything, for players who leave Dorothy alone. If she is locked
    up anyway, beating Cinderella loops the game into new game plus, which frees her so you can take her training
    and fight them on that lap."""
    display_name = "Dorothy's Targets in Logic"


class ShufflePrologue(DefaultOnToggle):
    """Include the prologue's pig fights and the dragon in Boss Shuffle and Enemy Shuffle. Off keeps the opening
    fights as the normal game has them."""
    display_name = "Shuffle the Prologue"


@dataclass
class BlackSoulsOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    goal: Goal
    randomize_fairy_tale_books: RandomizeFairyTaleBooks
    fairy_tale_books_needed: FairyTaleBooksNeeded
    unique_checks_only: UniqueChecksOnly
    skip_kun_yan: SkipKunYan
    skip_lost_empire: SkipLostEmpire
    skip_atlantica: SkipAtlantica
    shuffle_princesses: ShufflePrincesses
    shuffle_companions: ShuffleCompanions
    boss_shuffle: BossShuffle
    shuffle_special_bosses: ShuffleSpecialBosses
    boss_scaling: BossScaling
    enemy_shuffle: EnemyShuffle
    shuffle_prologue: ShufflePrologue
    pause_menu_checklist: PauseMenuChecklist
    dorothy_targets_in_logic: DorothyTargetsInLogic
