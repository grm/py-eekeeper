"""Tests for game-provided auxiliary value lists."""

from py_eekeeper.resources.game_lists import load_effect_text_items, load_haterace_items


def test_load_haterace_items_matches_legacy_column_order():
    data = """2DA V1.0
0
                NAME_REF    VALUE
GOBLIN          1001        21
ORC             1002        22
"""
    strings = {1001: "Goblin", 1002: "Orc"}

    items = load_haterace_items(data, strings.get)

    assert [(item.index, item.name) for item in items] == [
        (21, "Goblin"),
        (22, "Orc"),
    ]


def test_load_effect_text_items_uses_numeric_row_names():
    data = """2DA V1.0
0
                STRREF
12              2001
233             2002
"""
    strings = {2001: "Damage", 2002: "Proficiency Modifier"}

    items = load_effect_text_items(data, strings.get)

    assert [(item.index, item.name) for item in items] == [
        (12, "Damage"),
        (233, "Proficiency Modifier"),
    ]
