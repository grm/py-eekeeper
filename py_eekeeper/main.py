"""Entry point for py-eekeeper."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from .app import EEKeeperApp
from .ui.main_window import MainWindow
from .ui.installation_dialog import InstallationDialog


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("py-eekeeper")
    app.setOrganizationName("EEKeeper")

    # Initialize the application core
    eekeeper = EEKeeperApp.instance()
    eekeeper.config.read()

    # If no install path configured, ask the user
    if not eekeeper.config.install_path:
        dialog = InstallationDialog(config=eekeeper.config)
        if dialog.exec():
            eekeeper.config.write()
        else:
            sys.exit(0)

    # Try to initialize with the configured path
    if not eekeeper.initialize():
        result = QMessageBox.warning(
            None, "Initialization Failed",
            "Could not initialize game resources.\n"
            "Please check your installation directory setting.\n\n"
            "Would you like to configure it now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result == QMessageBox.StandardButton.Yes:
            dialog = InstallationDialog(config=eekeeper.config)
            if dialog.exec():
                eekeeper.config.write()
                if not eekeeper.initialize():
                    QMessageBox.critical(
                        None, "Error",
                        "Still could not initialize. Please verify the path."
                    )
                    sys.exit(1)
            else:
                sys.exit(0)
        else:
            sys.exit(1)

    # Show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
