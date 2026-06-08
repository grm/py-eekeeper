"""Affects tab — view and edit creature effects."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
)
from PySide6.QtCore import Qt

from ..formats.inf_creature import InfCreature
from ..formats.inf_affect import InfAffect
from ..app import EEKeeperApp


class AffectsTab(QWidget):
    """Tab for viewing/editing creature affects (effects)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._creature: InfCreature | None = None
        self._affects: list[InfAffect] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Opcode", "Effect", "Target", "Param1", "Param2",
            "Timing", "Duration", "Resource",
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self._table)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_add)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("Edit")
        btn_edit.clicked.connect(self._on_edit)
        btn_layout.addWidget(btn_edit)

        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self._on_remove)
        btn_layout.addWidget(btn_remove)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def load_creature(self, creature: InfCreature):
        self._creature = creature
        self._affects = creature.get_affects()
        self._refresh_table()

    def _refresh_table(self):
        self._table.setRowCount(len(self._affects))
        for row, aff in enumerate(self._affects):
            self._table.setItem(row, 0, QTableWidgetItem(str(aff.opcode)))
            self._table.setItem(row, 1, QTableWidgetItem(self._effect_name(aff.opcode)))
            self._table.setItem(row, 2, QTableWidgetItem(str(aff.target_type)))
            self._table.setItem(row, 3, QTableWidgetItem(str(aff.parameter1)))
            self._table.setItem(row, 4, QTableWidgetItem(str(aff.parameter2)))
            self._table.setItem(row, 5, QTableWidgetItem(str(aff.timing_mode)))
            self._table.setItem(row, 6, QTableWidgetItem(str(aff.duration)))
            self._table.setItem(row, 7, QTableWidgetItem(aff.resource or aff.resource3))

    @staticmethod
    def _effect_name(opcode: int) -> str:
        item = EEKeeperApp.instance().vl_affects.find_by_index(opcode)
        return item.name if item else ""

    def _on_add(self):
        if not self._creature:
            return
        from .affect_edit_dialog import AffectEditDialog
        dialog = AffectEditDialog(self, InfAffect())
        if dialog.exec():
            self._affects.append(dialog.get_affect())
            self._creature.set_affects(self._affects)
            self._refresh_table()

    def _on_edit(self):
        if not self._creature:
            return
        row = self._table.currentRow()
        if row < 0 or row >= len(self._affects):
            return
        from .affect_edit_dialog import AffectEditDialog
        dialog = AffectEditDialog(self, self._affects[row])
        if dialog.exec():
            self._affects[row] = dialog.get_affect()
            self._creature.set_affects(self._affects)
            self._refresh_table()

    def _on_remove(self):
        if not self._creature:
            return
        row = self._table.currentRow()
        if row < 0 or row >= len(self._affects):
            return
        self._affects.pop(row)
        self._creature.set_affects(self._affects)
        self._refresh_table()
