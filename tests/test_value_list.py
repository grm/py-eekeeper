"""Tests for generic game value lists."""

import sys
import types

from py_eekeeper.formats.constants import RESTYPE_IDS
from py_eekeeper.resources.value_list import ValueList


def test_value_list_load_from_ids_accepts_hex_indices():
    value_list = ValueList("Alignment")

    assert value_list.load_from_ids(
        """15
0x11 LAWFUL_GOOD
0x22 NEUTRAL
0x33 CHAOTIC_EVIL
"""
    )

    assert [(item.index, item.name) for item in value_list.get_items()] == [
        (0x11, "LAWFUL_GOOD"),
        (0x22, "NEUTRAL"),
        (0x33, "CHAOTIC_EVIL"),
    ]


def test_load_ids_value_list_tries_alignment_resource_names(monkeypatch):
    qtcore = types.ModuleType("PySide6.QtCore")

    class QSettings:
        def __init__(self, *_args, **_kwargs):
            pass

        def value(self, _key, default=None, *_args, **_kwargs):
            return default

        def setValue(self, *_args, **_kwargs):
            pass

        def sync(self):
            pass

    qtcore.QSettings = QSettings
    qtgui = types.ModuleType("PySide6.QtGui")
    qtgui.QPixmap = object
    qtgui.QImage = object
    pyside = types.ModuleType("PySide6")
    monkeypatch.setitem(sys.modules, "PySide6", pyside)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", qtcore)
    monkeypatch.setitem(sys.modules, "PySide6.QtGui", qtgui)

    from py_eekeeper.app import EEKeeperApp

    class StubResourceManager:
        def get_resource(self, res_type: int, res_name: str) -> bytes | None:
            if res_type == RESTYPE_IDS and res_name == "ALIGN":
                return b"15\n0x11 LAWFUL_GOOD\n"
            return None

    app = EEKeeperApp()
    app.resource_manager = StubResourceManager()
    value_list = ValueList("Alignment")

    assert app._load_ids_value_list(value_list, "ALIGN", "ALIGNMEN")
    assert [(item.index, item.name) for item in value_list.get_items()] == [
        (0x11, "LAWFUL_GOOD"),
    ]
