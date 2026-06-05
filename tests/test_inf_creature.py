"""Tests for creature parser."""

import struct
from py_eekeeper.formats.inf_affect import AFF_V1_SIZE, AFF_V2_SIZE, InfAffect
from py_eekeeper.formats.inf_creature import InfCreature, KnownSpell, MemInfo, CreItem, ProfData
from py_eekeeper.formats.constants import (
    AFF_TYPE_SPELL,
    AFF_TYPE_PROF,
    CRE_STAT_DEAD,
    INF_CRE_ST_INNATE,
    INF_CRE_ST_WIZARD,
    INF_CRE_ST_PRIEST,
    INF_NUM_ITEMSLOTS,
)


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


def test_version_rejection_and_ignore_flag():
    data = bytearray(_make_minimal_cre())
    data[4:8] = b"V9.9"

    strict = InfCreature()
    ignored = InfCreature(ignore_data_versions=True)

    assert strict.read(bytes(data)) is False
    assert ignored.read(bytes(data)) is True


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


def test_equipment_slots_roundtrip():
    cre = InfCreature()
    assert cre.read(_make_minimal_cre())

    cre.set_item(2, CreItem(res_name="SHLD15", quantity1=0, identified=True))
    cre.set_item(9, CreItem(res_name="SW1H04", quantity1=1, identified=True))
    cre.set_item(13, CreItem(res_name="AROW01", quantity1=20, identified=True))
    written = cre.write()

    cre2 = InfCreature()
    assert cre2.read(written)

    assert cre2.get_item(0).res_name == ""
    assert cre2.get_item(1).res_name == ""
    assert cre2.get_item(2).res_name == "SHLD15"
    assert cre2.get_item(9).res_name == "SW1H04"
    assert cre2.get_item(13).res_name == "AROW01"


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


def test_spell_type_constants_match_cre_format():
    assert INF_CRE_ST_PRIEST == 0
    assert INF_CRE_ST_WIZARD == 1
    assert INF_CRE_ST_INNATE == 2


def test_meminfo_binary_order_matches_cre_format():
    cre = InfCreature()
    assert cre.read(_make_minimal_cre())
    cre.set_memorization_info([
        MemInfo(
            type=INF_CRE_ST_PRIEST,
            level=2,
            num_memorizable=3,
            num_memorized=4,
        )
    ])

    written = cre.write()
    mem_info_offset = struct.unpack_from("<I", written, 0x2A8)[0]
    level, num1, num2, spell_type = struct.unpack_from("<HHHH", written, mem_info_offset)

    assert (level, num1, num2, spell_type) == (2, 3, 4, INF_CRE_ST_PRIEST)


def test_empty_cre_offsets_match_eekeeper_qt():
    cre = InfCreature()
    assert cre.read(_make_minimal_cre())

    written = cre.write()

    assert struct.unpack_from("<I", written, 0x2A0)[0] == 0
    assert struct.unpack_from("<I", written, 0x2A8)[0] == 0
    assert struct.unpack_from("<I", written, 0x2B0)[0] == 0
    assert struct.unpack_from("<I", written, 0x2BC)[0] == 0
    assert struct.unpack_from("<I", written, 0x2C4)[0] == 0
    assert struct.unpack_from("<I", written, 0x2B8)[0] == 724


def test_dead_creature_writes_zero_current_hp():
    cre = InfCreature()
    assert cre.read(_make_minimal_cre())
    cre.current_hp = 42
    cre.state_flags = CRE_STAT_DEAD

    written = cre.write()

    assert struct.unpack_from("<H", written, 0x24)[0] == 0


def test_affect_is_264_byte_inf_aff():
    raw = bytearray(AFF_V2_SIZE)
    struct.pack_into("<II", raw, 8, AFF_TYPE_PROF, 2)
    struct.pack_into("<ii", raw, 20, 5, 89)
    struct.pack_into("<I", raw, 28, 9)
    struct.pack_into("<HH", raw, 36, 100, 0)

    aff = InfAffect.from_bytes_v2(bytes(raw))

    assert aff.opcode == AFF_TYPE_PROF
    assert aff.target_type == 2
    assert aff.parameter1 == 5
    assert aff.parameter2 == 89
    assert aff.to_bytes_v2()[8:32] == bytes(raw)[8:32]


def test_effect_v1_roundtrip_uses_48_byte_layout():
    aff = InfAffect(
        opcode=12,
        target_type=2,
        power=3,
        parameter1=123,
        parameter2=456,
        timing_mode=9,
        dispel_type=1,
        duration=789,
        probability1=80,
        probability2=20,
        resource="SPWI101",
        dice_thrown=2,
        dice_sides=6,
        saving_throw_type=4,
        saving_throw_bonus=-2,
        special=99,
    )

    raw = aff.to_bytes_v1()
    reread = InfAffect.from_bytes_v1(raw)

    assert len(raw) == AFF_V1_SIZE
    assert reread.opcode == aff.opcode
    assert reread.parameter1 == aff.parameter1
    assert reread.parameter2 == aff.parameter2
    assert reread.resource == aff.resource
    assert reread.saving_throw_bonus == aff.saving_throw_bonus


def test_proficiencies_use_aff_type_prof():
    cre = InfCreature()
    assert cre.read(_make_minimal_cre())

    cre.set_profs([ProfData(prof_id=89, value=3)])
    profs = cre.get_profs()

    assert profs == [ProfData(prof_id=89, value=3)]

    written = cre.write()
    affects_offset = struct.unpack_from("<I", written, 0x2C4)[0]
    assert struct.unpack_from("<I", written, affects_offset + 8)[0] == AFF_TYPE_PROF
    assert struct.unpack_from("<i", written, affects_offset + 20)[0] == 3
    assert struct.unpack_from("<i", written, affects_offset + 24)[0] == 89


def test_speed_uses_spcl812_affect_and_is_filtered_from_general_affects():
    cre = InfCreature()
    assert cre.read(_make_minimal_cre())

    normal_aff = InfAffect(opcode=42, parameter1=1)
    cre.set_affects([normal_aff])
    cre.set_profs([ProfData(prof_id=89, value=2)])
    cre.set_speed(7)

    assert cre.get_speed() == 7
    assert cre.get_affects() == [normal_aff]

    written = cre.write()
    reread = InfCreature()
    assert reread.read(written)

    assert reread.get_speed() == 7
    assert reread.get_affects()[0].opcode == 42

    raw_affects_offset = struct.unpack_from("<I", written, 0x2C4)[0]
    raw_affects_count = struct.unpack_from("<I", written, 0x2C8)[0]
    raw_affects = [
        written[raw_affects_offset + i * AFF_V2_SIZE:raw_affects_offset + (i + 1) * AFF_V2_SIZE]
        for i in range(raw_affects_count)
    ]
    assert any(struct.unpack_from("<I", raw, 8)[0] == AFF_TYPE_SPELL and raw[140:147] == b"SPCL812" for raw in raw_affects)

    reread.set_speed(0)
    assert reread.get_speed() == 0
