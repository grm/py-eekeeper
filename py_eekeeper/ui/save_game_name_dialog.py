"""Dialog for renaming a save game."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox,
)


class SaveGameNameDialog(QDialog):
    """Simple dialog to rename a save game folder."""

    def __init__(self, parent=None, current_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Save Game Name")
        self._name = current_name
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter a new name for the save game:"))

        self._edit = QLineEdit()
        self._edit.setText(self._name)
        self._edit.selectAll()
        layout.addWidget(self._edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        self._name = self._edit.text().strip()
        if self._name:
            self.accept()

    @property
    def name(self) -> str:
        return self._name
