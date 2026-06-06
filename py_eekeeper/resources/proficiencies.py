"""Helpers for game-provided weapon proficiency lists."""

from collections.abc import Callable

from ..formats.inf_2da import Inf2DA
from .value_list import ValueItem


def _parse_int(value: str) -> int | None:
    try:
        return int(value, 0)
    except (TypeError, ValueError):
        return None


def load_weapprof_items(data: bytes | str, get_string: Callable[[int], str]) -> list[ValueItem]:
    """Build proficiency value items from WEAPPROF.2DA.

    WEAPPROF is the game-specific source of truth for proficiency IDs. This
    matters for IWD:EE, where the fighting style IDs differ from the old
    hard-coded table.
    """
    table = Inf2DA()
    if not table.parse(data):
        return []

    id_col = table.find_col("ID")
    name_col = table.find_col("NAME_REF")
    if id_col < 0 and table.cols > 1:
        id_col = 1
    if name_col < 0 and table.cols > 2:
        name_col = 2
    if id_col < 0:
        return []

    items: list[ValueItem] = []
    seen: set[int] = set()

    for row in range(table.rows):
        prof_id = _parse_int(table.get_value(row, id_col))
        if prof_id is None or prof_id < 89 or prof_id in seen:
            continue

        name = ""
        if name_col >= 0:
            strref = _parse_int(table.get_value(row, name_col))
            if strref is None or strref <= 0 or strref >= 0xFFFFFFFF:
                continue
            name = get_string(strref)

        if not name:
            name = table.get_row_name(row).replace("_", " ").title()
        if not name:
            continue

        items.append(ValueItem(index=prof_id, name=name))
        seen.add(prof_id)

    return items
