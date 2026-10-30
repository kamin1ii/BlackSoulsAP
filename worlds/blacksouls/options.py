from dataclasses import dataclass

from Options import Choice, DefaultOnToggle, Toggle, PerGameCommonOptions, StartInventoryPool


class Goal(Choice):
    """Which ending finishes your game.
    Any Ending counts whichever ending you reach first.
    Ending A and Ending B are reached by defeating Cinderella in the Lost Empire.
    Ending C is the fairy-tale book route through Alice's Library. Fairy-tale books stay in their normal spots.
    Ending D is the route through Kun-Yan."""
    display_name = "Goal"
    option_any_ending = 0
    option_ending_a = 1
    option_ending_b = 2
    option_ending_c = 3
    option_ending_d = 4
    default = 0


class RandomizeFairyTaleBooks(Toggle):
    """Shuffle the fairy-tale books into the item pool. When off, every book stays where the normal game gives it,
    from fairy-tale bosses and story events, and those spots are not checks. Ending C always keeps them in place."""
    display_name = "Randomize Fairy-Tale Books"


class BossShuffle(DefaultOnToggle):
    """Shuffle which boss you fight in each boss arena. Story progress stays tied to the arena, not the boss."""
    display_name = "Boss Shuffle"


class BossScaling(DefaultOnToggle):
    """Scale a shuffled boss so its HP and damage match the boss that normally lives in that arena."""
    display_name = "Boss Scaling"


class EnemyShuffle(DefaultOnToggle):
    """Shuffle the regular enemy groups you meet on maps. Their HP and damage are scaled to the group they replace."""
    display_name = "Enemy Shuffle"


@dataclass
class BlackSoulsOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    goal: Goal
    randomize_fairy_tale_books: RandomizeFairyTaleBooks
    boss_shuffle: BossShuffle
    boss_scaling: BossScaling
    enemy_shuffle: EnemyShuffle
