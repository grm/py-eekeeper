"""Dialog for searching items and spells across all party members."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt

from ..app import EEKeeperApp
from ..formats.constants import INF_CRE_ST_WIZARD, INF_CRE_ST_PRIEST, INF_CRE_ST_INNATE


_SPELL_TYPE_LABELS = {
    INF_CRE_ST_PRIEST: "Priest",
    INF_CRE_ST_WIZARD: "Wizard",
    INF_CRE_ST_INNATE: "Innate",
}


class PartySearchDialog(QDialog):
    """Search items and spells across all party and non-party characters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app = EEKeeperApp.instance()
        self.setWindowTitle("Party Search")
        self.setMinimumSize(700, 500)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search controls
        controls = QHBoxLayout()

        controls.addWidget(QLabel("Query:"))
        self._edit_query = QLineEdit()
        self._edit_query.setPlaceholderText("Resource name substring (case-insensitive)...")
        self._edit_query.returnPressed.connect(self._on_search)
        controls.addWidget(self._edit_query, 1)

        controls.addWidget(QLabel("Scope:"))
        self._combo_scope = QComboBox()
        self._combo_scope.addItems(["Items", "Spells", "Both"])
        self._combo_scope.setCurrentIndex(2)
        controls.addWidget(self._combo_scope)

        self._btn_search = QPushButton("Search")
        self._btn_search.clicked.connect(self._on_search)
        controls.addWidget(self._btn_search)

        layout.addLayout(controls)

        # Results tree
        self._tree = QTreeWidget()
        self._tree.setColumnCount(3)
        self._tree.setHeaderLabels(["Character / Match", "Resource Name", "Details"])
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.setRootIsDecorated(True)
        self._tree.setAlternatingRowColors(True)
        layout.addWidget(self._tree)

        # Status
        self._label_status = QLabel("")
        layout.addWidget(self._label_status)

    def _on_search(self):
        query = self._edit_query.text().strip().lower()
        if not query:
            return

        scope = self._combo_scope.currentText()
        search_items = scope in ("Items", "Both")
        search_spells = scope in ("Spells", "Both")

        self._tree.clear()
        total_matches = 0

        game = self._app.game
        if not game:
            self._label_status.setText("No save loaded.")
            return

        # Gather all creatures with their names
        creatures: list[tuple[str, object]] = []
        for i in range(game.party_count):
            cre = game.get_party_cre(i)
            name = game.get_party_char_name(i) or f"Party Member {i + 1}"
            if cre:
                creatures.append((name, cre))

        for i in range(game.out_of_party_count):
            cre = game.get_out_of_party_cre(i)
            name = game.get_out_of_party_char_name(i) or f"Non-Party {i + 1}"
            if cre:
                creatures.append((name, cre))

        for char_name, cre in creatures:
            matches: list[QTreeWidgetItem] = []

            if search_items:
                items = cre.get_items()
                for slot_idx, item in enumerate(items):
                    if not item.res_name:
                        continue
                    if query in item.res_name.lower():
                        friendly = self._app.get_item_name(item.res_name)
                        child = QTreeWidgetItem()
                        child.setText(0, friendly)
                        child.setText(1, item.res_name)
                        child.setText(2, f"Item slot {slot_idx}")
                        matches.append(child)

            if search_spells:
                for spell_type in (INF_CRE_ST_WIZARD, INF_CRE_ST_PRIEST, INF_CRE_ST_INNATE):
                    spells = cre.get_known_spells(spell_type)
                    for spell in spells:
                        if query in spell.name.lower():
                            friendly = self._app.get_spell_name(spell.name)
                            type_label = _SPELL_TYPE_LABELS.get(spell_type, "Unknown")
                            child = QTreeWidgetItem()
                            child.setText(0, friendly)
                            child.setText(1, spell.name)
                            child.setText(2, f"{type_label}, Level {spell.level + 1}")
                            matches.append(child)

            if matches:
                parent = QTreeWidgetItem(self._tree)
                parent.setText(0, f"{char_name} ({len(matches)} match{'es' if len(matches) != 1 else ''})")
                parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsAutoTristate)
                for child in matches:
                    parent.addChild(child)
                parent.setExpanded(True)
                total_matches += len(matches)

        self._label_status.setText(
            f"Found {total_matches} match{'es' if total_matches != 1 else ''} "
            f"across {self._tree.topLevelItemCount()} character(s)."
        )
