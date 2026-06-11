"""Small ITM header reader for UI display metadata."""

import struct
from dataclasses import dataclass
from typing import Callable


ITEM_TYPE_NAMES = {
    0: "Misc",
    1: "Amulet",
    2: "Armor",
    3: "Belt",
    4: "Boots",
    5: "Arrows",
    6: "Gloves",
    7: "Helm",
    8: "Key",
    9: "Potion",
    10: "Ring",
    11: "Scroll",
    12: "Shield",
    13: "Food",
    14: "Bullets",
    15: "Bow",
    16: "Dagger",
    17: "Mace",
    18: "Sling",
    19: "Short Sword",
    20: "Sword",
    21: "Hammer",
    22: "Morning Star",
    23: "Flail",
    24: "Darts",
    25: "Axe",
    26: "Staff",
    27: "Crossbow",
    28: "Hand to Hand",
    29: "Spear",
    30: "Halberd",
    31: "Bolts",
    32: "Cloak",
    33: "Gold",
    34: "Gem",
    35: "Wand",
    36: "Container",
    37: "Book",
    38: "Familiar",
    39: "Tattoo",
    40: "Lens",
    43: "Misc2",
    44: "Club",
    46: "Misc3",
    47: "Long Bow",
    48: "Misc4",
    49: "Misc5",
    57: "Greatsword",
}

ITEM_EQUIPMENT_TYPES = {
    1, 2, 3, 4, 6, 7, 10, 12, 32,
}
ITEM_WEAPON_TYPES = {
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 44, 47, 57,
}
ITEM_AMMO_TYPES = {
    5, 14, 31,
}
ITEM_CONSUMABLE_TYPES = {
    9, 11, 13, 35,
}
ITEM_CONTAINER_TYPES = {
    8, 33, 34, 36, 37, 38,
}

ITEM_CATEGORY_NAMES = {
    "equipment": "Equipment",
    "weapon": "Weapons",
    "ammo": "Ammunition",
    "consumable": "Consumables",
    "container": "Containers / Quest",
    "misc": "Miscellaneous",
}


@dataclass(frozen=True)
class ItemInfo:
    """Display-oriented metadata extracted from an ITM header."""

    resource_name: str
    generic_name: str
    identified_name: str
    type_id: int | None
    type_name: str
    base_value: int | None
    max_stackable: int | None
    lore: int | None
    weight: int | None
    enchantment: int | None

    @property
    def display_name(self) -> str:
        return self.identified_name or self.generic_name or self.resource_name

    @property
    def category(self) -> str:
        return get_item_category(self.type_id)


def parse_item_info(
    resource_name: str,
    data: bytes,
    get_string: Callable[[int], str],
) -> ItemInfo:
    """Parse stable ITM header fields used by the legacy inventory browser."""

    generic_name = _read_tlk_name(data, 0x08, get_string)
    identified_name = _read_tlk_name(data, 0x0C, get_string)
    type_id = _unpack_optional("<H", data, 0x1C)
    type_name = ITEM_TYPE_NAMES.get(type_id, "Unknown") if type_id is not None else ""

    return ItemInfo(
        resource_name=resource_name.upper(),
        generic_name=generic_name,
        identified_name=identified_name,
        type_id=type_id,
        type_name=type_name,
        base_value=_unpack_optional("<I", data, 0x34),
        max_stackable=_unpack_optional("<H", data, 0x38),
        lore=_unpack_optional("<H", data, 0x42),
        weight=_unpack_optional("<I", data, 0x4C),
        enchantment=_unpack_optional("<I", data, 0x60),
    )


def get_item_category(type_id: int | None) -> str:
    if type_id in ITEM_EQUIPMENT_TYPES:
        return "equipment"
    if type_id in ITEM_WEAPON_TYPES:
        return "weapon"
    if type_id in ITEM_AMMO_TYPES:
        return "ammo"
    if type_id in ITEM_CONSUMABLE_TYPES:
        return "consumable"
    if type_id in ITEM_CONTAINER_TYPES:
        return "container"
    return "misc"


def _read_tlk_name(data: bytes, offset: int, get_string: Callable[[int], str]) -> str:
    strref = _unpack_optional("<I", data, offset)
    if strref is None or strref == 0xFFFFFFFF:
        return ""
    return get_string(strref) or ""


def _unpack_optional(fmt: str, data: bytes, offset: int) -> int | None:
    size = struct.calcsize(fmt)
    if len(data) < offset + size:
        return None
    return struct.unpack_from(fmt, data, offset)[0]
