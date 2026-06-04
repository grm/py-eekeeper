"""Application configuration and settings management."""

import sys
from pathlib import Path
from PySide6.QtCore import QSettings


class Config:
    """Manages application settings via QSettings."""

    def __init__(self):
        self._settings = QSettings("EEKeeper", "py-eekeeper")
        self.install_path: str = ""
        self.language: str = "en_US"
        self.documents_path: str = ""
        self.use_known_spell_limit: bool = False
        self.known_spell_limit: int = 50
        self.use_mem_spell_limit: bool = False
        self.mem_spell_limit: int = 50
        self.mem_spells_on_save: bool = False
        self.allow_chr_overwrite: bool = True
        self.default_open_singleplayer: bool = True
        self.use_grid_lines: bool = True
        self.ignore_data_versions: bool = False

    def read(self):
        self.install_path = self._settings.value("strInstallPath", "", str)
        self.language = self._settings.value("strLanguage", "en_US", str)
        self.documents_path = self._settings.value("strDocumentsPath", self._default_documents_path(), str)
        self.use_known_spell_limit = self._settings.value("bUseKnownSpellLimit", False, bool)
        self.known_spell_limit = self._settings.value("nKnownSpellLimit", 50, int)
        self.use_mem_spell_limit = self._settings.value("bUseMemSpellLimit", False, bool)
        self.mem_spell_limit = self._settings.value("nMemSpellLimit", 50, int)
        self.mem_spells_on_save = self._settings.value("bMemSpellsOnSave", False, bool)
        self.allow_chr_overwrite = self._settings.value("bAllowCHROverwrite", True, bool)
        self.default_open_singleplayer = self._settings.value("bDefaultOpenSinglePlayer", True, bool)
        self.use_grid_lines = self._settings.value("bUseGridLines", True, bool)
        self.ignore_data_versions = self._settings.value("bIgnoreDataVersions", False, bool)

    def write(self):
        self._settings.setValue("strInstallPath", self.install_path)
        self._settings.setValue("strLanguage", self.language)
        self._settings.setValue("strDocumentsPath", self.documents_path)
        self._settings.setValue("bUseKnownSpellLimit", self.use_known_spell_limit)
        self._settings.setValue("nKnownSpellLimit", self.known_spell_limit)
        self._settings.setValue("bUseMemSpellLimit", self.use_mem_spell_limit)
        self._settings.setValue("nMemSpellLimit", self.mem_spell_limit)
        self._settings.setValue("bMemSpellsOnSave", self.mem_spells_on_save)
        self._settings.setValue("bAllowCHROverwrite", self.allow_chr_overwrite)
        self._settings.setValue("bDefaultOpenSinglePlayer", self.default_open_singleplayer)
        self._settings.setValue("bUseGridLines", self.use_grid_lines)
        self._settings.setValue("bIgnoreDataVersions", self.ignore_data_versions)
        self._settings.sync()

    def _default_documents_path(self) -> str:
        if sys.platform == "darwin":
            return str(Path.home() / "Documents" / "Baldur's Gate - Enhanced Edition")
        else:
            return str(Path.home() / ".local" / "share" / "bg2ee")

    def get_save_path(self) -> Path:
        base = Path(self.documents_path)
        if self.default_open_singleplayer:
            return base / "save"
        return base / "mpsave"

    def get_tlk_path(self) -> Path:
        return Path(self.install_path) / "lang" / self.language / "dialog.tlk"

    def get_override_path(self) -> Path:
        return Path(self.install_path) / "override"
