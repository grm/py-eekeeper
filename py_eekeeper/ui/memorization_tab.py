"""Memorization tab — edit spell memorization slots per level."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
)
from PySide6.QtCore import Qt

from ..formats.inf_creature import InfCreature, MemInfo
from ..formats.constants import INF_CRE_ST_WIZARD, INF_CRE_ST_PRIEST, INF_CRE_ST_INNATE
from ..app import EEKeeperApp


SPELL_TYPE_NAMES = {
    INF_CRE_ST_WIZARD: "Wizard",
    INF_CRE_ST_PRIEST: "Priest",
    INF_CRE_ST_INNATE: "Innate",
}


class MemorizationTab(QWidget):
    """Tab for editing spell memorization info (slots per level/type)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._creature: InfCreature | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Type", "Level", "Max Memorizable"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        self._btn_plus = QPushButton("+1")
        self._btn_plus.clicked.connect(lambda: self._modify_count(1))
        btn_layout.addWidget(self._btn_plus)

        self._btn_minus = QPushButton("-1")
        self._btn_minus.clicked.connect(lambda: self._modify_count(-1))
        btn_layout.addWidget(self._btn_minus)

        self._btn_max_plus = QPushButton("Max +1 (All)")
        self._btn_max_plus.clicked.connect(lambda: self._modify_all(1))
        btn_layout.addWidget(self._btn_max_plus)

        self._btn_max_minus = QPushButton("Max -1 (All)")
        self._btn_max_minus.clicked.connect(lambda: self._modify_all(-1))
        btn_layout.addWidget(self._btn_max_minus)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def load_creature(self, creature: InfCreature):
        self._creature = creature
        self._refresh_table()

    def _refresh_table(self):
        self._table.setRowCount(0)
        if not self._creature:
            return

        mem_info = self._creature.get_memorization_info()
        self._table.setRowCount(len(mem_info))

        for row, mi in enumerate(mem_info):
            type_name = SPELL_TYPE_NAMES.get(mi.type, f"Unknown ({mi.type})")
            type_item = QTableWidgetItem(type_name)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, type_item)

            level_item = QTableWidgetItem(str(mi.level + 1))
            level_item.setFlags(level_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 1, level_item)

            count_item = QTableWidgetItem(str(mi.num_memorizable))
            self._table.setItem(row, 2, count_item)

        self._table.cellChanged.connect(self._on_cell_changed)

    def _on_cell_changed(self, row: int, col: int):
        if col != 2 or not self._creature:
            return
        item = self._table.item(row, col)
        if not item:
            return
        try:
            value = int(item.text())
        except ValueError:
            return

        mem_info = self._creature.get_memorization_info()
        if 0 <= row < len(mem_info):
            mem_info[row].num_memorizable = max(0, value)
            self._creature.set_memorization_info(mem_info)

    def _is_mem_limit_reached(self, current_value: int) -> bool:
        """Check if the memorization limit prevents incrementing.

        Returns True if the limit is reached and the increment should be blocked.
        """
        app = EEKeeperApp.instance()
        if not app.config.use_mem_spell_limit:
            return False
        return current_value >= app.config.mem_spell_limit

    def _modify_count(self, delta: int):
        row = self._table.currentRow()
        if row < 0 or not self._creature:
            return

        mem_info = self._creature.get_memorization_info()
        if 0 <= row < len(mem_info):
            if delta > 0 and self._is_mem_limit_reached(mem_info[row].num_memorizable):
                return
            mem_info[row].num_memorizable = max(0, mem_info[row].num_memorizable + delta)
            self._creature.set_memorization_info(mem_info)
            self._table.blockSignals(True)
            self._table.item(row, 2).setText(str(mem_info[row].num_memorizable))
            self._table.blockSignals(False)

    def _modify_all(self, delta: int):
        if not self._creature:
            return
        mem_info = self._creature.get_memorization_info()
        for mi in mem_info:
            if delta > 0 and self._is_mem_limit_reached(mi.num_memorizable):
                continue
            mi.num_memorizable = max(0, mi.num_memorizable + delta)
        self._creature.set_memorization_info(mem_info)
        self._table.blockSignals(True)
        for row, mi in enumerate(mem_info):
            item = self._table.item(row, 2)
            if item:
                item.setText(str(mi.num_memorizable))
        self._table.blockSignals(False)
