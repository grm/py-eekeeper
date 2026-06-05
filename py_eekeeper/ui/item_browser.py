"""Item browser dialog — browse and select game items."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit,
    QDialogButtonBox, QLabel,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

from ..app import EEKeeperApp
from ..formats.constants import RESTYPE_ITM
from ..resources.descriptions import get_item_description


class ItemBrowserDialog(QDialog):
    """Browse and select an item resource."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Item Browser")
        self.setMinimumSize(550, 600)
        self._selected_item: str = ""
        self._all_items: list[tuple[str, str]] = []
        self._setup_ui()
        self._load_items()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter by name or resource...")
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._filter_edit)
        layout.addLayout(filter_layout)

        # Item list
        self._list = QListWidget()
        self._list.setIconSize(QSize(32, 32))
        self._list.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._list)

        # OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_items(self):
        app = EEKeeperApp.instance()
        item_names = app.resource_manager.get_resource_list(RESTYPE_ITM)
        for res_name in item_names:
            friendly = app.get_item_name(res_name)
            self._all_items.append((res_name, friendly))
        self._refresh_list()

    def _refresh_list(self):
        self._list.clear()
        filter_text = self._filter_edit.text().upper()
        app = EEKeeperApp.instance()

        for res_name, friendly in self._all_items:
            if filter_text and filter_text not in res_name.upper() and filter_text not in friendly.upper():
                continue
            display = f"{res_name} — {friendly}" if friendly != res_name else res_name
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, res_name)

            desc = get_item_description(res_name)
            if desc:
                item.setToolTip(desc)

            if app.spell_bitmaps:
                icon = app.spell_bitmaps.get_item_icon(res_name)
                if icon:
                    item.setIcon(QIcon(icon))

            self._list.addItem(item)

    def _on_filter_changed(self, _text: str):
        self._refresh_list()

    def _on_double_click(self):
        self._on_accept()

    def _on_accept(self):
        current = self._list.currentItem()
        if current:
            self._selected_item = current.data(Qt.ItemDataRole.UserRole)
            self.accept()

    @property
    def selected_item(self) -> str:
        return self._selected_item
