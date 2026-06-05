"""Dialog showing installed WeiDU mods detected from weidu.log."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt

from ..mods import InstalledMod


class ModsDialog(QDialog):
    """Display installed mods grouped by mod name with component details."""

    def __init__(self, parent, mods: list[InstalledMod]):
        super().__init__(parent)

        # Group mods by name
        groups: dict[str, list[InstalledMod]] = {}
        for mod in mods:
            groups.setdefault(mod.name, []).append(mod)

        mod_count = len(groups)
        component_count = len(mods)

        self.setWindowTitle(
            f"Installed Mods ({mod_count} mods, {component_count} components)"
        )
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Mod / Component", "Language", "Description"])
        self._tree.setColumnWidth(0, 220)
        self._tree.setColumnWidth(1, 70)
        self._tree.setAlternatingRowColors(True)
        layout.addWidget(self._tree)

        for mod_name in sorted(groups.keys(), key=str.lower):
            components = groups[mod_name]
            top_item = QTreeWidgetItem([mod_name, "", f"({len(components)} components)"])
            top_item.setFlags(top_item.flags() | Qt.ItemFlag.ItemIsEnabled)
            self._tree.addTopLevelItem(top_item)

            for comp in components:
                child = QTreeWidgetItem([
                    f"#{comp.component}",
                    str(comp.language),
                    comp.description,
                ])
                top_item.addChild(child)

            top_item.setExpanded(True)

        # Warnings label
        self._warnings_label = QLabel("")
        self._warnings_label.setWordWrap(True)
        layout.addWidget(self._warnings_label)

        warnings = self._check_warnings(mods)
        if warnings:
            self._warnings_label.setText("\n".join(warnings))
        else:
            self._warnings_label.hide()

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _check_warnings(mods: list[InstalledMod]) -> list[str]:
        """Return compatibility warnings based on installed mods."""
        warnings: list[str] = []
        mod_names_lower = {m.name.lower() for m in mods}

        # Example warnings for well-known large mods
        if "eetsetup" in mod_names_lower or "eet" in mod_names_lower:
            warnings.append(
                "EET detected: save structure may differ from standard BG2:EE."
            )

        return warnings
