"""Spell browser dialog — browse and select game spells."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit,
    QDialogButtonBox, QLabel, QComboBox,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

from ..app import EEKeeperApp
from ..formats.constants import RESTYPE_SPL
from ..resources.descriptions import get_spell_description


class SpellBrowserDialog(QDialog):
    """Browse and select a spell resource."""

    def __init__(self, parent=None, spell_type: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Spell Browser")
        self.setMinimumSize(550, 600)
        self._selected_spell: str = ""
        self._all_spells: list[tuple[str, str]] = []
        self._initial_type = spell_type
        self._setup_ui()
        self._load_spells()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Filters
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Type:"))
        self._combo_type = QComboBox()
        self._combo_type.addItem("All", "")
        self._combo_type.addItem("Wizard", "SPWI")
        self._combo_type.addItem("Priest", "SPPR")
        self._combo_type.addItem("Innate", "SPCL")
        self._combo_type.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._combo_type)

        filter_layout.addWidget(QLabel("Level:"))
        self._combo_level = QComboBox()
        self._combo_level.addItem("All", -1)
        for lvl in range(1, 10):
            self._combo_level.addItem(str(lvl), lvl)
        self._combo_level.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._combo_level)

        filter_layout.addWidget(QLabel("Search:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter by name...")
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._filter_edit)

        layout.addLayout(filter_layout)

        # Spell list
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

        # Set initial type filter
        if self._initial_type:
            for i in range(self._combo_type.count()):
                if self._combo_type.itemData(i) == self._initial_type:
                    self._combo_type.setCurrentIndex(i)
                    break

    def _load_spells(self):
        app = EEKeeperApp.instance()
        spell_names = app.resource_manager.get_resource_list(RESTYPE_SPL)
        for res_name in spell_names:
            friendly = app.get_spell_name(res_name)
            self._all_spells.append((res_name, friendly))
        self._refresh_list()

    def _refresh_list(self):
        self._list.clear()
        type_prefix = self._combo_type.currentData() or ""
        level_filter = self._combo_level.currentData()
        filter_text = self._filter_edit.text().upper()
        app = EEKeeperApp.instance()

        for res_name, friendly in self._all_spells:
            if type_prefix and not res_name.startswith(type_prefix):
                continue

            if level_filter and level_filter > 0:
                try:
                    spell_level = int(res_name[4])
                except (IndexError, ValueError):
                    spell_level = 0
                if spell_level != level_filter:
                    continue

            if filter_text and filter_text not in res_name.upper() and filter_text not in friendly.upper():
                continue

            display = f"{res_name} — {friendly}" if friendly != res_name else res_name
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, res_name)

            desc = get_spell_description(res_name)
            if desc:
                item.setToolTip(desc)

            if app.spell_bitmaps:
                icon = app.spell_bitmaps.get_icon(res_name)
                if icon:
                    item.setIcon(QIcon(icon))

            self._list.addItem(item)

    def _on_filter_changed(self, *_args):
        self._refresh_list()

    def _on_double_click(self):
        self._on_accept()

    def _on_accept(self):
        current = self._list.currentItem()
        if current:
            self._selected_spell = current.data(Qt.ItemDataRole.UserRole)
            self.accept()

    @property
    def selected_spell(self) -> str:
        return self._selected_spell
