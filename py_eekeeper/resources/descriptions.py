"""Description lookups for SPL and ITM resources via TLK."""

import struct

from ..formats.constants import RESTYPE_SPL, RESTYPE_ITM

# Module-level caches to avoid repeated resource loading and TLK lookups.
_spell_desc_cache: dict[str, str] = {}
_item_desc_cache: dict[str, str] = {}

_MAX_DESC_LENGTH = 200


def _truncate(text: str) -> str:
    """Truncate text to a reasonable tooltip length."""
    if len(text) <= _MAX_DESC_LENGTH:
        return text
    return text[:_MAX_DESC_LENGTH].rstrip() + "..."


def get_spell_description(res_name: str) -> str:
    """Load SPL resource and extract description text from TLK.

    SPL header: strref for identified description at offset 0x54 (uint32).
    Returns empty string on any error.
    """
    if res_name in _spell_desc_cache:
        return _spell_desc_cache[res_name]

    desc = _load_description(res_name, RESTYPE_SPL)
    _spell_desc_cache[res_name] = desc
    return desc


def get_item_description(res_name: str) -> str:
    """Load ITM resource and extract description text from TLK.

    ITM header: strref for identified description at offset 0x54 (uint32).
    Returns empty string on any error.
    """
    if res_name in _item_desc_cache:
        return _item_desc_cache[res_name]

    desc = _load_description(res_name, RESTYPE_ITM)
    _item_desc_cache[res_name] = desc
    return desc


def _load_description(res_name: str, res_type: int) -> str:
    """Common loader for SPL/ITM identified description at offset 0x54."""
    try:
        from ..app import EEKeeperApp

        app = EEKeeperApp.instance()
        data = app.resource_manager.get_resource(res_type, res_name)
        if not data or len(data) < 0x58:
            return ""

        strref = struct.unpack_from("<I", data, 0x54)[0]
        if strref == 0xFFFFFFFF:
            return ""

        text = app.tlk.get_string(strref)
        if not text:
            return ""

        return _truncate(text)
    except Exception:
        return ""


def clear_caches():
    """Clear description caches (e.g. when switching game installations)."""
    _spell_desc_cache.clear()
    _item_desc_cache.clear()
