import pytest
from unittest.mock import patch

from mlx_man.main import main

@patch("mlx_man.main.main_menu_select", side_effect=KeyboardInterrupt)
@patch("builtins.print")
def test_main_keyboard_interrupt(mock_print, mock_select):
    main()
    mock_print.assert_called_with("\n  \033[32m✔\033[0m  Goodbye! 👋\n")

def test_main_import():
    import mlx_man.__main__
