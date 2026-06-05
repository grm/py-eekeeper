"""Game tab — edit party-level data (gold, reputation)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QGridLayout, QLabel, QSpinBox, QPushButton,
)

from ..formats.inf_game import InfGame


class GameTab(QWidget):
    """Tab for editing game-level properties (gold, reputation)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._game: InfGame | None = None
        self._loading = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Party group
        party_group = QGroupBox("Party")
        party_layout = QGridLayout(party_group)

        party_layout.addWidget(QLabel("Gold:"), 0, 0)
        self._spin_gold = QSpinBox()
        self._spin_gold.setRange(0, 999_999_999)
        self._spin_gold.valueChanged.connect(self._on_gold_changed)
        party_layout.addWidget(self._spin_gold, 0, 1)

        party_layout.addWidget(QLabel("Reputation:"), 1, 0)
        self._spin_reputation = QSpinBox()
        self._spin_reputation.setRange(1, 20)
        self._spin_reputation.valueChanged.connect(self._on_reputation_changed)
        party_layout.addWidget(self._spin_reputation, 1, 1)

        layout.addWidget(party_group)

        # Editors group
        editors_group = QGroupBox("Game Data")
        editors_layout = QVBoxLayout(editors_group)

        btn_layout = QHBoxLayout()
        self._btn_globals = QPushButton("Global Variables...")
        self._btn_globals.clicked.connect(self._on_globals)
        btn_layout.addWidget(self._btn_globals)

        self._btn_journal = QPushButton("Journal...")
        self._btn_journal.clicked.connect(self._on_journal)
        btn_layout.addWidget(self._btn_journal)

        editors_layout.addLayout(btn_layout)
        layout.addWidget(editors_group)

        layout.addStretch()

    def load_game(self, game: InfGame):
        self._game = game
        self._loading = True
        self._spin_gold.setValue(game.party_gold)
        self._spin_reputation.setValue(game.party_reputation)
        self._loading = False

    def _on_gold_changed(self, value: int):
        if self._loading or not self._game:
            return
        self._game.party_gold = value

    def _on_reputation_changed(self, value: int):
        if self._loading or not self._game:
            return
        self._game.party_reputation = value

    def _on_globals(self):
        if not self._game:
            return
        from .globals_editor import GlobalsEditorDialog
        dialog = GlobalsEditorDialog(self, self._game)
        dialog.exec()

    def _on_journal(self):
        if not self._game:
            return
        from .journal_editor import JournalEditorDialog
        from ..app import EEKeeperApp
        app = EEKeeperApp.instance()
        dialog = JournalEditorDialog(self, self._game, app.tlk)
        dialog.exec()
