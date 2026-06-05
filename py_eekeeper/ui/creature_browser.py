"""Creature browser dialog — browse and select game creatures."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit,
    QDialogButtonBox, QLabel,
)
from PySide6.QtCore import Qt

from ..app import EEKeeperApp
from ..formats.constants import RESTYPE_CRE


class CreatureBrowserDialog(QDialog):
    """Browse and select a creature resource."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Creature Browser")
        self.setMinimumSize(550, 600)
        self._selected_creature: str = ""
        self._all_creatures: list[str] = []
        self._setup_ui()
        self._load_creatures()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter by resource name...")
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._filter_edit)
        layout.addLayout(filter_layout)

        # Creature list
        self._list = QListWidget()
        self._list.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._list)

        # OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_creatures(self):
        app = EEKeeperApp.instance()
        self._all_creatures = app.resource_manager.get_resource_list(RESTYPE_CRE)
        self._refresh_list()

    def _refresh_list(self):
        self._list.clear()
        filter_text = self._filter_edit.text().upper()

        for res_name in self._all_creatures:
            if filter_text and filter_text not in res_name.upper():
                continue
            item = QListWidgetItem(res_name)
            item.setData(Qt.ItemDataRole.UserRole, res_name)
            self._list.addItem(item)

    def _on_filter_changed(self, _text: str):
        self._refresh_list()

    def _on_double_click(self):
        self._on_accept()

    def _on_accept(self):
        current = self._list.currentItem()
        if current:
            self._selected_creature = current.data(Qt.ItemDataRole.UserRole)
            self.accept()

    @property
    def selected_creature(self) -> str:
        return self._selected_creature
