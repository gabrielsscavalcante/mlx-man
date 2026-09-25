with open("tests/test_cli_actions.py", "r") as f:
    content = f.read()

content = content.replace('@patch("mlx_man.cli_actions.subprocess.run")\ndef test_action_run_server_full_flow_chat', '@patch("mlx_man.cli_actions.run_chat_session")\ndef test_action_run_server_full_flow_chat')
content = content.replace('@patch("mlx_man.cli_actions.subprocess.run")\ndef test_action_run_server_keyboard_interrupt_chat', '@patch("mlx_man.cli_actions.run_chat_session")\ndef test_action_run_server_keyboard_interrupt_chat')

with open("tests/test_cli_actions.py", "w") as f:
    f.write(content)
