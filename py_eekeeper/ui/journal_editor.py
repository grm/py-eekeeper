"""Dialog for editing journal entries in a save game."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QDialogButtonBox, QSpinBox, QLabel,
    QGridLayout, QGroupBox,
)
from PySide6.QtCore import Qt

from ..formats.inf_game import InfGame
from ..formats.inf_journal import JournalEntry
from ..formats.inf_tlk import InfTlk

JOURNAL_FLAG_QUESTS = 0x04
JOURNAL_FLAG_DONE = 0x08
JOURNAL_FLAG_INFO = 0x10


class JournalEditorDialog(QDialog):
    """Editor for journal entries."""

    def __init__(self, parent=None, game: InfGame = None, tlk: InfTlk = None):
        super().__init__(parent)
        self.setWindowTitle("Journal Editor")
        self.setMinimumSize(700, 500)
        self._game = game
        self._tlk = tlk
        self._entries: list[JournalEntry] = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["StrRef", "Text", "Chapter", "Flags", "Section"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self._table)

        # Edit panel
        edit_group = QGroupBox("Entry Details")
        edit_layout = QGridLayout(edit_group)

        edit_layout.addWidget(QLabel("StrRef:"), 0, 0)
        self._spin_strref = QSpinBox()
        self._spin_strref.setRange(0, 0x7FFFFFFF)
        self._spin_strref.valueChanged.connect(self._on_entry_changed)
        edit_layout.addWidget(self._spin_strref, 0, 1)

        edit_layout.addWidget(QLabel("Time:"), 0, 2)
        self._spin_time = QSpinBox()
        self._spin_time.setRange(0, 0x7FFFFFFF)
        self._spin_time.valueChanged.connect(self._on_entry_changed)
        edit_layout.addWidget(self._spin_time, 0, 3)

        edit_layout.addWidget(QLabel("Chapter:"), 1, 0)
        self._spin_chapter = QSpinBox()
        self._spin_chapter.setRange(0, 255)
        self._spin_chapter.valueChanged.connect(self._on_entry_changed)
        edit_layout.addWidget(self._spin_chapter, 1, 1)

        edit_layout.addWidget(QLabel("Flags:"), 1, 2)
        self._spin_flags = QSpinBox()
        self._spin_flags.setRange(0, 255)
        self._spin_flags.valueChanged.connect(self._on_entry_changed)
        edit_layout.addWidget(self._spin_flags, 1, 3)

        edit_layout.addWidget(QLabel("Section:"), 2, 0)
        self._spin_section = QSpinBox()
        self._spin_section.setRange(0, 65535)
        self._spin_section.valueChanged.connect(self._on_entry_changed)
        edit_layout.addWidget(self._spin_section, 2, 1)

        layout.addWidget(edit_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Add Entry")
        btn_add.clicked.connect(self._on_add)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("Remove Entry")
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
        self._entries = self._game.get_journal_entries()
        self._refresh_table()

    def _refresh_table(self):
        self._table.blockSignals(True)
        self._table.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            strref_item = QTableWidgetItem(str(entry.strref))
            strref_item.setFlags(strref_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, strref_item)

            text = ""
            if self._tlk:
                text = self._tlk.get_string(entry.strref) or ""
            text_item = QTableWidgetItem(text[:80])
            text_item.setFlags(text_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 1, text_item)

            ch_item = QTableWidgetItem(str(entry.chapter))
            ch_item.setFlags(ch_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 2, ch_item)

            flags_str = self._flags_to_str(entry.flags)
            flags_item = QTableWidgetItem(flags_str)
            flags_item.setFlags(flags_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 3, flags_item)

            sec_item = QTableWidgetItem(str(entry.section_id))
            sec_item.setFlags(sec_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 4, sec_item)
        self._table.blockSignals(False)

    def _flags_to_str(self, flags: int) -> str:
        parts = []
        if flags & JOURNAL_FLAG_QUESTS:
            parts.append("Quest")
        if flags & JOURNAL_FLAG_DONE:
            parts.append("Done")
        if flags & JOURNAL_FLAG_INFO:
            parts.append("Info")
        if not parts:
            return f"0x{flags:02X}"
        return "|".join(parts)

    def _on_row_changed(self, row: int):
        if row < 0 or row >= len(self._entries):
            return
        entry = self._entries[row]
        self._spin_strref.blockSignals(True)
        self._spin_time.blockSignals(True)
        self._spin_chapter.blockSignals(True)
        self._spin_flags.blockSignals(True)
        self._spin_section.blockSignals(True)

        self._spin_strref.setValue(entry.strref)
        self._spin_time.setValue(entry.time)
        self._spin_chapter.setValue(entry.chapter)
        self._spin_flags.setValue(entry.flags)
        self._spin_section.setValue(entry.section_id)

        self._spin_strref.blockSignals(False)
        self._spin_time.blockSignals(False)
        self._spin_chapter.blockSignals(False)
        self._spin_flags.blockSignals(False)
        self._spin_section.blockSignals(False)

    def _on_entry_changed(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        entry = self._entries[row]
        entry.strref = self._spin_strref.value()
        entry.time = self._spin_time.value()
        entry.chapter = self._spin_chapter.value()
        entry.flags = self._spin_flags.value()
        entry.section_id = self._spin_section.value()
        self._refresh_table()
        self._table.setCurrentCell(row, 0)

    def _on_add(self):
        self._entries.append(JournalEntry())
        self._refresh_table()
        self._table.setCurrentCell(len(self._entries) - 1, 0)

    def _on_remove(self):
        row = self._table.currentRow()
        if 0 <= row < len(self._entries):
            self._entries.pop(row)
            self._refresh_table()

    def _on_accept(self):
        if self._game:
            self._game.set_journal_entries(self._entries)
        self.accept()
