"""Tests for WeiDU mod log parsing."""

from pathlib import Path
from textwrap import dedent

import pytest

from py_eekeeper.mods import InstalledMod, parse_weidu_log


@pytest.fixture
def weidu_log(tmp_path: Path) -> Path:
    """Create a sample weidu.log in a temp directory."""
    content = dedent("""\
        // Log of Currently Installed WeiDU Mods
        // The top of the file is the 'oldest' mod
        // ~TP2_File~ #language_number #component_number // comment

        ~STRATAGEMS/SETUP-STRATAGEMS.TP2~ #0 #3400 // Smarter Mages
        ~STRATAGEMS/SETUP-STRATAGEMS.TP2~ #0 #3500 // Smarter Priests
        ~DLC_MERGER/SETUP-DLC_MERGER.TP2~ #0 #0 // Merge DLC into game
        ~TWEAKS_ANTHOLOGY/SETUP-TWEAKS_ANTHOLOGY.TP2~ #0 #3340 // Remove fatigue from rest
    """)
    log_path = tmp_path / "weidu.log"
    log_path.write_text(content, encoding="utf-8")
    return log_path


def test_parse_basic(weidu_log: Path):
    mods = parse_weidu_log(weidu_log)
    assert len(mods) == 4


def test_parse_mod_names(weidu_log: Path):
    mods = parse_weidu_log(weidu_log)
    names = [m.name for m in mods]
    assert names == [
        "STRATAGEMS",
        "STRATAGEMS",
        "DLC_MERGER",
        "TWEAKS_ANTHOLOGY",
    ]


def test_parse_components(weidu_log: Path):
    mods = parse_weidu_log(weidu_log)
    assert mods[0].component == 3400
    assert mods[1].component == 3500
    assert mods[2].component == 0
    assert mods[3].component == 3340


def test_parse_language(weidu_log: Path):
    mods = parse_weidu_log(weidu_log)
    for m in mods:
        assert m.language == 0


def test_parse_descriptions(weidu_log: Path):
    mods = parse_weidu_log(weidu_log)
    assert mods[0].description == "Smarter Mages"
    assert mods[1].description == "Smarter Priests"
    assert mods[2].description == "Merge DLC into game"
    assert mods[3].description == "Remove fatigue from rest"


def test_parse_skips_comments_and_blanks(tmp_path: Path):
    content = dedent("""\
        // This is a comment
        // Another comment

        ~MYMOD/SETUP-MYMOD.TP2~ #0 #1 // First component

        // more comments
    """)
    log_path = tmp_path / "weidu.log"
    log_path.write_text(content, encoding="utf-8")
    mods = parse_weidu_log(log_path)
    assert len(mods) == 1
    assert mods[0].name == "MYMOD"


def test_parse_no_description(tmp_path: Path):
    content = "~BAREMOD/SETUP-BAREMOD.TP2~ #1 #5\n"
    log_path = tmp_path / "weidu.log"
    log_path.write_text(content, encoding="utf-8")
    mods = parse_weidu_log(log_path)
    assert len(mods) == 1
    assert mods[0].name == "BAREMOD"
    assert mods[0].component == 5
    assert mods[0].language == 1
    assert mods[0].description == ""


def test_parse_nonexistent_file(tmp_path: Path):
    log_path = tmp_path / "nonexistent.log"
    mods = parse_weidu_log(log_path)
    assert mods == []


def test_parse_bare_tp2_no_folder(tmp_path: Path):
    """Handle a mod entry without a folder path separator."""
    content = "~SETUP-SIMPLEMOD.TP2~ #0 #0 // Simple\n"
    log_path = tmp_path / "weidu.log"
    log_path.write_text(content, encoding="utf-8")
    mods = parse_weidu_log(log_path)
    assert len(mods) == 1
    assert mods[0].name == "SETUP-SIMPLEMOD"


def test_parse_different_language(tmp_path: Path):
    content = "~FRMOD/SETUP-FRMOD.TP2~ #3 #100 // French component\n"
    log_path = tmp_path / "weidu.log"
    log_path.write_text(content, encoding="utf-8")
    mods = parse_weidu_log(log_path)
    assert mods[0].language == 3
    assert mods[0].component == 100
