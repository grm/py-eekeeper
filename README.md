# py-eekeeper

Save game editor for **Baldur's Gate Enhanced Edition** (and other Infinity Engine games).

A complete Python/PySide6 rewrite of [eekeeper-qt](https://github.com/Goddard/eekeeper-qt) by Troodon80, originally based on Shadow Keeper by Aaron O'Neil.

## Features

- Open and edit save games (BALDUR.GAM)
- Edit character attributes (STR, DEX, CON, INT, WIS, CHA)
- Modify HP, AC, THAC0, XP, Gold, Levels
- Edit saving throws and resistances
- Manage known spells (Wizard, Priest, Innate) — add, remove, browse available
- Edit spell memorization slots per level
- Weapon proficiencies editor (0-5 stars)
- Full inventory editor (39 equipment slots)
- Thief skills, colors, portraits, scripts
- Export/import characters (.CHR files)
- String finder (search dialog.tlk)
- Auto-detect Steam game installations
- Support for BG:EE, BG2:EE, IWD:EE

## Supported Platforms

- Linux
- macOS

## Installation

### From source

```bash
git clone https://github.com/grm/py-eekeeper.git
cd py-eekeeper
pip install -e .
```

### Dependencies

- Python 3.11+
- PySide6 (Qt6)
- Pillow

## Usage

```bash
py-eekeeper
```

On first launch, you'll be asked to configure the game installation directory (where `chitin.key` is located). The auto-detect button searches common Steam paths.

### Workflow

1. **File → Open Save** — select a save game directory
2. Click a character in the party bar to edit them
3. Use the tabs (Character, Spells, Memorization, Proficiencies, Inventory) to make changes
4. **File → Save** to write changes back

## Project Structure

```
py_eekeeper/
├── main.py                  # Entry point
├── app.py                   # Core application logic (singleton)
├── config.py                # Settings management
├── formats/                 # Binary format parsers
│   ├── constants.py         # IE constants and enums
│   ├── inf_key.py           # chitin.key parser
│   ├── inf_bif.py           # BIF archive reader
│   ├── inf_game.py          # BALDUR.GAM parser
│   ├── inf_creature.py      # CRE (creature) parser
│   ├── inf_chr.py           # CHR (exported character)
│   ├── inf_tlk.py           # dialog.tlk string table
│   ├── inf_2da.py           # 2DA table parser
│   ├── inf_bam.py           # BAM sprite decoder
│   └── inf_affect.py        # Effect/affect structures
├── resources/               # Game resource management
│   ├── resource_manager.py  # KEY → BIF → resource facade
│   ├── value_list.py        # Key/value lists (kits, classes, etc.)
│   └── spell_bitmaps.py     # Spell icon loading
└── ui/                      # PySide6 GUI
    ├── main_window.py
    ├── character_sheet.py
    ├── spell_tab.py
    ├── memorization_tab.py
    ├── proficiencies_tab.py
    ├── inventory_tab.py
    └── ...dialogs
```

## Infinity Engine File Formats

This application reads and writes the following binary formats:

| Format | Extension | Description |
|--------|-----------|-------------|
| KEY | chitin.key | Master resource index |
| BIF | *.bif | Resource archive |
| GAM | BALDUR.GAM | Save game (party, gold, globals, journal) |
| CRE | embedded | Creature data (stats, spells, items, affects) |
| CHR | *.chr | Exported character |
| TLK | dialog.tlk | String table (70,000+ entries) |
| 2DA | *.2da | Data tables (kits, classes, etc.) |
| BAM | *.bam | Animated sprites / icons |

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## License

BSD 3-Clause — same as the original EE Keeper.

## Credits

- **Original EE Keeper**: Troodon80 (2013)
- **Shadow Keeper**: Aaron O'Neil (2000)
- **This rewrite**: Python/PySide6 port
