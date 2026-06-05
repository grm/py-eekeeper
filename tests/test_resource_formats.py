"""Tests for KEY, BIF, and TLK binary structures."""

import struct
import zlib

from py_eekeeper.formats.inf_bam import InfBam
from py_eekeeper.formats.inf_bif import InfBifFile
from py_eekeeper.formats.inf_chr import (
    CHR_DATA_LENGTH_OFFSET,
    CHR_DATA_START_OFFSET,
    CHR_HEADER_SIZE,
    InfChr,
)
from py_eekeeper.formats.inf_creature import InfCreature
from py_eekeeper.formats.inf_key import InfKey
from py_eekeeper.formats.inf_tlk import InfTlk
from py_eekeeper.resources.resource_manager import ResourceManager
from py_eekeeper.formats.constants import RESTYPE_BAM, RESTYPE_BMP, RESTYPE_BS


def _minimal_cre(version: bytes = b"V1.0") -> bytes:
    data = bytearray(724 + 80)
    data[0:4] = b"CRE "
    data[4:8] = version
    data[0x33] = 1
    for off in [0x2A0, 0x2A8, 0x2B0, 0x2B8, 0x2BC, 0x2C4]:
        struct.pack_into("<I", data, off, 724)
    for off in [0x2A4, 0x2AC, 0x2B4, 0x2C0, 0x2C8]:
        struct.pack_into("<I", data, off, 0)
    return bytes(data)


def test_key_bif_entry_reads_file_location(tmp_path):
    filename = b"DATA/test.bif\x00"
    bif_offset = 24
    res_offset = bif_offset + 12
    filename_offset = res_offset
    data = bytearray(filename_offset + len(filename))
    data[0:4] = b"KEY "
    data[4:8] = b"V1  "
    struct.pack_into("<IIII", data, 8, 1, 0, bif_offset, res_offset)
    struct.pack_into("<IIHH", data, bif_offset, 1234, filename_offset, len(filename), 7)
    data[filename_offset:filename_offset + len(filename)] = filename

    path = tmp_path / "chitin.key"
    path.write_bytes(data)

    key = InfKey()

    assert key.open(path)
    entry = key.get_bif_entry(0)
    assert entry is not None
    assert entry.file_location == 7
    assert entry.filename == "DATA/test.bif"


def test_key_normalizes_mac_colon_paths(tmp_path):
    filename = b":DATA:test.bif\x00"
    bif_offset = 24
    res_offset = bif_offset + 12
    filename_offset = res_offset
    data = bytearray(filename_offset + len(filename))
    data[0:4] = b"KEY "
    data[4:8] = b"V1  "
    struct.pack_into("<IIII", data, 8, 1, 0, bif_offset, res_offset)
    struct.pack_into("<IIHH", data, bif_offset, 1234, filename_offset, len(filename), 7)
    data[filename_offset:filename_offset + len(filename)] = filename

    path = tmp_path / "chitin.key"
    path.write_bytes(data)

    key = InfKey()

    assert key.open(path)
    assert key.get_bif_entry(0).filename == "/DATA:test.bif"


def test_bif_file_entry_uses_16_byte_stride(tmp_path):
    payload = b"ABCD"
    data = bytearray(20 + 16 + len(payload))
    data[0:4] = b"BIFF"
    data[4:8] = b"V1  "
    struct.pack_into("<III", data, 8, 1, 0, 20)
    struct.pack_into("<IIIH2s", data, 20, 3, 36, len(payload), 0x3ED, b"\x00\x00")
    data[36:40] = payload

    path = tmp_path / "test.bif"
    path.write_bytes(data)

    bif = InfBifFile()

    assert bif.open(path)
    entry = bif.get_entry(0x3ED, 3)
    assert entry is not None
    assert entry.offset == 36
    assert entry.size == 4


def test_bif_decompresses_qcompressed_bam_payload(tmp_path):
    bam_payload = b"BAM " + b"V1  " + b"\x00" * 16
    compressed = zlib.compress(bam_payload)
    wrapped = b"BAMC" + b"V1  " + struct.pack(">I", len(bam_payload)) + compressed
    data = bytearray(20 + 16 + len(wrapped))
    data[0:4] = b"BIFF"
    data[4:8] = b"V1  "
    struct.pack_into("<III", data, 8, 1, 0, 20)
    struct.pack_into("<IIIH2s", data, 20, 3, 36, len(wrapped), RESTYPE_BAM, b"\x00\x00")
    data[36:36 + len(wrapped)] = wrapped

    path = tmp_path / "icons.bif"
    path.write_bytes(data)

    bif = InfBifFile()
    assert bif.open(path)

    class Res:
        type = RESTYPE_BAM
        resource_index = 3

    assert bif.get_data(Res()) == bam_payload


