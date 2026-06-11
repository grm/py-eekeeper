"""Inventory tab — edit character items and equipment slots."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView, QMessageBox,
)
from PySide6.QtCore import Qt, QMimeData, QSize
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon

from ..formats.inf_creature import InfCreature, CreItem
from ..formats.constants import INF_NUM_ITEMSLOTS
from ..app import EEKeeperApp
from ..resources.descriptions import get_item_description


SLOT_NAMES = [
    "Helmet", "Armor", "Shield", "Gloves", "L. Ring", "R. Ring",
    "Amulet", "Belt", "Boots", "Weapon 1", "Weapon 2", "Weapon 3",
    "Weapon 4", "Quiver 1", "Quiver 2", "Quiver 3", "Unused",
    "Cloak", "Quick Item 1", "Quick Item 2", "Quick Item 3",
    "Inventory 1", "Inventory 2", "Inventory 3", "Inventory 4",
    "Inventory 5", "Inventory 6", "Inventory 7", "Inventory 8",
    "Inventory 9", "Inventory 10", "Inventory 11", "Inventory 12",
    "Inventory 13", "Inventory 14", "Inventory 15", "Inventory 16",
    "Selected Weapon",
]
assert len(SLOT_NAMES) == INF_NUM_ITEMSLOTS


class _DragDropInventoryTable(QTableWidget):
    """QTableWidget subclass that supports internal drag & drop to swap item slots."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_source_row: int = -1
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropOverwriteMode(False)

    def startDrag(self, supportedActions):
        """Record the source row when a drag begins."""
        self._drag_source_row = self.currentRow()
        super().startDrag(supportedActions)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept internal drags only."""
        if event.source() is self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Accept move over any row."""
        if event.source() is self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Swap items between source and target rows instead of moving rows."""
        if event.source() is not self:
            event.ignore()
            return

        target_item = self.itemAt(event.position().toPoint())
        target_row = target_item.row() if target_item else -1

        if target_row < 0 or target_row == self._drag_source_row:
            event.ignore()
            return

        # Notify the parent InventoryTab to perform the swap
        inventory_tab = self.parent()
        while inventory_tab and not isinstance(inventory_tab, InventoryTab):
            inventory_tab = inventory_tab.parent()

        if inventory_tab:
            inventory_tab._swap_items(self._drag_source_row, target_row)

        event.acceptProposedAction()
        self._drag_source_row = -1


class InventoryTab(QWidget):
    """Tab for viewing and editing character inventory."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._creature: InfCreature | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self._table = _DragDropInventoryTable()
        self._table.setColumnCount(12)
        self._table.setHorizontalHeaderLabels([
            "Icon", "Slot", "Type", "Resource", "Item", "Qty", "ID'd",
            "Stack", "Value", "Weight", "Lore", "Ench",
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for column in range(5, 12):
            self._table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
        self._table.setIconSize(QSize(48, 48))
        self._table.verticalHeader().setDefaultSectionSize(54)
        self._table.setColumnWidth(0, 56)
        self._table.setColumnWidth(1, 120)
        self._table.setColumnWidth(2, 105)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(5, 75)
        self._table.setColumnWidth(6, 45)
        self._table.setColumnWidth(7, 50)
        self._table.setColumnWidth(8, 60)
        self._table.setColumnWidth(9, 55)
        self._table.setColumnWidth(10, 45)
        self._table.setColumnWidth(11, 45)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        self._btn_set = QPushButton("Set Item...")
        self._btn_set.clicked.connect(self._on_set_item)
        btn_layout.addWidget(self._btn_set)

        self._btn_remove = QPushButton("Remove Item")
        self._btn_remove.clicked.connect(self._on_remove_item)
        btn_layout.addWidget(self._btn_remove)

        self._btn_identify = QPushButton("Identify All")
        self._btn_identify.clicked.connect(self._on_identify_all)
        btn_layout.addWidget(self._btn_identify)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def load_creature(self, creature: InfCreature):
        self._creature = creature
        self._refresh_table()
        self._warn_unknown_items()

    def _warn_unknown_items(self):
        if not self._creature:
            return

        app = EEKeeperApp.instance()
        unknown = sorted({
            item.res_name
            for item in self._creature.get_items()
            if item.res_name and not app.has_item(item.res_name)
        })
        if not unknown:
            return

        QMessageBox.warning(
            self,
            "Unknown items",
            "Some items assigned to this character were not found in the game "
            "database. If you save this character, those items may not work "
            "correctly in-game.\n\nCannot find: " + ", ".join(unknown),
        )

    def _refresh_table(self):
        self._table.setRowCount(0)
        if not self._creature:
            return

        items = self._creature.get_items()
        app = EEKeeperApp.instance()

        self._table.setRowCount(INF_NUM_ITEMSLOTS)
        for i in range(INF_NUM_ITEMSLOTS):
            slot_name = SLOT_NAMES[i] if i < len(SLOT_NAMES) else f"Slot {i}"
            slot_item = QTableWidgetItem(slot_name)
            slot_item.setFlags(slot_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(i, 1, slot_item)

            item = items[i] if i < len(items) else CreItem()
            info = app.get_item_info(item.res_name) if item.res_name else None
            if item.res_name:
                friendly = info.display_name if info else app.get_item_name(item.res_name)
                name_text = f"{item.res_name} - {friendly}"
                if not info:
                    name_text += " (unknown)"
            else:
                name_text = "(empty)"

            tooltip = self._build_item_tooltip(item, info)

            icon_item = QTableWidgetItem()
            icon_item.setFlags(icon_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if item.res_name and app.spell_bitmaps:
                icon = app.spell_bitmaps.get_item_icon(item.res_name)
                if icon:
                    icon_item.setIcon(QIcon(icon))
            if tooltip:
                icon_item.setToolTip(tooltip)
            self._table.setItem(i, 0, icon_item)

            type_item = QTableWidgetItem(info.type_name if info else "")
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if tooltip:
                type_item.setToolTip(tooltip)
            self._table.setItem(i, 2, type_item)

            resource_item = QTableWidgetItem(item.res_name if item.res_name else "")
            resource_item.setFlags(resource_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if tooltip:
                resource_item.setToolTip(tooltip)
            self._table.setItem(i, 3, resource_item)

            name_item = QTableWidgetItem(name_text)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if tooltip:
                name_item.setToolTip(tooltip)
            elif item.res_name:
                desc = get_item_description(item.res_name)
                if desc:
                    name_item.setToolTip(desc)
            self._table.setItem(i, 4, name_item)

            if item.res_name:
                qty_text = f"{item.quantity1}/{item.quantity2}/{item.quantity3}"
            else:
                qty_text = ""
            qty_item = QTableWidgetItem(qty_text)
            self._table.setItem(i, 5, qty_item)

            id_item = QTableWidgetItem("Yes" if item.identified else "No" if item.res_name else "")
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(i, 6, id_item)

            values = [
                info.max_stackable if info else None,
                info.base_value if info else None,
                info.weight if info else None,
                info.lore if info else None,
                info.enchantment if info else None,
            ]
            for offset, value in enumerate(values, start=7):
                value_item = QTableWidgetItem("" if value is None else str(value))
                value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if tooltip:
                    value_item.setToolTip(tooltip)
                self._table.setItem(i, offset, value_item)

    def _build_item_tooltip(self, item: CreItem, info) -> str:
        if not item.res_name:
            return ""

        lines = [f"Resource: {item.res_name}"]
        if info:
            if info.type_name:
                lines.append(f"Type: {info.type_name}")
            if info.generic_name and info.generic_name != info.display_name:
                lines.append(f"Generic name: {info.generic_name}")
            if info.display_name:
                lines.append(f"Identified name: {info.display_name}")
            if info.enchantment is not None:
                lines.append(f"Enchantment: {info.enchantment}")
            if info.base_value is not None:
                lines.append(f"Base value: {info.base_value}")
            if info.weight is not None:
                lines.append(f"Weight: {info.weight}")
            if info.max_stackable is not None:
                lines.append(f"Max stack: {info.max_stackable}")
            if info.lore is not None:
                lines.append(f"Lore: {info.lore}")
        else:
            lines.append("Status: not found in game resources")

        description = get_item_description(item.res_name)
        if description:
            lines.extend(["", description])
        return "\n".join(lines)

    def _swap_items(self, source_row: int, target_row: int):
        """Swap items between two inventory slots."""
        if not self._creature:
            return
        if source_row == target_row:
            return
        if not (0 <= source_row < INF_NUM_ITEMSLOTS and 0 <= target_row < INF_NUM_ITEMSLOTS):
            return

        item_a = self._creature.get_item(source_row)
        item_b = self._creature.get_item(target_row)
        self._creature.set_item(source_row, item_b)
        self._creature.set_item(target_row, item_a)
        self._refresh_table()

    def _on_set_item(self):
        if not self._creature:
            return
        row = self._table.currentRow()
        if row < 0:
            return

        from .item_browser import ItemBrowserDialog
        dialog = ItemBrowserDialog(self)
        if dialog.exec():
            item_name = dialog.selected_item
            if item_name:
                new_item = CreItem(
                    res_name=item_name,
                    quantity1=1,
                    quantity2=0,
                    quantity3=0,
                    identified=True,
                )
                self._creature.set_item(row, new_item)
                self._refresh_table()

    def _on_remove_item(self):
        if not self._creature:
            return
        row = self._table.currentRow()
        if row < 0:
            return
        self._creature.set_item(row, CreItem())
        self._refresh_table()

    def _on_identify_all(self):
        if not self._creature:
            return
        items = self._creature.get_items()
        for item in items:
            if item.res_name:
                item.identified = True
        self._creature.set_items(items)
        self._refresh_table()
