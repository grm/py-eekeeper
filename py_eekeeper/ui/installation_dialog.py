"""Dialog for configuring the game installation directory."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton,
    QDialogButtonBox, QFileDialog,
)

from ..config import Config


class InstallationDialog(QDialog):
    """Configure game installation path and language."""

    def __init__(self, parent=None, config: Config = None):
        super().__init__(parent)
        self.setWindowTitle("Installation Directory")
        self.setMinimumWidth(500)
        self._config = config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        grid = QGridLayout()

        grid.addWidget(QLabel("Installation Directory:"), 0, 0)
        self._edit_path = QLineEdit()
        if self._config:
            self._edit_path.setText(self._config.install_path)
        grid.addWidget(self._edit_path, 0, 1)

        self._btn_browse = QPushButton("Browse...")
        self._btn_browse.clicked.connect(self._on_browse)
        grid.addWidget(self._btn_browse, 0, 2)

        grid.addWidget(QLabel("Documents Path:"), 1, 0)
        self._edit_docs = QLineEdit()
        if self._config:
            self._edit_docs.setText(self._config.documents_path)
        grid.addWidget(self._edit_docs, 1, 1)

        self._btn_browse_docs = QPushButton("Browse...")
        self._btn_browse_docs.clicked.connect(self._on_browse_docs)
        grid.addWidget(self._btn_browse_docs, 1, 2)

        grid.addWidget(QLabel("Language:"), 2, 0)
        self._combo_lang = QComboBox()
        self._combo_lang.setEditable(True)
        self._combo_lang.addItems(["en_US", "fr_FR", "de_DE", "es_ES", "it_IT", "pl_PL", "ru_RU"])
        if self._config:
            idx = self._combo_lang.findText(self._config.language)
            if idx >= 0:
                self._combo_lang.setCurrentIndex(idx)
            else:
                self._combo_lang.setCurrentText(self._config.language)
        grid.addWidget(self._combo_lang, 2, 1)

        layout.addLayout(grid)

        # Auto-detect button
        btn_detect = QPushButton("Auto-detect Installation")
        btn_detect.clicked.connect(self._on_auto_detect)
        layout.addWidget(btn_detect)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Game Installation Directory")
        if path:
            self._edit_path.setText(path)

    def _on_browse_docs(self):
        path = QFileDialog.getExistingDirectory(self, "Select Documents/Save Directory")
        if path:
            self._edit_docs.setText(path)

    def _on_auto_detect(self):
        import sys
        candidates = []
        if sys.platform == "darwin":
            candidates = [
                Path.home() / "Library/Application Support/Steam/steamapps/common/Baldur's Gate Enhanced Edition",
                Path.home() / "Library/Application Support/Steam/steamapps/common/Baldur's Gate II Enhanced Edition",
                Path.home() / "Library/Application Support/Steam/steamapps/common/Icewind Dale Enhanced Edition",
            ]
        else:
            candidates = [
                Path.home() / ".local/share/Steam/steamapps/common/Baldur's Gate Enhanced Edition",
                Path.home() / ".local/share/Steam/steamapps/common/Baldur's Gate II Enhanced Edition",
                Path.home() / ".local/share/Steam/steamapps/common/Icewind Dale Enhanced Edition",
                Path.home() / ".steam/steam/steamapps/common/Baldur's Gate Enhanced Edition",
                Path.home() / ".steam/steam/steamapps/common/Baldur's Gate II Enhanced Edition",
            ]

        for path in candidates:
            if path.exists() and (path / "chitin.key").exists():
                self._edit_path.setText(str(path))
                break

    def _on_accept(self):
        if self._config:
            self._config.install_path = self._edit_path.text()
            self._config.documents_path = self._edit_docs.text()
            self._config.language = self._combo_lang.currentText()
        self.accept()
