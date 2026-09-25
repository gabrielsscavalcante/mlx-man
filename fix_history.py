with open('src/mlx_man/chat_history_view.py', 'r') as f:
    content = f.read()

content = content.replace(
    'default_path = str(Path.home() / "Documents" / f"mlx_chat_{choice.session_id}.md if fmt == "markdown" else "json"")',
    'default_path = str(Path.home() / "Documents" / f"mlx_chat_{choice.session_id}.{\'md\' if fmt == \'markdown\' else \'json\'}")'
)

with open('src/mlx_man/chat_history_view.py', 'w') as f:
    f.write(content)
