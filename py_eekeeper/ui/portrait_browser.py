"""Portrait browser dialog — browse and select character portraits."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit,
    QDialogButtonBox, QLabel,
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QSize

from ..app import EEKeeperApp


class PortraitBrowserDialog(QDialog):
    """Browse and select a portrait from the game installation."""

    def __init__(self, parent=None, size_filter: str = "L"):
        super().__init__(parent)
        self.setWindowTitle("Portrait Browser")
        self.setMinimumSize(500, 600)
        self._selected_portrait: str = ""
        self._size_filter = size_filter.upper()
        self._setup_ui()
        self._load_portraits()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter portraits...")
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._filter_edit)
        layout.addLayout(filter_layout)

        # Portrait grid
        self._list = QListWidget()
        self._list.setIconSize(QSize(64, 100))
        self._list.setViewMode(QListWidget.ViewMode.IconMode)
        self._list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list.setSpacing(8)
        self._list.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._list)

        # OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_portraits(self):
        app = EEKeeperApp.instance()
        install_path = Path(app.config.install_path)
        self._portraits: list[tuple[str, Path]] = []

        portrait_dirs = [
            install_path / "portraits",
            install_path / "override",
        ]

        for pdir in portrait_dirs:
            if not pdir.exists():
                continue
            for f in sorted(pdir.iterdir()):
                if not f.is_file():
                    continue
                name_upper = f.stem.upper()
                ext_lower = f.suffix.lower()
                if ext_lower not in (".bmp", ".png", ".jpg"):
                    continue
                if self._size_filter and not name_upper.endswith(self._size_filter):
                    continue
                base_name = f.stem[:-1] if len(f.stem) > 1 else f.stem
                self._portraits.append((base_name, f))

        self._refresh_list()

    def _refresh_list(self):
        self._list.clear()
        filter_text = self._filter_edit.text().upper()

        for base_name, path in self._portraits:
            if filter_text and filter_text not in base_name.upper():
                continue
            item = QListWidgetItem(base_name)
            item.setData(Qt.ItemDataRole.UserRole, base_name)
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                item.setIcon(QIcon(pixmap.scaled(
                    64, 100, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )))
            self._list.addItem(item)

    def _on_filter_changed(self, _text: str):
        self._refresh_list()

    def _on_double_click(self):
        self._on_accept()

    def _on_accept(self):
        current = self._list.currentItem()
        if current:
            self._selected_portrait = current.data(Qt.ItemDataRole.UserRole)
            self.accept()

    @property
    def selected_portrait(self) -> str:
        return self._selected_portrait
