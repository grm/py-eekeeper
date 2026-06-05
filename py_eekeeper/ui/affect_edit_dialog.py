"""Dialog for editing a single affect/effect."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel,
    QSpinBox, QLineEdit, QDialogButtonBox, QGroupBox,
)

from ..formats.inf_affect import InfAffect


class AffectEditDialog(QDialog):
    """Edit all fields of a single InfAffect."""

    def __init__(self, parent=None, affect: InfAffect = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Affect")
        self.setMinimumWidth(450)
        self._affect = affect or InfAffect()
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Main fields
        main_group = QGroupBox("Effect Parameters")
        grid = QGridLayout(main_group)

        self._spin_opcode = self._add_spin(grid, "Opcode:", 0, 0, 0, 0xFFFF)
        self._spin_target = self._add_spin(grid, "Target Type:", 1, 0, 0, 0xFFFFFFFF)
        self._spin_power = self._add_spin(grid, "Power:", 2, 0, 0, 255)
        self._spin_param1 = self._add_spin(grid, "Parameter 1:", 3, 0, -2147483648, 2147483647)
        self._spin_param2 = self._add_spin(grid, "Parameter 2:", 4, 0, -2147483648, 2147483647)
        self._spin_timing = self._add_spin(grid, "Timing Mode:", 5, 0, 0, 0xFFFFFFFF)
        self._spin_dispel = self._add_spin(grid, "Dispel Type:", 6, 0, 0, 255)
        self._spin_duration = self._add_spin(grid, "Duration:", 7, 0, -2147483648, 2147483647)

        layout.addWidget(main_group)

        # Probability & Dice
        prob_group = QGroupBox("Probability & Dice")
        prob_grid = QGridLayout(prob_group)

        self._spin_prob1 = self._add_spin(prob_grid, "Probability 1:", 0, 0, 0, 0xFFFF)
        self._spin_prob2 = self._add_spin(prob_grid, "Probability 2:", 1, 0, 0, 0xFFFF)
        self._spin_dice_thrown = self._add_spin(prob_grid, "Dice Thrown:", 2, 0, 0, 0xFFFFFFFF)
        self._spin_dice_sides = self._add_spin(prob_grid, "Dice Sides:", 3, 0, 0, 0xFFFFFFFF)

        layout.addWidget(prob_group)

        # Saves & Resources
        save_group = QGroupBox("Saving Throws & Resources")
        save_grid = QGridLayout(save_group)

        self._spin_save_type = self._add_spin(save_grid, "Save Type:", 0, 0, 0, 0xFFFFFFFF)
        self._spin_save_bonus = self._add_spin(save_grid, "Save Bonus:", 1, 0, -2147483648, 2147483647)
        self._spin_special = self._add_spin(save_grid, "Special:", 2, 0, 0, 0xFFFFFFFF)

        save_grid.addWidget(QLabel("Resource:"), 3, 0)
        self._edit_resource = QLineEdit()
        self._edit_resource.setMaxLength(8)
        save_grid.addWidget(self._edit_resource, 3, 1)

        save_grid.addWidget(QLabel("Resource 3:"), 4, 0)
        self._edit_resource3 = QLineEdit()
        self._edit_resource3.setMaxLength(8)
        save_grid.addWidget(self._edit_resource3, 4, 1)

        layout.addWidget(save_group)

        # OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_spin(self, grid, label: str, row: int, col: int,
                  min_val: int, max_val: int) -> QSpinBox:
        grid.addWidget(QLabel(label), row, col * 2)
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        grid.addWidget(spin, row, col * 2 + 1)
        return spin

    def _load_data(self):
        self._spin_opcode.setValue(self._affect.opcode)
        self._spin_target.setValue(self._affect.target_type)
        self._spin_power.setValue(self._affect.power)
        self._spin_param1.setValue(self._affect.parameter1)
        self._spin_param2.setValue(self._affect.parameter2)
        self._spin_timing.setValue(self._affect.timing_mode)
        self._spin_dispel.setValue(self._affect.dispel_type)
        self._spin_duration.setValue(self._affect.duration)
        self._spin_prob1.setValue(self._affect.probability1)
        self._spin_prob2.setValue(self._affect.probability2)
        self._spin_dice_thrown.setValue(self._affect.dice_thrown)
        self._spin_dice_sides.setValue(self._affect.dice_sides)
        self._spin_save_type.setValue(self._affect.saving_throw_type)
        self._spin_save_bonus.setValue(self._affect.saving_throw_bonus)
        self._spin_special.setValue(self._affect.special)
        self._edit_resource.setText(self._affect.resource)
        self._edit_resource3.setText(self._affect.resource3)

    def _on_accept(self):
        self._affect.opcode = self._spin_opcode.value()
        self._affect.target_type = self._spin_target.value()
        self._affect.power = self._spin_power.value()
        self._affect.parameter1 = self._spin_param1.value()
        self._affect.parameter2 = self._spin_param2.value()
        self._affect.timing_mode = self._spin_timing.value()
        self._affect.dispel_type = self._spin_dispel.value()
        self._affect.duration = self._spin_duration.value()
        self._affect.probability1 = self._spin_prob1.value()
        self._affect.probability2 = self._spin_prob2.value()
        self._affect.dice_thrown = self._spin_dice_thrown.value()
        self._affect.dice_sides = self._spin_dice_sides.value()
        self._affect.saving_throw_type = self._spin_save_type.value()
        self._affect.saving_throw_bonus = self._spin_save_bonus.value()
        self._affect.special = self._spin_special.value()
        self._affect.resource = self._edit_resource.text()
        self._affect.resource3 = self._edit_resource3.text()
        self.accept()

    def get_affect(self) -> InfAffect:
        return self._affect
