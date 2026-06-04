"""Widget displaying the party characters from a loaded save game."""

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QScrollArea, QFrame, QToolButton,
)
from PySide6.QtCore import QSize, Signal, Qt

from ..formats.inf_game import InfGame


class CharacterButton(QToolButton):
    """A button representing a single party character."""

    def __init__(self, name: str, index: int, portrait_path: Path | None = None, parent=None):
        super().__init__(parent)
        self.index = index
        self.setText(name or f"Character {index + 1}")
        if portrait_path and portrait_path.is_file():
            self.setIcon(QIcon(str(portrait_path)))
        self.setIconSize(QSize(64, 64))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setFixedSize(130, 96)
        self.setCheckable(True)


class SavedGameWidget(QWidget):
    """Shows the list of party characters for selection."""

    character_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: list[CharacterButton] = []
        self._current_index: int = -1

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFixedHeight(116)
        self._scroll.setFrameShape(QFrame.Shape.StyledPanel)

        self._content = QWidget()
        self._layout = QHBoxLayout(self._content)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(8)
        self._scroll.setWidget(self._content)

        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self._scroll)

    def load_game(self, game: InfGame):
        # Clear existing buttons
        for btn in self._buttons:
            self._layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
        self._current_index = -1
        save_path = self._current_save_path()

        # Add party characters
        for i in range(game.party_count):
            name = game.get_party_char_name(i)
            cre = game.get_party_cre(i)
            if cre and not name:
                strref = cre.long_name_strref
                from ..app import EEKeeperApp
                app = EEKeeperApp.instance()
                name = app.tlk.get_string(strref) or f"Character {i + 1}"

            btn = CharacterButton(name, i, self._portrait_path(save_path, i))
            btn.clicked.connect(lambda checked, idx=i: self._on_button_clicked(idx))
            self._layout.addWidget(btn)
            self._buttons.append(btn)

        # Add out-of-party characters
        for i in range(game.out_of_party_count):
            idx = game.party_count + i
            name = game.get_out_of_party_char_name(i)
            btn = CharacterButton(f"[NPC] {name}" if name else f"NPC {i + 1}", idx)
            btn.clicked.connect(lambda checked, idx=idx: self._on_button_clicked(idx))
            self._layout.addWidget(btn)
            self._buttons.append(btn)

        self._layout.addStretch()

        # Auto-select first character
        if self._buttons:
            self._on_button_clicked(0)

    def _current_save_path(self) -> Path | None:
        from ..app import EEKeeperApp

        save_path = EEKeeperApp.instance().save_path
        return Path(save_path) if save_path else None

    def _portrait_path(self, save_path: Path | None, index: int) -> Path | None:
        if not save_path:
            return None
        for suffix in ("bmp", "BMP"):
            path = save_path / f"PORTRT{index}.{suffix}"
            if path.is_file():
                return path
        return None

    def _on_button_clicked(self, index: int):
        self._current_index = index
        for btn in self._buttons:
            btn.setChecked(btn.index == index)
        self.character_selected.emit(index)
