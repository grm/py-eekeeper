"""Tests for game-provided proficiency list handling."""

from py_eekeeper.resources.proficiencies import load_weapprof_items


def test_load_weapprof_items_uses_game_specific_ids():
    data = """2DA V1.0
0
                ID      NAME_REF        DESC_REF    FIGHTER
AXE             92      31116           34149       5
2HANDED         111     31135           34171       2
2WEAPON         114     31138           34176       3
EXTRA2          116     4294967296      4294967296  5
"""
    strings = {
        31116: "Axe",
        31135: "Two-Handed Weapon Style",
        31138: "Two Weapon Style",
    }

    items = load_weapprof_items(data, strings.get)

    assert [(item.index, item.name) for item in items] == [
        (92, "Axe"),
        (111, "Two-Handed Weapon Style"),
        (114, "Two Weapon Style"),
    ]


def test_load_weapprof_items_falls_back_to_row_name_without_tlk_string():
    data = """2DA V1.0
0
                ID      NAME_REF        DESC_REF
SINGLEWEAPON    113     31137           34174
"""

    items = load_weapprof_items(data, lambda _strref: "")

    assert [(item.index, item.name) for item in items] == [(113, "Singleweapon")]
