"""Settings dialog — edit all application configuration options."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QGroupBox,
    QLabel, QSpinBox, QCheckBox, QDialogButtonBox,
    QTabWidget, QWidget, QLineEdit, QComboBox,
    QApplication,
)

from ..config import Config
from .theme import apply_theme


class SettingsDialog(QDialog):
    """Full application settings editor."""

    def __init__(self, parent=None, config: Config = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(450, 400)
        self._config = config
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # General tab
        general_tab = QWidget()
        general_layout = QGridLayout(general_tab)

        general_layout.addWidget(QLabel("Language:"), 0, 0)
        self._edit_language = QLineEdit()
        general_layout.addWidget(self._edit_language, 0, 1)

        self._check_default_single = QCheckBox("Default to single-player saves")
        general_layout.addWidget(self._check_default_single, 1, 0, 1, 2)

        self._check_auto_backup = QCheckBox("Auto-backup saves before writing")
        general_layout.addWidget(self._check_auto_backup, 2, 0, 1, 2)

        general_layout.setRowStretch(3, 1)
        tabs.addTab(general_tab, "General")

        # Spells tab
        spells_tab = QWidget()
        spells_layout = QGridLayout(spells_tab)

        self._check_known_limit = QCheckBox("Limit known spells")
        spells_layout.addWidget(self._check_known_limit, 0, 0)
        self._spin_known_limit = QSpinBox()
        self._spin_known_limit.setRange(1, 999)
        spells_layout.addWidget(self._spin_known_limit, 0, 1)

        self._check_mem_limit = QCheckBox("Limit memorized spells")
        spells_layout.addWidget(self._check_mem_limit, 1, 0)
        self._spin_mem_limit = QSpinBox()
        self._spin_mem_limit.setRange(1, 999)
        spells_layout.addWidget(self._spin_mem_limit, 1, 1)

        self._check_mem_on_save = QCheckBox("Memorize all spells on save")
        spells_layout.addWidget(self._check_mem_on_save, 2, 0, 1, 2)

        spells_layout.setRowStretch(3, 1)
        tabs.addTab(spells_tab, "Spells")

        # Display tab
        display_tab = QWidget()
        display_layout = QGridLayout(display_tab)

        display_layout.addWidget(QLabel("Theme:"), 0, 0)
        self._combo_theme = QComboBox()
        self._combo_theme.addItem("System", "system")
        self._combo_theme.addItem("Light", "light")
        self._combo_theme.addItem("Dark", "dark")
        display_layout.addWidget(self._combo_theme, 0, 1)

        self._check_grid_lines = QCheckBox("Show grid lines in tables")
        display_layout.addWidget(self._check_grid_lines, 1, 0, 1, 2)

        display_layout.setRowStretch(2, 1)
        tabs.addTab(display_tab, "Display")

        # Advanced tab
        advanced_tab = QWidget()
        advanced_layout = QGridLayout(advanced_tab)

        self._check_ignore_versions = QCheckBox("Ignore data version checks")
        advanced_layout.addWidget(self._check_ignore_versions, 0, 0, 1, 2)

        self._check_allow_overwrite = QCheckBox("Allow CHR file overwrite")
        advanced_layout.addWidget(self._check_allow_overwrite, 1, 0, 1, 2)

        advanced_layout.setRowStretch(2, 1)
        tabs.addTab(advanced_tab, "Advanced")

        layout.addWidget(tabs)

        # OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_settings(self):
        if not self._config:
            return
        self._edit_language.setText(self._config.language)
        self._check_default_single.setChecked(self._config.default_open_singleplayer)
        self._check_auto_backup.setChecked(self._config.auto_backup)
        self._check_known_limit.setChecked(self._config.use_known_spell_limit)
        self._spin_known_limit.setValue(self._config.known_spell_limit)
        self._check_mem_limit.setChecked(self._config.use_mem_spell_limit)
        self._spin_mem_limit.setValue(self._config.mem_spell_limit)
        self._check_mem_on_save.setChecked(self._config.mem_spells_on_save)
        self._check_grid_lines.setChecked(self._config.use_grid_lines)
        idx = self._combo_theme.findData(self._config.theme)
        if idx >= 0:
            self._combo_theme.setCurrentIndex(idx)
        self._check_ignore_versions.setChecked(self._config.ignore_data_versions)
        self._check_allow_overwrite.setChecked(self._config.allow_chr_overwrite)

    def _on_accept(self):
        if not self._config:
            self.accept()
            return
        self._config.language = self._edit_language.text()
        self._config.default_open_singleplayer = self._check_default_single.isChecked()
        self._config.auto_backup = self._check_auto_backup.isChecked()
        self._config.use_known_spell_limit = self._check_known_limit.isChecked()
        self._config.known_spell_limit = self._spin_known_limit.value()
        self._config.use_mem_spell_limit = self._check_mem_limit.isChecked()
        self._config.mem_spell_limit = self._spin_mem_limit.value()
        self._config.mem_spells_on_save = self._check_mem_on_save.isChecked()
        self._config.use_grid_lines = self._check_grid_lines.isChecked()
        self._config.theme = self._combo_theme.currentData()
        self._config.ignore_data_versions = self._check_ignore_versions.isChecked()
        self._config.allow_chr_overwrite = self._check_allow_overwrite.isChecked()

        # Apply the selected theme immediately
        app = QApplication.instance()
        if app:
            apply_theme(app, self._config.theme)

        self.accept()
