"""Parser for Infinity Engine CRE (Creature) data."""

import struct
from dataclasses import dataclass, field
from typing import Any

from .constants import (
    INF_NUM_ITEMSLOTS, INF_CRE_ST_INNATE, INF_CRE_ST_WIZARD,
    INF_CRE_ST_PRIEST, INF_CRE_SPELLTYPES, CRE_FLAG_HAS_DUALCLASS,
    CRE_STAT_DEAD, CRE_STAT_ACID_DEAD, CRE_STAT_FLAME_DEAD,
    CRE_STAT_EXPLODE_DEAD, CRE_STAT_STONE_DEAD, CRE_STAT_FROZEN_DEAD,
    AFF_TYPE_PROF, AFF_TYPE_SPELL, AFF_TARG_CRE,
    hi_tribble, lo_tribble, make_tribble,
)
from .inf_affect import InfAffect, AFF_V2_SIZE


CRE_HEADER_SIZE = 724


@dataclass
class KnownSpell:
    name: str
    level: int
    type: int
    times_memorized: int = 0
    times_can_cast: int = 0


@dataclass
class MemInfo:
    type: int
    level: int
    num_memorizable: int
    num_memorized: int
    offset: int = 0
    count: int = 0


@dataclass
class MemSpell:
    name: str
    memorized: bool


@dataclass
class CreItem:
    res_name: str = ""
    quantity1: int = 0
    quantity2: int = 0
    quantity3: int = 0
    identified: bool = False
    raw_data: bytes = b""


@dataclass
class ProfData:
    prof_id: int
    value: int
    second_value: int = 0


