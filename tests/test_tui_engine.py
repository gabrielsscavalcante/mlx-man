import pytest
from unittest.mock import patch

from rich.text import Text
from mlx_man.tui_engine import (
    tui_select,
    tui_confirm,
    tui_text_input,
    main_menu_select,
    tui_table_select
)

def test_tui_select_navigation():
    header = Text("Header")
    footer = "Footer"
    with patch("mlx_man.tui_engine._read_key", side_effect=["down", "down", "up", "enter"]):
        choice = tui_select("Test Select", ["A", "B", "C"], lambda x: x, header, footer)
    assert choice == "B"

def test_tui_select_cancel():
    with patch("mlx_man.tui_engine._read_key", side_effect=["down", "escape"]):
        choice = tui_select("Test Select", ["A", "B", "C"], lambda x: x, Text(""), "")
    assert choice is None
    
    with patch("mlx_man.tui_engine._read_key", side_effect=["down", "q"]):
        choice = tui_select("Test Select", ["A", "B", "C"], lambda x: x, Text(""), "")
    assert choice is None

def test_tui_confirm_yes():
    # tui_confirm uses "up" and "down" just like the others
    with patch("mlx_man.tui_engine._read_key", side_effect=["down", "up", "down", "enter"]):
        choice = tui_confirm("Are you sure?", Text(""), "")
    assert choice is True

def test_tui_confirm_no():
    with patch("mlx_man.tui_engine._read_key", side_effect=["enter"]):
        choice = tui_confirm("Are you sure?", Text(""), "")
    assert choice is False

def test_tui_confirm_cancel():
    with patch("mlx_man.tui_engine._read_key", side_effect=["escape"]):
        choice = tui_confirm("Sure?", Text(""), "")
    assert choice is False

    with patch("mlx_man.tui_engine._read_key", side_effect=["q"]):
        choice = tui_confirm("Sure?", Text(""), "")
    assert choice is False

def test_tui_text_input():
    with patch("mlx_man.tui_engine._read_key", side_effect=["H", "e", "backspace", "i", "enter"]):
        text = tui_text_input("Name:", Text(""), "")
    assert text == "Hi"

def test_tui_text_input_cancel():
    with patch("mlx_man.tui_engine._read_key", side_effect=["H", "escape"]):
        text = tui_text_input("Name:", Text(""), "")
    assert text is None

def test_main_menu_select():
    items = [("Item 1", "val1"), None, ("Item 2", "val2")]
    with patch("mlx_man.tui_engine._read_key", side_effect=["down", "enter"]):
        choice = main_menu_select(items, Text(""), Text(""), "")
    assert choice == "val2"
    
    with patch("mlx_man.tui_engine._read_key", side_effect=["up", "enter"]):
        choice = main_menu_select(items, Text(""), Text(""), "")
    assert choice == "val2"

def test_main_menu_select_quit():
    items = [("Item 1", "val1")]
    with patch("mlx_man.tui_engine._read_key", side_effect=["q"]):
        choice = main_menu_select(items, Text(""), Text(""), "")
    assert choice is None

def test_tui_table_select():
    columns = [{"header": "Col1"}, {"header": "Col2"}]
    data = ["Row1", "Row2"]
    with patch("mlx_man.tui_engine._read_key", side_effect=["down", "up", "down", "enter"]):
        choice = tui_table_select("Table", columns, data, lambda x: [x, "Data"], Text(""), "")
    assert choice == "Row2"

def test_tui_table_select_extra_hotkey():
    with patch("mlx_man.tui_engine._read_key", side_effect=["f"]):
        choice = tui_table_select("Table", [{"header": "Col1"}], ["Row1"], lambda x: [x], Text(""), "", extra_hotkeys={"f": "filter"})
    assert choice == "filter"

def test_tui_table_select_cancel():
    with patch("mlx_man.tui_engine._read_key", side_effect=["escape"]):
        choice = tui_table_select("T", [{"header": "Col1"}], ["A"], lambda x: [x], Text(""), "")
    assert choice is None
    
    with patch("mlx_man.tui_engine._read_key", side_effect=["q"]):
        choice = tui_table_select("T", [{"header": "Col1"}], ["A"], lambda x: [x], Text(""), "")
    assert choice is None

def test_tui_table_select_empty_data():
    choice = tui_table_select("T", [{"header": "Col1"}], [], lambda x: [x], Text(""), "")
    assert choice is None

def test_tui_table_select_styled_columns():
    columns = [
        {"header": "Col1"}, 
        {"header": "Col2", "style": "bold red", "justify": "right", "width": 10}
    ]
    with patch("mlx_man.tui_engine._read_key", side_effect=["enter"]):
        choice = tui_table_select("T", columns, ["A"], lambda x: [x, "B"], Text(""), "")
    assert choice == "A"

def test_tui_table_select_rich_cells():
    from rich.text import Text
    class DummyCell:
        def __rich__(self): return Text("dummy")
    
    columns = [{"header": "Col1"}, {"header": "Col2"}, {"header": "Col3"}]
    with patch("mlx_man.tui_engine._read_key", side_effect=["enter"]):
        choice = tui_table_select("T", columns, ["A"], lambda x: [x, Text("B"), DummyCell()], Text(""), "")
    assert choice == "A"

def test_build_layout_too_small():
    from mlx_man.tui_engine import build_layout
    layout = build_layout(Text(""), "", 30, 10)
    # just asserts it didn't crash and returns the warning text layout
    assert layout is not None
