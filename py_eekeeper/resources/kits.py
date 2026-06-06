"""Helpers for Infinity Engine kit identifiers."""

# Mage school bits in KITLIST / KIT.IDS before CRE shifting.
MAGE_SCHOOL_KIT_IDS = frozenset(1 << bit for bit in range(6, 14))


def encode_kit_ids_value(kit_id: int) -> int:
    """Convert a KITLIST/KIT.IDS value into the CRE kit field representation."""
    if kit_id < 0x10000:
        return (kit_id << 16) & 0xFFFFFFFF
    return kit_id & 0xFFFFFFFF


def normalize_kit_value(kit_value: int) -> int:
    """Repair unshifted mage-school kit values written by a broken encoder."""
    if 0 < kit_value < 0x4000 and kit_value in MAGE_SCHOOL_KIT_IDS:
        return (kit_value << 16) & 0xFFFFFFFF
    return kit_value & 0xFFFFFFFF
