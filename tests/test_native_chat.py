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


@patch("mlx_lm.load")
@patch("mlx_lm.stream_generate")
@patch("builtins.print")
def test_run_chat_session_with_adapter(mock_print, mock_stream, mock_load):
    from mlx_man.native_chat_view import run_chat_session
    mock_load.return_value = (MagicMock(), MagicMock())
    
    # Just to exit loop quickly
    with patch("mlx_man.native_chat_view.Console.input", side_effect=["quit"]):
        run_chat_session("my_model", adapter_path="my_adapter")
        
    mock_load.assert_called_once_with("my_model", adapter_path="my_adapter")

@patch("mlx_lm.load")
@patch("mlx_lm.stream_generate")
@patch("builtins.print")
def test_run_chat_session_with_adapter(mock_print, mock_stream, mock_load):
    from mlx_man.native_chat_view import run_chat_session
    mock_load.return_value = (MagicMock(), MagicMock())
    
    # Just to exit loop quickly
    with patch("mlx_man.native_chat_view.Console.input", side_effect=["quit"]):
        run_chat_session("my_model", adapter_path="my_adapter")
        
    mock_load.assert_called_once_with("my_model", adapter_path="my_adapter")

@patch("mlx_lm.load")
@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.save_session")
@patch("mlx_man.native_chat_view.AVAILABLE_TOOLS")
def test_run_chat_session_agentic_loop(mock_tools, mock_save, mock_console_cls, mock_load):
    from mlx_man.native_chat_view import run_chat_session
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console
    # First input is "hi", then input to confirm tool is "y", then we exit.
    mock_console.input.side_effect = ["hi", "y", "quit"]
    
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "prompt"
    
    # We will simulate stream_generate yielding a tool call response first, then a regular response
    def mock_stream(*args, **kwargs):
        # first time called (len of messages is 2: system + user) -> return tool call
        if "prompt" in kwargs.get("prompt", ""): # just generic check
            # return tool call
            yield MockResponseObj('<tool_call>{"name": "test_tool", "arguments": {"a": 1}}</tool_call>')
        else:
            yield MockResponseObj("normal response")

    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (mock_model, mock_tokenizer)
    
    # Needs to hold state to return different things
    call_count = [0]
    def mock_stream_stateful(*args, **kwargs):
        if call_count[0] == 0:
            call_count[0] += 1
            yield MockResponseObj('<tool_call>{"name": "test_tool", "arguments": {"a": 1}}</tool_call>')
        else:
            yield MockResponseObj("Done.")
            
    mock_mlx.stream_generate = mock_stream_stateful
    
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    mock_tools.__contains__.side_effect = lambda x: True
    mock_tool = MagicMock(return_value="tool output")
    mock_tools.__getitem__.return_value = mock_tool
    
    run_chat_session("model_id")
    
    # Check that tool was called
    mock_tool.assert_called_once_with(a=1)
    
    # Check that the tool result was added to the session
    saved_session = mock_save.call_args[0][0]
    messages = saved_session.messages
    # system, user (hi), assistant (tool_call), user (tool_result), assistant (Done.)
    assert len(messages) >= 5
    assert "tool output" in messages[-2]["content"]
    assert messages[-1]["content"] == "Done."

@patch("mlx_lm.load")
@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.save_session")
@patch("mlx_man.native_chat_view.AVAILABLE_TOOLS")
def test_run_chat_session_agentic_loop_denied_tool(mock_tools, mock_save, mock_console_cls, mock_load):
    from mlx_man.native_chat_view import run_chat_session
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console
    # First input is "hi", then input to confirm tool is "n" (deny), then we exit.
    mock_console.input.side_effect = ["hi", "n", "quit"]
    
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    
    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (mock_model, mock_tokenizer)
    
    call_count = [0]
    def mock_stream_stateful(*args, **kwargs):
        if call_count[0] == 0:
            call_count[0] += 1
            yield MockResponseObj('<tool_call>{"name": "test_tool", "arguments": {"a": 1}}</tool_call>')
        else:
            yield MockResponseObj("Done.")
            
    mock_mlx.stream_generate = mock_stream_stateful
    
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    mock_tools.__contains__.side_effect = lambda x: True
    mock_tool = MagicMock()
    mock_tools.__getitem__.return_value = mock_tool
    
    run_chat_session("model_id")
    
    # Check that tool was NOT called
    mock_tool.assert_not_called()
    
    # Check that the tool result contains denied message
    saved_session = mock_save.call_args[0][0]
    messages = saved_session.messages
    assert "User denied permission" in messages[-2]["content"]

@patch("mlx_lm.load")
@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.save_session")
def test_run_chat_session_agentic_invalid_json(mock_save, mock_console_cls, mock_load):
    from mlx_man.native_chat_view import run_chat_session
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console
    mock_console.input.side_effect = ["hi", "quit"]
    
    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (MagicMock(), MagicMock())
    
    call_count = [0]
    def mock_stream_stateful(*args, **kwargs):
        if call_count[0] == 0:
            call_count[0] += 1
            yield MockResponseObj('<tool_call>invalid json</tool_call>')
        else:
            yield MockResponseObj("Done.")
            
    mock_mlx.stream_generate = mock_stream_stateful
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    run_chat_session("model_id")
    
    saved_session = mock_save.call_args[0][0]
    assert "Error parsing tool call" in saved_session.messages[-2]["content"]

@patch("mlx_lm.load")
@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.save_session")
def test_run_chat_session_agentic_invalid_tool(mock_save, mock_console_cls, mock_load):
    from mlx_man.native_chat_view import run_chat_session
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console
    mock_console.input.side_effect = ["hi", "quit"]
    
    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (MagicMock(), MagicMock())
    
    call_count = [0]
    def mock_stream_stateful(*args, **kwargs):
        if call_count[0] == 0:
            call_count[0] += 1
            yield MockResponseObj('<tool_call>{"name": "fake", "arguments": {}}</tool_call>')
        else:
            yield MockResponseObj("Done.")
            
    mock_mlx.stream_generate = mock_stream_stateful
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    run_chat_session("model_id")
    
    saved_session = mock_save.call_args[0][0]
    assert "Error: Tool 'fake' not found" in saved_session.messages[-2]["content"]

@patch("mlx_lm.load")
@patch("mlx_man.native_chat_view.Console")
@patch("mlx_man.native_chat_view.save_session")
@patch("mlx_man.native_chat_view.AVAILABLE_TOOLS")
def test_run_chat_session_agentic_get_time(mock_tools, mock_save, mock_console_cls, mock_load):
    from mlx_man.native_chat_view import run_chat_session
    mock_console = MagicMock()
    mock_console_cls.return_value = mock_console
    mock_console.input.side_effect = ["hi", "y", "quit"]
    
    mock_mlx = MagicMock()
    mock_mlx.load.return_value = (MagicMock(), MagicMock())
    
    call_count = [0]
    def mock_stream_stateful(*args, **kwargs):
        if call_count[0] == 0:
            call_count[0] += 1
            yield MockResponseObj('<tool_call>{"name": "get_time", "arguments": {}}</tool_call>')
        else:
            yield MockResponseObj("Done.")
            
    mock_mlx.stream_generate = mock_stream_stateful
    import sys
    sys.modules["mlx_lm"] = mock_mlx
    
    mock_tools.__contains__.side_effect = lambda x: True
    mock_tool = MagicMock(return_value="the time")
    mock_tools.__getitem__.return_value = mock_tool
    
    run_chat_session("model_id")
    
    mock_tool.assert_called_once_with()
    saved_session = mock_save.call_args[0][0]
    assert "the time" in saved_session.messages[-2]["content"]

