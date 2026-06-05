"""Tests for game (BALDUR.GAM) parser."""

import struct
import tempfile
from pathlib import Path

from py_eekeeper.formats.inf_game import InfGame, GAME_HEADER_SIZE, CHARINFO_SIZE
from py_eekeeper.formats.constants import INF_MAX_CHARACTERS


def _make_minimal_gam() -> bytes:
    """Create a minimal valid BALDUR.GAM file."""
    # We need: header + 1 charinfo + 1 CRE
    cre_data = bytearray(1024)
    cre_data[0:4] = b"CRE "
    cre_data[4:8] = b"V2.2"
    cre_data[0x33] = 1  # eff_structure v2
    cre_data[0x238] = 15  # strength
    # Set all offsets to point to after header
    struct.pack_into("<I", cre_data, 0x2A0, 724)
    struct.pack_into("<I", cre_data, 0x2A4, 0)
    struct.pack_into("<I", cre_data, 0x2A8, 724)
    struct.pack_into("<I", cre_data, 0x2AC, 0)
    struct.pack_into("<I", cre_data, 0x2B0, 724)
    struct.pack_into("<I", cre_data, 0x2B4, 0)
    struct.pack_into("<I", cre_data, 0x2B8, 724)
    struct.pack_into("<I", cre_data, 0x2BC, 724)
    struct.pack_into("<I", cre_data, 0x2C0, 0)
    struct.pack_into("<I", cre_data, 0x2C4, 724)
    struct.pack_into("<I", cre_data, 0x2C8, 0)

    # Build game file
    header = bytearray(GAME_HEADER_SIZE)
    header[0:4] = b"GAME"
    header[4:8] = b"V2.0"

    # Gold
    struct.pack_into("<I", header, 0x18, 5000)

    # 1 character in party
    in_party_offset = GAME_HEADER_SIZE
    cre_offset = in_party_offset + CHARINFO_SIZE
    end_offset = cre_offset + len(cre_data)
    struct.pack_into("<I", header, 0x20, in_party_offset)
    struct.pack_into("<I", header, 0x24, 1)

    # 0 out of party
    struct.pack_into("<I", header, 0x30, end_offset)
    struct.pack_into("<I", header, 0x34, 0)

    # No globals
    struct.pack_into("<I", header, 0x38, end_offset)
    struct.pack_into("<I", header, 0x3C, 0)

    # No journal
    struct.pack_into("<I", header, 0x4C, 0)
    struct.pack_into("<I", header, 0x50, end_offset)

    # Reputation (14 * 10 = 140)
    header[0x54] = 140

    # Build charinfo
    charinfo = bytearray(CHARINFO_SIZE)
    struct.pack_into("<H", charinfo, 0x02, 0)  # party position 0
    struct.pack_into("<I", charinfo, 0x04, cre_offset)
    struct.pack_into("<I", charinfo, 0x08, len(cre_data))
    # Name
    name = b"TestChar"
    charinfo[0xC0:0xC0 + len(name)] = name

    result = bytearray()
    result.extend(header)
    result.extend(charinfo)
    result.extend(cre_data)

    return bytes(result)


def test_read_basic():
    data = _make_minimal_gam()

    with tempfile.NamedTemporaryFile(suffix=".GAM", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name

    game = InfGame()
    assert game.read(path) is True
    assert game.party_count == 1
    assert game.out_of_party_count == 0
    assert game.party_gold == 5000
    assert game.party_reputation == 14
    assert game.get_party_char_name(0) == "TestChar"

    Path(path).unlink()


def test_read_cre():
    data = _make_minimal_gam()

    with tempfile.NamedTemporaryFile(suffix=".GAM", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name

    game = InfGame()
    game.read(path)

    cre = game.get_party_cre(0)
    assert cre is not None
    assert cre.strength == 15

    Path(path).unlink()


def test_modify_and_write():
    data = _make_minimal_gam()

    with tempfile.NamedTemporaryFile(suffix=".GAM", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name

    game = InfGame()
    game.read(path)

    game.party_gold = 99999
    cre = game.get_party_cre(0)
    cre.strength = 25

    # Write to a new file
    out_path = path + ".out"
    assert game.write(out_path) is True

    # Read back
    game2 = InfGame()
    assert game2.read(out_path)
    assert game2.party_gold == 99999
    assert game2.get_party_cre(0).strength == 25
    assert not game.has_changed()

    Path(path).unlink()
    Path(out_path).unlink()


def test_game_header_size_matches_eekeeper_qt():
    assert GAME_HEADER_SIZE == 0xB4


def test_party_char_name_updates_raw_charinfo():
    data = _make_minimal_gam()

    with tempfile.NamedTemporaryFile(suffix=".GAM", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name

    game = InfGame()
    assert game.read(path)
    game.set_party_char_name(0, "Ilya")

    out_path = path + ".out"
    assert game.write(out_path)
    out_data = Path(out_path).read_bytes()
    charinfo_offset = struct.unpack_from("<I", out_data, 0x20)[0]

    assert out_data[charinfo_offset + 0xC0:charinfo_offset + 0xC5] == b"Ilya\x00"

    Path(path).unlink()
    Path(out_path).unlink()


def test_invalid_file():
    game = InfGame()
    assert game.read("/nonexistent/path.GAM") is False

    with tempfile.NamedTemporaryFile(suffix=".GAM", delete=False) as f:
        f.write(b"NOT A GAME FILE")
        f.flush()
        path = f.name

    assert game.read(path) is False
    Path(path).unlink()


def test_game_version_rejection_and_ignore_flag():
    data = bytearray(_make_minimal_gam())
    data[4:8] = b"V9.9"

    with tempfile.NamedTemporaryFile(suffix=".GAM", delete=False) as f:
        f.write(data)
        f.flush()
        path = f.name

    strict = InfGame()
    ignored = InfGame(ignore_data_versions=True)

    assert strict.read(path) is False
    assert ignored.read(path) is True

    Path(path).unlink()
