"""Dialog for editing creature local variables (opcode 309 affects)."""

import struct

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QDialogButtonBox, QLineEdit, QLabel,
    QInputDialog,
)
from PySide6.QtCore import Qt

from ..formats.inf_creature import InfCreature
from ..formats.inf_affect import InfAffect, AFF_V2_SIZE
from ..formats.constants import AFF_TYPE_SET_LOCAL_VAR, AFF_TARG_CRE


class LocalsEditorDialog(QDialog):
    """Editor for creature local variables (SET_LOCAL_VARIABLE affects, opcode 309)."""

    def __init__(self, parent=None, creature: InfCreature = None):
        super().__init__(parent)
        self.setWindowTitle("Local Variables")
        self.setMinimumSize(600, 500)
        self._creature = creature
        self._local_vars: list[dict] = []  # [{name: str, value: int, affect: InfAffect}]
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Type to filter by name...")
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._filter_edit)
        layout.addLayout(filter_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Variable Name", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(1, 120)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self._table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_add)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self._on_remove)
        btn_layout.addWidget(btn_remove)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        if not self._creature:
            return
        # Get all affects from the creature (including proficiency/speed ones
        # since we need the full list). We filter for opcode 309.
        all_affects = self._creature.get_affects()
        self._local_vars = []
        for aff in all_affects:
            if aff.opcode == AFF_TYPE_SET_LOCAL_VAR:
                self._local_vars.append({
                    "name": aff.resource,
                    "value": aff.parameter1,
                    "affect": aff,
                })
        self._refresh_table()

    def _refresh_table(self):
        self._table.blockSignals(True)
        filter_text = self._filter_edit.text().upper()
        visible = [
            (i, v) for i, v in enumerate(self._local_vars)
            if filter_text in v["name"].upper()
        ]

        self._table.setRowCount(len(visible))
        for row, (idx, var) in enumerate(visible):
            name_item = QTableWidgetItem(var["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, idx)
            self._table.setItem(row, 0, name_item)

            value_item = QTableWidgetItem(str(var["value"]))
            self._table.setItem(row, 1, value_item)
        self._table.blockSignals(False)

    def _on_filter_changed(self, _text: str):
        self._refresh_table()

    def _on_cell_changed(self, row: int, col: int):
        item = self._table.item(row, 0)
        if not item:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx is None or idx >= len(self._local_vars):
            return

        if col == 0:
            # Variable name: max 8 chars (resource field limit)
            new_name = self._table.item(row, 0).text()[:8]
            self._local_vars[idx]["name"] = new_name
        elif col == 1:
            try:
                self._local_vars[idx]["value"] = int(self._table.item(row, 1).text())
            except ValueError:
                pass

    def _on_add(self):
        name, ok = QInputDialog.getText(
            self, "Add Local Variable", "Name (max 8 chars):"
        )
        if not ok or not name:
            return
        name = name[:8]
        value, ok = QInputDialog.getInt(
            self, "Add Local Variable", "Value:",
            0, -2147483648, 2147483647,
        )
        if not ok:
            return
        # Create a new affect for the local variable
        aff = self._make_local_var_affect(name, value)
        self._local_vars.append({"name": name, "value": value, "affect": aff})
        self._refresh_table()

    def _on_remove(self):
        row = self._table.currentRow()
        if row < 0:
            return
        item = self._table.item(row, 0)
        if not item:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx is not None and idx < len(self._local_vars):
            self._local_vars.pop(idx)
            self._refresh_table()

    def _on_accept(self):
        if not self._creature:
            self.accept()
            return

        # Get current affects list (non-proficiency/non-speed)
        current_affects = self._creature.get_affects()
        # Remove all existing opcode 309 affects
        non_local_affects = [
            aff for aff in current_affects
            if aff.opcode != AFF_TYPE_SET_LOCAL_VAR
        ]
        # Build new opcode 309 affects from our edited list
        new_local_affects = []
        for var in self._local_vars:
            aff = var.get("affect")
            if aff:
                # Update the existing affect with potentially edited values
                aff.resource = var["name"]
                aff.parameter1 = var["value"]
            else:
                aff = self._make_local_var_affect(var["name"], var["value"])
            new_local_affects.append(aff)

        # Merge and set back
        self._creature.set_affects(non_local_affects + new_local_affects)
        self.accept()

    @staticmethod
    def _make_local_var_affect(name: str, value: int) -> InfAffect:
        """Create a new SET_LOCAL_VARIABLE affect (opcode 309)."""
        raw_data = bytearray(AFF_V2_SIZE)
        # Set common v2 header bytes used by the engine
        struct.pack_into("<I", raw_data, 120, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 124, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 128, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 132, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 136, 0x01)
        struct.pack_into("<I", raw_data, 156, 0xFFFFFFFF)
        struct.pack_into("<I", raw_data, 192, 0x0F)
        struct.pack_into("<I", raw_data, 196, 0x01)

        aff = InfAffect(
            opcode=AFF_TYPE_SET_LOCAL_VAR,
            target_type=AFF_TARG_CRE,
            parameter1=value,
            parameter2=0,
            timing_mode=9,  # Instant/permanent
            duration=0,
            probability1=100,
            probability2=0,
            resource=name[:8],
            special=2,
            raw_data=bytes(raw_data),
        )
        return aff
