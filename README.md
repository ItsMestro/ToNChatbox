<h1 align="center">
    <img src="resources/icon.ico" alt="ToN Chatbox Icon">
    <br>
    ToNChatbox
</h1>

<div align="center">
<p>Terrors of Nowhere lobby/round statistics chatbox tool.</p>
<a href="/LICENSE"><img alt="License" src="https://img.shields.io/github/license/ItsMestro/ToNChatbox"></a> <a href="https://discord.mestro.cc"><img alt="Discord Server" src="https://discordapp.com/api/guilds/128856147162562560/widget.png?style=shield"></a> <a href="https://github.com/ItsMestro/ToNChatbox/releases/latest"><img alt="Latest Version" src="https://img.shields.io/github/v/release/ItsMestro/ToNChatbox?label=Latest%20Version"></a> <img alt="Total Downloads" src="https://img.shields.io/github/downloads/ItsMestro/ToNChatbox/ToNChatbox.exe?label=Downloads">
</div>

---

## Overview

This is a simple program for the game [Terrors of Nowhere](https://vrchat.com/home/world/wrld_a61cdabe-1218-4287-9ffc-2a4d1414e5bd) in VRChat that outputs some of the lobby and round info into your chatbox.

The program is extremely basic in its current form and features no customization or options. If there is enough interest for it I'll work on more features in the future.

With that said. Here's the current list of features:

> These are all "since joined" because there is no way to get data for a lobby earlier than that.

- <ins>Lobby</ins>
  - Display __last 5 terrors__ encountered
    > Due to the line limit of chatboxes terrors might get cut off at the bottom
  - Display how many of each __round type__ has been played
  - Display how many __moon rounds__ have been played
- <ins>Round</ins>
  - Display __round type__
  - Display __map__
  - Display __stuns__ by the entire lobby
  - Display __survivors__
    > This is currently a bit inaccurate due to using all users in instance. Somebody who is respawned or just joined will still be counted.
  - Display __terror(s)__
    - Fog: Will reveal the terror ~30 seconds into the round
    > It will try to guess the terror based on enrage events. As an example, Furnace/Starved will enrage immediately when the round starts and their name gets displayed.
    - Multi-terror rounds: Displays all terrors immediately when the first spawns
  - Warn players that you're a pacifist murderer for sabotage rounds
    > Don't like this and which you could turn it off? Well too bad you can't. (I'll probasbly add a toggle some day if enough people bug me for it).
- Display __time in lobby__
- Display __rounds played__
- Detect if in ToN instance and opted in to play. Else stop sending chat messages

## Requirements

This program relies on [ToNSaveManager](https://github.com/ChrisFeline/ToNSaveManager) for its data. Go install that before continuing.

Inside the settings of `ToN Save Manager` enable:

- `WebSocket API Server`

For the fog terror estimation to work you'll also need to enable:

- `Live Tracker Compatability`

## Installation

### Run with pre-built binaries

Grab the latest version of the program __[here](https://github.com/ItsMestro/ToNChatbox/releases/latest)__

Place the `ToNChatbox.exe` file anywhere and run it after starting `ToN Save Manager`. That's it!

There's currently no GUI or other settings but a console with some basic output is displayed while running. Program will automatically close when `ToN Save Manager` is closed.

### Run from source

Clone the repository:

```shell
git clone https://github.com/ItsMestro/ToNChatbox
cd ToNChatbox
```

Install dependencies:

```shell
pip install python-osc rel websocket-client[optional]
```

Run the script:

```shell
python ton-chatbox.py
```

---

### Build from source

Clone the repository:

```shell
git clone https://github.com/ItsMestro/ToNChatbox
cd ToNChatbox
```

Install dependencies:

```shell
pip install pyinstaller pyinstaller_versionfile python-osc rel websocket-client[optional]
```

Generate a version file:

```shell
pyivf-make_version --source-format yaml --metadata-source .\\resources\\versioninfo.yml --outfile .\\versioninfo.txt --version 0.0.0
```

Build Binary:

```shell
pyinstaller ton-chatbox.spec
```

---

## License

The code of this repository is licensed under the [MIT licence](https://opensource.org/licenses/MIT). Please see [the license file](LICENSE) for more information. [tl;dr](https://tldrlegal.com/license/mit-license) you can do whatever you want as long as you include the original copyright and license notice in any copy of the software/source.