def test_tlk_entry_field_order(tmp_path):
    text = "Hello".encode("utf-8")
    data = bytearray(18 + 26 + len(text))
    data[0:4] = b"TLK "
    data[4:8] = b"V1  "
    struct.pack_into("<HII", data, 8, 0, 1, 18 + 26)
    struct.pack_into("<H8sIIII", data, 18, 1, b"SOUND\x00\x00\x00", 2, 3, 0, len(text))
    data[44:44 + len(text)] = text

    path = tmp_path / "dialog.tlk"
    path.write_bytes(data)

    tlk = InfTlk()

    assert tlk.open(path)
    assert tlk.get_string(0) == "Hello"


def test_tlk_falls_back_to_latin1(tmp_path):
    text = "Café".encode("latin-1")
    data = bytearray(18 + 26 + len(text))
    data[0:4] = b"TLK "
    data[4:8] = b"V1  "
    struct.pack_into("<HII", data, 8, 0, 1, 18 + 26)
    struct.pack_into("<H8sIIII", data, 18, 1, b"\x00" * 8, 0, 0, 0, len(text))
    data[44:44 + len(text)] = text

    path = tmp_path / "dialog.tlk"
    path.write_bytes(data)

    tlk = InfTlk()

    assert tlk.open(path)
    assert tlk.get_string(0) == "Café"


def test_chr_accepts_v20_and_v21_and_writes_v20_by_default(tmp_path):
    cre = _minimal_cre()
    for version in (b"V2.0", b"V2.1"):
        data = bytearray(CHR_HEADER_SIZE + len(cre))
        data[0:4] = b"CHR "
        data[4:8] = version
        data[8:12] = b"Hero"
        struct.pack_into("<II", data, CHR_DATA_START_OFFSET, CHR_HEADER_SIZE, len(cre))
        data[CHR_HEADER_SIZE:] = cre

        path = tmp_path / f"{version.decode('ascii')}.chr"
        path.write_bytes(data)

        chr_file = InfChr()
        assert chr_file.read(path)
        assert chr_file.name == "Hero"

    creature = InfCreature()
    assert creature.read(cre)
    new_chr = InfChr()
    new_chr.set_creature(creature)
    out_path = tmp_path / "new.chr"
    assert new_chr.write(out_path)
    out_data = out_path.read_bytes()
    assert out_data[4:8] == b"V2.0"
    assert struct.unpack_from("<II", out_data, CHR_DATA_START_OFFSET) == (CHR_HEADER_SIZE, len(creature.write()))


def test_chr_rejects_unknown_version_unless_ignored(tmp_path):
    cre = _minimal_cre()
    data = bytearray(CHR_HEADER_SIZE + len(cre))
    data[0:4] = b"CHR "
    data[4:8] = b"V2.2"
    struct.pack_into("<II", data, CHR_DATA_START_OFFSET, CHR_HEADER_SIZE, len(cre))
    data[CHR_HEADER_SIZE:] = cre

    path = tmp_path / "bad.chr"
    path.write_bytes(data)

    assert not InfChr().read(path)
    assert InfChr(ignore_data_versions=True).read(path)


def test_bam_reads_header_offsets_and_uncompressed_frame():
    data_offset = 24 + 12 + 256 * 4
    data = bytearray(data_offset + 2)
    data[0:4] = b"BAM "
    data[4:8] = b"V1  "
    struct.pack_into("<HBBIII", data, 8, 1, 0, 0, 24, 36, 36)
    struct.pack_into("<HHhhI", data, 24, 2, 1, -3, 4, data_offset | 0x80000000)
    data[36 + 4:36 + 8] = bytes([30, 20, 10, 255])
    data[data_offset:data_offset + 2] = bytes([1, 0])

    bam = InfBam()

    assert bam.read(bytes(data))
    assert bam.get_frame_count() == 1
    assert bam.get_frame_dimensions(0) == (2, 1)
    assert bam.get_frame_pixels(0) == [(10, 20, 30, 255), (0, 0, 0, 0)]


def test_bam_rle_transparent_count_is_next_byte_plus_one():
    data_offset = 24 + 12 + 256 * 4
    data = bytearray(data_offset + 2)
    data[0:4] = b"BAM "
    data[4:8] = b"V1  "
    struct.pack_into("<HBBIII", data, 8, 1, 0, 0, 24, 36, 36)
    struct.pack_into("<HHhhI", data, 24, 2, 1, 0, 0, data_offset)
    data[data_offset:data_offset + 2] = bytes([0, 1])

    bam = InfBam()

    assert bam.read(bytes(data))
    assert bam.get_frame_pixels(0) == [(0, 0, 0, 0), (0, 0, 0, 0)]


def test_resource_manager_scans_bmp_and_bs_overrides(tmp_path):
    (tmp_path / "chitin.key").write_bytes(b"KEY V1  " + struct.pack("<IIII", 0, 0, 24, 24))
    override = tmp_path / "override"
    override.mkdir()
    (override / "PORTRT0.bmp").write_bytes(b"BMP")
    (override / "SCRIPT.bs").write_bytes(b"BS")

    manager = ResourceManager()

    assert manager.initialize(tmp_path)
    assert "PORTRT0" in manager.get_resource_list(RESTYPE_BMP)
    assert "SCRIPT" in manager.get_resource_list(RESTYPE_BS)
