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

@patch("mlx_man.main.main_menu_select", side_effect=["sync", "exit"])
@patch("mlx_man.main.action_sync_models")
def test_main_sync(mock_sync, mock_select):
    main()
    mock_sync.assert_called_once()

@patch("mlx_man.main.action_manage_server")
@patch("mlx_man.main.main_menu_select", side_effect=["server_manage", "exit"])
def test_main_server_manage(mock_select, mock_manage):
    from mlx_man.main import main
    main()
    mock_manage.assert_called_once()

@patch("mlx_man.main.action_run_server")
@patch("mlx_man.main.action_manage_server")
@patch("mlx_man.main.run_memory_cleaner")
@patch("mlx_man.main.run_model_inspector")
@patch("mlx_man.main.run_insights_history")
@patch("mlx_man.main.action_chat_history")
@patch("mlx_man.main.action_sync_models")
@patch("mlx_man.main.main_menu_select", side_effect=["run", "server_manage", "clean", "manage", "insights", "history", "sync", "exit"])
def test_main_all_branches(mock_select, mock_sync, mock_history, mock_insights, mock_inspector, mock_cleaner, mock_manage, mock_run):
    from mlx_man.main import main
    main()
    mock_run.assert_called_once()
    mock_manage.assert_called_once()
    mock_cleaner.assert_called_once()
    mock_inspector.assert_called_once()
    mock_insights.assert_called_once()
    mock_history.assert_called_once()
    mock_sync.assert_called_once()

@patch("mlx_man.main.main_menu_select", side_effect=["quantize", "exit"])
@patch("mlx_man.main.action_quantize_model")
@patch("builtins.print")
def test_main_menu_quantize(mock_print, mock_quantize, mock_select):
    from mlx_man.main import main
    main()
    mock_quantize.assert_called_once()
