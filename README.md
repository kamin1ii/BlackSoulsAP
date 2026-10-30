# Black Souls Archipelago

An [Archipelago](https://archipelago.gg) world for BLACK SOULS (RPG Maker VX Ace).

- Pickups and boss rewards are shuffled into the multiworld (595 locations)
- Every boss kill is a check (55 bosses)
- Optional boss shuffle with HP and damage scaled to the arena
- Goal is defeating Cinderella in the Lost Empire

No game files are included. The client patches a copy of your own install.

## Playing

1. Install [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 0.6.2 or newer
2. Download `blacksouls.apworld` from [Releases](../../releases) and double click it
3. Open the Archipelago Launcher and start **Black Souls Client**
4. Type `/install <path to your BLACK SOULS folder>` in the client
5. Connect to the server and play `Game.exe` from the new `BLACK SOULS Archipelago` folder

The full guide is in [worlds/blacksouls/docs/setup_en.md](worlds/blacksouls/docs/setup_en.md).

## Repo layout

- `worlds/blacksouls` is the apworld source
- `worlds/blacksouls/game/ap.rb` is the script injected into the game
- `tools` holds the scripts used to read the game data and build the location tables
