with open("tests/test_cli_actions.py", "r") as f:
    content = f.read()

content = content.replace(
    """
@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_full_flow_chat""",
    """
@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.cli_actions.run_chat_session")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_full_flow_chat"""
)

content = content.replace(
    "def test_action_run_server_full_flow_chat(mock_get, mock_select, mock_run, mock_footer, tmp_path):",
    "def test_action_run_server_full_flow_chat(mock_get, mock_select, mock_chat, mock_run, mock_footer, tmp_path):"
)

content = content.replace(
    'mock_run.assert_called_with([sys.executable, "-m", "mlx_lm", "chat", "--model", "test/mock-model"])',
    'mock_chat.assert_called_with("test/mock-model")'
)

content = content.replace(
    """
@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run", side_effect=KeyboardInterrupt)
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_keyboard_interrupt_chat""",
    """
@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.cli_actions.run_chat_session", side_effect=KeyboardInterrupt)
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_keyboard_interrupt_chat"""
)

content = content.replace(
    "def test_action_run_server_keyboard_interrupt_chat(mock_get, mock_select, mock_run, mock_footer, tmp_path):",
    "def test_action_run_server_keyboard_interrupt_chat(mock_get, mock_select, mock_chat, mock_run, mock_footer, tmp_path):"
)

with open("tests/test_cli_actions.py", "w") as f:
    f.write(content)
