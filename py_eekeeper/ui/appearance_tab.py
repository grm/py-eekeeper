"""Appearance tab — visual color editor for creature colors."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSpinBox, QGroupBox,
)
from PySide6.QtGui import QColor, QUndoStack
from PySide6.QtCore import Qt

from ..formats.inf_creature import InfCreature
from .undo_commands import SetAttributeCommand


# Color slot definitions: (label, property_name)
COLOR_SLOTS = [
    ("Metal Color", "metal_color"),
    ("Minor Color", "minor_color"),
    ("Major Color", "major_color"),
    ("Skin Color", "skin_color"),
    ("Leather Color", "leather_color"),
    ("Armor Color", "armor_color"),
    ("Hair Color", "hair_color"),
]


def _index_to_color(index: int) -> QColor:
    """Map a color index (0-255) to an approximate display color.

    Uses HSV wheel: index maps to hue 0-360 with fixed saturation and value.
    This is an approximation since we don't have the actual game palette.
    """
    hue = int((index / 256.0) * 360.0) % 360
    saturation = 200
    value = 220
    color = QColor()
    color.setHsv(hue, saturation, value)
    return color


class AppearanceTab(QWidget):
    """Tab for viewing and editing creature color indices."""

    def __init__(self, parent=None, undo_stack: QUndoStack | None = None):
        super().__init__(parent)
        self._creature: InfCreature | None = None
        self._spinboxes: dict[str, QSpinBox] = {}
        self._previews: dict[str, QLabel] = {}
        self._updating = False
        self._undo_stack = undo_stack
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        group = QGroupBox("Character Colors")
        grid = QGridLayout(group)
        grid.setColumnMinimumWidth(2, 60)

        for row, (label_text, prop_name) in enumerate(COLOR_SLOTS):
            # Label
            label = QLabel(label_text)
            grid.addWidget(label, row, 0)

            # SpinBox
            spinbox = QSpinBox()
            spinbox.setRange(0, 255)
            spinbox.setFixedWidth(80)
            spinbox.valueChanged.connect(
                lambda val, pn=prop_name: self._on_color_changed(pn, val)
            )
            grid.addWidget(spinbox, row, 1)
            self._spinboxes[prop_name] = spinbox

            # Color preview
            preview = QLabel()
            preview.setFixedSize(60, 24)
            preview.setAutoFillBackground(True)
            preview.setFrameShape(QLabel.Shape.Box)
            self._update_preview(preview, 0)
            grid.addWidget(preview, row, 2)
            self._previews[prop_name] = preview

        grid.setRowStretch(len(COLOR_SLOTS), 1)
        layout.addWidget(group)
        layout.addStretch()

    def load_creature(self, creature: InfCreature):
        """Load color values from a creature into the UI."""
        self._creature = creature
        self._updating = True
        try:
            for _label, prop_name in COLOR_SLOTS:
                value = getattr(creature, prop_name)
                self._spinboxes[prop_name].setValue(value)
                self._update_preview(self._previews[prop_name], value)
        finally:
            self._updating = False

    def _on_color_changed(self, prop_name: str, value: int):
        """Handle a spinbox value change."""
        if self._updating:
            return
        if self._creature:
            old_value = getattr(self._creature, prop_name)
            if old_value != value:
                if self._undo_stack:
                    cmd = SetAttributeCommand(
                        self._creature, prop_name, old_value, value
                    )
                    self._undo_stack.push(cmd)
                else:
                    setattr(self._creature, prop_name, value)
        self._update_preview(self._previews[prop_name], value)

    def _update_preview(self, label: QLabel, index: int):
        """Update a preview label's background color based on the index."""
        color = _index_to_color(index)
        label.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #888;"
        )
