"""Main application window."""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar,
    QMessageBox, QFileDialog,
)
from PySide6.QtGui import QAction, QUndoStack
from PySide6.QtCore import Qt

from pathlib import Path

from ..app import EEKeeperApp
from ..mods import parse_weidu_log
from .saved_game_widget import SavedGameWidget
from .character_sheet import CharacterSheetWidget
from .spell_tab import SpellTab
from .memorization_tab import MemorizationTab
from .proficiencies_tab import ProficienciesTab
from .inventory_tab import InventoryTab
from .appearance_tab import AppearanceTab
from .affects_tab import AffectsTab
from .game_tab import GameTab
from .open_saved_game_dialog import OpenSavedGameDialog
from .installation_dialog import InstallationDialog
from .string_finder_dialog import StringFinderDialog
from .save_game_name_dialog import SaveGameNameDialog
from .party_search_dialog import PartySearchDialog
from .batch_operations import full_hp_all, memorize_all_spells, identify_all_items


class MainWindow(QMainWindow):
    """EEKeeper main window."""

    def __init__(self):
        super().__init__()
        self._app = EEKeeperApp.instance()
        self._current_char_index: int = -1

        # Undo/Redo stack
        self._undo_stack = QUndoStack(self)

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

        self._action_save_as = QAction("Save &As...", self)
        self._action_save_as.setShortcut("Ctrl+Shift+S")
        self._action_save_as.triggered.connect(self._on_save_as)
        self._action_save_as.setEnabled(False)
        file_menu.addAction(self._action_save_as)

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

        # Edit menu (Undo/Redo)
        edit_menu = menubar.addMenu("&Edit")

        self._action_undo = self._undo_stack.createUndoAction(self, "&Undo")
        self._action_undo.setShortcut("Ctrl+Z")
        edit_menu.addAction(self._action_undo)

        self._action_redo = self._undo_stack.createRedoAction(self, "&Redo")
        self._action_redo.setShortcut("Ctrl+Y")
        edit_menu.addAction(self._action_redo)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        self._action_string_finder = QAction("&String Finder...", self)
        self._action_string_finder.triggered.connect(self._on_string_finder)
        tools_menu.addAction(self._action_string_finder)

        tools_menu.addSeparator()

        self._action_globals = QAction("&Global Variables...", self)
        self._action_globals.triggered.connect(self._on_globals)
        self._action_globals.setEnabled(False)
        tools_menu.addAction(self._action_globals)

        self._action_locals = QAction("&Local Variables...", self)
        self._action_locals.triggered.connect(self._on_locals)
        self._action_locals.setEnabled(False)
        tools_menu.addAction(self._action_locals)

        self._action_journal = QAction("&Journal...", self)
        self._action_journal.triggered.connect(self._on_journal)
        self._action_journal.setEnabled(False)
        tools_menu.addAction(self._action_journal)

        tools_menu.addSeparator()

        self._action_compare = QAction("Compare C&haracters...", self)
        self._action_compare.triggered.connect(self._on_compare_characters)
        self._action_compare.setEnabled(False)
        tools_menu.addAction(self._action_compare)

        tools_menu.addSeparator()

        self._action_creature_browser = QAction("&Creature Browser...", self)
        self._action_creature_browser.triggered.connect(self._on_creature_browser)
        tools_menu.addAction(self._action_creature_browser)

        tools_menu.addSeparator()

        self._action_party_search = QAction("&Party Search...", self)
        self._action_party_search.setShortcut("Ctrl+F")
        self._action_party_search.triggered.connect(self._on_party_search)
        self._action_party_search.setEnabled(False)
        tools_menu.addAction(self._action_party_search)

        # Party menu
        party_menu = menubar.addMenu("&Party")

        self._action_full_hp = QAction("Full HP All", self)
        self._action_full_hp.triggered.connect(self._on_full_hp_all)
        self._action_full_hp.setEnabled(False)
        party_menu.addAction(self._action_full_hp)

        self._action_memorize_all = QAction("Memorize All Spells", self)
        self._action_memorize_all.triggered.connect(self._on_memorize_all_spells)
        self._action_memorize_all.setEnabled(False)
        party_menu.addAction(self._action_memorize_all)

        self._action_identify_all = QAction("Identify All Items", self)
        self._action_identify_all.triggered.connect(self._on_identify_all_items)
        self._action_identify_all.setEnabled(False)
        party_menu.addAction(self._action_identify_all)

        # Options menu
        options_menu = menubar.addMenu("&Options")

        self._action_install_dir = QAction("&Installation Directory...", self)
        self._action_install_dir.triggered.connect(self._on_install_dir)
        options_menu.addAction(self._action_install_dir)

        self._action_settings = QAction("&Settings...", self)
        self._action_settings.triggered.connect(self._on_settings)
        options_menu.addAction(self._action_settings)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        self._action_mods = QAction("Installed &Mods...", self)
        self._action_mods.triggered.connect(self._on_installed_mods)
        help_menu.addAction(self._action_mods)

        help_menu.addSeparator()

        action_about = QAction("&About", self)
        action_about.triggered.connect(self._on_about)
        help_menu.addAction(action_about)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addAction(self._action_open)
        toolbar.addAction(self._action_save)
        toolbar.addAction(self._action_save_as)
        toolbar.addSeparator()
        toolbar.addAction(self._action_export)
        toolbar.addAction(self._action_import)
        toolbar.addSeparator()
        toolbar.addAction(self._action_string_finder)

    def _setup_ui(self):
        # Saved game widget (character selector)
        self._saved_game_widget = SavedGameWidget()
        self._saved_game_widget.character_selected.connect(self._on_character_selected)

        # Tab widget for character editing
        self._tab_widget = QTabWidget()
        self._game_tab = GameTab()
        self._character_sheet = CharacterSheetWidget(undo_stack=self._undo_stack)
        self._spell_tab = SpellTab()
        self._memorization_tab = MemorizationTab()
        self._proficiencies_tab = ProficienciesTab()
        self._inventory_tab = InventoryTab()
        self._appearance_tab = AppearanceTab(undo_stack=self._undo_stack)
        self._affects_tab = AffectsTab()

        self._tab_widget.addTab(self._game_tab, "Game")
        self._tab_widget.addTab(self._character_sheet, "Character")
        self._tab_widget.addTab(self._spell_tab, "Spells")
        self._tab_widget.addTab(self._memorization_tab, "Memorization")
        self._tab_widget.addTab(self._proficiencies_tab, "Proficiencies")
        self._tab_widget.addTab(self._inventory_tab, "Inventory")
        self._tab_widget.addTab(self._appearance_tab, "Appearance")
        self._tab_widget.addTab(self._affects_tab, "Affects")

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

        # Refresh UI after undo/redo so widgets reflect model state
        self._undo_stack.indexChanged.connect(self._on_undo_redo)

        self._tab_widget.setEnabled(False)

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("Ready")

    # --- Actions ---

    def _on_undo_redo(self):
        """Refresh tabs after an undo or redo operation."""
        self._refresh_current_character()

    def _on_open(self):
        dialog = OpenSavedGameDialog(self, self._app.config)
        if dialog.exec():
            save_dir = dialog.selected_path
            if save_dir and self._app.open_save(save_dir):
                self._undo_stack.clear()
                self._saved_game_widget.load_game(self._app.game)
                self._game_tab.load_game(self._app.game)
                self._tab_widget.setEnabled(True)
                self._action_save.setEnabled(True)
                self._action_save_as.setEnabled(True)
                self._action_export.setEnabled(True)
                self._action_import.setEnabled(True)
                self._action_globals.setEnabled(True)
                self._action_locals.setEnabled(True)
                self._action_journal.setEnabled(True)
                self._action_full_hp.setEnabled(True)
                self._action_memorize_all.setEnabled(True)
                self._action_identify_all.setEnabled(True)
                self._action_party_search.setEnabled(True)
                # Enable compare only when 2+ characters are available
                total_chars = (
                    self._app.game.party_count + self._app.game.out_of_party_count
                )
                self._action_compare.setEnabled(total_chars >= 2)
                self._statusbar.showMessage(f"Loaded: {save_dir}")
                self._show_mod_count()
                self._app.game.mark_saved()
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

    def _on_save_as(self):
        dialog = SaveGameNameDialog(self)
        if dialog.exec():
            new_name = dialog.name
            if new_name:
                if self._app.save_game_as(new_name):
                    self._statusbar.showMessage(f"Saved as: {new_name}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to save. Directory may already exist.")

    def _on_import_chr(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Character", "", "Character Files (*.chr)"
        )
        if path:
            chr_file = self._app.import_character(path)
            if chr_file:
                if self._app.game:
                    result = QMessageBox.question(
                        self, "Import Character",
                        f"Add '{chr_file.name}' to the save game reserves?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if result == QMessageBox.StandardButton.Yes:
                        self._app.game.add_out_of_party_character(
                            chr_file.get_creature(), chr_file.name
                        )
                        self._saved_game_widget.load_game(self._app.game)
                        self._statusbar.showMessage(f"Imported: {chr_file.name}")
                else:
                    self._statusbar.showMessage(f"Parsed: {chr_file.name} (no save loaded)")

    def _on_string_finder(self):
        dialog = StringFinderDialog(self, self._app.tlk)
        dialog.exec()

    def _on_globals(self):
        if not self._app.game:
            return
        from .globals_editor import GlobalsEditorDialog
        dialog = GlobalsEditorDialog(self, self._app.game)
        dialog.exec()

    def _on_locals(self):
        if not self._app.game:
            return
        cre = self._get_current_creature()
        if not cre:
            QMessageBox.information(
                self, "Local Variables",
                "Please select a character first."
            )
            return
        from .locals_editor import LocalsEditorDialog
        dialog = LocalsEditorDialog(self, cre)
        dialog.exec()

    def _on_journal(self):
        if not self._app.game:
            return
        from .journal_editor import JournalEditorDialog
        dialog = JournalEditorDialog(self, self._app.game, self._app.tlk)
        dialog.exec()

    def _on_compare_characters(self):
        if not self._app.game:
            return
        from .compare_dialog import CompareCharactersDialog
        dialog = CompareCharactersDialog(self, self._app.game)
        dialog.exec()

    def _on_creature_browser(self):
        from .creature_browser import CreatureBrowserDialog
        dialog = CreatureBrowserDialog(self)
        if dialog.exec():
            name = dialog.selected_creature
            if name:
                QMessageBox.information(
                    self, "Creature Selected",
                    f"Selected creature: {name}"
                )

    def _on_settings(self):
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self, self._app.config)
        if dialog.exec():
            self._app.config.write()

    def _on_install_dir(self):
        dialog = InstallationDialog(self, self._app.config)
        if dialog.exec():
            self._app.config.write()
            QMessageBox.information(
                self, "Restart Required",
                "Please restart the application for changes to take effect."
            )

    def _on_installed_mods(self):
        if not self._app.config.install_path:
            QMessageBox.information(
                self, "Installed Mods",
                "No installation directory configured."
            )
            return

        log_path = Path(self._app.config.install_path) / "weidu.log"
        if not log_path.exists():
            QMessageBox.information(
                self, "Installed Mods",
                "No weidu.log found in the game installation directory."
            )
            return

        mods = parse_weidu_log(log_path)
        from .mods_dialog import ModsDialog
        dialog = ModsDialog(self, mods)
        dialog.exec()

    def _show_mod_count(self):
        """Show mod count in status bar if weidu.log exists."""
        if not self._app.config.install_path:
            return
        log_path = Path(self._app.config.install_path) / "weidu.log"
        if not log_path.exists():
            return
        mods = parse_weidu_log(log_path)
        if mods:
            mod_names = {m.name for m in mods}
            self._statusbar.showMessage(
                f"Loaded save | {len(mods)} mod components detected "
                f"({len(mod_names)} mods)",
                5000,
            )

    def _on_about(self):
        QMessageBox.about(
            self, "About py-eekeeper",
            "py-eekeeper v0.1.0\n\n"
            "Save game editor for Baldur's Gate Enhanced Edition.\n\n"
            "Based on EE Keeper by Troodon80,\n"
            "originally based on Shadow Keeper by Aaron O'Neil."
        )

    def _get_party_creatures(self) -> list:
        """Return all in-party creatures."""
        if not self._app.game:
            return []
        creatures = []
        for i in range(self._app.game.party_count):
            cre = self._app.game.get_party_cre(i)
            if cre:
                creatures.append(cre)
        return creatures

    def _on_full_hp_all(self):
        creatures = self._get_party_creatures()
        if not creatures:
            return
        count = full_hp_all(creatures)
        self._statusbar.showMessage(f"Healed {count} characters")
        self._refresh_current_character()

    def _on_memorize_all_spells(self):
        creatures = self._get_party_creatures()
        if not creatures:
            return
        count = memorize_all_spells(creatures)
        self._statusbar.showMessage(f"Memorized all spells for {count} characters")
        self._refresh_current_character()

    def _on_identify_all_items(self):
        creatures = self._get_party_creatures()
        if not creatures:
            return
        count = identify_all_items(creatures)
        self._statusbar.showMessage(f"Identified all items for {count} characters")
        self._refresh_current_character()

    def _refresh_current_character(self):
        """Reload the current character's data in all tabs."""
        cre = self._get_current_creature()
        if cre:
            self._character_sheet.load_creature(cre)
            self._spell_tab.load_creature(cre)
            self._memorization_tab.load_creature(cre)
            self._proficiencies_tab.load_creature(cre)
            self._inventory_tab.load_creature(cre)
            self._appearance_tab.load_creature(cre)
            self._affects_tab.load_creature(cre)

    def _on_party_search(self):
        if not self._app.game:
            return
        dialog = PartySearchDialog(self)
        dialog.show()

    def _get_current_creature(self):
        """Return the currently selected creature, or None."""
        if not self._app.game or self._current_char_index < 0:
            return None
        cre = self._app.game.get_party_cre(self._current_char_index)
        if not cre:
            cre = self._app.game.get_out_of_party_cre(
                self._current_char_index - self._app.game.party_count
            )
        return cre

    def _on_character_selected(self, index: int):
        self._current_char_index = index
        self._undo_stack.clear()
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
            self._appearance_tab.load_creature(cre)
            self._affects_tab.load_creature(cre)

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
