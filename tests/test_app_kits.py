"""Tests for application-level kit value handling."""

from py_eekeeper.resources.kits import encode_kit_ids_value, normalize_kit_value


def test_encode_kit_ids_value_shifts_kitlist_values():
    assert encode_kit_ids_value(0x00000800) == 0x08000000
    assert encode_kit_ids_value(0x00000080) == 0x00800000
    assert encode_kit_ids_value(0x00004001) == 0x40010000
    assert encode_kit_ids_value(0x80000000) == 0x80000000


def test_normalize_kit_value_repairs_unshifted_mage_schools():
    assert normalize_kit_value(0x00800000) == 0x00800000
    assert normalize_kit_value(0x08000000) == 0x08000000
    assert normalize_kit_value(0x00000800) == 0x08000000
    assert normalize_kit_value(0x00000080) == 0x00800000
    assert normalize_kit_value(0x40010000) == 0x40010000
