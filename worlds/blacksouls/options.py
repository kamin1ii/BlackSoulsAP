from dataclasses import dataclass

from Options import DefaultOnToggle, PerGameCommonOptions, StartInventoryPool


class BossShuffle(DefaultOnToggle):
    """Shuffle which boss you fight in each boss arena. Story progress stays tied to the arena, not the boss."""
    display_name = "Boss Shuffle"


class BossScaling(DefaultOnToggle):
    """Scale a shuffled boss so its HP and damage match the boss that normally lives in that arena."""
    display_name = "Boss Scaling"


@dataclass
class BlackSoulsOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    boss_shuffle: BossShuffle
    boss_scaling: BossScaling
