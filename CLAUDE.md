# CLAUDE.md

## Language Policy

- Write all project documentation, reports, code comments, commit messages, pull request text, and agent-facing guidance in English by default.
- Use another language only when the user explicitly asks for it in that specific task.
- Keep existing code identifiers, file names, resource names, binary format names, and Infinity Engine terminology unchanged unless a change is required by the task.

## Project Context

`py-eekeeper` is a Python 3.11+ / PySide6 rewrite of the legacy C++/Qt `eekeeper-qt` save game editor for Infinity Engine Enhanced Edition games.

The main goal is not a line-by-line translation. The goal is a maintainable, tested Python implementation that preserves the important binary behavior of the original tool while avoiding legacy Qt technical debt.

Key modules:

- `py_eekeeper/formats/`: binary parsers and writers for Infinity Engine formats.
- `py_eekeeper/resources/`: game resource loading through KEY/BIF/override/TLK/2DA/BAM.
- `py_eekeeper/ui/`: PySide6 widgets and dialogs.
- `py_eekeeper/app.py`: application orchestration through `EEKeeperApp`.
- `py_eekeeper/config.py`: persistent settings.
- `tests/`: parser and workflow tests.

## Living Comparison Report

`COMPARAISON_EEKEEPER_QT_PYTHON.md` is a living project reference.

Agents must keep this file up to date automatically when they discover or implement changes that affect the comparison between the legacy Qt implementation and the Python rewrite.

Update the report when:

- a feature reaches parity with `eekeeper-qt`;
- a feature intentionally diverges from `eekeeper-qt`;
- a parser behavior changes for `GAM`, `CRE`, `CHR`, `KEY`, `BIF`, `TLK`, `2DA`, `BAM`, `IDS`, `ITM`, `SPL`, or `AFF`;
- UI coverage changes, especially inventory, spells, memorization, proficiencies, character sheet, save dialogs, browsers, globals, journal, affects, or CHR import/export;
- tests are added that validate legacy parity or real save round-trips;
- documentation in `README.md` or `SPEC.md` becomes inconsistent with the implementation;
- a previous assumption in the report is proven wrong.

When updating the report:

- keep it in English;
- preserve the existing structure unless a better structure is clearly useful;
- update both detailed sections and summary/parity tables when applicable;
- distinguish observed implementation state from intended future behavior;
- mention test evidence when available.

## Current Parity Notes

The Python implementation is already close to the legacy Qt behavior for core binary formats, especially:

- `BALDUR.GAM` read/write and offset rebuilding;
- embedded CRE handling;
- `CHR` parsing/export;
- KEY/BIF resource lookup;
- TLK string lookup;
- 2DA parsing, including encrypted cases;
- BAM decoding;
- affects and proficiencies at model level.

The main known gaps are UI and workflow coverage:

- no complete `Save As` flow;
- `.CHR` import parses the file but does not yet integrate it into the open save;
- no graphical Item Browser or Spell Browser;
- no generic affects editor;
- no globals, locals, or journal editor;
- no complete party/global editor for gold and reputation;
- `SpellBitmaps` exists but icons are not broadly wired into the UI;
- `ValueListDialog` and `SaveGameNameDialog` exist but are not fully wired;
- Windows support is not documented for the Python rewrite.

## Engineering Guidelines

- Prefer the existing architecture over new abstractions: `formats` for binary structures, `resources` for game data, `ui` for widgets, `app.py` for orchestration.
- Treat binary compatibility as a first-class requirement. Be especially careful with offsets, structure sizes, ordering, unknown bytes, and round-trip preservation.
- Preserve unknown or unedited binary blocks unless there is a strong reason not to.
- Avoid copying legacy Qt bugs. Use `eekeeper-qt` as a behavioral reference, not as an unquestioned source of truth.
- Keep UI changes aligned with model capabilities. If a model feature exists but is not exposed, prefer wiring it cleanly rather than duplicating logic in widgets.
- Do not invent compatibility shims for unfinished branch-local behavior. If a local implementation is wrong and not a shipped public interface, replace it cleanly.
- Prefer tests for parser and writer changes. Add focused round-trip tests for any binary format change.
- For UI changes, test the underlying model behavior even when full GUI automation is not practical.

## Known Documentation Drift

`README.md` and `SPEC.md` may describe intended behavior rather than the current implementation.

Known drift to watch:

- inventory slot count is described as 39 in places, while the current implementation is aligned around 38 useful slots;
- `spell_browser.py`, `item_browser.py`, `pal_image_list.py`, and `data/kits.dat` are mentioned in the specification but are not present in the current implementation;
- character import is documented more strongly than the current behavior supports;
- `Save As` and some toolbar behavior are described but not wired;
- class-based proficiency filtering is described but not observed.

When changing code or docs in these areas, reconcile the implementation and documentation together when practical.

## Testing Notes

- Use `pytest` for the Python test suite.
- Parser changes should include synthetic binary tests and, when possible, round-trip tests.
- Real save/resource fixtures are still a desired validation layer for full parity.
- A UI integration test may fail in environments without `PySide6`; distinguish dependency failures from application behavior failures.

## Legacy Reference

The legacy reference used for the current comparison was `Goddard/eekeeper-qt` at commit `41b612e`.

If future work depends on legacy behavior, inspect the relevant original C++/Qt code before assuming details from memory or from the specification.
