"""Parser for Infinity Engine BIF (Bif Archive) files."""

import struct
from dataclasses import dataclass
from pathlib import Path

from .inf_key import ResInfo


@dataclass
class BifFileEntry:
    locator: int
    offset: int
    size: int
    res_type: int


class InfBifFile:
    """Opens and reads data from BIF archive files."""

    def __init__(self):
        self._file_path: Path | None = None
        self._entries: dict[tuple[int, int], BifFileEntry] = {}
        self._is_override: bool = False
        self._data: bytes = b""

    def open(self, path: str | Path, as_override: bool = False) -> bool:
        path = Path(path)
        if not path.exists():
            return False

        self._file_path = path
        self._is_override = as_override

        with open(path, "rb") as f:
            self._data = f.read()

        if len(self._data) < 12:
            return False

        sig = self._data[0:4]
        if sig not in (b"BIFF", b"BIF "):
            return False

        ver = self._data[4:8]
        file_entry_count, tileset_count = struct.unpack_from("<II", self._data, 8)

        # File entries start after the header (at offset 16 for BIFF V1)
        entries_offset = struct.unpack_from("<I", self._data, 16)[0] if len(self._data) > 16 else 20

        self._entries = {}
        for i in range(file_entry_count):
            entry_offset = entries_offset + i * 16
            if entry_offset + 16 > len(self._data):
                break
            locator, data_offset, data_size, res_type = struct.unpack_from(
                "<IIIH", self._data, entry_offset
            )
            resource_index = locator & 0x3FFF
            entry = BifFileEntry(
                locator=locator,
                offset=data_offset,
                size=data_size,
                res_type=res_type,
            )
            self._entries[(res_type, resource_index)] = entry

        return True

    def get_data(self, res_info: ResInfo) -> bytes | None:
        key = (res_info.type, res_info.resource_index)
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.offset + entry.size > len(self._data):
            return None
        return self._data[entry.offset : entry.offset + entry.size]

    def get_entry(self, res_type: int, resource_index: int) -> BifFileEntry | None:
        return self._entries.get((res_type, resource_index))

    @property
    def filename(self) -> str:
        return str(self._file_path) if self._file_path else ""

    @property
    def is_override(self) -> bool:
        return self._is_override
