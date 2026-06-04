"""Proficiencies tab — edit weapon proficiency levels."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QSpinBox, QStyledItemDelegate,
)
from PySide6.QtCore import Qt

from ..formats.inf_creature import InfCreature, ProfData
from ..app import EEKeeperApp
from ..formats.constants import PROF_LARGESWORDS, PROF_SWORDANDSHIELD


class SpinDelegate(QStyledItemDelegate):
    """Delegate that uses a SpinBox (0-5) for proficiency editing."""

    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setRange(0, 5)
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.ItemDataRole.EditRole)
        if value is not None:
            editor.setValue(int(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), Qt.ItemDataRole.EditRole)


class ProficienciesTab(QWidget):
    """Tab for editing weapon proficiencies."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._creature: InfCreature | None = None
        self._loading = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Proficiency", "Stars"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 80)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setItemDelegateForColumn(1, SpinDelegate(self._table))
        self._table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self._table)

    def load_creature(self, creature: InfCreature):
        self._loading = True
        self._creature = creature
        self._refresh_table()
        self._loading = False

    def _refresh_table(self):
        self._table.setRowCount(0)
        if not self._creature:
            return

        app = EEKeeperApp.instance()
        profs = self._creature.get_profs()
        prof_map = {p.prof_id: p.value for p in profs}

        prof_items = app.vl_profs.get_items()
        self._table.setRowCount(len(prof_items))

        for row, item in enumerate(prof_items):
            name_cell = QTableWidgetItem(item.name)
            name_cell.setFlags(name_cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_cell.setData(Qt.ItemDataRole.UserRole, item.index)
            self._table.setItem(row, 0, name_cell)

            value = prof_map.get(item.index, 0)
            value_cell = QTableWidgetItem(str(value))
            self._table.setItem(row, 1, value_cell)

    def _on_cell_changed(self, row: int, col: int):
        if self._loading or col != 1 or not self._creature:
            return

        name_item = self._table.item(row, 0)
        value_item = self._table.item(row, 1)
        if not name_item or not value_item:
            return

        prof_id = name_item.data(Qt.ItemDataRole.UserRole)
        try:
            value = int(value_item.text())
        except ValueError:
            return

        value = max(0, min(5, value))

        # Update creature profs
        profs = self._creature.get_profs()
        found = False
        for p in profs:
            if p.prof_id == prof_id:
                p.value = value
                found = True
                break
        if not found and value > 0:
            profs.append(ProfData(prof_id=prof_id, value=value))

        # Remove zero-value profs
        profs = [p for p in profs if p.value > 0]
        self._creature.set_profs(profs)
