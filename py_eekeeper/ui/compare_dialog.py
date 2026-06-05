"""Compare Characters dialog — side-by-side stat and inventory diff."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QTabWidget,
    QWidget,
)
from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import Qt

from ..formats.inf_game import InfGame
from ..formats.constants import INF_CRE_ST_PRIEST, INF_CRE_ST_WIZARD, INF_CRE_ST_INNATE


# Colors for highlighting differences
COLOR_HIGHER = QColor(200, 255, 200)  # light green — better value
COLOR_LOWER = QColor(255, 200, 200)   # light red — worse value
COLOR_DIFFER = QColor(255, 255, 200)  # light yellow — non-numeric difference


class CompareCharactersDialog(QDialog):
    """Dialog that compares two party characters side by side."""

    def __init__(self, parent, game: InfGame):
        super().__init__(parent)
        self._game = game
        self.setWindowTitle("Compare Characters")
        self.setMinimumSize(700, 550)

        self._setup_ui()
        self._populate_combos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Character selection row
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Character A:"))
        self._combo_a = QComboBox()
        self._combo_a.setMinimumWidth(180)
        select_layout.addWidget(self._combo_a)

        select_layout.addSpacing(20)
        select_layout.addWidget(QLabel("Character B:"))
        self._combo_b = QComboBox()
        self._combo_b.setMinimumWidth(180)
        select_layout.addWidget(self._combo_b)

        select_layout.addSpacing(20)
        self._btn_compare = QPushButton("Compare")
        self._btn_compare.clicked.connect(self._on_compare)
        select_layout.addWidget(self._btn_compare)
        select_layout.addStretch()

        layout.addLayout(select_layout)

        # Tab widget for stats and inventory
        self._tabs = QTabWidget()

        # Stats tab
        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(3)
        self._stats_table.setHorizontalHeaderLabels(["Attribute", "Character A", "Character B"])
        self._stats_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._stats_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._stats_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._stats_table.setAlternatingRowColors(True)
        self._tabs.addTab(self._stats_table, "Stats")

        # Inventory tab
        self._inv_widget = QWidget()
        inv_layout = QVBoxLayout(self._inv_widget)
        self._inv_table = QTableWidget()
        self._inv_table.setColumnCount(3)
        self._inv_table.setHorizontalHeaderLabels(["Item", "Character A", "Character B"])
        self._inv_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._inv_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._inv_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._inv_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._inv_table.setAlternatingRowColors(True)
        inv_layout.addWidget(self._inv_table)
        self._tabs.addTab(self._inv_widget, "Inventory")

        layout.addWidget(self._tabs)

    def _populate_combos(self):
        """Populate combo boxes with all party and out-of-party characters."""
        from ..app import EEKeeperApp
        app = EEKeeperApp.instance()

        entries: list[tuple[str, int, bool]] = []  # (display_name, index, is_party)

        for i in range(self._game.party_count):
            name = self._game.get_party_char_name(i)
            if not name:
                cre = self._game.get_party_cre(i)
                if cre:
                    strref = cre.long_name_strref
                    name = app.tlk.get_string(strref) or f"Character {i + 1}"
                else:
                    name = f"Character {i + 1}"
            entries.append((name, i, True))

        for i in range(self._game.out_of_party_count):
            name = self._game.get_out_of_party_char_name(i)
            if not name:
                name = f"NPC {i + 1}"
            entries.append((f"[NPC] {name}", i, False))

        for display_name, idx, is_party in entries:
            data = ("party", idx) if is_party else ("out", idx)
            self._combo_a.addItem(display_name, data)
            self._combo_b.addItem(display_name, data)

        # Default: select first two different characters
        if self._combo_b.count() >= 2:
            self._combo_b.setCurrentIndex(1)

    def _get_creature(self, combo: QComboBox):
        """Get the InfCreature for the selected combo item."""
        data = combo.currentData()
        if not data:
            return None
        source, idx = data
        if source == "party":
            return self._game.get_party_cre(idx)
        else:
            return self._game.get_out_of_party_cre(idx)

    def _on_compare(self):
        cre_a = self._get_creature(self._combo_a)
        cre_b = self._get_creature(self._combo_b)
        if not cre_a or not cre_b:
            return

        self._populate_stats(cre_a, cre_b)
        self._populate_inventory(cre_a, cre_b)

    def _populate_stats(self, cre_a, cre_b):
        """Fill the stats comparison table."""
        # Define comparison rows: (label, getter, higher_is_better)
        # For THAC0 and AC, lower is better in AD&D.
        rows = [
            ("Strength", lambda c: c.strength, True),
            ("Strength Bonus", lambda c: c.strength_bonus, True),
            ("Dexterity", lambda c: c.dexterity, True),
            ("Constitution", lambda c: c.constitution, True),
            ("Intelligence", lambda c: c.intelligence, True),
            ("Wisdom", lambda c: c.wisdom, True),
            ("Charisma", lambda c: c.charisma, True),
            ("", None, None),  # separator
            ("Current HP", lambda c: c.current_hp, True),
            ("Max HP", lambda c: c.base_hp, True),
            ("", None, None),
            ("THAC0", lambda c: c.thac0, False),
            ("AC", lambda c: c.ac1, False),
            ("Attacks per Round", lambda c: c.attacks, True),
            ("", None, None),
            ("Level (1st class)", lambda c: c.level_first_class, True),
            ("Level (2nd class)", lambda c: c.level_second_class, True),
            ("Level (3rd class)", lambda c: c.level_third_class, True),
            ("", None, None),
            ("Experience", lambda c: c.exp, True),
            ("Gold", lambda c: c.gold, True),
            ("", None, None),
            ("Save vs. Death", lambda c: c.save_death, False),
            ("Save vs. Wands", lambda c: c.save_wands, False),
            ("Save vs. Polymorph", lambda c: c.save_poly, False),
            ("Save vs. Breath", lambda c: c.save_breath, False),
            ("Save vs. Spells", lambda c: c.save_spells, False),
            ("", None, None),
            ("Resist Fire", lambda c: c.resist_fire, True),
            ("Resist Cold", lambda c: c.resist_cold, True),
            ("Resist Electricity", lambda c: c.resist_electricity, True),
            ("Resist Acid", lambda c: c.resist_acid, True),
            ("Resist Magic", lambda c: c.resist_magic, True),
            ("", None, None),
            ("Total Items", lambda c: sum(1 for item in c.get_items() if item.res_name), True),
            ("Known Spells (Priest)", lambda c: c.get_known_spell_count(INF_CRE_ST_PRIEST), True),
            ("Known Spells (Wizard)", lambda c: c.get_known_spell_count(INF_CRE_ST_WIZARD), True),
            ("Known Spells (Innate)", lambda c: c.get_known_spell_count(INF_CRE_ST_INNATE), True),
        ]

        self._stats_table.setRowCount(len(rows))

        for row_idx, (label, getter, higher_is_better) in enumerate(rows):
            if getter is None:
                # Separator row
                item = QTableWidgetItem("")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self._stats_table.setItem(row_idx, 0, item)
                self._stats_table.setItem(row_idx, 1, QTableWidgetItem(""))
                self._stats_table.setItem(row_idx, 2, QTableWidgetItem(""))
                self._stats_table.setRowHeight(row_idx, 8)
                continue

            val_a = getter(cre_a)
            val_b = getter(cre_b)

            item_label = QTableWidgetItem(label)
            item_label.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item_a = QTableWidgetItem(str(val_a))
            item_a.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_b = QTableWidgetItem(str(val_b))
            item_b.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Highlight differences
            if val_a != val_b:
                if higher_is_better:
                    if val_a > val_b:
                        item_a.setBackground(QBrush(COLOR_HIGHER))
                        item_b.setBackground(QBrush(COLOR_LOWER))
                    else:
                        item_a.setBackground(QBrush(COLOR_LOWER))
                        item_b.setBackground(QBrush(COLOR_HIGHER))
                else:
                    # Lower is better (THAC0, AC, saves)
                    if val_a < val_b:
                        item_a.setBackground(QBrush(COLOR_HIGHER))
                        item_b.setBackground(QBrush(COLOR_LOWER))
                    else:
                        item_a.setBackground(QBrush(COLOR_LOWER))
                        item_b.setBackground(QBrush(COLOR_HIGHER))

            self._stats_table.setItem(row_idx, 0, item_label)
            self._stats_table.setItem(row_idx, 1, item_a)
            self._stats_table.setItem(row_idx, 2, item_b)

    def _populate_inventory(self, cre_a, cre_b):
        """Fill the inventory comparison table showing items unique to each character."""
        items_a = {item.res_name for item in cre_a.get_items() if item.res_name}
        items_b = {item.res_name for item in cre_b.get_items() if item.res_name}

        all_items = sorted(items_a | items_b)

        self._inv_table.setRowCount(len(all_items))

        for row_idx, item_name in enumerate(all_items):
            in_a = item_name in items_a
            in_b = item_name in items_b

            item_label = QTableWidgetItem(item_name)
            item_col_a = QTableWidgetItem("Yes" if in_a else "-")
            item_col_a.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_col_b = QTableWidgetItem("Yes" if in_b else "-")
            item_col_b.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Highlight items unique to one character
            if in_a and not in_b:
                item_col_a.setBackground(QBrush(COLOR_HIGHER))
                item_col_b.setBackground(QBrush(COLOR_LOWER))
            elif in_b and not in_a:
                item_col_a.setBackground(QBrush(COLOR_LOWER))
                item_col_b.setBackground(QBrush(COLOR_HIGHER))

            self._inv_table.setItem(row_idx, 0, item_label)
            self._inv_table.setItem(row_idx, 1, item_col_a)
            self._inv_table.setItem(row_idx, 2, item_col_b)
