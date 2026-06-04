"""Dialog for opening a saved game directory."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QDialogButtonBox, QTabWidget, QWidget,
)
from PySide6.QtCore import Qt

from ..config import Config


class OpenSavedGameDialog(QDialog):
    """Dialog to select a save game directory."""

    def __init__(self, parent=None, config: Config = None):
        super().__init__(parent)
        self.setWindowTitle("Open Saved Game")
        self.setMinimumSize(500, 400)
        self._config = config
        self._selected_path: str = ""
        self._setup_ui()
        self._load_saves()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Tabs for single/multiplayer
        self._tabs = QTabWidget()

        self._list_single = QListWidget()
        self._list_single.itemDoubleClicked.connect(self._on_double_click)
        self._tabs.addTab(self._list_single, "Single Player")

        self._list_multi = QListWidget()
        self._list_multi.itemDoubleClicked.connect(self._on_double_click)
        self._tabs.addTab(self._list_multi, "Multiplayer")

        layout.addWidget(self._tabs)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_saves(self):
        if not self._config:
            return

        base = Path(self._config.documents_path)

        # Single player saves
        save_dir = base / "save"
        if save_dir.exists():
            for entry in sorted(save_dir.iterdir()):
                if entry.is_dir() and (entry / "BALDUR.GAM").exists():
                    item = QListWidgetItem(entry.name)
                    item.setData(Qt.ItemDataRole.UserRole, str(entry))
                    self._list_single.addItem(item)

        # Multiplayer saves
        mp_dir = base / "mpsave"
        if mp_dir.exists():
            for entry in sorted(mp_dir.iterdir()):
                if entry.is_dir() and (entry / "BALDUR.GAM").exists():
                    item = QListWidgetItem(entry.name)
                    item.setData(Qt.ItemDataRole.UserRole, str(entry))
                    self._list_multi.addItem(item)

        # Select default tab
        if self._config.default_open_singleplayer:
            self._tabs.setCurrentIndex(0)
        else:
            self._tabs.setCurrentIndex(1)

    def _on_double_click(self, item: QListWidgetItem):
        self._selected_path = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_accept(self):
        current_list = self._list_single if self._tabs.currentIndex() == 0 else self._list_multi
        item = current_list.currentItem()
        if item:
            self._selected_path = item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    @property
    def selected_path(self) -> str:
        return self._selected_path
