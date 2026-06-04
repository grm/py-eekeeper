"""Integration tests — full workflow from load to save."""

import os
import struct
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from py_eekeeper.formats.inf_game import InfGame, GAME_HEADER_SIZE, CHARINFO_SIZE
from py_eekeeper.formats.inf_creature import InfCreature, CreItem
from py_eekeeper.formats.inf_2da import Inf2DA
from py_eekeeper.formats.constants import INF_CRE_ST_WIZARD, INF_CRE_ST_PRIEST


def _make_test_save_dir() -> Path:
    """Create a temporary directory with a minimal BALDUR.GAM."""
    save_dir = Path(tempfile.mkdtemp())

    # Build CRE
    cre_data = bytearray(1024)
    cre_data[0:4] = b"CRE "
    cre_data[4:8] = b"V2.2"
    cre_data[0x33] = 1
    cre_data[0x238] = 18  # strength
    cre_data[0x23C] = 16  # dexterity
    struct.pack_into("<H", cre_data, 0x24, 75)  # current HP
    struct.pack_into("<H", cre_data, 0x26, 100)  # max HP
    struct.pack_into("<I", cre_data, 0x18, 250000)  # XP
    for off in [0x2A0, 0x2A8, 0x2B0, 0x2B8, 0x2BC, 0x2C4]:
        struct.pack_into("<I", cre_data, off, 724)
    for off in [0x2A4, 0x2AC, 0x2B4, 0x2C0, 0x2C8]:
        struct.pack_into("<I", cre_data, off, 0)

    # Build GAM
    header = bytearray(GAME_HEADER_SIZE)
    header[0:4] = b"GAME"
    header[4:8] = b"V2.0"
    struct.pack_into("<I", header, 0x14, 10000)  # gold
    header[0x44] = 180  # reputation (18*10)

    in_party_offset = GAME_HEADER_SIZE
    struct.pack_into("<I", header, 0x18, in_party_offset)
    struct.pack_into("<I", header, 0x1C, 1)
    struct.pack_into("<I", header, 0x24, in_party_offset + CHARINFO_SIZE)
    struct.pack_into("<I", header, 0x28, 0)
    struct.pack_into("<I", header, 0x2C, in_party_offset + CHARINFO_SIZE)
    struct.pack_into("<I", header, 0x30, 0)
    struct.pack_into("<I", header, 0x3C, 0)
    struct.pack_into("<I", header, 0x40, in_party_offset + CHARINFO_SIZE)
    struct.pack_into("<I", header, 0x58, in_party_offset + CHARINFO_SIZE + len(cre_data))

    charinfo = bytearray(CHARINFO_SIZE)
    struct.pack_into("<H", charinfo, 0x02, 0)
    cre_offset = in_party_offset + CHARINFO_SIZE
    struct.pack_into("<I", charinfo, 0x04, cre_offset)
    struct.pack_into("<I", charinfo, 0x08, len(cre_data))
    charinfo[0xC0:0xC0 + 6] = b"Minsc\x00"

    gam_data = bytearray()
    gam_data.extend(header)
    gam_data.extend(charinfo)
    gam_data.extend(cre_data)

    (save_dir / "BALDUR.GAM").write_bytes(gam_data)
    return save_dir


def test_full_edit_workflow():
    """Test: open save → edit character → save → re-read → verify."""
    save_dir = _make_test_save_dir()

    # Open
    game = InfGame()
    assert game.read(save_dir / "BALDUR.GAM")
    assert game.party_count == 1
    assert game.get_party_char_name(0) == "Minsc"
    assert game.party_gold == 10000

    # Get character
    cre = game.get_party_cre(0)
    assert cre.strength == 18
    assert cre.dexterity == 16
    assert cre.current_hp == 75
    assert cre.base_hp == 100

    # Modify stats
    cre.strength = 25
    cre.dexterity = 20
    cre.current_hp = 200
    cre.base_hp = 200
    cre.exp = 5000000
    game.party_gold = 99999

    # Add spells
    cre.add_known_spell(INF_CRE_ST_WIZARD, "SPWI101", 0)
    cre.add_known_spell(INF_CRE_ST_WIZARD, "SPWI205", 1)
    cre.add_known_spell(INF_CRE_ST_PRIEST, "SPPR101", 0)

    # Add items
    cre.set_item(0, CreItem(res_name="HELM07", quantity1=1, identified=True))
    cre.set_item(1, CreItem(res_name="PLAT05", quantity1=1, identified=True))

    # Save
    out_path = save_dir / "BALDUR.GAM"
    assert game.write(out_path)

    # Re-read
    game2 = InfGame()
    assert game2.read(out_path)
    assert game2.party_gold == 99999
    assert game2.party_count == 1

    cre2 = game2.get_party_cre(0)
    assert cre2.strength == 25
    assert cre2.dexterity == 20
    assert cre2.current_hp == 200
    assert cre2.base_hp == 200
    assert cre2.exp == 5000000

    # Spells
    assert cre2.get_known_spell_count(INF_CRE_ST_WIZARD) == 2
    assert cre2.get_known_spell_count(INF_CRE_ST_PRIEST) == 1
    wizard_spells = cre2.get_known_spells(INF_CRE_ST_WIZARD)
    assert any(s.name == "SPWI101" for s in wizard_spells)
    assert any(s.name == "SPWI205" for s in wizard_spells)

    # Items
    assert cre2.get_item(0).res_name == "HELM07"
    assert cre2.get_item(1).res_name == "PLAT05"
    assert cre2.get_item(2).res_name == ""

    # Cleanup
    import shutil
    shutil.rmtree(save_dir)


def test_ui_character_sheet_loading():
    """Test that the character sheet widget can load a creature."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    from py_eekeeper.ui.character_sheet import CharacterSheetWidget

    widget = CharacterSheetWidget()

    # Create a test creature
    cre_data = bytearray(1024)
    cre_data[0:4] = b"CRE "
    cre_data[4:8] = b"V2.2"
    cre_data[0x33] = 1
    cre_data[0x238] = 18  # str
    cre_data[0x23C] = 16  # dex
    cre_data[0x23D] = 14  # con
    cre_data[0x23A] = 12  # int
    cre_data[0x23B] = 10  # wis
    cre_data[0x23E] = 8   # cha
    struct.pack_into("<H", cre_data, 0x24, 50)
    struct.pack_into("<H", cre_data, 0x26, 80)
    for off in [0x2A0, 0x2A8, 0x2B0, 0x2B8, 0x2BC, 0x2C4]:
        struct.pack_into("<I", cre_data, off, 724)
    for off in [0x2A4, 0x2AC, 0x2B4, 0x2C0, 0x2C8]:
        struct.pack_into("<I", cre_data, off, 0)

    cre = InfCreature()
    cre.read(bytes(cre_data))

    # Load into widget
    widget.load_creature(cre)

    # Verify widget values reflect creature data
    assert widget._spin_str.value() == 18
    assert widget._spin_dex.value() == 16
    assert widget._spin_con.value() == 14
    assert widget._spin_int.value() == 12
    assert widget._spin_wis.value() == 10
    assert widget._spin_cha.value() == 8
    assert widget._spin_hp.value() == 50
    assert widget._spin_max_hp.value() == 80

    # Modify via widget and verify creature is updated
    widget._spin_str.setValue(25)
    assert cre.strength == 25
