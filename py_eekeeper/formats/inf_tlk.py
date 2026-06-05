"""Parser for Infinity Engine TLK (Talk/String Table) files."""

import struct
from pathlib import Path


TLK_HEADER_SIZE = 18
TLK_ENTRY_SIZE = 26


class InfTlk:
    """Reads dialog.tlk string table files."""

    def __init__(self):
        self._string_count: int = 0
        self._strings_offset: int = 0
        self._entries: list[tuple[int, int, int]] = []  # (flags, offset, length)
        self._file_path: Path | None = None
        self._cache: dict[int, str] = {}

    def open(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.exists():
            return False

        self._file_path = path
        self._cache.clear()

        with open(path, "rb") as f:
            header = f.read(TLK_HEADER_SIZE)
            if len(header) < TLK_HEADER_SIZE:
                return False

            sig = header[0:4]
            ver = header[4:8]
            if sig != b"TLK ":
                return False

            lang_id, self._string_count, self._strings_offset = struct.unpack_from(
                "<HII", header, 8
            )

            self._entries = []
            for _ in range(self._string_count):
                entry_data = f.read(TLK_ENTRY_SIZE)
                if len(entry_data) < TLK_ENTRY_SIZE:
                    break
                flags = struct.unpack_from("<H", entry_data, 0)[0]
                offset, length = struct.unpack_from("<II", entry_data, 18)
                self._entries.append((flags, offset, length))

        return True

    def get_string(self, index: int) -> str | None:
        if index == 0xFFFFFFFF or index >= self._string_count:
            return None

        if index in self._cache:
            return self._cache[index]

        flags, offset, length = self._entries[index]
        if length == 0:
            return ""

        if not self._file_path:
            return None

        with open(self._file_path, "rb") as f:
            f.seek(self._strings_offset + offset)
            data = f.read(length)

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        self._cache[index] = text
        return text

    @property
    def string_count(self) -> int:
        return self._string_count
