# Black Souls Archipelago

An [Archipelago](https://archipelago.gg) world for BLACK SOULS (RPG Maker VX Ace).

- Pickups and boss rewards are shuffled into the multiworld, including the prologue
- Every boss kill is a check (56 bosses)
- Optional boss shuffle with HP and damage scaled to the arena
- Pick which ending counts as your goal (any ending, or A, B, C or D)
- Optional enemy shuffle

No game files are included. The client patches a copy of your own install.

## Playing

1. Install [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 0.6.2 or newer
2. Download `blacksouls.apworld` from [Releases](../../releases) and double click it
3. Open the Archipelago Launcher and start **Black Souls Client**
4. Type `/install <path to your BLACK SOULS folder>` in the client
5. Connect to the server and play `Game.exe` from the new `BLACK SOULS Archipelago` folder

Or skip the client while playing. `/install` also sets up `Game_Archipelago.exe`, which connects to the server by itself using the address in `archipelago.json` (the client fills it in the first time you connect it).

## Tracker

`blacksouls_tracker.zip` in Releases is a [PopTracker](https://github.com/black-sliver/PopTracker/releases) pack. Drag it into the PopTracker window, then connect it to the same server as the client. It marks every check as reachable, out of logic or done.

The full guide is in [worlds/blacksouls/docs/setup_en.md](worlds/blacksouls/docs/setup_en.md).

## Repo layout

- `worlds/blacksouls` is the apworld source
- `worlds/blacksouls/game/ap.rb` is the script injected into the game
- `worlds/blacksouls/game/ap_net.rb` is the direct connection used by `Game_Archipelago.exe`
- `tools` holds the scripts used to read the game data, build the location tables and build the tracker

## Credits

- Direct connection uses [RPGMaker VX Ace AP](https://github.com/EggSlashEther/RPGMaker-VX-Ace-AP) and [archipelago_rb](https://github.com/EggSlashEther/archipelago_rb) by EggSlashEther (MIT). `/install` downloads them from the original repo, and their license ships next to the game as `LICENSE RPGMaker-VX-Ace-AP.txt`
- `Game_Archipelago.exe` is [mkxp-z](https://github.com/mkxp-z/mkxp-z) (GPL-2.0), as included in the kit above
- The direct connection idea comes from the Black Souls 2 Archipelago mod by CthulhusShoes
