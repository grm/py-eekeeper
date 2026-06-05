"""Theme support — apply light, dark, or system-following palette."""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


def _dark_palette() -> QPalette:
    """Create a dark color palette for the Fusion style."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
    return palette


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply the chosen theme to the application.

    Args:
        app: The QApplication instance.
        theme: One of 'system', 'light', or 'dark'.
    """
    app.setStyle("Fusion")

    if theme == "dark":
        app.setPalette(_dark_palette())
    elif theme == "light":
        # Reset to the default Fusion palette (light)
        app.setPalette(app.style().standardPalette())
    else:
        # "system" — let Qt/Fusion follow the OS preference naturally.
        # On macOS, Qt6 Fusion respects the system dark mode when no
        # palette override is set.
        app.setPalette(app.style().standardPalette())
