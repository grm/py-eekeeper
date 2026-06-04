"""Tests for creature parser."""

import struct
from py_eekeeper.formats.inf_creature import InfCreature, KnownSpell, MemInfo, CreItem
from py_eekeeper.formats.constants import INF_CRE_ST_WIZARD, INF_CRE_ST_PRIEST, INF_NUM_ITEMSLOTS


def _make_minimal_cre() -> bytes:
    """Create a minimal valid CRE data blob."""
    # Header (724 bytes minimum)
    data = bytearray(1024)
    data[0:4] = b"CRE "
    data[4:8] = b"V2.2"
    # Set eff_structure = 1 (v2 effects)
    data[0x33] = 1
    # Set some basic stats
    data[0x238] = 18  # strength
    data[0x239] = 50  # str bonus
    data[0x23A] = 16  # intelligence
    data[0x23B] = 14  # wisdom
    data[0x23C] = 17  # dexterity
    data[0x23D] = 15  # constitution
    data[0x23E] = 12  # charisma
    data[0x234] = 10  # level first class
    # Current/base HP
    struct.pack_into("<H", data, 0x24, 50)
    struct.pack_into("<H", data, 0x26, 80)
    # XP
    struct.pack_into("<I", data, 0x18, 500000)

    # Offsets all point past the header with zero counts
    struct.pack_into("<I", data, 0x2A0, 724)  # known spells offset
    struct.pack_into("<I", data, 0x2A4, 0)    # known spells count
    struct.pack_into("<I", data, 0x2A8, 724)  # mem info offset
    struct.pack_into("<I", data, 0x2AC, 0)    # mem info count
    struct.pack_into("<I", data, 0x2B0, 724)  # mem spells offset
    struct.pack_into("<I", data, 0x2B4, 0)    # mem spells count
    struct.pack_into("<I", data, 0x2B8, 724)  # item slots offset
    struct.pack_into("<I", data, 0x2BC, 724)  # items offset
    struct.pack_into("<I", data, 0x2C0, 0)    # items count
    struct.pack_into("<I", data, 0x2C4, 724)  # affects offset
    struct.pack_into("<I", data, 0x2C8, 0)    # affects count

    return bytes(data)


def test_read_basic():
    data = _make_minimal_cre()
    cre = InfCreature()
    assert cre.read(data) is True
    assert cre.strength == 18
    assert cre.strength_bonus == 50
    assert cre.intelligence == 16
    assert cre.wisdom == 14
    assert cre.dexterity == 17
    assert cre.constitution == 15
    assert cre.charisma == 12
    assert cre.level_first_class == 10
    assert cre.current_hp == 50
    assert cre.base_hp == 80
    assert cre.exp == 500000


def test_read_invalid():
    cre = InfCreature()
    assert cre.read(b"") is False
    assert cre.read(b"NOTACRE!") is False


def test_modify_attributes():
    data = _make_minimal_cre()
    cre = InfCreature()
    cre.read(data)

    assert not cre.has_changed()
    cre.strength = 20
    assert cre.has_changed()
    assert cre.strength == 20

    cre.dexterity = 25
    assert cre.dexterity == 25


def test_write_roundtrip():
    data = _make_minimal_cre()
    cre = InfCreature()
    cre.read(data)

    cre.strength = 22
    cre.exp = 1000000

    written = cre.write()
    assert len(written) > 0

    # Read back
    cre2 = InfCreature()
    assert cre2.read(written)
    assert cre2.strength == 22
    assert cre2.exp == 1000000


def test_known_spells():
    data = _make_minimal_cre()
    cre = InfCreature()
    cre.read(data)

    assert cre.get_known_spell_count(INF_CRE_ST_WIZARD) == 0

    cre.add_known_spell(INF_CRE_ST_WIZARD, "SPWI103", 0)
    assert cre.get_known_spell_count(INF_CRE_ST_WIZARD) == 1

    cre.add_known_spell(INF_CRE_ST_WIZARD, "SPWI205", 1)
    assert cre.get_known_spell_count(INF_CRE_ST_WIZARD) == 2

    # No duplicates
    cre.add_known_spell(INF_CRE_ST_WIZARD, "SPWI103", 0)
    assert cre.get_known_spell_count(INF_CRE_ST_WIZARD) == 2

    # Remove
    cre.remove_known_spell(INF_CRE_ST_WIZARD, "SPWI103")
    assert cre.get_known_spell_count(INF_CRE_ST_WIZARD) == 1

    # Priest spells are separate
    cre.add_known_spell(INF_CRE_ST_PRIEST, "SPPR101", 0)
    assert cre.get_known_spell_count(INF_CRE_ST_PRIEST) == 1
    assert cre.get_known_spell_count(INF_CRE_ST_WIZARD) == 1


def test_items():
    data = _make_minimal_cre()
    cre = InfCreature()
    cre.read(data)

    items = cre.get_items()
    assert len(items) == INF_NUM_ITEMSLOTS
    assert items[0].res_name == ""

    cre.set_item(0, CreItem(res_name="HELM01", quantity1=1, identified=True))
    assert cre.get_item(0).res_name == "HELM01"
    assert cre.get_item(0).identified is True

    # Write and re-read
    written = cre.write()
    cre2 = InfCreature()
    cre2.read(written)
    assert cre2.get_item(0).res_name == "HELM01"


def test_spell_roundtrip():
    data = _make_minimal_cre()
    cre = InfCreature()
    cre.read(data)

    cre.add_known_spell(INF_CRE_ST_WIZARD, "SPWI103", 0)
    cre.add_known_spell(INF_CRE_ST_WIZARD, "SPWI218", 1)
    cre.add_known_spell(INF_CRE_ST_PRIEST, "SPPR101", 0)

    written = cre.write()
    cre2 = InfCreature()
    cre2.read(written)
    assert cre2.get_known_spell_count(INF_CRE_ST_WIZARD) == 2
    assert cre2.get_known_spell_count(INF_CRE_ST_PRIEST) == 1

    spells = cre2.get_known_spells(INF_CRE_ST_WIZARD)
    names = [s.name for s in spells]
    assert "SPWI103" in names
    assert "SPWI218" in names
