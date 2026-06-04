"""Tests for 2DA parser."""

from py_eekeeper.formats.inf_2da import Inf2DA


def test_parse_basic():
    text = """2DA V1.0
*
       COL1    COL2    COL3
ROW1   val1    val2    val3
ROW2   val4    val5    val6
"""
    da = Inf2DA()
    assert da.parse(text) is True
    assert da.rows == 2
    assert da.cols == 3
    assert da.get_value(0, 0) == "val1"
    assert da.get_value(1, 2) == "val6"
    assert da.get_row_name(0) == "ROW1"
    assert da.get_col_name(1) == "COL2"


def test_parse_bytes():
    data = b"2DA V1.0\n*\n       A    B\nR1   1    2\n"
    da = Inf2DA()
    assert da.parse(data) is True
    assert da.rows == 1
    assert da.cols == 2
    assert da.get_value(0, 0) == "1"
    assert da.get_value(0, 1) == "2"


def test_find_row_col():
    text = "2DA V1.0\n*\n       WEAPON    ARMOR\nFIGHTER   5    3\nTHIEF   2    1\n"
    da = Inf2DA()
    assert da.parse(text)
    assert da.find_row("FIGHTER") == 0
    assert da.find_row("THIEF") == 1
    assert da.find_row("MAGE") == -1
    assert da.find_col("WEAPON") == 0
    assert da.find_col("ARMOR") == 1


def test_default_value():
    text = "2DA V1.0\nDEFAULT\n       A    B\nR1   1\n"
    da = Inf2DA()
    assert da.parse(text)
    assert da.get_value(0, 0) == "1"
    assert da.get_value(0, 1) == "DEFAULT"
    assert da.get_value(5, 5) == "DEFAULT"


def test_empty_input():
    da = Inf2DA()
    assert da.parse("") is False
    assert da.parse("INVALID") is False
