"""Parser for Infinity Engine CHR (exported character) files."""

import struct
from pathlib import Path

from .inf_creature import InfCreature


CHR_HEADER_SIZE = 0x64
CHR_NAME_MAXLEN = 32
CHR_DATA_START_OFFSET = 0x28
CHR_DATA_LENGTH_OFFSET = 0x2C


class InfChr:
    """Reads and writes .CHR character files."""

    def __init__(self, ignore_data_versions: bool = False, mem_spells_on_save: bool = False):
        self._header_data: bytearray = bytearray(CHR_HEADER_SIZE)
        self._creature: InfCreature = InfCreature(ignore_data_versions, mem_spells_on_save)
        self._error: int = 0
        self._filepath: str = ""
        self._ignore_data_versions = ignore_data_versions
        self._mem_spells_on_save = mem_spells_on_save

    def read(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.exists():
            self._error = 2001
            return False

        self._filepath = str(path)

        with open(path, "rb") as f:
            data = f.read()

        if len(data) < CHR_HEADER_SIZE:
            self._error = 2002
            return False

        sig = data[0:4]
        if sig != b"CHR ":
            self._error = 2003
            return False

        version = data[4:8]
        if not self._ignore_data_versions and version not in (b"V2.0", b"V2.1"):
            self._error = 2004
            return False

        self._header_data = bytearray(data[:CHR_HEADER_SIZE])

        cre_offset = struct.unpack_from("<I", data, CHR_DATA_START_OFFSET)[0]
        cre_size = struct.unpack_from("<I", data, CHR_DATA_LENGTH_OFFSET)[0]
        if cre_offset == 0:
            cre_offset = CHR_HEADER_SIZE
        if cre_size == 0:
            cre_size = len(data) - cre_offset

        if cre_offset + cre_size > len(data):
            self._error = 2002
            return False

        cre_data = data[cre_offset:cre_offset + cre_size]
        self._creature = InfCreature(self._ignore_data_versions, self._mem_spells_on_save)
        if not self._creature.read(cre_data):
            self._error = self._creature.error
            return False

        return True

    def write(self, path: str | Path) -> bool:
        path = Path(path)

        cre_data = self._creature.write()

        # Update header with CRE offset and size
        header = bytearray(self._header_data[:CHR_HEADER_SIZE])
        # Ensure signature
        header[0:4] = b"CHR "
        if header[4:8] not in (b"V2.0", b"V2.1"):
            header[4:8] = b"V2.0"
        struct.pack_into("<I", header, CHR_DATA_START_OFFSET, CHR_HEADER_SIZE)
        struct.pack_into("<I", header, CHR_DATA_LENGTH_OFFSET, len(cre_data))

        with open(path, "wb") as f:
            f.write(header)
            f.write(cre_data)

        return True

    @property
    def name(self) -> str:
        raw = self._header_data[8:8 + CHR_NAME_MAXLEN]
        return raw.decode("latin-1").rstrip("\x00")

    @name.setter
    def name(self, value: str):
        # Match C++ qstrncpy(szName, pszName, CHR_NAME_MAXLEN-1): max 31 chars + null terminator
        encoded = value.encode("latin-1")[:CHR_NAME_MAXLEN - 1].ljust(CHR_NAME_MAXLEN, b"\x00")
        self._header_data[8:8 + CHR_NAME_MAXLEN] = encoded

    def get_creature(self) -> InfCreature:
        return self._creature

    def set_creature(self, creature: InfCreature):
        self._creature = creature

    def has_changed(self) -> bool:
        return self._creature.has_changed()

    @property
    def error(self) -> int:
        return self._error
