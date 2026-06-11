"""Tests for application-level item list handling."""

import struct

from py_eekeeper.app import EEKeeperApp
from py_eekeeper.formats.constants import RESTYPE_ITM
from py_eekeeper.resources.resource_manager import ResourceManager
from py_eekeeper.resources.item_info import get_item_category


def _make_itm_data(strref: int = 12345) -> bytes:
    data = bytearray(12)
    struct.pack_into("<I", data, 8, strref)
    return bytes(data)


def _make_full_itm_data() -> bytes:
    data = bytearray(0x64)
    struct.pack_into("<I", data, 0x08, 100)
    struct.pack_into("<I", data, 0x0C, 101)
    struct.pack_into("<H", data, 0x1C, 20)
    struct.pack_into("<I", data, 0x34, 250)
    struct.pack_into("<H", data, 0x38, 1)
    struct.pack_into("<H", data, 0x42, 15)
    struct.pack_into("<I", data, 0x4C, 7)
    struct.pack_into("<I", data, 0x60, 2)
    return bytes(data)


def test_load_items_populates_value_list_from_game_resources(tmp_path):
    (tmp_path / "chitin.key").write_bytes(b"KEY V1  " + struct.pack("<IIII", 0, 0, 24, 24))
    override = tmp_path / "override"
    override.mkdir()
    (override / "SWOR01.itm").write_bytes(_make_itm_data())
    (override / "SHLD01.itm").write_bytes(_make_itm_data(54321))

    manager = ResourceManager()
    assert manager.initialize(tmp_path)

    app = EEKeeperApp()
    app.resource_manager = manager
    app.tlk = type("TlkStub", (), {"get_string": lambda _self, _ref: ""})()
    app._load_items()

    assert app.vl_items.count == 2
    assert list(app.iter_items()) == [
        ("SHLD01", "SHLD01"),
        ("SWOR01", "SWOR01"),
    ]


def test_has_item_checks_resource_manager(tmp_path):
    (tmp_path / "chitin.key").write_bytes(b"KEY V1  " + struct.pack("<IIII", 0, 0, 24, 24))
    override = tmp_path / "override"
    override.mkdir()
    (override / "RING01.itm").write_bytes(_make_itm_data())

    manager = ResourceManager()
    assert manager.initialize(tmp_path)

    app = EEKeeperApp()
    app.resource_manager = manager

    assert app.has_item("RING01")
    assert app.has_item("ring01")
    assert not app.has_item("MISSING")
    assert not app.has_item("")


def test_get_item_info_reads_display_fields(tmp_path):
    (tmp_path / "chitin.key").write_bytes(b"KEY V1  " + struct.pack("<IIII", 0, 0, 24, 24))
    override = tmp_path / "override"
    override.mkdir()
    (override / "SWOR01.itm").write_bytes(_make_full_itm_data())

    manager = ResourceManager()
    assert manager.initialize(tmp_path)

    strings = {100: "Long Sword", 101: "Varscona"}
    app = EEKeeperApp()
    app.resource_manager = manager
    app.tlk = type("TlkStub", (), {"get_string": lambda _self, ref: strings.get(ref, "")})()

    info = app.get_item_info("swor01")

    assert info is not None
    assert info.resource_name == "SWOR01"
    assert info.generic_name == "Long Sword"
    assert info.identified_name == "Varscona"
    assert info.display_name == "Varscona"
    assert info.type_name == "Sword"
    assert info.base_value == 250
    assert info.max_stackable == 1
    assert info.lore == 15
    assert info.weight == 7
    assert info.enchantment == 2


def test_item_type_categories_cover_browser_filters():
    assert get_item_category(2) == "equipment"
    assert get_item_category(20) == "weapon"
    assert get_item_category(5) == "ammo"
    assert get_item_category(9) == "consumable"
    assert get_item_category(36) == "container"
    assert get_item_category(0) == "misc"
    assert get_item_category(None) == "misc"
