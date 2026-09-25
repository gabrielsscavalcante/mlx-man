import re

with open('tests/test_hub_search.py', 'r') as f:
    content = f.read()

content = content.replace('@patch("mlx_man.hub_search_view.tui_table_select")', '@patch("mlx_man.hub_search_view.tui_table_select", return_value=None)')

with open('tests/test_hub_search.py', 'w') as f:
    f.write(content)
