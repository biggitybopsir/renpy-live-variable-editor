# Ren'Py Live Variable Editor

A lightweight, drop-in variable browser and editor for Ren'Py games.

Search variables, inspect their current values, and edit them directly in-game.

## Features

* Search variables by name, value, or type
* Browse Store and Persistent variables
* Edit values in-game
* Optional Deep mode for nested values
* Supports common Python-style values
* Configurable hotkey
* Single `.rpy` file, no external tools required

## Installation

1. Download `renpy_live_variable_editor.rpy`
2. Copy it into the game's:

```text
game/
```

folder.

Example:

```text
GameName/
├── GameName.exe
└── game/
    ├── renpy_live_variable_editor.rpy
    ├── script.rpy
    └── ...
```

3. Start the game and load a save or create a new game.
4. Press **F8** to open the editor.

Press **F8** again or **Escape** to close it.

> Make sure you do not have an older copy of the variable browser installed at the same time.

## Usage

Search for a variable, click it, change the value, then press **Apply**.

Examples:

```text
999
12.5
True
False
None
"hello"
[1, 2, 3]
{"key": 5}
```

For string variables, plain text usually works without quotes.

## Deep Mode

Fast mode shows top-level variables.

Enable **Deep** to inspect nested lists, dictionaries, tuples, and objects.

Deep mode may be slower in larger games.

## Persistent Variables

Be careful when editing variables beginning with:

```text
persistent.
```

These changes can be written to Ren'Py's persistent data and may remain after restarting the game or loading another save.

## Changing the Hotkey

F8 is used by default.

Change this line in the script:

```python
_VB_HOTKEY = "K_F8"
```

For example:

```python
_VB_HOTKEY = "K_F9"
```

## Compatibility

Tested with Ren'Py 8.1.3+ / Ren'Py 8.x.

Ren'Py 7.x is currently untested.

## Disclaimer

This is a debugging/modding utility.

Changing unexpected variables can break game logic, saves, or persistent data, so use it carefully.
