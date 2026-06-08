"""Character sheet widget — displays and edits creature stats."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QSpinBox, QLineEdit, QComboBox, QScrollArea, QPushButton,
)
from PySide6.QtGui import QUndoStack
from PySide6.QtCore import Qt

from ..formats.inf_creature import InfCreature
from ..app import EEKeeperApp
from .undo_commands import SetAttributeCommand


class CharacterSheetWidget(QWidget):
    """Main character editing tab — stats, info, resistances, thief skills."""

    def __init__(self, parent=None, undo_stack: QUndoStack | None = None):
        super().__init__(parent)
        self._creature: InfCreature | None = None
        self._loading = False
        self._undo_stack = undo_stack
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        main_layout = QVBoxLayout(content)

        # Top row: attributes + combat
        top_row = QHBoxLayout()
        top_row.addWidget(self._create_attributes_group())
        top_row.addWidget(self._create_combat_group())
        top_row.addWidget(self._create_info_group())
        main_layout.addLayout(top_row)

        # Middle row: saves + resistances
        mid_row = QHBoxLayout()
        mid_row.addWidget(self._create_saves_group())
        mid_row.addWidget(self._create_resistances_group())
        mid_row.addWidget(self._create_thief_skills_group())
        main_layout.addLayout(mid_row)

        # Bottom: colors + scripts + IDS
        bot_row = QHBoxLayout()
        bot_row.addWidget(self._create_colors_group())
        bot_row.addWidget(self._create_ids_group())
        main_layout.addLayout(bot_row)

        main_layout.addStretch()
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _create_spin(self, min_val: int, max_val: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setFixedWidth(70)
        return spin

    def _create_attributes_group(self) -> QGroupBox:
        group = QGroupBox("Attributes")
        layout = QGridLayout(group)

        self._spin_str = self._create_spin(1, 25)
        self._spin_str_bonus = self._create_spin(0, 100)
        self._spin_dex = self._create_spin(1, 25)
        self._spin_con = self._create_spin(1, 25)
        self._spin_int = self._create_spin(1, 25)
        self._spin_wis = self._create_spin(1, 25)
        self._spin_cha = self._create_spin(1, 25)

        attrs = [
            ("STR:", self._spin_str), ("STR Bonus:", self._spin_str_bonus),
            ("DEX:", self._spin_dex), ("CON:", self._spin_con),
            ("INT:", self._spin_int), ("WIS:", self._spin_wis),
            ("CHA:", self._spin_cha),
        ]
        for i, (label, spin) in enumerate(attrs):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(spin, i, 1)
            spin.valueChanged.connect(self._on_attribute_changed)

        return group

    def _create_combat_group(self) -> QGroupBox:
        group = QGroupBox("Combat")
        layout = QGridLayout(group)

        self._spin_hp = self._create_spin(1, 9999)
        self._spin_max_hp = self._create_spin(1, 9999)
        self._spin_ac = self._create_spin(-20, 20)
        self._spin_thac0 = self._create_spin(-20, 20)
        self._spin_attacks = self._create_spin(0, 10)
        self._spin_xp = self._create_spin(0, 99999999)
        self._spin_xp.setFixedWidth(100)
        self._spin_gold = self._create_spin(0, 99999999)
        self._spin_gold.setFixedWidth(100)

        fields = [
            ("HP:", self._spin_hp), ("Max HP:", self._spin_max_hp),
            ("AC:", self._spin_ac), ("THAC0:", self._spin_thac0),
            ("Attacks:", self._spin_attacks), ("XP:", self._spin_xp),
            ("Gold:", self._spin_gold),
        ]
        for i, (label, spin) in enumerate(fields):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(spin, i, 1)
            spin.valueChanged.connect(self._on_combat_changed)

        return group

    def _create_info_group(self) -> QGroupBox:
        group = QGroupBox("Info")
        layout = QGridLayout(group)

        self._spin_level1 = self._create_spin(1, 50)
        self._spin_level2 = self._create_spin(0, 50)
        self._spin_level3 = self._create_spin(0, 50)

        app = EEKeeperApp.instance()
        self._combo_class = QComboBox()
        self._combo_race = QComboBox()
        self._combo_gender = QComboBox()
        self._combo_alignment = QComboBox()
        self._combo_kit = QComboBox()
        self._combo_enemy_ally = QComboBox()
        self._combo_racial_enemy = QComboBox()
        self._combo_animation = QComboBox()
        self._edit_state_flags = QLineEdit()
        self._label_state_names = QLabel("")

        for vl, combo in [
            (app.vl_class, self._combo_class),
            (app.vl_race, self._combo_race),
            (app.vl_gender, self._combo_gender),
            (app.vl_alignment, self._combo_alignment),
            (app.vl_kit, self._combo_kit),
            (app.vl_enemy_ally, self._combo_enemy_ally),
            (app.vl_racial_enemy, self._combo_racial_enemy),
            (app.vl_animations, self._combo_animation),
        ]:
            self._fill_combo(combo, vl.get_items())

        self._edit_state_flags.setPlaceholderText("0x0")

        fields = [
            ("Level 1:", self._spin_level1), ("Level 2:", self._spin_level2),
            ("Level 3:", self._spin_level3),
        ]
        for i, (label, w) in enumerate(fields):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(w, i, 1)

        combos = [
            ("Class:", self._combo_class), ("Race:", self._combo_race),
            ("Gender:", self._combo_gender), ("Alignment:", self._combo_alignment),
            ("Kit:", self._combo_kit),
            ("Enemy/Ally:", self._combo_enemy_ally),
            ("Racial Enemy:", self._combo_racial_enemy),
            ("Animation:", self._combo_animation),
        ]
        for i, (label, combo) in enumerate(combos, start=len(fields)):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(combo, i, 1)

        state_row = len(fields) + len(combos)
        layout.addWidget(QLabel("State Flags:"), state_row, 0)
        layout.addWidget(self._edit_state_flags, state_row, 1)
        layout.addWidget(QLabel("Active States:"), state_row + 1, 0)
        layout.addWidget(self._label_state_names, state_row + 1, 1)

        for spin in [self._spin_level1, self._spin_level2, self._spin_level3]:
            spin.valueChanged.connect(self._on_info_changed)
        for combo in [self._combo_class, self._combo_race, self._combo_gender,
                      self._combo_alignment, self._combo_kit,
                      self._combo_enemy_ally, self._combo_racial_enemy,
                      self._combo_animation]:
            combo.currentIndexChanged.connect(self._on_info_changed)
        self._edit_state_flags.textChanged.connect(self._on_state_flags_changed)

        return group

    def _create_saves_group(self) -> QGroupBox:
        group = QGroupBox("Saving Throws")
        layout = QGridLayout(group)

        self._spin_save_death = self._create_spin(0, 20)
        self._spin_save_wands = self._create_spin(0, 20)
        self._spin_save_poly = self._create_spin(0, 20)
        self._spin_save_breath = self._create_spin(0, 20)
        self._spin_save_spells = self._create_spin(0, 20)

        saves = [
            ("Death:", self._spin_save_death),
            ("Wands:", self._spin_save_wands),
            ("Polymorph:", self._spin_save_poly),
            ("Breath:", self._spin_save_breath),
            ("Spells:", self._spin_save_spells),
        ]
        for i, (label, spin) in enumerate(saves):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(spin, i, 1)
            spin.valueChanged.connect(self._on_saves_changed)

        return group

    def _create_resistances_group(self) -> QGroupBox:
        group = QGroupBox("Resistances")
        layout = QGridLayout(group)

        self._spin_res_fire = self._create_spin(-128, 127)
        self._spin_res_cold = self._create_spin(-128, 127)
        self._spin_res_elec = self._create_spin(-128, 127)
        self._spin_res_acid = self._create_spin(-128, 127)
        self._spin_res_magic = self._create_spin(-128, 127)
        self._spin_res_slash = self._create_spin(-128, 127)
        self._spin_res_crush = self._create_spin(-128, 127)
        self._spin_res_pierce = self._create_spin(-128, 127)
        self._spin_res_missile = self._create_spin(-128, 127)

        resistances = [
            ("Fire:", self._spin_res_fire), ("Cold:", self._spin_res_cold),
            ("Electricity:", self._spin_res_elec), ("Acid:", self._spin_res_acid),
            ("Magic:", self._spin_res_magic), ("Slashing:", self._spin_res_slash),
            ("Crushing:", self._spin_res_crush), ("Piercing:", self._spin_res_pierce),
            ("Missile:", self._spin_res_missile),
        ]
        for i, (label, spin) in enumerate(resistances):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(spin, i, 1)
            spin.valueChanged.connect(self._on_resistances_changed)

        return group

    def _create_thief_skills_group(self) -> QGroupBox:
        group = QGroupBox("Thief Skills")
        layout = QGridLayout(group)

        self._spin_open_locks = self._create_spin(0, 255)
        self._spin_find_traps = self._create_spin(0, 255)
        self._spin_pick_pockets = self._create_spin(0, 255)
        self._spin_move_silently = self._create_spin(0, 255)
        self._spin_hide_shadows = self._create_spin(0, 255)
        self._spin_detect_illusions = self._create_spin(0, 255)
        self._spin_set_traps = self._create_spin(0, 255)

        skills = [
            ("Open Locks:", self._spin_open_locks),
            ("Find Traps:", self._spin_find_traps),
            ("Pick Pockets:", self._spin_pick_pockets),
            ("Move Silently:", self._spin_move_silently),
            ("Hide in Shadows:", self._spin_hide_shadows),
            ("Detect Illusions:", self._spin_detect_illusions),
            ("Set Traps:", self._spin_set_traps),
        ]
        for i, (label, spin) in enumerate(skills):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(spin, i, 1)
            spin.valueChanged.connect(self._on_thief_changed)

        return group

    def _create_colors_group(self) -> QGroupBox:
        group = QGroupBox("Colors & Portraits")
        layout = QGridLayout(group)

        self._spin_metal = self._create_spin(0, 255)
        self._spin_minor = self._create_spin(0, 255)
        self._spin_major = self._create_spin(0, 255)
        self._spin_skin = self._create_spin(0, 255)
        self._spin_leather = self._create_spin(0, 255)
        self._spin_armor = self._create_spin(0, 255)
        self._spin_hair = self._create_spin(0, 255)

        self._edit_small_portrait = QLineEdit()
        self._edit_small_portrait.setMaxLength(8)
        self._edit_large_portrait = QLineEdit()
        self._edit_large_portrait.setMaxLength(8)

        colors = [
            ("Metal:", self._spin_metal), ("Minor:", self._spin_minor),
            ("Major:", self._spin_major), ("Skin:", self._spin_skin),
            ("Leather:", self._spin_leather), ("Armor:", self._spin_armor),
            ("Hair:", self._spin_hair),
        ]
        for i, (label, spin) in enumerate(colors):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(spin, i, 1)
            spin.valueChanged.connect(self._on_colors_changed)

        row = len(colors)
        layout.addWidget(QLabel("Small Portrait:"), row, 0)
        small_row = QHBoxLayout()
        small_row.addWidget(self._edit_small_portrait)
        btn_browse_small = QPushButton("...")
        btn_browse_small.setFixedWidth(30)
        btn_browse_small.clicked.connect(lambda: self._browse_portrait("S", self._edit_small_portrait))
        small_row.addWidget(btn_browse_small)
        layout.addLayout(small_row, row, 1)

        layout.addWidget(QLabel("Large Portrait:"), row + 1, 0)
        large_row = QHBoxLayout()
        large_row.addWidget(self._edit_large_portrait)
        btn_browse_large = QPushButton("...")
        btn_browse_large.setFixedWidth(30)
        btn_browse_large.clicked.connect(lambda: self._browse_portrait("L", self._edit_large_portrait))
        large_row.addWidget(btn_browse_large)
        layout.addLayout(large_row, row + 1, 1)

        self._edit_small_portrait.textChanged.connect(self._on_colors_changed)
        self._edit_large_portrait.textChanged.connect(self._on_colors_changed)

        return group

    def _create_ids_group(self) -> QGroupBox:
        group = QGroupBox("Scripts & IDS")
        layout = QGridLayout(group)

        self._edit_override_script = QLineEdit()
        self._edit_override_script.setMaxLength(8)
        self._edit_class_script = QLineEdit()
        self._edit_class_script.setMaxLength(8)
        self._edit_race_script = QLineEdit()
        self._edit_race_script.setMaxLength(8)
        self._edit_general_script = QLineEdit()
        self._edit_general_script.setMaxLength(8)
        self._edit_default_script = QLineEdit()
        self._edit_default_script.setMaxLength(8)

        scripts = [
            ("Override:", self._edit_override_script),
            ("Class:", self._edit_class_script),
            ("Race:", self._edit_race_script),
            ("General:", self._edit_general_script),
            ("Default:", self._edit_default_script),
        ]
        for i, (label, edit) in enumerate(scripts):
            layout.addWidget(QLabel(label), i, 0)
            layout.addWidget(edit, i, 1)
            edit.textChanged.connect(self._on_scripts_changed)

        return group

    # --- Load/Save ---

    def load_creature(self, creature: InfCreature):
        self._loading = True
        self._creature = creature

        # Attributes
        self._spin_str.setValue(creature.strength)
        self._spin_str_bonus.setValue(creature.strength_bonus)
        self._spin_dex.setValue(creature.dexterity)
        self._spin_con.setValue(creature.constitution)
        self._spin_int.setValue(creature.intelligence)
        self._spin_wis.setValue(creature.wisdom)
        self._spin_cha.setValue(creature.charisma)

        # Combat
        self._spin_hp.setValue(creature.current_hp)
        self._spin_max_hp.setValue(creature.base_hp)
        self._spin_ac.setValue(creature.ac1)
        self._spin_thac0.setValue(creature.thac0)
        self._spin_attacks.setValue(creature.attacks)
        self._spin_xp.setValue(creature.exp)
        self._spin_gold.setValue(creature.gold)

        # Levels
        self._spin_level1.setValue(creature.level_first_class)
        self._spin_level2.setValue(creature.level_second_class)
        self._spin_level3.setValue(creature.level_third_class)

        # Combos
        self._set_combo_value(self._combo_class, creature.class_id)
        self._set_combo_value(self._combo_race, creature.race)
        self._set_combo_value(self._combo_gender, creature.gender)
        self._set_combo_value(self._combo_alignment, creature.alignment)
        self._set_combo_value(self._combo_kit, creature.kit)
        self._set_combo_value(self._combo_enemy_ally, creature.enemy_ally)
        self._set_combo_value(self._combo_racial_enemy, creature.racial_enemy)
        self._set_combo_value(self._combo_animation, creature.animation_id)
        self._edit_state_flags.setText(f"0x{creature.state_flags:X}")
        self._label_state_names.setText(self._describe_state_flags(creature.state_flags))

        # Saves
        self._spin_save_death.setValue(creature.save_death)
        self._spin_save_wands.setValue(creature.save_wands)
        self._spin_save_poly.setValue(creature.save_poly)
        self._spin_save_breath.setValue(creature.save_breath)
        self._spin_save_spells.setValue(creature.save_spells)

        # Resistances
        self._spin_res_fire.setValue(creature.resist_fire)
        self._spin_res_cold.setValue(creature.resist_cold)
        self._spin_res_elec.setValue(creature.resist_electricity)
        self._spin_res_acid.setValue(creature.resist_acid)
        self._spin_res_magic.setValue(creature.resist_magic)
        self._spin_res_slash.setValue(creature.resist_slashing)
        self._spin_res_crush.setValue(creature.resist_crushing)
        self._spin_res_pierce.setValue(creature.resist_piercing)
        self._spin_res_missile.setValue(creature.resist_missile)

        # Thief
        self._spin_open_locks.setValue(creature.open_locks)
        self._spin_find_traps.setValue(creature.find_traps)
        self._spin_pick_pockets.setValue(creature.pick_pockets)
        self._spin_move_silently.setValue(creature.move_silently)
        self._spin_hide_shadows.setValue(creature.hide_in_shadows)
        self._spin_detect_illusions.setValue(creature.detect_illusions)
        self._spin_set_traps.setValue(creature.set_traps)

        # Colors
        self._spin_metal.setValue(creature.metal_color)
        self._spin_minor.setValue(creature.minor_color)
        self._spin_major.setValue(creature.major_color)
        self._spin_skin.setValue(creature.skin_color)
        self._spin_leather.setValue(creature.leather_color)
        self._spin_armor.setValue(creature.armor_color)
        self._spin_hair.setValue(creature.hair_color)

        # Portraits
        self._edit_small_portrait.setText(creature.small_portrait)
        self._edit_large_portrait.setText(creature.large_portrait)

        # Scripts
        self._edit_override_script.setText(creature.override_script)
        self._edit_class_script.setText(creature.class_script)
        self._edit_race_script.setText(creature.race_script)
        self._edit_general_script.setText(creature.general_script)
        self._edit_default_script.setText(creature.default_script)

        self._loading = False

    def _set_combo_value(self, combo: QComboBox, value: int):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return
        combo.addItem(f"Unknown ({value})", value)
        combo.setCurrentIndex(combo.count() - 1)

    @staticmethod
    def _fill_combo(combo: QComboBox, items):
        for item in items:
            combo.addItem(item.name, item.index)

    def _describe_state_flags(self, state_flags: int) -> str:
        app = EEKeeperApp.instance()
        names = [
            item.name
            for item in app.vl_state.get_items()
            if item.index and (state_flags & item.index) == item.index
        ]
        return ", ".join(names) if names else "None"

    # --- Undo helper ---

    def _push_change(self, attr_name: str, new_value):
        """Push a SetAttributeCommand or directly apply the change."""
        if not self._creature:
            return
        old_value = getattr(self._creature, attr_name)
        if old_value == new_value:
            return
        if self._undo_stack:
            cmd = SetAttributeCommand(
                self._creature, attr_name, old_value, new_value
            )
            self._undo_stack.push(cmd)
        else:
            setattr(self._creature, attr_name, new_value)

    # --- Handlers ---

    def _on_attribute_changed(self):
        if self._loading or not self._creature:
            return
        self._push_change("strength", self._spin_str.value())
        self._push_change("strength_bonus", self._spin_str_bonus.value())
        self._push_change("dexterity", self._spin_dex.value())
        self._push_change("constitution", self._spin_con.value())
        self._push_change("intelligence", self._spin_int.value())
        self._push_change("wisdom", self._spin_wis.value())
        self._push_change("charisma", self._spin_cha.value())

    def _on_combat_changed(self):
        if self._loading or not self._creature:
            return
        self._push_change("current_hp", self._spin_hp.value())
        self._push_change("base_hp", self._spin_max_hp.value())
        self._push_change("ac1", self._spin_ac.value())
        self._push_change("thac0", self._spin_thac0.value())
        self._push_change("attacks", self._spin_attacks.value())
        self._push_change("exp", self._spin_xp.value())
        self._push_change("gold", self._spin_gold.value())

    def _on_info_changed(self):
        if self._loading or not self._creature:
            return
        self._push_change("level_first_class", self._spin_level1.value())
        self._push_change("level_second_class", self._spin_level2.value())
        self._push_change("level_third_class", self._spin_level3.value())
        self._push_change("class_id", self._combo_class.currentData() or 0)
        self._push_change("race", self._combo_race.currentData() or 0)
        self._push_change("gender", self._combo_gender.currentData() or 0)
        self._push_change("alignment", self._combo_alignment.currentData() or 0)
        self._push_change("kit", self._combo_kit.currentData() or 0)
        self._push_change("enemy_ally", self._combo_enemy_ally.currentData() or 0)
        self._push_change("racial_enemy", self._combo_racial_enemy.currentData() or 0)
        self._push_change("animation_id", self._combo_animation.currentData() or 0)

    def _on_state_flags_changed(self):
        if self._loading or not self._creature:
            return
        try:
            value = int(self._edit_state_flags.text().strip() or "0", 0)
        except ValueError:
            return
        self._push_change("state_flags", value)
        self._label_state_names.setText(self._describe_state_flags(value))

    def _on_saves_changed(self):
        if self._loading or not self._creature:
            return
        self._push_change("save_death", self._spin_save_death.value())
        self._push_change("save_wands", self._spin_save_wands.value())
        self._push_change("save_poly", self._spin_save_poly.value())
        self._push_change("save_breath", self._spin_save_breath.value())
        self._push_change("save_spells", self._spin_save_spells.value())

    def _on_resistances_changed(self):
        if self._loading or not self._creature:
            return
        self._push_change("resist_fire", self._spin_res_fire.value())
        self._push_change("resist_cold", self._spin_res_cold.value())
        self._push_change("resist_electricity", self._spin_res_elec.value())
        self._push_change("resist_acid", self._spin_res_acid.value())
        self._push_change("resist_magic", self._spin_res_magic.value())
        self._push_change("resist_slashing", self._spin_res_slash.value())
        self._push_change("resist_crushing", self._spin_res_crush.value())
        self._push_change("resist_piercing", self._spin_res_pierce.value())
        self._push_change("resist_missile", self._spin_res_missile.value())

    def _on_thief_changed(self):
        if self._loading or not self._creature:
            return
        self._push_change("open_locks", self._spin_open_locks.value())
        self._push_change("find_traps", self._spin_find_traps.value())
        self._push_change("pick_pockets", self._spin_pick_pockets.value())
        self._push_change("move_silently", self._spin_move_silently.value())
        self._push_change("hide_in_shadows", self._spin_hide_shadows.value())
        self._push_change("detect_illusions", self._spin_detect_illusions.value())
        self._push_change("set_traps", self._spin_set_traps.value())

    def _on_colors_changed(self):
        if self._loading or not self._creature:
            return
        self._push_change("metal_color", self._spin_metal.value())
        self._push_change("minor_color", self._spin_minor.value())
        self._push_change("major_color", self._spin_major.value())
        self._push_change("skin_color", self._spin_skin.value())
        self._push_change("leather_color", self._spin_leather.value())
        self._push_change("armor_color", self._spin_armor.value())
        self._push_change("hair_color", self._spin_hair.value())
        self._push_change("small_portrait", self._edit_small_portrait.text())
        self._push_change("large_portrait", self._edit_large_portrait.text())

    def _on_scripts_changed(self):
        if self._loading or not self._creature:
            return
        self._push_change("override_script", self._edit_override_script.text())
        self._push_change("class_script", self._edit_class_script.text())
        self._push_change("race_script", self._edit_race_script.text())
        self._push_change("general_script", self._edit_general_script.text())
        self._push_change("default_script", self._edit_default_script.text())

    def _browse_portrait(self, size_filter: str, target_edit: QLineEdit):
        from .portrait_browser import PortraitBrowserDialog
        dialog = PortraitBrowserDialog(self, size_filter=size_filter)
        if dialog.exec():
            name = dialog.selected_portrait
            if name:
                target_edit.setText(name + size_filter)
