"""Main application window."""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar,
    QMessageBox, QFileDialog,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from ..app import EEKeeperApp
from .saved_game_widget import SavedGameWidget
from .character_sheet import CharacterSheetWidget
from .spell_tab import SpellTab
from .memorization_tab import MemorizationTab
from .proficiencies_tab import ProficienciesTab
from .inventory_tab import InventoryTab
from .open_saved_game_dialog import OpenSavedGameDialog
from .installation_dialog import InstallationDialog
from .string_finder_dialog import StringFinderDialog


class MainWindow(QMainWindow):
    """EEKeeper main window."""

    def __init__(self):
        super().__init__()
        self._app = EEKeeperApp.instance()
        self._current_char_index: int = -1

        self.setWindowTitle("py-eekeeper — Baldur's Gate Save Editor")
        self.setMinimumSize(900, 700)

        self._setup_menus()
        self._setup_toolbar()
        self._setup_ui()
        self._setup_statusbar()

    def _setup_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        self._action_open = QAction("&Open Save...", self)
        self._action_open.setShortcut("Ctrl+O")
        self._action_open.triggered.connect(self._on_open)
        file_menu.addAction(self._action_open)

        self._action_save = QAction("&Save", self)
        self._action_save.setShortcut("Ctrl+S")
        self._action_save.triggered.connect(self._on_save)
        self._action_save.setEnabled(False)
        file_menu.addAction(self._action_save)

        file_menu.addSeparator()

        self._action_export = QAction("&Export Character...", self)
        self._action_export.triggered.connect(self._on_export_chr)
        self._action_export.setEnabled(False)
        file_menu.addAction(self._action_export)

        self._action_import = QAction("&Import Character...", self)
        self._action_import.triggered.connect(self._on_import_chr)
        self._action_import.setEnabled(False)
        file_menu.addAction(self._action_import)

        file_menu.addSeparator()

        action_quit = QAction("&Quit", self)
        action_quit.setShortcut("Ctrl+Q")
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        self._action_string_finder = QAction("&String Finder...", self)
        self._action_string_finder.triggered.connect(self._on_string_finder)
        tools_menu.addAction(self._action_string_finder)

        # Options menu
        options_menu = menubar.addMenu("&Options")

        self._action_install_dir = QAction("&Installation Directory...", self)
        self._action_install_dir.triggered.connect(self._on_install_dir)
        options_menu.addAction(self._action_install_dir)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        action_about = QAction("&About", self)
        action_about.triggered.connect(self._on_about)
        help_menu.addAction(action_about)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addAction(self._action_open)
        toolbar.addAction(self._action_save)

    def _setup_ui(self):
        # Saved game widget (character selector)
        self._saved_game_widget = SavedGameWidget()
        self._saved_game_widget.character_selected.connect(self._on_character_selected)

        # Tab widget for character editing
        self._tab_widget = QTabWidget()
        self._character_sheet = CharacterSheetWidget()
        self._spell_tab = SpellTab()
        self._memorization_tab = MemorizationTab()
        self._proficiencies_tab = ProficienciesTab()
        self._inventory_tab = InventoryTab()

        self._tab_widget.addTab(self._character_sheet, "Character")
        self._tab_widget.addTab(self._spell_tab, "Spells")
        self._tab_widget.addTab(self._memorization_tab, "Memorization")
        self._tab_widget.addTab(self._proficiencies_tab, "Proficiencies")
        self._tab_widget.addTab(self._inventory_tab, "Inventory")

        # Layout
        from PySide6.QtWidgets import QVBoxLayout, QWidget, QSplitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._saved_game_widget)
        splitter.addWidget(self._tab_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        self.setCentralWidget(central)

        self._tab_widget.setEnabled(False)

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready")

    # --- Actions ---

    def _on_open(self):
        dialog = OpenSavedGameDialog(self, self._app.config)
        if dialog.exec():
            save_dir = dialog.selected_path
            if save_dir and self._app.open_save(save_dir):
                self._saved_game_widget.load_game(self._app.game)
                self._action_save.setEnabled(True)
                self._action_export.setEnabled(True)
                self._action_import.setEnabled(True)
                self._statusbar.showMessage(f"Loaded: {save_dir}")
            else:
                QMessageBox.warning(self, "Error", "Failed to open save game.")

    def _on_save(self):
        if self._app.save_game():
            self._statusbar.showMessage("Saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to save game.")

    def _on_export_chr(self):
        if self._current_char_index < 0:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Character", "", "Character Files (*.chr)"
        )
        if path:
            self._app.export_character(self._current_char_index, path)

    def _on_import_chr(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Character", "", "Character Files (*.chr)"
        )
        if path:
            chr_file = self._app.import_character(path)
            if chr_file:
                self._statusbar.showMessage(f"Imported: {chr_file.name}")

    def _on_string_finder(self):
        dialog = StringFinderDialog(self, self._app.tlk)
        dialog.exec()

    def _on_install_dir(self):
        dialog = InstallationDialog(self, self._app.config)
        if dialog.exec():
            self._app.config.write()
            QMessageBox.information(
                self, "Restart Required",
                "Please restart the application for changes to take effect."
            )

    def _on_about(self):
        QMessageBox.about(
            self, "About py-eekeeper",
            "py-eekeeper v0.1.0\n\n"
            "Save game editor for Baldur's Gate Enhanced Edition.\n\n"
            "Based on EE Keeper by Troodon80,\n"
            "originally based on Shadow Keeper by Aaron O'Neil."
        )

    def _on_character_selected(self, index: int):
        self._current_char_index = index
        if not self._app.game:
            return

        cre = self._app.game.get_party_cre(index)
        if not cre:
            cre = self._app.game.get_out_of_party_cre(
                index - self._app.game.party_count
            )

        if cre:
            self._tab_widget.setEnabled(True)
            self._character_sheet.load_creature(cre)
            self._spell_tab.load_creature(cre)
            self._memorization_tab.load_creature(cre)
            self._proficiencies_tab.load_creature(cre)
            self._inventory_tab.load_creature(cre)

    def closeEvent(self, event):
        if self._app.game and self._app.game.has_changed():
            result = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Yes:
                self._app.save_game()
            elif result == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()
