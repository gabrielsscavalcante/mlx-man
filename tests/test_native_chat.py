import pytest
from unittest.mock import patch, MagicMock
from mlx_man.native_chat_view import run_chat_session
from mlx_man.chat_manager import ChatSession

class MockResponseObj:
    def __init__(self, text):
        self.text = text

@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.load_session")
@patch("mlx_man.native_chat_view.save_session")
def test_run_chat_session_no_mlx_lm(mock_save, mock_load, mock_console):
    import builtins
    original_import = builtins.__import__
    
    def mock_import(name, *args):
        if name == "mlx_lm":
            raise ImportError("mock error")
        return original_import(name, *args)
        
    with patch("builtins.__import__", side_effect=mock_import):
        run_chat_session("m")
        
@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.load_session")
@patch("mlx_man.native_chat_view.save_session")
def test_run_chat_session_load_fail(mock_save, mock_load, mock_console):
    mock_mlx = MagicMock()
    mock_mlx.load.side_effect = Exception("load error")
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    with patch("builtins.input"): # intercept "Press enter"
        run_chat_session("m")

@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.load_session")
@patch("mlx_man.native_chat_view.save_session")
def test_run_chat_session_resume_not_found(mock_save, mock_load, mock_console):
    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (MagicMock(), MagicMock())
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    mock_load.return_value = None
    
    with patch("builtins.input"):
        run_chat_session("m", "bad_id")

@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.load_session")
@patch("mlx_man.native_chat_view.save_session")
def test_run_chat_session_resume_and_chat(mock_save, mock_load, mock_console_cls):
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console
    
    # User inputs: empty, hello, quit
    mock_console.input.side_effect = ["", "hello", "quit"]
    
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "prompt"
    
    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (mock_model, mock_tokenizer)
    mock_mlx.stream_generate.return_value = [MockResponseObj("hi"), MockResponseObj("!")]
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    session = ChatSession("id", "m", "2024", [
        {"role": "user", "content": "u"},
        {"role": "assistant", "content": "a"}
    ])
    mock_load.return_value = session
    
    run_chat_session("m", "id")
    assert mock_save.call_count == 2 # once after user input, once after assistant

@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.save_session")
def test_run_chat_session_new_interrupt(mock_save, mock_console_cls):
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console
    mock_console.input.side_effect = KeyboardInterrupt
    
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    
    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (mock_model, mock_tokenizer)
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    run_chat_session("m")
    
@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.save_session")
def test_run_chat_session_generation_interrupt(mock_save, mock_console_cls):
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console
    mock_console.input.side_effect = ["test", EOFError]
    
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.side_effect = Exception("no template")
    
    def mock_stream(*args, **kwargs):
        yield MockResponseObj("hi")
        raise KeyboardInterrupt()
        
    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (mock_model, mock_tokenizer)
    mock_mlx.stream_generate = mock_stream
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    run_chat_session("m")
    # should save the "hi" generated so far
    saved_session = mock_save.call_args[0][0]
    assert saved_session.messages[-1]["content"] == "hi"

