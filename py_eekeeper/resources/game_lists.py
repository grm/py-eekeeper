"""Helpers for game-provided 2DA/IDS value lists."""

from collections.abc import Callable

from ..formats.inf_2da import Inf2DA
from .value_list import ValueItem


def parse_int(value: str) -> int | None:
    try:
        return int(value, 0)
    except (TypeError, ValueError):
        return None


def load_haterace_items(data: bytes | str, get_string: Callable[[int], str]) -> list[ValueItem]:
    """Build racial enemy choices from HATERACE.2DA."""
    table = Inf2DA()
    if not table.parse(data):
        return []

    name_ref_col = _first_existing_col(table, ("NAME_REF", "STRREF", "NAME"))
    value_col = _first_existing_col(table, ("ID", "IDS", "VALUE", "RACE"))
    if name_ref_col < 0 and table.cols >= 1:
        name_ref_col = 0
    if value_col < 0 and table.cols >= 2:
        value_col = 1
    if name_ref_col < 0 or value_col < 0:
        return []

    items: list[ValueItem] = []
    seen: set[int] = set()
    for row in range(table.rows):
        value = parse_int(table.get_value(row, value_col))
        strref = parse_int(table.get_value(row, name_ref_col))
        if value is None or strref is None or value in seen:
            continue

        name = get_string(strref) if 0 < strref < 0xFFFFFFFF else ""
        if not name:
            name = table.get_row_name(row).replace("_", " ").title()
        if not name:
            continue

        items.append(ValueItem(index=value, name=name))
        seen.add(value)

    return items


def load_effect_text_items(data: bytes | str, get_string: Callable[[int], str]) -> list[ValueItem]:
    """Build effect opcode labels from an opcode-name 2DA such as EFFTEXT."""
    table = Inf2DA()
    if not table.parse(data):
        return []

    opcode_col = _first_existing_col(table, ("ID", "IDS", "OPCODE", "EFFECT", "VALUE"))
    name_ref_col = _first_existing_col(table, ("NAME_REF", "STRREF", "NAME", "TITLE"))

    items: list[ValueItem] = []
    seen: set[int] = set()
    for row in range(table.rows):
        opcode = parse_int(table.get_row_name(row)) if opcode_col < 0 else parse_int(table.get_value(row, opcode_col))
        if opcode is None or opcode in seen:
            continue

        name = ""
        if name_ref_col >= 0:
            strref_or_name = table.get_value(row, name_ref_col)
            strref = parse_int(strref_or_name)
            if strref is not None and 0 < strref < 0xFFFFFFFF:
                name = get_string(strref)
            elif strref is None:
                name = strref_or_name
        if not name:
            name = table.get_row_name(row).replace("_", " ").title()

        items.append(ValueItem(index=opcode, name=name))
        seen.add(opcode)

    return items


def _first_existing_col(table: Inf2DA, names: tuple[str, ...]) -> int:
    for name in names:
        col = table.find_col(name)
        if col >= 0:
            return col
    return -1
