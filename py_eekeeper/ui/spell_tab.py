"""Spell tab — view and edit known spells."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QListWidget, QListWidgetItem, QPushButton, QComboBox, QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt

from ..formats.inf_creature import InfCreature, KnownSpell
from ..formats.constants import INF_CRE_ST_WIZARD, INF_CRE_ST_PRIEST, INF_CRE_ST_INNATE
from ..app import EEKeeperApp
from ..resources.descriptions import get_spell_description


class SpellTab(QWidget):
    """Tab for viewing and editing known spells (Wizard, Priest, Innate)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._creature: InfCreature | None = None
        self._current_type: int = INF_CRE_ST_WIZARD
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Spell Type:"))
        self._combo_type = QComboBox()
        self._combo_type.addItem("Wizard", INF_CRE_ST_WIZARD)
        self._combo_type.addItem("Priest", INF_CRE_ST_PRIEST)
        self._combo_type.addItem("Innate", INF_CRE_ST_INNATE)
        self._combo_type.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self._combo_type)

        self._combo_level = QComboBox()
        for i in range(1, 10):
            self._combo_level.addItem(f"Level {i}", i - 1)
        self._combo_level.addItem("All Levels", -1)
        self._combo_level.setCurrentIndex(self._combo_level.count() - 1)
        self._combo_level.currentIndexChanged.connect(self._refresh_list)
        type_layout.addWidget(QLabel("Level:"))
        type_layout.addWidget(self._combo_level)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Content
        content_layout = QHBoxLayout()

        # Known spells list
        known_group = QGroupBox("Known Spells")
        known_layout = QVBoxLayout(known_group)
        self._list_known = QListWidget()
        known_layout.addWidget(self._list_known)

        btn_layout = QHBoxLayout()
        self._btn_remove = QPushButton("Remove")
        self._btn_remove.clicked.connect(self._on_remove)
        btn_layout.addWidget(self._btn_remove)
        self._btn_remove_all = QPushButton("Remove All")
        self._btn_remove_all.clicked.connect(self._on_remove_all)
        btn_layout.addWidget(self._btn_remove_all)
        known_layout.addLayout(btn_layout)
        content_layout.addWidget(known_group)

        # Available spells list
        avail_group = QGroupBox("Available Spells")
        avail_layout = QVBoxLayout(avail_group)
        self._list_available = QListWidget()
        avail_layout.addWidget(self._list_available)

        btn_layout2 = QHBoxLayout()
        self._btn_add = QPushButton("Add")
        self._btn_add.clicked.connect(self._on_add)
        btn_layout2.addWidget(self._btn_add)
        self._btn_add_all = QPushButton("Add All")
        self._btn_add_all.clicked.connect(self._on_add_all)
        btn_layout2.addWidget(self._btn_add_all)
        self._btn_browse = QPushButton("Browse...")
        self._btn_browse.clicked.connect(self._on_browse)
        btn_layout2.addWidget(self._btn_browse)
        avail_layout.addLayout(btn_layout2)
        content_layout.addWidget(avail_group)

        layout.addLayout(content_layout)

    def load_creature(self, creature: InfCreature):
        self._creature = creature
        self._refresh_list()
        self._load_available_spells()

    def _on_type_changed(self):
        self._current_type = self._combo_type.currentData()
        self._refresh_list()
        self._load_available_spells()

    def _refresh_list(self):
        self._list_known.clear()
        if not self._creature:
            return

        level_filter = self._combo_level.currentData()
        spells = self._creature.get_known_spells(self._current_type)

        app = EEKeeperApp.instance()
        for spell in spells:
            if level_filter >= 0 and spell.level != level_filter:
                continue
            friendly_name = app.get_spell_name(spell.name)
            item = QListWidgetItem(f"{spell.name} - {friendly_name} (L{spell.level + 1})")
            item.setData(Qt.ItemDataRole.UserRole, spell.name)
            item.setData(Qt.ItemDataRole.UserRole + 1, spell.level)
            desc = get_spell_description(spell.name)
            if desc:
                item.setToolTip(desc)
            self._list_known.addItem(item)

    def _load_available_spells(self):
        self._list_available.clear()
        app = EEKeeperApp.instance()

        # Determine prefix based on spell type
        if self._current_type == INF_CRE_ST_WIZARD:
            prefix = "SPWI"
        elif self._current_type == INF_CRE_ST_PRIEST:
            prefix = "SPPR"
        else:
            prefix = "SPCL"

        from ..formats.constants import RESTYPE_SPL
        all_spells = app.resource_manager.get_resource_list(RESTYPE_SPL)

        level_filter = self._combo_level.currentData()
        known_names = {s.name.upper() for s in (self._creature.get_known_spells(self._current_type) if self._creature else [])}

        for res_name in all_spells:
            if not res_name.startswith(prefix):
                continue
            if res_name in known_names:
                continue

            # Derive level from resource name (e.g., SPWI103 -> level 1)
            try:
                level = int(res_name[4]) - 1
            except (IndexError, ValueError):
                level = 0

            if level_filter >= 0 and level != level_filter:
                continue

            friendly_name = app.get_spell_name(res_name)
            item = QListWidgetItem(f"{res_name} - {friendly_name} (L{level + 1})")
            item.setData(Qt.ItemDataRole.UserRole, res_name)
            item.setData(Qt.ItemDataRole.UserRole + 1, level)
            desc = get_spell_description(res_name)
            if desc:
                item.setToolTip(desc)
            self._list_available.addItem(item)

    def _can_add_spell(self, show_warning: bool = True) -> bool:
        """Check if adding another known spell is allowed by the configured limit.

        Returns True if the spell can be added, False otherwise.
        """
        app = EEKeeperApp.instance()
        if not app.config.use_known_spell_limit:
            return True
        if not self._creature:
            return True

        current_count = len(self._creature.get_known_spells(self._current_type))
        if current_count >= app.config.known_spell_limit:
            if show_warning:
                QMessageBox.warning(
                    self,
                    "Spell Limit Reached",
                    f"Cannot add more spells. The known spell limit "
                    f"({app.config.known_spell_limit}) has been reached "
                    f"for this spell type.",
                )
            return False
        return True

    def _on_add(self):
        if not self._creature:
            return
        item = self._list_available.currentItem()
        if not item:
            return
        if not self._can_add_spell():
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        level = item.data(Qt.ItemDataRole.UserRole + 1)
        self._creature.add_known_spell(self._current_type, name, level)
        self._refresh_list()
        self._load_available_spells()

    def _on_add_all(self):
        if not self._creature:
            return
        for i in range(self._list_available.count()):
            if not self._can_add_spell(show_warning=False):
                QMessageBox.warning(
                    self,
                    "Spell Limit Reached",
                    f"Stopped adding spells. The known spell limit "
                    f"({EEKeeperApp.instance().config.known_spell_limit}) "
                    f"has been reached for this spell type.",
                )
                break
            item = self._list_available.item(i)
            name = item.data(Qt.ItemDataRole.UserRole)
            level = item.data(Qt.ItemDataRole.UserRole + 1)
            self._creature.add_known_spell(self._current_type, name, level)
        self._refresh_list()
        self._load_available_spells()

    def _on_remove(self):
        if not self._creature:
            return
        item = self._list_known.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        self._creature.remove_known_spell(self._current_type, name)
        self._refresh_list()
        self._load_available_spells()

    def _on_remove_all(self):
        if not self._creature:
            return
        spells = self._creature.get_known_spells(self._current_type)
        for spell in spells[:]:
            self._creature.remove_known_spell(self._current_type, spell.name)
        self._refresh_list()
        self._load_available_spells()

    def _on_browse(self):
        if not self._creature:
            return
        prefixes = {
            INF_CRE_ST_WIZARD: "SPWI",
            INF_CRE_ST_PRIEST: "SPPR",
            INF_CRE_ST_INNATE: "SPCL",
        }
        from .spell_browser import SpellBrowserDialog
        dialog = SpellBrowserDialog(self, spell_type=prefixes.get(self._current_type, ""))
        if dialog.exec():
            res_name = dialog.selected_spell
            if res_name:
                if not self._can_add_spell():
                    return
                try:
                    level = int(res_name[4]) - 1
                except (IndexError, ValueError):
                    level = 0
                self._creature.add_known_spell(self._current_type, res_name, level)
                self._refresh_list()
                self._load_available_spells()
