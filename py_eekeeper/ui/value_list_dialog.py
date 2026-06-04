"""Dialog for editing a ValueList (generic key/value list editor)."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QDialogButtonBox, QInputDialog,
)
from PySide6.QtCore import Qt

from ..resources.value_list import ValueList, ValueItem


class ValueListDialog(QDialog):
    """Generic editor for ValueList data."""

    def __init__(self, parent=None, value_list: ValueList = None, title: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title or "Edit List")
        self.setMinimumSize(400, 500)
        self._value_list = value_list
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Index", "Name"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 80)
        layout.addWidget(self._table)

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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        self._table.setRowCount(0)
        if not self._value_list:
            return

        items = self._value_list.get_items()
        self._table.setRowCount(len(items))
        for row, item in enumerate(items):
            idx_cell = QTableWidgetItem(str(item.index))
            self._table.setItem(row, 0, idx_cell)
            name_cell = QTableWidgetItem(item.name)
            self._table.setItem(row, 1, name_cell)

    def _on_add(self):
        index, ok1 = QInputDialog.getInt(self, "Add Item", "Index:", 0, 0, 65535)
        if not ok1:
            return
        name, ok2 = QInputDialog.getText(self, "Add Item", "Name:")
        if not ok2 or not name:
            return
        if self._value_list:
            self._value_list.add(ValueItem(index=index, name=name))
            self._load_data()

    def _on_edit(self):
        row = self._table.currentRow()
        if row < 0 or not self._value_list:
            return
        items = self._value_list.get_items()
        if row >= len(items):
            return

        name, ok = QInputDialog.getText(
            self, "Edit Item", "Name:", text=items[row].name
        )
        if ok and name:
            items[row].name = name
            self._load_data()

    def _on_remove(self):
        row = self._table.currentRow()
        if row < 0 or not self._value_list:
            return
        items = self._value_list.get_items()
        if row >= len(items):
            return
        self._value_list.remove(items[row].index)
        self._load_data()
