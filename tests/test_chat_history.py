import pytest
from unittest.mock import patch, MagicMock
from mlx_man.chat_manager import ChatSession
from mlx_man.chat_history_view import action_chat_history

@patch("mlx_man.chat_history_view.get_all_sessions")
@patch("mlx_man.chat_history_view.tui_text_input")
def test_action_chat_history_empty(mock_input, mock_get_sessions):
    mock_get_sessions.return_value = []
    action_chat_history()
    mock_input.assert_called_once()

@patch("mlx_man.chat_history_view.get_all_sessions")
@patch("mlx_man.chat_history_view.tui_table_select")
def test_action_chat_history_back(mock_table, mock_get_sessions):
    s = ChatSession("id1", "m", "2024-01-01T12:00", [{"role": "user", "content": "hi"}])
    mock_get_sessions.return_value = [s]
    mock_table.return_value = None # user pressed esc
    action_chat_history()
    mock_table.assert_called_once()
    
    # Also test row formatting manually
    row_func = mock_table.call_args.kwargs["row_func"]
    row = row_func(s)
    assert row[1] == "m"
    assert row[2] == "1"
    
    s_empty = ChatSession("id2", "m", "2024-01-01T12:00", [])
    row_empty = row_func(s_empty)
    assert row_empty[3] == "Empty"

@patch("mlx_man.chat_history_view.delete_session")
@patch("mlx_man.chat_history_view.tui_confirm", return_value=True)
@patch("mlx_man.chat_history_view.tui_select", return_value=("delete", ""))
@patch("mlx_man.chat_history_view.tui_table_select")
@patch("mlx_man.chat_history_view.get_all_sessions")
def test_action_chat_history_delete(mock_get_sessions, mock_table, mock_select, mock_confirm, mock_delete):
    s = ChatSession("id1", "m", "2024-01-01T12:00", [])
    mock_get_sessions.return_value = [s]
    # first returns s, second loop returns None to exit
    mock_table.side_effect = [s, None] 
    
    action_chat_history()
    mock_delete.assert_called_with("id1")

@patch("mlx_man.chat_history_view.export_session")
@patch("mlx_man.chat_history_view.tui_text_input", return_value="") # use default path
@patch("mlx_man.chat_history_view.tui_select")
@patch("mlx_man.chat_history_view.tui_table_select")
@patch("mlx_man.chat_history_view.get_all_sessions")
def test_action_chat_history_export(mock_get_sessions, mock_table, mock_select, mock_input, mock_export):
    s = ChatSession("id1", "m", "2024-01-01T12:00", [])
    mock_get_sessions.return_value = [s]
    mock_table.side_effect = [s, None] 
    
    # action select returns export, format select returns markdown
    mock_select.side_effect = [("export", ""), ("markdown", "")]
    
    action_chat_history()
    mock_export.assert_called_once()
    
    # Test error handling on export
    mock_table.side_effect = [s, None]
    mock_select.side_effect = [("export", ""), ("json", "")]
    mock_input.return_value = "custom_path.json"
    mock_export.side_effect = Exception("failed")
    action_chat_history()

@patch("mlx_man.native_chat_view.run_chat_session")
@patch("mlx_man.chat_history_view.tui_select", return_value=("resume", ""))
@patch("mlx_man.chat_history_view.tui_table_select")
@patch("mlx_man.chat_history_view.get_all_sessions")
def test_action_chat_history_resume(mock_get_sessions, mock_table, mock_select, mock_run):
    s = ChatSession("id1", "m", "2024-01-01T12:00", [])
    mock_get_sessions.return_value = [s]
    mock_table.side_effect = [s, None] 
    action_chat_history()
    mock_run.assert_called_with("m", "id1")

@patch("mlx_man.chat_history_view.tui_select", return_value=("back", ""))
@patch("mlx_man.chat_history_view.tui_table_select")
@patch("mlx_man.chat_history_view.get_all_sessions")
def test_action_chat_history_back_action(mock_get_sessions, mock_table, mock_select):
    s = ChatSession("id1", "m", "2024-01-01T12:00", [])
    mock_get_sessions.return_value = [s]
    mock_table.side_effect = [s, None] 
    action_chat_history()
    
@patch("mlx_man.chat_history_view.tui_select", return_value=None)
@patch("mlx_man.chat_history_view.tui_table_select")
@patch("mlx_man.chat_history_view.get_all_sessions")
def test_action_chat_history_none_action(mock_get_sessions, mock_table, mock_select):
    s = ChatSession("id1", "m", "2024-01-01T12:00", [])
    mock_get_sessions.return_value = [s]
    mock_table.side_effect = [s, None] 
    action_chat_history()
    
@patch("mlx_man.chat_history_view.tui_select")
@patch("mlx_man.chat_history_view.tui_table_select")
@patch("mlx_man.chat_history_view.get_all_sessions")
def test_action_chat_history_none_format(mock_get_sessions, mock_table, mock_select):
    s = ChatSession("id1", "m", "2024-01-01T12:00", [])
    mock_get_sessions.return_value = [s]
    mock_table.side_effect = [s, None] 
    mock_select.side_effect = [("export", ""), None]
    action_chat_history()
