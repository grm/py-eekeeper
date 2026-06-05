"""Batch party operations: heal all, memorize all spells, identify all items."""

from __future__ import annotations

from ..formats.inf_creature import InfCreature


def full_hp_all(creatures: list[InfCreature]) -> int:
    """Set current_hp = base_hp for all creatures. Returns count modified."""
    count = 0
    for cre in creatures:
        if cre.current_hp < cre.base_hp:
            cre.current_hp = cre.base_hp
            count += 1
    return count


def memorize_all_spells(creatures: list[InfCreature]) -> int:
    """Set memorized = True for all memorized spell slots. Returns count modified."""
    count = 0
    for cre in creatures:
        mem_spells = cre.get_memorized_spells()
        changed = False
        for ms in mem_spells:
            if not ms.memorized:
                ms.memorized = True
                changed = True
        if changed:
            cre.set_memorized_spells(mem_spells)
            count += 1
    return count


def identify_all_items(creatures: list[InfCreature]) -> int:
    """Set identified = True for all items. Returns count modified."""
    count = 0
    for cre in creatures:
        items = cre.get_items()
        changed = False
        for item in items:
            if item.res_name and not item.identified:
                item.identified = True
                changed = True
        if changed:
            cre.set_items(items)
            count += 1
    return count
