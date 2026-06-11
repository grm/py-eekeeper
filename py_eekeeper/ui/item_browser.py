"""Item browser dialog — browse and select game items."""

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLineEdit,
    QDialogButtonBox, QLabel, QComboBox, QTextBrowser,
    QHeaderView, QAbstractItemView,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize

from ..app import EEKeeperApp
from ..resources.descriptions import get_item_description
from ..resources.item_info import ITEM_CATEGORY_NAMES, ITEM_TYPE_NAMES, ItemInfo


@dataclass(frozen=True)
class _ItemBrowserEntry:
    res_name: str
    friendly_name: str
    info: ItemInfo | None

    @property
    def type_id(self) -> int | None:
        return self.info.type_id if self.info else None

    @property
    def type_name(self) -> str:
        return self.info.type_name if self.info else "Unknown"

    @property
    def category(self) -> str:
        return self.info.category if self.info else "misc"


class ItemBrowserDialog(QDialog):
    """Browse and select an item resource."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Item Browser")
        self.setMinimumSize(900, 650)
        self._selected_item: str = ""
        self._all_items: list[_ItemBrowserEntry] = []
        self._setup_ui()
        self._load_items()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Filters
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Category:"))
        self._combo_category = QComboBox()
        self._combo_category.addItem("All", "")
        for category, label in ITEM_CATEGORY_NAMES.items():
            self._combo_category.addItem(label, category)
        self._combo_category.currentIndexChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self._combo_category)

        filter_layout.addWidget(QLabel("Type:"))
        self._combo_type = QComboBox()
        self._combo_type.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._combo_type)

        filter_layout.addWidget(QLabel("Search:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter by name or resource...")
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._filter_edit)
        layout.addLayout(filter_layout)

        # Item table
        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            "Icon", "Type", "Resource", "Name", "Value",
            "Weight", "Lore", "Ench", "Stack",
        ])
        self._table.setIconSize(QSize(48, 48))
        self._table.verticalHeader().setDefaultSectionSize(54)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for column in range(4, 9):
            self._table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 56)
        self._table.setColumnWidth(1, 115)
        self._table.setColumnWidth(2, 85)
        self._table.setColumnWidth(4, 65)
        self._table.setColumnWidth(5, 60)
        self._table.setColumnWidth(6, 50)
        self._table.setColumnWidth(7, 50)
        self._table.setColumnWidth(8, 55)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.currentCellChanged.connect(self._on_current_cell_changed)
        layout.addWidget(self._table)

        self._details = QTextBrowser()
        self._details.setMaximumHeight(120)
        layout.addWidget(self._details)

        # OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_items(self):
        app = EEKeeperApp.instance()
        self._all_items = []
        for res_name, friendly in app.iter_items():
            info = app.get_item_info(res_name)
            self._all_items.append(_ItemBrowserEntry(res_name, friendly, info))
        self._refresh_type_filter()
        self._refresh_list()

    def _refresh_type_filter(self):
        selected_type = self._combo_type.currentData()
        category = self._combo_category.currentData() or ""
        type_ids = sorted({
            entry.type_id
            for entry in self._all_items
            if entry.type_id is not None and (not category or entry.category == category)
        }, key=lambda type_id: ITEM_TYPE_NAMES.get(type_id, "Unknown"))

        self._combo_type.blockSignals(True)
        self._combo_type.clear()
        self._combo_type.addItem("All", None)
        for type_id in type_ids:
            self._combo_type.addItem(ITEM_TYPE_NAMES.get(type_id, "Unknown"), type_id)
        if selected_type is not None:
            index = self._combo_type.findData(selected_type)
            if index >= 0:
                self._combo_type.setCurrentIndex(index)
        self._combo_type.blockSignals(False)

    def _refresh_list(self):
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        filter_text = self._filter_edit.text().upper()
        category = self._combo_category.currentData() or ""
        type_id = self._combo_type.currentData()
        app = EEKeeperApp.instance()

        for entry in self._all_items:
            if category and entry.category != category:
                continue
            if type_id is not None and entry.type_id != type_id:
                continue
            if (
                filter_text
                and filter_text not in entry.res_name.upper()
                and filter_text not in entry.friendly_name.upper()
                and filter_text not in entry.type_name.upper()
            ):
                continue

            row = self._table.rowCount()
            self._table.insertRow(row)
            tooltip = self._build_tooltip(entry)

            icon_item = self._make_item("", entry.res_name, tooltip)
            if app.spell_bitmaps:
                icon = app.spell_bitmaps.get_item_icon(entry.res_name)
                if icon:
                    icon_item.setIcon(QIcon(icon))
            self._table.setItem(row, 0, icon_item)

            self._table.setItem(row, 1, self._make_item(entry.type_name, entry.res_name, tooltip))
            self._table.setItem(row, 2, self._make_item(entry.res_name, entry.res_name, tooltip))
            self._table.setItem(row, 3, self._make_item(entry.friendly_name, entry.res_name, tooltip))

            info = entry.info
            values = [
                info.base_value if info else None,
                info.weight if info else None,
                info.lore if info else None,
                info.enchantment if info else None,
                info.max_stackable if info else None,
            ]
            for column, value in enumerate(values, start=4):
                cell = self._make_item("" if value is None else str(value), entry.res_name, tooltip)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._table.setItem(row, column, cell)

        self._table.setSortingEnabled(True)
        self._details.clear()

    def _make_item(self, text: str, res_name: str, tooltip: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, res_name)
        if tooltip:
            item.setToolTip(tooltip)
        return item

    def _build_tooltip(self, entry: _ItemBrowserEntry) -> str:
        lines = [f"Resource: {entry.res_name}"]
        info = entry.info
        if info:
            lines.append(f"Category: {ITEM_CATEGORY_NAMES.get(entry.category, entry.category)}")
            lines.append(f"Type: {entry.type_name}")
            if info.generic_name and info.generic_name != info.display_name:
                lines.append(f"Generic name: {info.generic_name}")
            lines.append(f"Identified name: {info.display_name}")
            if info.enchantment is not None:
                lines.append(f"Enchantment: {info.enchantment}")
            if info.base_value is not None:
                lines.append(f"Base value: {info.base_value}")
            if info.weight is not None:
                lines.append(f"Weight: {info.weight}")
            if info.lore is not None:
                lines.append(f"Lore: {info.lore}")
            if info.max_stackable is not None:
                lines.append(f"Max stack: {info.max_stackable}")

        desc = get_item_description(entry.res_name)
        if desc:
            lines.extend(["", desc])
        return "\n".join(lines)

    def _on_category_changed(self, *_args):
        self._refresh_type_filter()
        self._refresh_list()

    def _on_filter_changed(self, *_args):
        self._refresh_list()

    def _on_current_cell_changed(self, row: int, _column: int, _old_row: int, _old_column: int):
        if row < 0:
            self._details.clear()
            return
        item = self._table.item(row, 0)
        if item:
            self._details.setPlainText(item.toolTip())

    def _on_double_click(self, *_args):
        self._on_accept()

    def _on_accept(self):
        current = self._table.currentItem()
        if current:
            self._selected_item = current.data(Qt.ItemDataRole.UserRole)
            self.accept()

    @property
    def selected_item(self) -> str:
        return self._selected_item