class InfCreature:
    """Parses and manipulates CRE (creature) data from save games."""

    def __init__(self, ignore_data_versions: bool = False, mem_spells_on_save: bool = False):
        self._header_data: bytearray = bytearray(CRE_HEADER_SIZE)
        self._known_spells: list[KnownSpell] = []
        self._mem_info: list[MemInfo] = []
        self._mem_spells: list[MemSpell] = []
        self._mem_but_not_known: list[MemSpell] = []
        self._item_slots: list[int] = [0xFFFF] * INF_NUM_ITEMSLOTS
        self._item_slots_unknown: bytes = b"\x00\x00\x00\x00"
        self._items: list[CreItem] = [CreItem() for _ in range(INF_NUM_ITEMSLOTS)]
        self._affects: list[InfAffect] = []
        self._has_changed: bool = False
        self._error: int = 0
        self._charinfo: Any = None
        self._eff_version: int = 0
        self._ignore_data_versions = ignore_data_versions
        self._mem_spells_on_save = mem_spells_on_save

    def read(self, data: bytes, charinfo: Any = None) -> bool:
        self._charinfo = charinfo

        if len(data) < 12:
            self._error = 1002
            return False

        sig = data[0:4]
        if sig != b"CRE ":
            self._error = 1003
            return False

        ver = data[4:8]
        if not self._ignore_data_versions and ver not in (b"V1.0", b"V2.2"):
            self._error = 1002
            return False

        header_size = min(CRE_HEADER_SIZE, len(data))
        self._header_data = bytearray(data[:header_size])
        if len(self._header_data) < CRE_HEADER_SIZE:
            self._header_data.extend(b"\x00" * (CRE_HEADER_SIZE - len(self._header_data)))

        self._eff_version = self._header_data[0x33]

        known_spells_offset = struct.unpack_from("<I", data, 0x2A0)[0]
        known_spells_count = struct.unpack_from("<I", data, 0x2A4)[0]
        mem_info_offset = struct.unpack_from("<I", data, 0x2A8)[0]
        mem_info_count = struct.unpack_from("<I", data, 0x2AC)[0]
        mem_spells_offset = struct.unpack_from("<I", data, 0x2B0)[0]
        mem_spells_count = struct.unpack_from("<I", data, 0x2B4)[0]
        items_slots_offset = struct.unpack_from("<I", data, 0x2B8)[0]
        items_offset = struct.unpack_from("<I", data, 0x2BC)[0]
        items_count = struct.unpack_from("<I", data, 0x2C0)[0]
        affects_offset = struct.unpack_from("<I", data, 0x2C4)[0]
        affects_count = struct.unpack_from("<I", data, 0x2C8)[0]

        # Read known spells
        self._known_spells = []
        for i in range(known_spells_count):
            off = known_spells_offset + i * 12
            if off + 12 > len(data):
                break
            name_raw = data[off:off + 8]
            name = name_raw.decode("latin-1").rstrip("\x00")
            level, spell_type = struct.unpack_from("<HH", data, off + 8)
            self._known_spells.append(KnownSpell(name=name, level=level, type=spell_type))

        # Read memorization info
        self._mem_info = []
        for i in range(mem_info_count):
            off = mem_info_offset + i * 16
            if off + 16 > len(data):
                break
            level, num_memorizable, num_memorized, mtype = struct.unpack_from(
                "<HHHH", data, off
            )
            m_offset, m_count = struct.unpack_from("<II", data, off + 8)
            self._mem_info.append(MemInfo(
                type=mtype, level=level,
                num_memorizable=num_memorizable, num_memorized=num_memorized,
                offset=m_offset, count=m_count,
            ))

        # Read memorized spells
        self._mem_spells = []
        for i in range(mem_spells_count):
            off = mem_spells_offset + i * 12
            if off + 12 > len(data):
                break
            name_raw = data[off:off + 8]
            name = name_raw.decode("latin-1").rstrip("\x00")
            memorized = struct.unpack_from("<I", data, off + 8)[0]
            self._mem_spells.append(MemSpell(name=name, memorized=bool(memorized)))

        self._sync_spell_data_from_mem_spells()

        # Read item slots
        self._item_slots = [0xFFFF] * INF_NUM_ITEMSLOTS
        if items_slots_offset + INF_NUM_ITEMSLOTS * 2 <= len(data):
            for i in range(INF_NUM_ITEMSLOTS):
                self._item_slots[i] = struct.unpack_from(
                    "<H", data, items_slots_offset + i * 2
                )[0]
            unknown_offset = items_slots_offset + INF_NUM_ITEMSLOTS * 2
            self._item_slots_unknown = data[unknown_offset:unknown_offset + 4]

        # CRE stores a compact item list plus a slot -> item-index table. Expose
        # items to the UI by equipment slot, like the original editor does.
        compact_items: list[CreItem] = []
        for i in range(min(items_count, INF_NUM_ITEMSLOTS)):
            off = items_offset + i * 20
            if off + 20 > len(data):
                break
            name_raw = data[off:off + 8]
            res_name = name_raw.decode("latin-1").rstrip("\x00")
            qty1, qty2, qty3 = struct.unpack_from("<HHH", data, off + 10)
            identified = data[off + 16]
            compact_items.append(CreItem(
                res_name=res_name,
                quantity1=qty1,
                quantity2=qty2,
                quantity3=qty3,
                identified=bool(identified),
                raw_data=data[off:off + 20],
            ))

        self._items = [CreItem() for _ in range(INF_NUM_ITEMSLOTS)]
        for slot_idx, item_idx in enumerate(self._item_slots):
            if item_idx < len(compact_items):
                self._items[slot_idx] = compact_items[item_idx]

        # Read affects
        self._affects = []
        aff_size = AFF_V2_SIZE
        for i in range(affects_count):
            off = affects_offset + i * aff_size
            if off + aff_size > len(data):
                break
            aff_data = data[off:off + aff_size]
            self._affects.append(InfAffect.from_bytes_v2(aff_data))

        self._has_changed = False
        return True

    def write(self) -> bytes:
        self._update_spell_info()

        result = bytearray()

        # Calculate offsets
        header_size = CRE_HEADER_SIZE
        known_spells_offset = header_size
        known_spells_size = len(self._known_spells) * 12
        mem_info_offset = known_spells_offset + known_spells_size
        mem_info_size = len(self._mem_info) * 16
        mem_spells_offset = mem_info_offset + mem_info_size
        mem_spells_size = len(self._mem_spells) * 12

        item_count = sum(1 for item in self._items if item.res_name)
        items_size = item_count * 20

        items_slots_offset = mem_spells_offset + mem_spells_size
        items_slots_size = INF_NUM_ITEMSLOTS * 2 + 4
        items_offset = items_slots_offset + items_slots_size

        aff_size = AFF_V2_SIZE
        affects_offset = items_offset + items_size

        # Update header offsets
        header = bytearray(self._header_data[:CRE_HEADER_SIZE])
        struct.pack_into("<I", header, 0x2A0, known_spells_offset if self._known_spells else 0)
        struct.pack_into("<I", header, 0x2A4, len(self._known_spells))
        struct.pack_into("<I", header, 0x2A8, mem_info_offset if self._mem_info else 0)
        struct.pack_into("<I", header, 0x2AC, len(self._mem_info))
        struct.pack_into("<I", header, 0x2B0, mem_spells_offset if self._mem_spells else 0)
        struct.pack_into("<I", header, 0x2B4, len(self._mem_spells))
        struct.pack_into("<I", header, 0x2B8, items_slots_offset)
        struct.pack_into("<I", header, 0x2BC, items_offset if item_count else 0)
        struct.pack_into("<I", header, 0x2C0, item_count)
        struct.pack_into("<I", header, 0x2C4, affects_offset if self._affects else 0)
        struct.pack_into("<I", header, 0x2C8, len(self._affects))

        death_flags = (
            CRE_STAT_DEAD | CRE_STAT_ACID_DEAD | CRE_STAT_FLAME_DEAD |
            CRE_STAT_EXPLODE_DEAD | CRE_STAT_STONE_DEAD | CRE_STAT_FROZEN_DEAD
        )
        if self.state_flags & death_flags:
            struct.pack_into("<H", header, 0x24, 0)

        result.extend(header)

        # Write known spells
        for spell in self._ordered_known_spells():
            name_bytes = spell.name.encode("latin-1")[:8].ljust(8, b"\x00")
            result.extend(name_bytes)
            result.extend(struct.pack("<HH", spell.level, spell.type))

        # Write memorization info
        for mi in self._mem_info:
            result.extend(struct.pack("<HHHH", mi.level, mi.num_memorizable,
                                      mi.num_memorized, mi.type))
            result.extend(struct.pack("<II", mi.offset, mi.count))

        # Write memorized spells
        for ms in self._mem_spells:
            name_bytes = ms.name.encode("latin-1")[:8].ljust(8, b"\x00")
            result.extend(name_bytes)
            result.extend(struct.pack("<I", 1 if ms.memorized else 0))

        # Write item slots and compact item list in the order used by CRE files.
        compact_items: list[CreItem] = []
        for i in range(INF_NUM_ITEMSLOTS):
            item = self._items[i]
            if item.res_name:
                result.extend(struct.pack("<H", len(compact_items)))
                compact_items.append(item)
            else:
                result.extend(struct.pack("<H", 0xFFFF))
        result.extend(self._item_slots_unknown[:4].ljust(4, b"\x00"))

        # Write items (only non-empty), preserving unknown bytes from the
        # original binary data when available (expiry timer at offset 8-9 and
        # flag bits at offset 17-19).
        for item in compact_items:
            if len(item.raw_data) >= 20:
                item_bytes = bytearray(item.raw_data[:20])
            else:
                item_bytes = bytearray(20)
            # Overlay fields that may have been edited:
            name_bytes = item.res_name.encode("latin-1")[:8].ljust(8, b"\x00")
            item_bytes[0:8] = name_bytes
            struct.pack_into("<HHH", item_bytes, 10, item.quantity1, item.quantity2, item.quantity3)
            item_bytes[16] = 1 if item.identified else 0
            result.extend(item_bytes)

        # Write affects
        for aff in self._affects:
            result.extend(aff.to_bytes_v2())

        return bytes(result)

    def _sync_spell_data_from_mem_spells(self):
        self._mem_but_not_known = []
        for spell in self._known_spells:
            spell.times_memorized = 0
            spell.times_can_cast = 0

        for mem_spell in self._mem_spells:
            known = self._find_known_spell(mem_spell.name)
            if known is None:
                self._mem_but_not_known.append(mem_spell)
                continue
            known.times_memorized += 1
            if mem_spell.memorized:
                known.times_can_cast += 1

    def _find_known_spell(self, name: str) -> KnownSpell | None:
        name_upper = name.upper()
        for spell in self._known_spells:
            if spell.name.upper() == name_upper:
                return spell
        return None

    def _ordered_known_spells(self) -> list[KnownSpell]:
        return [
            spell
            for spell_type in range(INF_CRE_SPELLTYPES)
            for spell in self._known_spells
            if spell.type == spell_type
        ]

    def _rebuild_mem_spells(self):
        mem_spells: list[MemSpell] = []
        for spell in self._ordered_known_spells():
            for i in range(spell.times_memorized):
                memorized = self._mem_spells_on_save or i < spell.times_can_cast
                mem_spells.append(MemSpell(name=spell.name, memorized=memorized))
        mem_spells.extend(MemSpell(name=s.name, memorized=True) for s in self._mem_but_not_known)
        self._mem_spells = mem_spells

    def _update_spell_info(self):
        known_unique: list[KnownSpell] = []
        seen: set[tuple[int, str]] = set()
        for spell in self._known_spells:
            key = (spell.type, spell.name.upper())
            if spell.type >= INF_CRE_SPELLTYPES or key in seen:
                continue
            seen.add(key)
            known_unique.append(spell)
        self._known_spells = known_unique

        for mi in self._mem_info:
            mi.offset = 0
            mi.count = 0

        for spell in self._known_spells:
            if spell.times_memorized <= 0:
                continue
            for mi in self._mem_info:
                if spell.type == mi.type and (spell.type == INF_CRE_ST_INNATE or spell.level == mi.level):
                    mi.count += spell.times_memorized

        for mem_spell in self._mem_but_not_known:
            for mi in self._mem_info:
                if mi.type == INF_CRE_ST_INNATE:
                    mi.count += 1
                    if mi.count > mi.num_memorizable:
                        mi.num_memorizable = mi.count
                        mi.num_memorized = mi.count

        spell_idx = 0
        for mi in self._mem_info:
            mi.offset = spell_idx
            spell_idx += mi.count

        self._rebuild_mem_spells()

    # --- Properties for creature attributes ---

    def _get_u8(self, offset: int) -> int:
        return self._header_data[offset]

    def _set_u8(self, offset: int, value: int):
        self._header_data[offset] = value & 0xFF
        self._has_changed = True

    def _get_i8(self, offset: int) -> int:
        return struct.unpack_from("<b", self._header_data, offset)[0]

    def _set_i8(self, offset: int, value: int):
        struct.pack_into("<b", self._header_data, offset, value)
        self._has_changed = True

    def _get_u16(self, offset: int) -> int:
        return struct.unpack_from("<H", self._header_data, offset)[0]

    def _set_u16(self, offset: int, value: int):
        struct.pack_into("<H", self._header_data, offset, value)
        self._has_changed = True

    def _get_i16(self, offset: int) -> int:
        return struct.unpack_from("<h", self._header_data, offset)[0]

    def _set_i16(self, offset: int, value: int):
        struct.pack_into("<h", self._header_data, offset, value)
        self._has_changed = True

    def _get_u32(self, offset: int) -> int:
        return struct.unpack_from("<I", self._header_data, offset)[0]

    def _set_u32(self, offset: int, value: int):
        struct.pack_into("<I", self._header_data, offset, value)
        self._has_changed = True

    def _get_str(self, offset: int, length: int) -> str:
        raw = self._header_data[offset:offset + length]
        return raw.decode("latin-1").rstrip("\x00")

    def _set_str(self, offset: int, length: int, value: str):
        encoded = value.encode("latin-1")[:length].ljust(length, b"\x00")
        self._header_data[offset:offset + length] = encoded
        self._has_changed = True

    # Signature & version
    @property
    def signature(self) -> str:
        return self._get_str(0, 4)

    @property
    def version(self) -> str:
        return self._get_str(4, 4)

    # Names (string references)
    @property
    def long_name_strref(self) -> int:
        return self._get_u32(0x08)

    @long_name_strref.setter
    def long_name_strref(self, value: int):
        self._set_u32(0x08, value)

    @property
    def short_name_strref(self) -> int:
        return self._get_u32(0x0C)

    @short_name_strref.setter
    def short_name_strref(self, value: int):
        self._set_u32(0x0C, value)

    # Flags
    @property
    def flags(self) -> int:
        return self._get_u32(0x10)

    @flags.setter
    def flags(self, value: int):
        self._set_u32(0x10, value)

    # Experience
    @property
    def exp_for_killing(self) -> int:
        return self._get_u32(0x14)

    @exp_for_killing.setter
    def exp_for_killing(self, value: int):
        self._set_u32(0x14, value)

    @property
    def exp(self) -> int:
        return self._get_u32(0x18)

    @exp.setter
    def exp(self, value: int):
        self._set_u32(0x18, value)

    @property
    def gold(self) -> int:
        return self._get_u32(0x1C)

    @gold.setter
    def gold(self, value: int):
        self._set_u32(0x1C, value)

    # State
    @property
    def state_flags(self) -> int:
        return self._get_u32(0x20)

    @state_flags.setter
    def state_flags(self, value: int):
        self._set_u32(0x20, value)

    # HP
    @property
    def current_hp(self) -> int:
        return self._get_u16(0x24)

    @current_hp.setter
    def current_hp(self, value: int):
        self._set_u16(0x24, value)

    @property
    def base_hp(self) -> int:
        return self._get_u16(0x26)

    @base_hp.setter
    def base_hp(self, value: int):
        self._set_u16(0x26, value)

    @property
    def animation_id(self) -> int:
        return self._get_u16(0x28)

    @animation_id.setter
    def animation_id(self, value: int):
        self._set_u16(0x28, value)

    # Colors
    @property
    def metal_color(self) -> int:
        return self._get_u8(0x2C)

    @metal_color.setter
    def metal_color(self, value: int):
        self._set_u8(0x2C, value)

    @property
    def minor_color(self) -> int:
        return self._get_u8(0x2D)

    @minor_color.setter
    def minor_color(self, value: int):
        self._set_u8(0x2D, value)

    @property
    def major_color(self) -> int:
        return self._get_u8(0x2E)

    @major_color.setter
    def major_color(self, value: int):
        self._set_u8(0x2E, value)

    @property
    def skin_color(self) -> int:
        return self._get_u8(0x2F)

    @skin_color.setter
    def skin_color(self, value: int):
        self._set_u8(0x2F, value)

    @property
    def leather_color(self) -> int:
        return self._get_u8(0x30)

    @leather_color.setter
    def leather_color(self, value: int):
        self._set_u8(0x30, value)

    @property
    def armor_color(self) -> int:
        return self._get_u8(0x31)

    @armor_color.setter
    def armor_color(self, value: int):
        self._set_u8(0x31, value)

    @property
    def hair_color(self) -> int:
        return self._get_u8(0x32)

    @hair_color.setter
    def hair_color(self, value: int):
        self._set_u8(0x32, value)

    # Effect structure version
    @property
    def eff_structure(self) -> int:
        return self._get_u8(0x33)

    # Portraits
    @property
    def small_portrait(self) -> str:
        return self._get_str(0x34, 8)

    @small_portrait.setter
    def small_portrait(self, value: str):
        self._set_str(0x34, 8, value)

    @property
    def large_portrait(self) -> str:
        return self._get_str(0x3C, 8)

    @large_portrait.setter
    def large_portrait(self, value: str):
        self._set_str(0x3C, 8, value)

    # Reputation & thief skills
    @property
    def reputation(self) -> int:
        return self._get_u8(0x44) // 10

    @reputation.setter
    def reputation(self, value: int):
        self._set_u8(0x44, min(value * 10, 200))

    @property
    def hide_in_shadows(self) -> int:
        return self._get_u8(0x45)

    @hide_in_shadows.setter
    def hide_in_shadows(self, value: int):
        self._set_u8(0x45, value)

    # AC
    @property
    def ac1(self) -> int:
        return self._get_i16(0x46)

    @ac1.setter
    def ac1(self, value: int):
        self._set_i16(0x46, value)

    @property
    def ac2(self) -> int:
        return self._get_i16(0x48)

    @ac2.setter
    def ac2(self, value: int):
        self._set_i16(0x48, value)

    @property
    def ac_mod_crushing(self) -> int:
        return self._get_i16(0x4A)

    @ac_mod_crushing.setter
    def ac_mod_crushing(self, value: int):
        self._set_i16(0x4A, value)

    @property
    def ac_mod_missile(self) -> int:
        return self._get_i16(0x4C)

    @ac_mod_missile.setter
    def ac_mod_missile(self, value: int):
        self._set_i16(0x4C, value)

    @property
    def ac_mod_piercing(self) -> int:
        return self._get_i16(0x4E)

    @ac_mod_piercing.setter
    def ac_mod_piercing(self, value: int):
        self._set_i16(0x4E, value)

    @property
    def ac_mod_slashing(self) -> int:
        return self._get_i16(0x50)

    @ac_mod_slashing.setter
    def ac_mod_slashing(self, value: int):
        self._set_i16(0x50, value)

    # Combat
    @property
    def thac0(self) -> int:
        return self._get_i8(0x52)

    @thac0.setter
    def thac0(self, value: int):
        self._set_i8(0x52, value)

    @property
    def attacks(self) -> int:
        return self._get_u8(0x53)

    @attacks.setter
    def attacks(self, value: int):
        self._set_u8(0x53, value)

    # Saving throws
    @property
    def save_death(self) -> int:
        return self._get_u8(0x54)

    @save_death.setter
    def save_death(self, value: int):
        self._set_u8(0x54, value)

    @property
    def save_wands(self) -> int:
        return self._get_u8(0x55)

    @save_wands.setter
    def save_wands(self, value: int):
        self._set_u8(0x55, value)

    @property
    def save_poly(self) -> int:
        return self._get_u8(0x56)

    @save_poly.setter
    def save_poly(self, value: int):
        self._set_u8(0x56, value)

    @property
    def save_breath(self) -> int:
        return self._get_u8(0x57)

    @save_breath.setter
    def save_breath(self, value: int):
        self._set_u8(0x57, value)

    @property
    def save_spells(self) -> int:
        return self._get_u8(0x58)

    @save_spells.setter
    def save_spells(self, value: int):
        self._set_u8(0x58, value)

    # Resistances
    @property
    def resist_fire(self) -> int:
        return self._get_u8(0x59)

    @resist_fire.setter
    def resist_fire(self, value: int):
        self._set_u8(0x59, value)

    @property
    def resist_cold(self) -> int:
        return self._get_u8(0x5A)

    @resist_cold.setter
    def resist_cold(self, value: int):
        self._set_u8(0x5A, value)

    @property
    def resist_electricity(self) -> int:
        return self._get_u8(0x5B)

    @resist_electricity.setter
    def resist_electricity(self, value: int):
        self._set_u8(0x5B, value)

    @property
    def resist_acid(self) -> int:
        return self._get_u8(0x5C)

    @resist_acid.setter
    def resist_acid(self, value: int):
        self._set_u8(0x5C, value)

    @property
    def resist_magic(self) -> int:
        return self._get_u8(0x5D)

    @resist_magic.setter
    def resist_magic(self, value: int):
        self._set_u8(0x5D, value)

    @property
    def resist_magic_fire(self) -> int:
        return self._get_u8(0x5E)

    @resist_magic_fire.setter
    def resist_magic_fire(self, value: int):
        self._set_u8(0x5E, value)

    @property
    def resist_magic_cold(self) -> int:
        return self._get_u8(0x5F)

    @resist_magic_cold.setter
    def resist_magic_cold(self, value: int):
        self._set_u8(0x5F, value)

    @property
    def resist_slashing(self) -> int:
        return self._get_u8(0x60)

    @resist_slashing.setter
    def resist_slashing(self, value: int):
        self._set_u8(0x60, value)

    @property
    def resist_crushing(self) -> int:
        return self._get_u8(0x61)

    @resist_crushing.setter
    def resist_crushing(self, value: int):
        self._set_u8(0x61, value)

    @property
    def resist_piercing(self) -> int:
        return self._get_u8(0x62)

    @resist_piercing.setter
    def resist_piercing(self, value: int):
        self._set_u8(0x62, value)

    @property
    def resist_missile(self) -> int:
        return self._get_u8(0x63)

    @resist_missile.setter
    def resist_missile(self, value: int):
        self._set_u8(0x63, value)

    # Thief skills
    @property
    def detect_illusions(self) -> int:
        return self._get_u8(0x64)

    @detect_illusions.setter
    def detect_illusions(self, value: int):
        self._set_u8(0x64, value)

    @property
    def set_traps(self) -> int:
        return self._get_u8(0x65)

    @set_traps.setter
    def set_traps(self, value: int):
        self._set_u8(0x65, value)

    @property
    def lore(self) -> int:
        return self._get_u8(0x66)

    @lore.setter
    def lore(self, value: int):
        self._set_u8(0x66, value)

    @property
    def open_locks(self) -> int:
        return self._get_u8(0x67)

    @open_locks.setter
    def open_locks(self, value: int):
        self._set_u8(0x67, value)

    @property
    def move_silently(self) -> int:
        return self._get_u8(0x68)

    @move_silently.setter
    def move_silently(self, value: int):
        self._set_u8(0x68, value)

    @property
    def find_traps(self) -> int:
        return self._get_u8(0x69)

    @find_traps.setter
    def find_traps(self, value: int):
        self._set_u8(0x69, value)

    @property
    def pick_pockets(self) -> int:
        return self._get_u8(0x6A)

    @pick_pockets.setter
    def pick_pockets(self, value: int):
        self._set_u8(0x6A, value)

    @property
    def fatigue(self) -> int:
        return self._get_u8(0x6B)

    @fatigue.setter
    def fatigue(self, value: int):
        self._set_u8(0x6B, value)

    @property
    def intoxication(self) -> int:
        return self._get_u8(0x6C)

    @intoxication.setter
    def intoxication(self, value: int):
        self._set_u8(0x6C, value)

    @property
    def luck(self) -> int:
        return self._get_u8(0x6D)

    @luck.setter
    def luck(self, value: int):
        self._set_u8(0x6D, value)

    # Levels
    @property
    def level_first_class(self) -> int:
        return self._get_u8(0x234)

    @level_first_class.setter
    def level_first_class(self, value: int):
        self._set_u8(0x234, value)

    @property
    def level_second_class(self) -> int:
        return self._get_u8(0x235)

    @level_second_class.setter
    def level_second_class(self, value: int):
        self._set_u8(0x235, value)

    @property
    def level_third_class(self) -> int:
        return self._get_u8(0x236)

    @level_third_class.setter
    def level_third_class(self, value: int):
        self._set_u8(0x236, value)

    @property
    def sex(self) -> int:
        return self._get_u8(0x237)

    @sex.setter
    def sex(self, value: int):
        self._set_u8(0x237, value)

    # Attributes
    @property
    def strength(self) -> int:
        return self._get_u8(0x238)

    @strength.setter
    def strength(self, value: int):
        self._set_u8(0x238, value)

    @property
    def strength_bonus(self) -> int:
        return self._get_u8(0x239)

    @strength_bonus.setter
    def strength_bonus(self, value: int):
        self._set_u8(0x239, value)

    @property
    def intelligence(self) -> int:
        return self._get_u8(0x23A)

    @intelligence.setter
    def intelligence(self, value: int):
        self._set_u8(0x23A, value)

    @property
    def wisdom(self) -> int:
        return self._get_u8(0x23B)

    @wisdom.setter
    def wisdom(self, value: int):
        self._set_u8(0x23B, value)

    @property
    def dexterity(self) -> int:
        return self._get_u8(0x23C)

    @dexterity.setter
    def dexterity(self, value: int):
        self._set_u8(0x23C, value)

    @property
    def constitution(self) -> int:
        return self._get_u8(0x23D)

    @constitution.setter
    def constitution(self, value: int):
        self._set_u8(0x23D, value)

    @property
    def charisma(self) -> int:
        return self._get_u8(0x23E)

    @charisma.setter
    def charisma(self, value: int):
        self._set_u8(0x23E, value)

    @property
    def morale(self) -> int:
        return self._get_u8(0x23F)

    @morale.setter
    def morale(self, value: int):
        self._set_u8(0x23F, value)

    @property
    def morale_break(self) -> int:
        return self._get_u8(0x240)

    @morale_break.setter
    def morale_break(self, value: int):
        self._set_u8(0x240, value)

    @property
    def racial_enemy(self) -> int:
        return self._get_u8(0x241)

    @racial_enemy.setter
    def racial_enemy(self, value: int):
        self._set_u8(0x241, value)

    @property
    def morale_recovery_time(self) -> int:
        return self._get_u16(0x242)

    @morale_recovery_time.setter
    def morale_recovery_time(self, value: int):
        self._set_u16(0x242, value)

    @property
    def kit(self) -> int:
        return self._get_u32(0x244)

    @kit.setter
    def kit(self, value: int):
        self._set_u32(0x244, value)

    # Scripts
    @property
    def override_script(self) -> str:
        return self._get_str(0x248, 8)

    @override_script.setter
    def override_script(self, value: str):
        self._set_str(0x248, 8, value)

    @property
    def class_script(self) -> str:
        return self._get_str(0x250, 8)

    @class_script.setter
    def class_script(self, value: str):
        self._set_str(0x250, 8, value)

    @property
    def race_script(self) -> str:
        return self._get_str(0x258, 8)

    @race_script.setter
    def race_script(self, value: str):
        self._set_str(0x258, 8, value)

    @property
    def general_script(self) -> str:
        return self._get_str(0x260, 8)

    @general_script.setter
    def general_script(self, value: str):
        self._set_str(0x260, 8, value)

    @property
    def default_script(self) -> str:
        return self._get_str(0x268, 8)

    @default_script.setter
    def default_script(self, value: str):
        self._set_str(0x268, 8, value)

    # IDS fields
    @property
    def enemy_ally(self) -> int:
        return self._get_u8(0x270)

    @enemy_ally.setter
    def enemy_ally(self, value: int):
        self._set_u8(0x270, value)

    @property
    def general_id(self) -> int:
        return self._get_u8(0x271)

    @general_id.setter
    def general_id(self, value: int):
        self._set_u8(0x271, value)

    @property
    def race(self) -> int:
        return self._get_u8(0x272)

    @race.setter
    def race(self, value: int):
        self._set_u8(0x272, value)

    @property
    def class_id(self) -> int:
        return self._get_u8(0x273)

    @class_id.setter
    def class_id(self, value: int):
        self._set_u8(0x273, value)

    @property
    def specific(self) -> int:
        return self._get_u8(0x274)

    @specific.setter
    def specific(self, value: int):
        self._set_u8(0x274, value)

    @property
    def gender(self) -> int:
        return self._get_u8(0x275)

    @gender.setter
    def gender(self, value: int):
        self._set_u8(0x275, value)

    @property
    def alignment(self) -> int:
        return self._get_u8(0x27B)

    @alignment.setter
    def alignment(self, value: int):
        self._set_u8(0x27B, value)

    # --- Spell methods ---

    def get_known_spells(self, spell_type: int) -> list[KnownSpell]:
        return [s for s in self._known_spells if s.type == spell_type]

    def get_known_spell_count(self, spell_type: int) -> int:
        return sum(1 for s in self._known_spells if s.type == spell_type)

    def add_known_spell(self, spell_type: int, name: str, level: int) -> bool:
        for s in self._known_spells:
            if s.name.upper() == name.upper() and s.type == spell_type:
                return False
        self._known_spells.append(KnownSpell(name=name.upper(), level=level, type=spell_type))
        self._has_changed = True
        return True

    def remove_known_spell(self, spell_type: int, name: str) -> bool:
        for i, s in enumerate(self._known_spells):
            if s.name.upper() == name.upper() and s.type == spell_type:
                self._known_spells.pop(i)
                self._has_changed = True
                return True
        return False

    def get_memorization_info(self) -> list[MemInfo]:
        return self._mem_info[:]

    def set_memorization_info(self, info: list[MemInfo]):
        self._mem_info = info[:]
        # Keep wNumMemorizable1 and wNumMemorizable2 in sync (C++ behavior)
        for mi in self._mem_info:
            mi.num_memorized = mi.num_memorizable
        self._has_changed = True

    def get_memorized_spells(self) -> list[MemSpell]:
        return self._mem_spells[:]

    def set_memorized_spells(self, spells: list[MemSpell]):
        self._mem_spells = spells[:]
        self._sync_spell_data_from_mem_spells()
        self._has_changed = True

    # --- Item methods ---

    def get_items(self) -> list[CreItem]:
        return self._items[:]

    def set_items(self, items: list[CreItem]):
        self._items = items[:INF_NUM_ITEMSLOTS]
        while len(self._items) < INF_NUM_ITEMSLOTS:
            self._items.append(CreItem())
        self._has_changed = True

    def get_item(self, slot: int) -> CreItem:
        if 0 <= slot < INF_NUM_ITEMSLOTS:
            return self._items[slot]
        return CreItem()

    def set_item(self, slot: int, item: CreItem):
        if 0 <= slot < INF_NUM_ITEMSLOTS:
            self._items[slot] = item
            self._has_changed = True

    # --- Proficiency methods (via affects) ---

    def get_profs(self) -> list[ProfData]:
        profs = []
        for aff in self._affects:
            if aff.opcode == AFF_TYPE_PROF:
                if self.is_dual_class():
                    profs.append(ProfData(
                        prof_id=aff.parameter2 & 0xFF,
                        value=hi_tribble(aff.parameter1),
                        second_value=lo_tribble(aff.parameter1),
                    ))
                else:
                    profs.append(ProfData(
                        prof_id=aff.parameter2 & 0xFF,
                        value=aff.parameter1,
                    ))
        return profs

    def set_profs(self, profs: list[ProfData]):
        self._affects = [a for a in self._affects if a.opcode != AFF_TYPE_PROF]
        for prof in profs:
            aff = InfAffect()
            aff.opcode = AFF_TYPE_PROF
            aff.parameter2 = prof.prof_id
            if self.is_dual_class():
                aff.parameter1 = make_tribble(prof.second_value, prof.value)
            else:
                aff.parameter1 = prof.value
            aff.timing_mode = 9
            aff.probability1 = 100
            raw_data = bytearray(AFF_V2_SIZE)
            struct.pack_into("<I", raw_data, 120, 0xFFFFFFFF)
            struct.pack_into("<I", raw_data, 124, 0xFFFFFFFF)
            struct.pack_into("<I", raw_data, 128, 0xFFFFFFFF)
            struct.pack_into("<I", raw_data, 132, 0xFFFFFFFF)
            struct.pack_into("<I", raw_data, 156, 0xFFFFFFFF)
            struct.pack_into("<I", raw_data, 196, 0x01)
            aff.raw_data = bytes(raw_data)
            self._affects.append(aff)
        self._has_changed = True

    def _is_speed_affect(self, aff: InfAffect) -> bool:
        return aff.opcode == AFF_TYPE_SPELL and aff.resource3.upper().startswith("SPCL812")

    def get_speed(self) -> int:
        for aff in self._affects:
            if self._is_speed_affect(aff):
                return aff.parameter1
        return 0

    def set_speed(self, speed: int):
        for i, aff in enumerate(self._affects):
            if self._is_speed_affect(aff):
                if speed:
                    aff.parameter1 = speed
                else:
                    self._affects.pop(i)
                self._has_changed = True
                return

        if not speed:
            return

        aff = InfAffect()
        aff.opcode = AFF_TYPE_SPELL
        aff.target_type = AFF_TARG_CRE
        aff.parameter1 = speed
        aff.timing_mode = 9
        aff.probability1 = 100
        aff.special = 2
        aff.resource3 = "SPCL812"
        raw_data = bytearray(AFF_V2_SIZE)
        struct.pack_into("<I", raw_data, 120, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 124, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 128, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 132, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 136, 0x01)
        struct.pack_into("<I", raw_data, 156, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 192, 0x0F)
        struct.pack_into("<I", raw_data, 196, 0x01)
        aff.raw_data = bytes(raw_data)
        self._affects.append(aff)
        self._has_changed = True

    # --- Affects methods ---

    def get_affects(self) -> list[InfAffect]:
        return [
            aff for aff in self._affects
            if aff.opcode != AFF_TYPE_PROF and not self._is_speed_affect(aff)
        ]

    def set_affects(self, affects: list[InfAffect]):
        special_affects = [
            aff for aff in self._affects
            if aff.opcode == AFF_TYPE_PROF or self._is_speed_affect(aff)
        ]
        self._affects = special_affects + affects[:]
        self._has_changed = True

    def add_affect(self, affect: InfAffect, index: int = -1):
        """Add an affect to the creature's affect list."""
        if index < 0 or index >= len(self._affects):
            self._affects.append(affect)
        else:
            self._affects.insert(index, affect)
        self._has_changed = True

    def remove_affect(self, affect: InfAffect):
        """Remove a specific affect instance from the creature."""
        try:
            self._affects.remove(affect)
            self._has_changed = True
        except ValueError:
            pass

    # --- Dual/Multi class ---

    def is_dual_class(self) -> bool:
        return bool(self.flags & CRE_FLAG_HAS_DUALCLASS)

    def is_multi_class(self) -> bool:
        return self.level_second_class > 0 and not self.is_dual_class()

    # --- State ---

    def has_changed(self) -> bool:
        return self._has_changed

    def mark_changed(self):
        self._has_changed = True

    def mark_saved(self):
        self._has_changed = False

    @property
    def error(self) -> int:
        return self._error
