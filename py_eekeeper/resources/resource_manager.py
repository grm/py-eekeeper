"""Resource manager — orchestrates KEY + BIF + Override for resource access."""

from pathlib import Path

from ..formats.inf_key import InfKey, ResInfo
from ..formats.inf_bif import InfBifFile


class ResourceManager:
    """Provides unified access to game resources via KEY/BIF/Override."""

    def __init__(self):
        self._key: InfKey = InfKey()
        self._bif_cache: dict[int, InfBifFile] = {}
        self._override_files: dict[tuple[int, str], Path] = {}
        self._base_path: Path = Path()
        self._ignore_data_versions: bool = False

    def initialize(self, install_path: str | Path, ignore_data_versions: bool = False) -> bool:
        self._base_path = Path(install_path)
        self._ignore_data_versions = ignore_data_versions
        key_path = self._base_path / "chitin.key"
        if not self._key.open(key_path):
            return False
        self._scan_override()
        return True

    def _scan_override(self):
        override_dir = self._base_path / "override"
        if not override_dir.exists():
            return

        from ..formats.constants import (
            RESTYPE_ITM, RESTYPE_SPL, RESTYPE_2DA, RESTYPE_BCS,
            RESTYPE_CRE, RESTYPE_BAM, RESTYPE_IDS, RESTYPE_BMP, RESTYPE_BS,
        )
        ext_to_type = {
            ".bmp": RESTYPE_BMP,
            ".itm": RESTYPE_ITM,
            ".spl": RESTYPE_SPL,
            ".2da": RESTYPE_2DA,
            ".bcs": RESTYPE_BCS,
            ".bs": RESTYPE_BS,
            ".cre": RESTYPE_CRE,
            ".bam": RESTYPE_BAM,
            ".ids": RESTYPE_IDS,
        }

        for file_path in override_dir.iterdir():
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in ext_to_type:
                    res_type = ext_to_type[ext]
                    res_name = file_path.stem.upper()
                    self._override_files[(res_type, res_name)] = file_path

    def get_resource(self, res_type: int, res_name: str) -> bytes | None:
        res_name = res_name.upper()

        # Check override first
        override_key = (res_type, res_name)
        if override_key in self._override_files:
            path = self._override_files[override_key]
            if path.exists():
                return path.read_bytes()

        # Look up in KEY
        res_info = self._key.get_res_info(res_type, res_name)
        if res_info is None:
            return None

        # Get or open the BIF file
        bif = self._get_bif(res_info.bif_index)
        if bif is None:
            return None

        return bif.get_data(res_info)

    def _get_bif(self, bif_index: int) -> InfBifFile | None:
        if bif_index in self._bif_cache:
            return self._bif_cache[bif_index]

        bif_path = self._key.get_bif_path(bif_index)
        if bif_path is None:
            return None

        if not bif_path.exists():
            # Try case-insensitive lookup
            parent = bif_path.parent
            name_lower = bif_path.name.lower()
            if parent.exists():
                for f in parent.iterdir():
                    if f.name.lower() == name_lower:
                        bif_path = f
                        break
                else:
                    return None
            else:
                return None

        bif = InfBifFile(ignore_data_versions=self._ignore_data_versions)
        if not bif.open(bif_path):
            return None

        self._bif_cache[bif_index] = bif
        return bif

    def get_resource_list(self, res_type: int) -> list[str]:
        names = set()
        for info in self._key.get_resource_list(res_type):
            names.add(info.name)
        for (rt, name) in self._override_files:
            if rt == res_type:
                names.add(name)
        return sorted(names)

    @property
    def key(self) -> InfKey:
        return self._key

    @property
    def base_path(self) -> Path:
        return self._base_path
