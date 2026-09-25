import re

with open("tests/test_cli_actions.py", "r") as f:
    content = f.read()

# For full_flow_chat
content = re.sub(
    r'(@patch\("mlx_man\.cli_actions\.subprocess\.run"\)\n@patch\("mlx_man\.cli_actions\.tui_select"\)\n@patch\("mlx_man\.cli_actions\.tui_confirm"\)\n@patch\("mlx_man\.model_registry\.get_models_by_role"\)\ndef test_action_run_server_full_flow_chat\(mock_get_models, mock_confirm, mock_select, mock_run, mock_footer, tmp_path\):)',
    r'@patch("mlx_man.cli_actions.run_chat_session")\n\1',
    content
)
content = content.replace(
    'def test_action_run_server_full_flow_chat(mock_get_models, mock_confirm, mock_select, mock_run, mock_footer, tmp_path):',
    'def test_action_run_server_full_flow_chat(mock_chat, mock_get_models, mock_confirm, mock_select, mock_run, mock_footer, tmp_path):'
)

# For keyboard interrupt
content = re.sub(
    r'(@patch\("mlx_man\.cli_actions\.subprocess\.run", side_effect=KeyboardInterrupt\)\n@patch\("mlx_man\.cli_actions\.tui_select"\)\n@patch\("mlx_man\.model_registry\.get_models_by_role"\)\ndef test_action_run_server_keyboard_interrupt_chat\(mock_get, mock_select, mock_run, mock_footer, tmp_path\):)',
    r'@patch("mlx_man.cli_actions.run_chat_session", side_effect=KeyboardInterrupt)\n\1',
    content
)
content = content.replace(
    'def test_action_run_server_keyboard_interrupt_chat(mock_get, mock_select, mock_run, mock_footer, tmp_path):',
    'def test_action_run_server_keyboard_interrupt_chat(mock_chat, mock_get, mock_select, mock_run, mock_footer, tmp_path):'
)

with open("tests/test_cli_actions.py", "w") as f:
    f.write(content)
