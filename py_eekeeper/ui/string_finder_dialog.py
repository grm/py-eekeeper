"""Dialog for searching strings in the TLK file."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QApplication,
)
from PySide6.QtCore import Qt

from ..formats.inf_tlk import InfTlk


class StringFinderDialog(QDialog):
    """Search dialog.tlk for strings matching criteria."""

    def __init__(self, parent=None, tlk: InfTlk = None):
        super().__init__(parent)
        self.setWindowTitle("String Finder")
        self.setMinimumSize(700, 500)
        self._tlk = tlk
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search criteria
        criteria_layout = QHBoxLayout()
        criteria_layout.addWidget(QLabel("Search:"))
        self._edit_search = QLineEdit()
        self._edit_search.setPlaceholderText("Enter text to search for...")
        self._edit_search.returnPressed.connect(self._on_search)
        criteria_layout.addWidget(self._edit_search)

        criteria_layout.addWidget(QLabel("Max Length:"))
        self._spin_max_len = QSpinBox()
        self._spin_max_len.setRange(0, 10000)
        self._spin_max_len.setValue(100)
        criteria_layout.addWidget(self._spin_max_len)

        self._btn_search = QPushButton("Search")
        self._btn_search.clicked.connect(self._on_search)
        criteria_layout.addWidget(self._btn_search)

        layout.addLayout(criteria_layout)

        # Results table
        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Index", "String"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 80)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        # Status
        self._label_status = QLabel("")
        layout.addWidget(self._label_status)

    def _on_search(self):
        if not self._tlk:
            return

        search_text = self._edit_search.text().lower()
        max_len = self._spin_max_len.value()

        if not search_text and (max_len == 0 or max_len > 100):
            result = QMessageBox.warning(
                self, "Large Search",
                "This will generate many results and may take a while. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.No:
                return

        self._table.setRowCount(0)
        self._label_status.setText("Searching...")
        QApplication.processEvents()

        results = []
        for i in range(self._tlk.string_count):
            text = self._tlk.get_string(i)
            if text is None:
                continue
            if max_len > 0 and len(text) > max_len:
                continue
            if search_text and search_text not in text.lower():
                continue
            results.append((i, text))
            if len(results) >= 5000:
                break

        self._table.setRowCount(len(results))
        for row, (idx, text) in enumerate(results):
            idx_item = QTableWidgetItem(str(idx))
            idx_item.setFlags(idx_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, idx_item)

            text_item = QTableWidgetItem(text.replace("\n", " "))
            text_item.setFlags(text_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 1, text_item)

        self._label_status.setText(f"Found {len(results)} results")
