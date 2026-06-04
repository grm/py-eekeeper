"""Parser for Infinity Engine GAM (BALDUR.GAM) save game files."""

import struct
from dataclasses import dataclass
from pathlib import Path

from .constants import INF_MAX_CHARACTERS
from .inf_creature import InfCreature


GAME_HEADER_SIZE = 0xB4
CHARINFO_SIZE = 0x160


@dataclass
class GameCharInfo:
    party_position: int = 0xFFFF
    cre_offset: int = 0
    cre_size: int = 0
    area: str = ""
    player_x: int = 0
    player_y: int = 0
    view_x: int = 0
    view_y: int = 0
    name: str = ""
    raw_data: bytes = b""


@dataclass
class GameGlobal:
    name: str = ""
    value: int = 0
    raw_data: bytes = b""


class InfGame:
    """Parses and writes BALDUR.GAM save game files."""

    def __init__(self):
        self._header_data: bytearray = bytearray(GAME_HEADER_SIZE)
        self._charinfo: list[GameCharInfo] = []
        self._party: list[InfCreature] = []
        self._out_charinfo: list[GameCharInfo] = []
        self._out_party: list[InfCreature] = []
        self._globals: list[GameGlobal] = []
        self._journal_data: bytes = b""
        self._after_journal_data: bytes = b""
        self._has_changed: bool = False
        self._error: int = 0
        self._filepath: str = ""

    def read(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.exists():
            self._error = 1501
            return False

        self._filepath = str(path)

        with open(path, "rb") as f:
            data = f.read()

        if len(data) < GAME_HEADER_SIZE:
            self._error = 1502
            return False

        sig = data[0:4]
        if sig != b"GAME":
            self._error = 1521
            return False

        ver = data[4:8]

        self._header_data = bytearray(data[:GAME_HEADER_SIZE])

        # Parse header fields
        in_party_offset = struct.unpack_from("<I", data, 0x18)[0]
        in_party_count = struct.unpack_from("<I", data, 0x1C)[0]
        out_party_offset = struct.unpack_from("<I", data, 0x24)[0]
        out_party_count = struct.unpack_from("<I", data, 0x28)[0]
        global_var_offset = struct.unpack_from("<I", data, 0x2C)[0]
        global_var_count = struct.unpack_from("<I", data, 0x30)[0]
        journal_count = struct.unpack_from("<I", data, 0x3C)[0]
        journal_offset = struct.unpack_from("<I", data, 0x40)[0]
        after_journal_offset = struct.unpack_from("<I", data, 0x58)[0]

        # Read in-party characters
        self._charinfo = []
        self._party = []
        for i in range(min(in_party_count, INF_MAX_CHARACTERS)):
            ci_offset = in_party_offset + i * CHARINFO_SIZE
            if ci_offset + CHARINFO_SIZE > len(data):
                break
            ci_data = data[ci_offset:ci_offset + CHARINFO_SIZE]
            charinfo = self._parse_charinfo(ci_data)
            self._charinfo.append(charinfo)

            # Parse embedded CRE
            cre = InfCreature()
            if charinfo.cre_offset > 0 and charinfo.cre_size > 0:
                cre_data = data[charinfo.cre_offset:charinfo.cre_offset + charinfo.cre_size]
                cre.read(cre_data, charinfo)
            self._party.append(cre)

        # Read out-of-party characters
        self._out_charinfo = []
        self._out_party = []
        for i in range(out_party_count):
            ci_offset = out_party_offset + i * CHARINFO_SIZE
            if ci_offset + CHARINFO_SIZE > len(data):
                break
            ci_data = data[ci_offset:ci_offset + CHARINFO_SIZE]
            charinfo = self._parse_charinfo(ci_data)
            self._out_charinfo.append(charinfo)

            cre = InfCreature()
            if charinfo.cre_offset > 0 and charinfo.cre_size > 0:
                cre_data = data[charinfo.cre_offset:charinfo.cre_offset + charinfo.cre_size]
                cre.read(cre_data, charinfo)
            self._out_party.append(cre)

        # Read global variables
        self._globals = []
        for i in range(global_var_count):
            g_offset = global_var_offset + i * 0x54
            if g_offset + 0x54 > len(data):
                break
            g_data = data[g_offset:g_offset + 0x54]
            name = g_data[0:0x20].decode("latin-1").rstrip("\x00")
            value = struct.unpack_from("<i", g_data, 0x28)[0]
            self._globals.append(GameGlobal(name=name, value=value, raw_data=g_data))

        # Read journal
        if journal_offset > 0 and journal_count > 0:
            journal_entry_size = 0x0C
            journal_end = journal_offset + journal_count * journal_entry_size
            if journal_end <= len(data):
                self._journal_data = data[journal_offset:journal_end]
            else:
                self._journal_data = data[journal_offset:]
        else:
            self._journal_data = b""

        # Read after-journal data
        if after_journal_offset > 0 and after_journal_offset < len(data):
            self._after_journal_data = data[after_journal_offset:]
        else:
            self._after_journal_data = b""

        self._has_changed = False
        return True

    def write(self, path: str | Path) -> bool:
        path = Path(path)

        # Build CRE data for all characters
        cre_datas: list[bytes] = []
        for cre in self._party:
            cre_datas.append(cre.write())

        out_cre_datas: list[bytes] = []
        for cre in self._out_party:
            out_cre_datas.append(cre.write())

        # Calculate offsets
        header_size = GAME_HEADER_SIZE

        # In-party charinfo follows header
        in_party_offset = header_size
        in_party_size = len(self._charinfo) * CHARINFO_SIZE

        # Out-party charinfo follows in-party
        out_party_offset = in_party_offset + in_party_size
        out_party_size = len(self._out_charinfo) * CHARINFO_SIZE

        # Global variables follow out-party
        global_var_offset = out_party_offset + out_party_size
        global_var_size = len(self._globals) * 0x54

        # Journal follows globals
        journal_offset = global_var_offset + global_var_size
        journal_size = len(self._journal_data)

        # CRE data follows journal
        cre_data_offset = journal_offset + journal_size

        # Calculate individual CRE offsets
        current_offset = cre_data_offset
        in_cre_offsets: list[int] = []
        for cre_data in cre_datas:
            in_cre_offsets.append(current_offset)
            current_offset += len(cre_data)

        out_cre_offsets: list[int] = []
        for cre_data in out_cre_datas:
            out_cre_offsets.append(current_offset)
            current_offset += len(cre_data)

        # After-journal data
        after_journal_offset = current_offset

        # Update header
        header = bytearray(self._header_data)
        struct.pack_into("<I", header, 0x18, in_party_offset)
        struct.pack_into("<I", header, 0x1C, len(self._charinfo))
        struct.pack_into("<I", header, 0x24, out_party_offset)
        struct.pack_into("<I", header, 0x28, len(self._out_charinfo))
        struct.pack_into("<I", header, 0x2C, global_var_offset)
        struct.pack_into("<I", header, 0x30, len(self._globals))
        struct.pack_into("<I", header, 0x3C, len(self._journal_data) // 0x0C if self._journal_data else 0)
        struct.pack_into("<I", header, 0x40, journal_offset)
        struct.pack_into("<I", header, 0x58, after_journal_offset)

        # Write file
        result = bytearray()
        result.extend(header)

        # Write in-party charinfo
        for i, ci in enumerate(self._charinfo):
            ci_bytes = bytearray(ci.raw_data) if len(ci.raw_data) >= CHARINFO_SIZE else bytearray(CHARINFO_SIZE)
            if i < len(in_cre_offsets):
                struct.pack_into("<I", ci_bytes, 0x04, in_cre_offsets[i])
                struct.pack_into("<I", ci_bytes, 0x08, len(cre_datas[i]))
            result.extend(ci_bytes[:CHARINFO_SIZE])

        # Write out-party charinfo
        for i, ci in enumerate(self._out_charinfo):
            ci_bytes = bytearray(ci.raw_data) if len(ci.raw_data) >= CHARINFO_SIZE else bytearray(CHARINFO_SIZE)
            if i < len(out_cre_offsets):
                struct.pack_into("<I", ci_bytes, 0x04, out_cre_offsets[i])
                struct.pack_into("<I", ci_bytes, 0x08, len(out_cre_datas[i]))
            result.extend(ci_bytes[:CHARINFO_SIZE])

        # Write globals
        for g in self._globals:
            if len(g.raw_data) >= 0x54:
                g_bytes = bytearray(g.raw_data[:0x54])
            else:
                g_bytes = bytearray(0x54)
            name_bytes = g.name.encode("latin-1")[:0x20].ljust(0x20, b"\x00")
            g_bytes[0:0x20] = name_bytes
            struct.pack_into("<i", g_bytes, 0x28, g.value)
            result.extend(g_bytes)

        # Write journal
        result.extend(self._journal_data)

        # Write CRE data
        for cre_data in cre_datas:
            result.extend(cre_data)
        for cre_data in out_cre_datas:
            result.extend(cre_data)

        # Write after-journal
        result.extend(self._after_journal_data)

        with open(path, "wb") as f:
            f.write(result)

        self._has_changed = False
        return True

    def _parse_charinfo(self, data: bytes) -> GameCharInfo:
        party_position = struct.unpack_from("<H", data, 0x02)[0]
        cre_offset = struct.unpack_from("<I", data, 0x04)[0]
        cre_size = struct.unpack_from("<I", data, 0x08)[0]
        area = data[0x18:0x20].decode("latin-1").rstrip("\x00")
        player_x = struct.unpack_from("<H", data, 0x20)[0]
        player_y = struct.unpack_from("<H", data, 0x22)[0]
        view_x = struct.unpack_from("<H", data, 0x24)[0]
        view_y = struct.unpack_from("<H", data, 0x26)[0]
        name = data[0xC0:0xD5].decode("latin-1").rstrip("\x00")

        return GameCharInfo(
            party_position=party_position,
            cre_offset=cre_offset,
            cre_size=cre_size,
            area=area,
            player_x=player_x,
            player_y=player_y,
            view_x=view_x,
            view_y=view_y,
            name=name,
            raw_data=data,
        )

    # --- Public interface ---

    @property
    def party_count(self) -> int:
        return len(self._charinfo)

    @property
    def out_of_party_count(self) -> int:
        return len(self._out_charinfo)

    @property
    def party_gold(self) -> int:
        return struct.unpack_from("<I", self._header_data, 0x14)[0]

    @party_gold.setter
    def party_gold(self, value: int):
        struct.pack_into("<I", self._header_data, 0x14, value)
        self._has_changed = True

    @property
    def party_reputation(self) -> int:
        return self._header_data[0x44] // 10

    @party_reputation.setter
    def party_reputation(self, value: int):
        self._header_data[0x44] = min(value * 10, 200)
        for cre in self._party:
            cre.reputation = min(value * 10, 200)
        self._has_changed = True

    def get_party_cre(self, index: int) -> InfCreature | None:
        if 0 <= index < len(self._party):
            return self._party[index]
        return None

    def get_out_of_party_cre(self, index: int) -> InfCreature | None:
        if 0 <= index < len(self._out_party):
            return self._out_party[index]
        return None

    def get_party_char_name(self, index: int) -> str:
        if 0 <= index < len(self._charinfo):
            return self._charinfo[index].name
        return ""

    def set_party_char_name(self, index: int, name: str):
        if 0 <= index < len(self._charinfo):
            self._charinfo[index].name = name
            self._has_changed = True

    def get_out_of_party_char_name(self, index: int) -> str:
        if 0 <= index < len(self._out_charinfo):
            return self._out_charinfo[index].name
        return ""

    def get_globals(self) -> list[GameGlobal]:
        return self._globals[:]

    def set_globals(self, globals_list: list[GameGlobal]):
        self._globals = globals_list[:]
        self._has_changed = True

    def has_changed(self) -> bool:
        if self._has_changed:
            return True
        for cre in self._party:
            if cre.has_changed():
                return True
        for cre in self._out_party:
            if cre.has_changed():
                return True
        return False

    @property
    def error(self) -> int:
        return self._error
