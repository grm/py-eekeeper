"""Dialog for editing global variables in a save game."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QDialogButtonBox, QLineEdit, QLabel,
    QInputDialog,
)
from PySide6.QtCore import Qt

from ..formats.inf_game import InfGame, GameGlobal


class GlobalsEditorDialog(QDialog):
    """Editor for GAM global variables (name/value pairs)."""

    def __init__(self, parent=None, game: InfGame = None):
        super().__init__(parent)
        self.setWindowTitle("Global Variables")
        self.setMinimumSize(600, 500)
        self._game = game
        self._globals: list[GameGlobal] = []
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
        self._table.setHorizontalHeaderLabels(["Name", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
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
        if not self._game:
            return
        self._globals = self._game.get_globals()
        self._refresh_table()

    def _refresh_table(self):
        self._table.blockSignals(True)
        filter_text = self._filter_edit.text().upper()
        visible = [g for g in self._globals if filter_text in g.name.upper()]

        self._table.setRowCount(len(visible))
        for row, g in enumerate(visible):
            name_item = QTableWidgetItem(g.name)
            name_item.setData(Qt.ItemDataRole.UserRole, self._globals.index(g))
            self._table.setItem(row, 0, name_item)

            value_item = QTableWidgetItem(str(g.value))
            self._table.setItem(row, 1, value_item)
        self._table.blockSignals(False)

    def _on_filter_changed(self, _text: str):
        self._refresh_table()

    def _on_cell_changed(self, row: int, col: int):
        item = self._table.item(row, 0)
        if not item:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx is None or idx >= len(self._globals):
            return

        if col == 0:
            new_name = self._table.item(row, 0).text()[:32]
            self._globals[idx].name = new_name
        elif col == 1:
            try:
                self._globals[idx].value = int(self._table.item(row, 1).text())
            except ValueError:
                pass

    def _on_add(self):
        name, ok = QInputDialog.getText(self, "Add Variable", "Name (max 32 chars):")
        if not ok or not name:
            return
        name = name[:32]
        value, ok = QInputDialog.getInt(self, "Add Variable", "Value:", 0, -2147483648, 2147483647)
        if not ok:
            return
        self._globals.append(GameGlobal(name=name, value=value, raw_data=bytes(0x54)))
        self._refresh_table()

    def _on_remove(self):
        row = self._table.currentRow()
        if row < 0:
            return
        item = self._table.item(row, 0)
        if not item:
            return
        idx = item.data(Qt.ItemDataRole.UserRole)
        if idx is not None and idx < len(self._globals):
            self._globals.pop(idx)
            self._refresh_table()

    def _on_accept(self):
        if self._game:
            self._game.set_globals(self._globals)
        self.accept()
