"""Parser for Infinity Engine KEY (chitin.key) resource index files."""

import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ResInfo:
    name: str
    type: int
    locator: int
    bif_index: int
    resource_index: int


@dataclass
class BifEntry:
    file_length: int
    filename_offset: int
    filename_length: int
    filename: str = ""


class InfKey:
    """Parses chitin.key and provides access to the resource index."""

    def __init__(self):
        self._bif_entries: list[BifEntry] = []
        self._resources: dict[tuple[int, str], ResInfo] = {}
        self._resources_by_type: dict[int, list[ResInfo]] = {}
        self._base_path: Path = Path()

    def open(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.exists():
            return False

        self._base_path = path.parent

        with open(path, "rb") as f:
            data = f.read()

        if len(data) < 24:
            return False

        sig = data[0:4]
        ver = data[4:8]
        if sig != b"KEY ":
            return False

        bif_count, res_count, bif_offset, res_offset = struct.unpack_from(
            "<IIII", data, 8
        )

        self._bif_entries = []
        for i in range(bif_count):
            offset = bif_offset + i * 12
            file_len, fname_offset, fname_len = struct.unpack_from(
                "<IIH", data, offset
            )
            # filename_length includes the drive letter prefix on Windows
            # but we just need the path part
            fname_end = fname_offset + fname_len
            filename_raw = data[fname_offset:fname_end]
            filename = filename_raw.decode("latin-1").rstrip("\x00")
            # Normalize path separators
            filename = filename.replace("\\", "/")

            entry = BifEntry(
                file_length=file_len,
                filename_offset=fname_offset,
                filename_length=fname_len,
                filename=filename,
            )
            self._bif_entries.append(entry)

        self._resources = {}
        self._resources_by_type = {}
        for i in range(res_count):
            offset = res_offset + i * 14
            res_name_raw, res_type, locator = struct.unpack_from(
                "<8sHI", data, offset
            )
            res_name = res_name_raw.decode("latin-1").rstrip("\x00").upper()
            bif_index = (locator >> 20) & 0xFFF
            resource_index = locator & 0x3FFF

            info = ResInfo(
                name=res_name,
                type=res_type,
                locator=locator,
                bif_index=bif_index,
                resource_index=resource_index,
            )
            self._resources[(res_type, res_name)] = info

            if res_type not in self._resources_by_type:
                self._resources_by_type[res_type] = []
            self._resources_by_type[res_type].append(info)

        return True

    def get_res_info(self, res_type: int, res_name: str) -> ResInfo | None:
        return self._resources.get((res_type, res_name.upper()))

    def get_resource_list(self, res_type: int) -> list[ResInfo]:
        return self._resources_by_type.get(res_type, [])

    def get_bif_entry(self, index: int) -> BifEntry | None:
        if 0 <= index < len(self._bif_entries):
            return self._bif_entries[index]
        return None

    def get_bif_path(self, index: int) -> Path | None:
        entry = self.get_bif_entry(index)
        if entry is None:
            return None
        return self._base_path / entry.filename

    @property
    def bif_count(self) -> int:
        return len(self._bif_entries)

    @property
    def resource_count(self) -> int:
        return len(self._resources)

    @property
    def base_path(self) -> Path:
        return self._base_path
