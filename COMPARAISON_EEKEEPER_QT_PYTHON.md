# Exhaustive Comparison Between eekeeper-qt and py-eekeeper

## 1. Comparison Scope

This report compares:

- the legacy C++/Qt application **eekeeper-qt**, analyzed from the upstream [Goddard/eekeeper-qt](https://github.com/Goddard/eekeeper-qt) repository cloned locally at `/tmp/eekeeper-qt` at commit `41b612e`;
- the **py-eekeeper** Python/PySide6 implementation, analyzed from the current working tree of this repository.

The Python repository had uncommitted changes at the time of analysis, especially in format parsers, resource management, the inventory UI, and tests. This report therefore describes the observed state of the files, not only the documentation.

The legacy Qt project is not stored directly in the Python repository. The comparison is based on the upstream C++/Qt source code, `SPEC.md`, `README.md`, the current Python code, and the Python test suite execution.

---

## 2. Executive Summary

`py-eekeeper` correctly follows the same overall direction as `eekeeper-qt`: the same functional domain, the same save-opening flow around `BALDUR.GAM`, the same dependency on Infinity Engine resources (`KEY/BIF/TLK/2DA/BAM`), and the same goal of editing characters stored inside a save game.

The main difference is that legacy `eekeeper-qt` is a partial but fairly dense C++/Qt port of Shadow Keeper logic, with a large amount of historical code, binary structures, and planned dialogs. The Python version is smaller, more testable, more readable, and better split into modules, but it does not yet cover the full application surface visible or planned in the old Qt version.

The Python parsers are already close to parity for several critical formats: `GAM`, `CRE`, `CHR`, `KEY`, `BIF`, `TLK`, `2DA`, `BAM`, and `AFF`. Python's strongest advantage is automated testing. The UI gap has been largely closed: item/spell/portrait browsers, globals/journal/affects editors, `.CHR` import integration into the save game, `Save As`, a full settings dialog, and a dedicated Game tab for party-level editing are all implemented. The remaining gaps are primarily: creature browser, local variables editor, and documented Windows support.

---

## 3. Overall Project State

| Area | eekeeper-qt C++/Qt | py-eekeeper Python/PySide6 |
|---|---|---|
| Language | C++ | Python 3.11+ |
| UI toolkit | Qt Widgets, qmake, Qt5 target | PySide6 / Qt6 |
| Packaging | qmake, KDE 5.15 Flatpak | `pyproject.toml`, hatchling, `py-eekeeper` script |
| Announced platforms | Windows, Linux, macOS | Linux, macOS |
| Automated tests | No tests found | `pytest`, 43 tests, 42 pass locally |
| Architecture | Historical globals and singletons | `formats`, `resources`, `ui`, `app`, `config` modules |
| UI | Many `.ui` dialogs, some stubs | Comprehensive: 7 tabs, 8+ dialogs, toolbar |
| Format engine | Very complete for its time | Already substantial and more testable |
| Functional maturity | Partial editing, much historical logic | Partial editing, better validation base |

---

## 4. Tree Layout and Organization

### 4.1 eekeeper-qt

The legacy project is organized around:

- `EEKeeperQt.pro`: main qmake project;
- `EEKeeper/main.cpp`: entry point;
- `EEKeeper/EEKeeperQt.cpp` and `EEKeeper/include/EEKeeperQt.h`: application singleton, global variables, resource loading;
- `EEKeeper/Inf*.cpp` and `EEKeeper/include/Inf*.h`: Infinity Engine format parsers;
- `EEKeeper/ui/*.cpp`, `EEKeeper/ui/*.h`, and `EEKeeper/ui/{linux,mac,win32}/*.ui`: widgets and platform-specific UI files;
- `res/` and `eekeeper.qrc`: embedded icons;
- `res/lang/en_US/*.uld` and `KitLists/Kits.uld`: user lists in Qt binary format.

The old Qt application duplicates `.ui` files for Linux, macOS, and Windows. This provides some platform adaptation, but greatly increases maintenance cost.

### 4.2 py-eekeeper

The Python version is organized around:

- `py_eekeeper/main.py`: entry point;
- `py_eekeeper/app.py`: `EEKeeperApp` singleton and orchestration;
- `py_eekeeper/config.py`: configuration through `QSettings`;
- `py_eekeeper/formats/`: binary parsers;
- `py_eekeeper/resources/`: game resource facade;
- `py_eekeeper/ui/`: PySide6 interface;
- `tests/`: unit tests and synthetic integration tests.

This organization is cleaner than the old Qt code: formats, resources, and UI are better separated. `spell_browser.py` and `item_browser.py` are now present and functional. `SPEC.md` still describes files that are not present: `pal_image_list.py` and `data/kits.dat`.

---

## 5. Build, Installation, and Dependencies

### 5.1 Legacy Qt

`eekeeper-qt` uses qmake through `EEKeeperQt.pro`. It depends on Qt Widgets and builds an `EEKeeperQt` executable. Graphic resources are embedded with `eekeeper.qrc`.

A `flatpak.json` also targets a KDE/Qt 5.15 runtime. This provides a Linux distribution path, but the project contains no CI pipeline and no associated tests.

### 5.2 Python

`py-eekeeper` uses `pyproject.toml` with `hatchling`. The declared runtime dependencies are:

- `PySide6>=6.5`;
- `Pillow>=10.0`.

Important observation: `Pillow` is declared, but the current BAM/icon loading implementation mostly uses `QImage`/`QPixmap`. Pillow therefore appears to have little real use, or may be obsolete in the current state.

The exposed command is:

```bash
py-eekeeper
```

---

## 6. Configuration and Persistence

### 6.1 Common Ground

Both implementations keep the idea of persistent configuration containing:

- the game installation path;
- the language;
- the documents / save games path;
- editor options such as spell limits, memorized spell writing behavior, and whether data versions should be ignored.

### 6.2 Differences

| Topic | eekeeper-qt | py-eekeeper |
|---|---|---|
| Settings system | Historical `QSettings("EEKeeper", ...)` | `QSettings("EEKeeper", "py-eekeeper")` |
| Install path | Manual, auto-detection stubbed | Dialog with Steam auto-detection on Linux/macOS |
| Documents path | Stored in settings | Stored, with Linux/macOS defaults |
| Spell limit options | Persisted but rarely or never applied | Persisted but not applied in the current UI |
| CHR/CRE overwrite | Persisted, barely wired | `allow_chr_overwrite` persisted but unused |
| UI grid | Setting present | Setting present but not applied |
| Ignore versions | Used in parsers | Propagated to parsers |
| Hot reinitialization | Partial | Installation changes require restart |

The Python version improves install auto-detection compared with the old Qt version, especially on Linux/macOS. However, several inherited options exist in configuration without visible UI effect.

---

## 7. Game Resource Loading

### 7.1 eekeeper-qt

The historical loading sequence is roughly:

1. open `dialog.tlk` from `lang/<lang>/dialog.tlk`;
2. read `chitin.key`;
3. open referenced BIF files;
4. scan `override/`;
5. load spell icons from BAM files;
6. read IDS and 2DA resources;
7. build class, race, alignment, kit, proficiency, spell, and other lists;
8. load `.uld` lists such as `Kits.uld` and `Affects.uld`.

The C++ model relies heavily on globals: `_infKey`, `_infTlk`, `_spellBitmaps`, `_vlClass`, `_vlRace`, `_vlKit`, `_vlAffects`, and others.

### 7.2 py-eekeeper

The Python version centralizes more behavior in:

- `ResourceManager` for `KEY -> BIF -> resource`;
- `EEKeeperApp` for orchestration;
- `ValueList` for display lists;
- `SpellBitmaps` for BAM icons.

`ResourceManager` scans `override/`, prioritizes override files, then falls back to BIF data. It can also expose a resource list by type.

### 7.3 Observed Differences

| Topic | eekeeper-qt | py-eekeeper |
|---|---|---|
| `override/` priority | Yes | Yes |
| KEY/BIF | Yes | Yes |
| TLK | Yes | Yes |
| XOR-encrypted IDS | Yes | Yes for 2DA/IDS depending on current parser path |
| 2DA | Yes | Yes |
| BAM | Yes, Qt images | Yes, pixels/Qt pixmap |
| Spell bitmaps | Loaded and intended for UI | Loaded but barely or not used in UI |
| Character palettes | `CPalImageList` | No observed `pal_image_list.py` |
| `.uld` | Qt binary format | Replaced by `ValueList` JSON/IDS/2DA depending on case |
| `Affects.uld` | Present and editable | Replaced by game-provided effect text when available |

The Python version has a cleaner resource model, but it has not yet wired all visual richness or configurable lists from the old Qt application.

---

## 8. Supported Binary Formats

### 8.1 Overview

| Format | eekeeper-qt | py-eekeeper | Comment |
|---|---|---|---|
| `chitin.key` / KEY | Read | Read | Expected functional parity |
| `.bif` / BIF | Read | Read | Python also handles tested compressed BAM cases |
| `BALDUR.GAM` | Read/write | Read/write | Critical format in both |
| embedded `.cre` / CRE | Read/write | Read/write | Editor core |
| `.chr` | Read/write parser | Read/write | Python exports; import does not yet modify the party |
| `dialog.tlk` | Read | Read | Python lazily caches strings |
| `.2da` | Read | Read | Python tests parsing + XOR |
| `.ids` | Indirect read | Read through resources/lists | Less explicitly exposed |
| `.bam` | Read/decode | Read/decode | Python tests the decoder |
| `.bmp` | Resource/portraits | Resource/portraits | Python handles save portraits |
| `.itm` | Read for name/display | Read for name/display | No full Python browser |
| `.spl` | Read for name/display | Read for spell lists | No dedicated graphical browser |
| `.bcs`, `.bs` | Indexed/resources | Scanned depending on type | No editing |

### 8.2 GAME

Both implementations treat `BALDUR.GAM` as the main save game file:

- in-party characters;
- out-of-party characters;
- party gold;
- party reputation;
- global variables;
- journal;
- embedded CRE data.

Differences:

- the old Qt UI mainly exposes party characters; out-of-party characters are read but barely or not manipulated;
- Python displays an `[NPC]` marker for out-of-party characters in `SavedGameWidget`, but full out-of-party editing still depends on the current UI flow and should be verified;
- Python now exposes a Journal Editor dialog (`ui/journal_editor.py`) with full add/edit/remove and text preview from TLK, backed by `formats/inf_journal.py`;
- Python exposes `party_gold`, `party_reputation`, `get_globals`, and `set_globals` through a dedicated Game tab and a Global Variables Editor dialog (`ui/globals_editor.py`).

### 8.3 CRE

CRE is the central format in both applications.

Common or close features:

- main attributes;
- HP, AC, THAC0, XP, personal gold;
- levels;
- race, class, gender, alignment, kit;
- saving throws;
- resistances;
- thief skills;
- colors;
- portraits;
- scripts;
- known spells;
- memorization;
- inventory;
- proficiencies through affects for BG2/EE;
- effects/affects at model level.

Differences:

| Topic | eekeeper-qt | py-eekeeper |
|---|---|---|
| Inventory slot count | Historical code aligned with 38 useful slots | Current code constant `INF_NUM_ITEMSLOTS = 38` in modified code |
| Slot documentation | UI/spec sometimes mention 39 | Python README/SPEC still mention 39 in places |
| Generic affects | Parser present, UI tab empty | Model present, full Affects tab with add/edit/remove (`ui/affects_tab.py`, `ui/affect_edit_dialog.py`) |
| Speed | Observed Qt bug: wrong UI line read | Python has `get_speed`/`set_speed`, not widely exposed |
| Proficiencies | Through affects + dual-class tribbles | Through affects + game `WEAPPROF.2DA` IDs |
| Memorized spells without known spell | Preserved in Qt | Mechanism should be watched/validated in Python |
| Death / HP | Historical logic | Python forces HP to 0 when death flags are set, according to model |

The Python code appears to have made strong progress on binary CRE fidelity, but the UI surface remains more limited than the model.

### 8.4 CHR

| Topic | eekeeper-qt | py-eekeeper |
|---|---|---|
| `.CHR` parser | Yes | Yes |
| Export | Planned / partially wired depending on UI | Yes through `export_character` |
| Import | Historical goal of replacement/addition | Reads `.CHR`, integrates into GAM via `add_out_of_party_character()`, user is asked to add to reserves |
| Overwrite policy | Settings present | Settings present, `allow_chr_overwrite` in settings dialog |

Python import now achieves parity: the character is parsed from `.CHR` and integrated into the party reserves through `InfGame.add_out_of_party_character()`. The main window refreshes `SavedGameWidget` after import.

### 8.5 TLK

Both versions read `dialog.tlk`.

Differences:

- old Qt uses TLK for names and has a `StringFinderDialog`;
- Python also has a `StringFinderDialog`, limits results, and uses `InfTlk.get_string`;
- Python tries UTF-8 and then latin-1, which is more convenient for encoding than the historical C++ approach.

### 8.6 2DA / IDS

Both versions use 2DA/IDS tables to build game lists.

Differences:

- old Qt builds many global lists from `HATERACE`, `WEAPPROF`, `KITLIST`, `ALIGN`, `CLASS`, `RACE`, and others;
- Python now loads the same core game lists from IDS/2DA resources, including `HATERACE.2DA`, `WEAPPROF.2DA`, `KITLIST.2DA`, `ALIGN.IDS`, `EA.IDS`, `STATE.IDS`, and `ANIMATE.IDS`. IDS parsing accepts hexadecimal values such as alignment ids (`0x11`, `0x22`, etc.). Effect opcode labels use game effect text resources such as `EFFTEXT.2DA` when available instead of the legacy user-editable `Affects.uld`.

### 8.7 BAM / Images

Both versions can decode BAM.

Differences:

- old Qt uses spell bitmaps and palette mechanisms for display;
- Python has `SpellBitmaps` with spell icons wired into `SpellBrowserDialog` and item icons wired into `ItemBrowserDialog` via `get_item_icon()` (reads ITM header offset 0x3A for BAM reference);
- Python has no observed `PalImageList`, even though the specification mentions it.

---

## 9. Main User Interface

### 9.1 Main Window

| Element | eekeeper-qt | py-eekeeper |
|---|---|---|
| File menu | Open Saved Game, Open Character, Open Creature, Save, Exit planned | Open Save, Save, Save As, Export Character, Import Character, Quit |
| Save As | Present through historical dialog/flow | Present — `SaveGameNameDialog` + `app.save_game_as()` (Ctrl+Shift+S) |
| View | Dockable item/spell/creature browsers planned | Missing (browsers are dialogs, not docked panels) |
| Tools | No strict equivalent | String Finder, Global Variables, Journal |
| Options / Settings | Installation Directory, lists, various options | Installation Directory, Settings (4-tab dialog: General, Spells, Display, Advanced) |
| Help | About/Readme/Website planned but incomplete | About |
| Toolbar | Open/Save/Web/About planned | Open, Save, Save As, Export, Import, String Finder with separators |
| Layout | Window + tabs + historical widgets | Vertical splitter + party bar + tabs (Game, Character, Spells, Memorization, Proficiencies, Inventory, Affects) |

The Python version now covers most main window actions present in the legacy Qt version. The toolbar is functional with grouped buttons, and the menu structure exposes all major features through File, Tools, and Options menus.

### 9.2 Opening Save Games

**eekeeper-qt**:

- dedicated dialog;
- lists save games;
- excludes Quick-Save / Auto-Save according to observed behavior;
- supports single-player, multiplayer, and Black Pits;
- shows a `BALDUR.BMP` preview;
- avoids duplicate openings.

**py-eekeeper**:

- dedicated dialog;
- lists `save`, `mpsave`, and `bpsave` (Black Pits);
- opens directories containing `BALDUR.GAM`;
- displays characters in `SavedGameWidget`;
- handles portraits from save BMP files;
- Quick-Save / Auto-Save exclusion should be verified in the current Python flow.

### 9.3 Character Bar / Selection

`eekeeper-qt` uses a `SavedGameWidget` and creates a `CharacterSheetWidget` for each in-party member. NPCs/out-of-party characters are read but barely exposed.

`py-eekeeper` also has a `SavedGameWidget`, displays characters, and can show an `[NPC]` marker for out-of-party characters. Selection feeds a set of tabs: Game, Character, Spells, Memorization, Proficiencies, Inventory, Affects. The Game tab is always active (party-level data), while other tabs load per-character data on selection.

---

## 10. Character Editing Tabs

### 10.1 Characteristics / Character Sheet

| Field | eekeeper-qt | py-eekeeper |
|---|---|---|
| STR/DEX/CON/INT/WIS/CHA attributes | Yes | Yes |
| Current/base HP | Yes | Yes |
| AC | Yes | Yes |
| THAC0 | Yes | Yes |
| XP | Yes | Yes |
| Personal gold | Yes | Yes |
| Levels | Yes | Yes |
| Class/race/gender/alignment | Yes | Yes |
| Kit | Yes | Yes |
| Racial enemy | Yes | Yes, loaded from `HATERACE.2DA` |
| Enemy-Ally / General / Specific | Yes in old model/UI | Enemy-Ally exposed from `EA.IDS`; General/Specific remain model-only |
| Speed | Field present but Qt bug | Python model, no obvious UI |
| Resistances | Yes | Yes |
| Saving throws | Yes | Yes |
| Thief skills | Yes | Yes |
| Colors | Yes | Yes |
| Portraits | Yes | Yes |
| Scripts | Yes | Yes |
| Detailed AC by type | Partial | Not fully exposed |
| Morale/fatigue/intoxication/luck | Present in CRE | Not widely exposed |

The Python version covers the most useful character editing fields, but not the full CRE granularity.

### 10.2 Inventory

**eekeeper-qt**:

- displays slots, names, quantities, identification;
- inventory is essentially read-only in the observed historical UI;
- the item browser exists as a stub widget / planned UI, but logic is weak or absent.

**py-eekeeper**:

- displays 38 rows;
- supports `Set Item` through a full graphical `ItemBrowserDialog` with search filter, item icons from BAM, and name display;
- supports `Remove`;
- supports `Identify All`;
- item icons are shown in the browser dialog via `SpellBitmaps.get_item_icon()`;
- displays quantities but does not provide rich charge/quantity editing.

Python surpasses old Qt for effective inventory editing and now includes a graphical item browser.

### 10.3 Known Spells

**eekeeper-qt**:

- Innate/Wizard/Priest tabs;
- spell display;
- some memorization actions;
- incomplete add/remove behavior according to the historical UI code;
- spell browser planned but stubbed.

**py-eekeeper**:

- Wizard/Priest/Innate types;
- level filter;
- Known and Available lists;
- Add, Add All, Remove, Remove All buttons;
- Browse... button opens `SpellBrowserDialog` with type/level filters, search, and BAM icons;
- names retrieved through TLK/SPL.

Python is more usable for adding/removing known spells and now includes a full graphical spell browser with icons.

### 10.4 Memorization

**eekeeper-qt**:

- edits maximum memorization by type/level;
- +/- buttons;
- write logic with an option to refresh memorized spells.

**py-eekeeper**:

- Type / Level / Max memorizable table;
- +1, -1, Max +1, Max -1 buttons;
- no detailed per-spell editing of memorized spells;
- `mem_spells_on_save` option present at model level.

Parity is partial. Both focus mainly on memorization slots.

### 10.5 Proficiencies

**eekeeper-qt**:

- `WEAPPROF` list;
- 0-5 editing;
- affect-based handling for BG2/EE;
- historical dual-class/tribble logic.

**py-eekeeper**:

- proficiency list loaded from game `WEAPPROF.2DA`, with a common EE fallback;
- 0-5 editing;
- affect-based implementation;
- no observed class-based filtering, unlike the specification.

Basic parity is good. Python now follows the same game-resource source as `eekeeper-qt`, which avoids BG2/IWD:EE proficiency ID drift such as IWD:EE `2WEAPON = 114`.

### 10.6 Missing or Incomplete Tabs

In `eekeeper-qt`, some tabs or areas exist but are empty or barely wired:

- Appearance;
- Affects;
- Global Variables;
- Local Variables;
- Journal Entries;
- Item/Spell/Creature browsers.

In `py-eekeeper`, most of these are now implemented:

- **Affects tab** (`ui/affects_tab.py`): full table of creature affects with add/edit/remove and a detailed edit dialog (`ui/affect_edit_dialog.py`) covering all 18 InfAffect fields;
- **Game tab** (`ui/game_tab.py`): dedicated tab for party gold, reputation, with buttons to open Globals and Journal editors;
- **Global Variables**: full editor dialog (`ui/globals_editor.py`) with table, filter, add/remove;
- **Journal Entries**: full editor dialog (`ui/journal_editor.py`) with text preview from TLK;
- **Item Browser**: dialog (`ui/item_browser.py`) with icons, search filter;
- **Spell Browser**: dialog (`ui/spell_browser.py`) with type/level filters, icons, search;
- **Portrait Browser**: dialog (`ui/portrait_browser.py`) scanning game directories for BMP/PNG/JPG, grid view with thumbnails.

Remaining gaps: Appearance tab, Local Variables editor, Creature browser.

---

## 11. Auxiliary Dialogs

| Dialog | eekeeper-qt | py-eekeeper | Difference |
|---|---|---|---|
| Installation Directory | Yes, incomplete Linux validation | Yes, Steam auto-detection | Python more complete |
| Open Saved Game | Yes | Yes | Qt covers more save types |
| Save Game Name | Yes, used for save-as/rename | Yes, wired through File > Save As (Ctrl+Shift+S) | Parity |
| ValueListDialog | Yes, wired for Kits/Affects | File present but not wired | Python incomplete |
| ValueItemDialog | Yes | No equivalent standalone dialog observed | Python incomplete |
| StringFinderDialog | Yes | Yes | Python limits/structures results |
| SpellBrowserDialog | UI/stub | Yes, full dialog with type/level filters, icons, search | Python better |
| ItemBrowserDialog | UI/stub | Yes, full dialog with search filter and item icons | Python better |
| PortraitBrowserDialog | Not present | Yes, scans game directories, grid thumbnail view | Python only |
| GlobalsEditorDialog | Empty tab | Yes, full table editor with filter, add/remove | Python better |
| JournalEditorDialog | Empty tab | Yes, full editor with TLK text preview | Python better |
| AffectEditDialog | Empty tab | Yes, 18-field editor in 3 grouped sections | Python better |
| SettingsDialog | Various options in menus | Yes, 4-tab dialog (General, Spells, Display, Advanced) | Parity |
| About | Planned/incomplete | Simple implementation | Python more wired |

---

## 12. Save Features

### 12.1 Save

Both versions can rewrite `BALDUR.GAM`, recalculate offsets, and reinject modified CRE data.

### 12.2 Save As / Rename

`eekeeper-qt` contains a save-as flow:

- name dialog;
- folder numbering;
- adjacent file copy;
- new `BALDUR.GAM` write.

`py-eekeeper` now exposes `File -> Save As` (Ctrl+Shift+S) which opens `SaveGameNameDialog`, then calls `app.save_game_as(new_name)`. The implementation copies the save directory with `shutil.copytree`, updates internal paths, and writes the modified GAM to the new location.

### 12.3 Closing With Changes

Both versions include a change check:

- old Qt: Save/Discard/Cancel dialog when closing a modified tab;
- Python: Yes/No/Cancel dialog when closing the application if `game.has_changed()`.

---

## 13. Value List Management

### 13.1 Legacy Qt

`eekeeper-qt` uses `CValueList` and `.uld` files in Qt `QDataStream` binary format. Examples:

- `Kits.uld`;
- `Affects.uld`, replaced by game-provided effect opcode labels when available;
- planned `NumAttacks.uld`.

These lists can be edited through historical dialogs, at least for Kits and Affects.

### 13.2 Python

`py-eekeeper` uses `ValueList`, loading from JSON or IDS/resource-like formats. Kits are mostly built from `KITLIST.2da` and TLK. Like legacy `Kits.uld` in `eekeeper-qt`, CRE kit values are stored shifted for both classic kits and mage schools (`CONJURER = 0x00800000`, `INVOKER = 0x08000000`, `BERSERKER = 0x40010000`). CRE loading normalizes briefly broken unshifted mage-school values such as `0x00000800` back to `0x08000000`. This is covered by `tests/test_app_kits.py` and `tests/test_inf_creature.py`. The specification mentions `data/kits.dat`, but that file was not observed in the repository.

### 13.3 Important Difference

The Python version does not try to reproduce the Qt `.uld` format. This is a useful technical simplification, but it means:

- no direct compatibility with legacy `.uld` files;
- no custom affects/kits value-list editor wired in the UI;
- the source of truth is more strongly derived from game resources.

---

## 14. Platforms and Paths

| Topic | eekeeper-qt | py-eekeeper |
|---|---|---|
| Windows | UI and `Baldur.exe` validation planned | Not announced in README |
| Linux | Dedicated UI, stubbed install validation | Linux announced, Steam auto-detection |
| macOS | Dedicated UI, `.app/Contents/Resources` validation | macOS announced, Steam auto-detection |
| Documents | Settings and manual paths | Linux/macOS defaults |
| Black Pits | `bpsave/` directory planned | `bpsave/` exposed in Open dialog (dedicated tab) |
| Multiplayer saves | `mpsave/` | `mpsave/` |

Python simplifies the platform target by leaving Windows out for now. This is consistent with the README, but it is a coverage regression compared with the old project.

---

## 15. Tests and Validation

### 15.1 eekeeper-qt

No automated unit or integration tests were found. Validation appears to be mostly manual.

### 15.2 py-eekeeper

The `pytest` suite contains tests for:

- `InfCreature`;
- `InfGame`;
- `Inf2DA`;
- synthetic open/edit/save integration;
- resource formats (`KEY`, `BIF`, `TLK`, `CHR`, `BAM`, `ResourceManager`) in a file that was untracked at the time of analysis.

Local execution:

```text
42 passed, 1 failed
```

The observed failure is:

```text
tests/test_integration.py::test_ui_character_sheet_loading
ModuleNotFoundError: No module named 'PySide6'
```

This is not a functional failure of the tested code. It is an environment issue: PySide6 is not installed in the environment used for the test run.

### 15.3 Major Difference

The Python version is clearly stronger on testability. It can protect binary parsers with synthetic blobs and round-trips. However, it still lacks tests using real game saves and real game resources, which is critical for guaranteeing parity with the old tool.

---

## 16. Documentation and Specification

### 16.1 eekeeper-qt

The project contains:

- `AUTHORS`;
- `COPYING`;
- `TODO`;
- Qt and Shadow Keeper licenses;
- little modern user documentation.

The historical `TODO` notably mentions:

- making Item/Spell browsers functional;
- loading out-of-party CRE/CHR files;
- changing portraits;
- adding translations, About, and website support.

### 16.2 py-eekeeper

The repository contains:

- `README.md`;
- `SPEC.md`;
- tests;
- Python packaging.

### 16.3 Gaps Between README/SPEC and Python Code

| Documented topic | Observed state |
|---|---|
| `Full inventory editor (39 equipment slots)` | Current code uses 38 slots (`INF_NUM_ITEMSLOTS = 38`); full item browser now present |
| `Export/import characters` | Export OK, import now integrates character into GAM party reserves |
| `spell_browser.py` / `item_browser.py` | Now present and functional (`ui/spell_browser.py`, `ui/item_browser.py`) |
| `pal_image_list.py` | Mentioned in `SPEC.md`, not present |
| `data/kits.dat` | Mentioned in `SPEC.md`, not present |
| splash screen | Mentioned in `SPEC.md`, not observed |
| `Save As` toolbar | Now wired — toolbar button + File menu action (Ctrl+Shift+S) |
| class-based proficiency filtering | Mentioned, not observed |

The specification remains useful as a target, but it should be treated as an intent document, not as an exact description of the current state.

---

## 17. Detailed Functional Differences

### 17.1 Features Present in Both

- Opening a `BALDUR.GAM` save.
- Reading embedded characters.
- Editing main attributes.
- Editing HP/AC/THAC0/XP/gold/levels.
- Editing saving throws and resistances.
- Editing thief skills.
- Editing colors, portraits, and scripts.
- Managing known spells.
- Managing memorization slots.
- Managing proficiencies.
- Reading/writing inventory at model level.
- Reading `dialog.tlk`.
- Searching TLK strings.
- Exporting `.CHR` at least at model/function level.
- Loading resources through KEY/BIF.
- Prioritizing `override/` resources.
- Decoding BAM.

### 17.2 Qt Features or Behaviors Missing/Incomplete in Python

**Now implemented:**

- ~~`Save As` with creation of a new save folder.~~ → Done via `app.save_game_as()`.
- ~~Full save rename through `SaveGameNameDialog`.~~ → Wired through File > Save As.
- ~~Graphical item browser.~~ → `ui/item_browser.py` with icons and search.
- ~~Graphical spell browser.~~ → `ui/spell_browser.py` with type/level filters and icons.
- ~~Generic affects editor.~~ → `ui/affects_tab.py` + `ui/affect_edit_dialog.py`.
- ~~Global variables editor.~~ → `ui/globals_editor.py`.
- ~~Journal editor.~~ → `ui/journal_editor.py` + `formats/inf_journal.py`.
- ~~Portrait change through a browser.~~ → `ui/portrait_browser.py` wired into character sheet.
- ~~Historical toolbar.~~ → Toolbar with Open, Save, Save As, Export, Import, String Finder.
- ~~Complete View/Settings menus.~~ → Settings dialog with 4 tabs.
- ~~`.CHR` import into the party or character replacement.~~ → `InfGame.add_out_of_party_character()`.
- ~~Visible spell/item icons.~~ → Icons in browser dialogs via `SpellBitmaps`.

**Still missing:**

- Creature browser.
- Custom Kits/Affects list editor (`.uld` equivalent).
- Local variables editor.
- Appearance tab equivalent to the old UI.
- ~~Explicit Black Pits handling.~~ (done: `bpsave/` tab in Open dialog)
- Documented Windows support.
- Effective enforcement of known/memorized spell limits (settings exist but not enforced in add flows).
- Grid option application (setting exists, not applied to all tables).
- Character palette images (`PalImageList`).

### 17.3 Python Features That Are More Advanced or Better Structured

- Automated tests.
- Clearer modular architecture.
- Parsers that are easier to validate independently of the UI.
- More useful Linux/macOS Steam auto-detection than the Qt stub.
- More flexible TLK encoding behavior.
- More centralized Python resource management.
- Effective basic inventory editing, whereas old Qt was mostly read-only in the UI.
- More directly usable known-spell add/remove flow.
- Standard Python packaging.

### 17.4 Legacy Qt Bugs or Debt Not to Reproduce

- Incomplete Linux install path validation.
- Stubbed `FindInstallPath()`.
- Some declared menus/actions without implementation.
- Item/Spell browsers present but without real logic.
- Inventory displayed but not really editable.
- Empty Appearance/Affects/Globals/Journal tabs.
- Observed speed bug: wrong UI line used in `SetSpeed()`.
- Potentially incorrect spell update loop.
- Several persistent settings not applied.
- File logging planned but mostly disabled.

---

## 18. Technical Differences by Module

### 18.1 Application Core

| eekeeper-qt | py-eekeeper | Difference |
|---|---|---|
| `EEKeeper` / global variables | `EEKeeperApp` singleton | Python reduces scattered globals |
| resource loading in window/app | `ResourceManager` + app | better Python separation |
| historical `QSettings` | `Config` | Python encapsulates better |
| custom log | little observed logging | Python logging could be enriched |

### 18.2 Formats

| eekeeper-qt | py-eekeeper | Python state |
|---|---|---|
| `CInfKey` | `InfKey` | close |
| `CInfBifFile` | `InfBifFile` | close, tests present |
| `CInfGame` | `InfGame` | close, tests present |
| `CInfCreature` | `InfCreature` | close, much recent logic |
| `CInfChr` | `InfChr` | close |
| `CInfTlk` | `InfTlk` | close |
| `CInf2DA` | `Inf2DA` | close |
| `CInfBam` | `InfBam` | close |
| `CValueList` | `ValueList` | different format |
| `CSpellBitmaps` | `SpellBitmaps` | wired to spell and item browser dialogs |
| `CPalImageList` | missing | gap |

### 18.3 UI

| eekeeper-qt | py-eekeeper | Python state |
|---|---|---|
| `EEKeeperWindow` | `MainWindow` | simpler |
| `SavedGameWidget` | `SavedGameWidget` | close, NPCs better marked |
| `CharacterSheetWidget` | `CharacterSheetWidget` | close for main fields |
| `InventoryTab` | `InventoryTab` | Python more editable |
| `SpellTab` | `SpellTab` | Python more editable |
| `MemorizationTab` | `MemorizationTab` | close |
| `ProficienciesTab` | `ProficienciesTab` | close |
| `SpellBrowserWidget` | `SpellBrowserDialog` | functional with icons |
| `ItemBrowserWidget` | `ItemBrowserDialog` | functional with icons |
| `ValueListDialog` | present but orphaned | missing from menu |
| `SaveGameNameDialog` | wired through Save As | parity |
| — | `GameTab` | dedicated party tab |
| — | `AffectsTab` | full affects editor |
| — | `GlobalsEditorDialog` | full table editor |
| — | `JournalEditorDialog` | full entry editor |
| — | `PortraitBrowserDialog` | grid thumbnail browser |
| — | `SettingsDialog` | 4-tab config editor |
| — | `AffectEditDialog` | 18-field editor |
| `InstallationDirectory` | `InstallationDialog` | Python more practical |

---

## 19. Functional Parity Matrix

| Feature | Qt | Python | Verdict |
|---|---|---|---|
| Open save | Yes | Yes | Parity |
| Save game | Yes | Yes | Parity |
| Save As | Yes | Yes | Parity |
| Edit main stats | Yes | Yes | Parity |
| Edit known spells | Partial | Yes | Python better wired |
| Edit memorization | Yes | Yes | Partial parity |
| Edit proficiencies | Yes | Yes | Parity |
| Edit inventory UI | Read-only | Full browser | Python better |
| Edit generic affects | No UI | Full tab + edit dialog | Python better |
| Edit globals | No UI | Full dialog editor | Python better |
| Edit journal | No UI | Full dialog editor | Python better |
| Edit gold/reputation | Model only | Dedicated Game tab | Python better |
| Export CHR | Partial | Yes | Python better |
| Import CHR | Planned | Full integration into party | Python better |
| String finder | Yes | Yes | Parity |
| Item browser | Stub | Full dialog with icons | Python better |
| Spell browser | Stub | Full dialog with icons | Python better |
| Portrait browser | Not present | Full dialog with thumbnails | Python only |
| Settings dialog | Scattered options | 4-tab dialog | Python better |
| Toolbar | Planned | Functional with 6 actions | Python better |
| Auto-detect install | Stub | Yes | Python better |
| Automated tests | No | Yes | Python better |
| Windows | Yes | No | Qt better |
| Black Pits saves | Yes | Yes (dedicated tab) | Parity |
| Creature browser | Stub | Missing | Low parity |
| Local variables | No UI | Missing | Low parity |

---

## 20. Binary Non-Parity Risks

Even though the Python UI is already usable, the following points must be validated on real save games:

1. `BALDUR.GAM` round-trip without journal alteration;
2. CRE round-trip with affects, dual-class proficiencies, and speed;
3. preservation of memorized spells without known spell entries;
4. priest/wizard/innate write order;
5. equipped item and quantity behavior;
6. `override/` priority for modded resources;
7. BG:EE / BG2:EE / IWD:EE compatibility beyond game-provided proficiency IDs;
8. `.CHR` import/export truly integrated into the party.

---

## 21. Convergence Recommendations

Most historical recommendations have been implemented. Remaining priorities:

1. ~~Wire existing dialogs~~ → Done.
2. ~~Complete CHR import into the GAM~~ → Done.
3. ~~Add a party/global editor~~ → Done (Game tab, globals editor, journal editor).
4. ~~Create Item/Spell browsers with BAM icons~~ → Done.
5. **Expose remaining advanced CRE fields**: speed, detailed AC, morale/fatigue/intoxication/luck.
6. **Add a creature browser** and **local variables editor**.
7. **Wire `ValueListDialog`** from the UI (currently still orphaned).
8. **Validate on real save games** and add integration tests with game fixtures.
9. **Fix documentation** (`README`, `SPEC`) to reflect 38 slots and the current feature state.
10. **Enforce spell limits** at add-time when the setting is active.
11. **Apply grid option** to all table widgets when the setting is toggled.

---

## 22. Conclusion

`py-eekeeper` is not a line-by-line translation of `eekeeper-qt`. It is a more modern, more testable, and more maintainable rewrite that has recovered the core format engine and now surpasses the legacy Qt version in most functional areas.

Compared with old Qt:

- **the binary engine is already close, and stronger on testability**;
- **the UI now covers more functional ground than the legacy Qt version** — including areas (affects editor, globals editor, journal editor, item/spell/portrait browsers) that were only stubs or empty tabs in `eekeeper-qt`;
- **Save As, CHR import integration, settings, and toolbar are all functional**;
- **remaining gaps are narrow**: creature browser, local variables, appearance tab, and Windows support.

In practice, `py-eekeeper` is now a more complete editor than `eekeeper-qt` ever was for most use cases. The legacy Qt project remains useful only as a reference for subtle binary behaviors and edge-case CRE fields not yet exposed in the Python UI.

---

## 23. Sources Analyzed

- `/tmp/eekeeper-qt` - commit `41b612e`
- `/home/grm/dev/py-eekeeper/py_eekeeper/`
- `/home/grm/dev/py-eekeeper/tests/`
- `/home/grm/dev/py-eekeeper/README.md`
- `/home/grm/dev/py-eekeeper/SPEC.md`
- `/home/grm/dev/py-eekeeper/pyproject.toml`

Report date: June 5, 2026.
