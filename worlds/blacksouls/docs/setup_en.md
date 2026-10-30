# Black Souls Setup Guide

## What you need

- A copy of BLACK SOULS, either the Steam release or the English 2019 release
- The RPG Maker VX Ace RTP, which the game already needs to run
- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 0.6.2 or newer
- `blacksouls.apworld` from the [Black Souls AP releases](https://github.com/kamin1ii/BlackSoulsAP/releases)

## Install

1. Double click `blacksouls.apworld`. Archipelago installs it. You can also copy it into the
   `custom_worlds` folder inside your Archipelago folder.
2. Open the Archipelago Launcher and click **Black Souls Client**.
3. In the client's text box type the line below, using the path to your own game folder

   ```
   /install C:\Games\BLACK SOULS
   ```

   This makes a separate copy next to it called `BLACK SOULS Archipelago`. Your normal game and
   saves are left alone.

## Make your options file

Open the Launcher, click **Options Creator** (or Generate Template Options), pick Black Souls and
save the yaml. Give the yaml to whoever is hosting the game.

## Play

1. Connect the Black Souls Client to the server address the host gives you.
2. Start `Game.exe` inside `BLACK SOULS Archipelago` and begin a **new game**.
3. Keep the client open while you play. Items you find are sent through it, and items from other
   players show up as popups when you are walking around.

If the client was closed while you played, connect it again. Everything you found in the
meantime is sent as soon as you reach a map.
