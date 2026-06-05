"""QUndoCommand subclasses for undo/redo support."""

from PySide6.QtGui import QUndoCommand

from ..formats.inf_creature import InfCreature, CreItem, KnownSpell
from ..formats.inf_affect import InfAffect


class SetAttributeCommand(QUndoCommand):
    """Generic property change on a creature."""

    def __init__(self, creature: InfCreature, attr_name: str,
                 old_value, new_value, description: str = ""):
        text = description or f"Set {attr_name}"
        super().__init__(text)
        self._creature = creature
        self._attr_name = attr_name
        self._old_value = old_value
        self._new_value = new_value

    def redo(self):
        setattr(self._creature, self._attr_name, self._new_value)

    def undo(self):
        setattr(self._creature, self._attr_name, self._old_value)

    def id(self) -> int:
        # Use a stable id based on the attribute name to allow merging
        return hash(("SetAttribute", self._attr_name)) & 0x7FFFFFFF

    def mergeWith(self, other: QUndoCommand) -> bool:
        """Merge consecutive changes to the same attribute on the same creature."""
        if not isinstance(other, SetAttributeCommand):
            return False
        if self._creature is not other._creature:
            return False
        if self._attr_name != other._attr_name:
            return False
        # Keep our old_value, take the new command's new_value
        self._new_value = other._new_value
        return True


class AddItemCommand(QUndoCommand):
    """Add an item to a creature's inventory slot."""

    def __init__(self, creature: InfCreature, slot_index: int, item: CreItem):
        super().__init__(f"Add item {item.res_name} to slot {slot_index}")
        self._creature = creature
        self._slot_index = slot_index
        self._item = item
        self._previous_item: CreItem | None = None

    def redo(self):
        self._previous_item = self._creature.get_item(self._slot_index)
        self._creature.set_item(self._slot_index, self._item)

    def undo(self):
        if self._previous_item is not None:
            self._creature.set_item(self._slot_index, self._previous_item)


class RemoveItemCommand(QUndoCommand):
    """Remove an item from a creature's inventory slot."""

    def __init__(self, creature: InfCreature, slot_index: int):
        super().__init__(f"Remove item from slot {slot_index}")
        self._creature = creature
        self._slot_index = slot_index
        self._removed_item: CreItem | None = None

    def redo(self):
        self._removed_item = self._creature.get_item(self._slot_index)
        self._creature.set_item(self._slot_index, CreItem())

    def undo(self):
        if self._removed_item is not None:
            self._creature.set_item(self._slot_index, self._removed_item)


class AddSpellCommand(QUndoCommand):
    """Add a known spell to a creature."""

    def __init__(self, creature: InfCreature, spell_type: int,
                 name: str, level: int):
        super().__init__(f"Add spell {name}")
        self._creature = creature
        self._spell_type = spell_type
        self._name = name
        self._level = level

    def redo(self):
        self._creature.add_known_spell(self._spell_type, self._name, self._level)

    def undo(self):
        self._creature.remove_known_spell(self._spell_type, self._name)


class RemoveSpellCommand(QUndoCommand):
    """Remove a known spell from a creature."""

    def __init__(self, creature: InfCreature, spell_type: int,
                 name: str, level: int):
        super().__init__(f"Remove spell {name}")
        self._creature = creature
        self._spell_type = spell_type
        self._name = name
        self._level = level

    def redo(self):
        self._creature.remove_known_spell(self._spell_type, self._name)

    def undo(self):
        self._creature.add_known_spell(self._spell_type, self._name, self._level)


class AddAffectCommand(QUndoCommand):
    """Add an affect (effect) to a creature."""

    def __init__(self, creature: InfCreature, affect: InfAffect):
        super().__init__(f"Add affect (opcode {affect.opcode})")
        self._creature = creature
        self._affect = affect

    def redo(self):
        self._creature.add_affect(self._affect)

    def undo(self):
        self._creature.remove_affect(self._affect)


class RemoveAffectCommand(QUndoCommand):
    """Remove an affect (effect) from a creature."""

    def __init__(self, creature: InfCreature, affect: InfAffect,
                 index: int = -1):
        super().__init__(f"Remove affect (opcode {affect.opcode})")
        self._creature = creature
        self._affect = affect
        self._index = index

    def redo(self):
        self._creature.remove_affect(self._affect)

    def undo(self):
        self._creature.add_affect(self._affect, self._index)
