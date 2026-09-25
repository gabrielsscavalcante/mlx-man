import pytest
from rich.console import Console
from mlx_man.tui_engine import build_layout
from rich.text import Text
from mlx_man.cli_dashboard import get_banner

def test_main_menu_snapshot():
    console = Console(width=100, height=30, record=True, force_terminal=True)
    header = get_banner()
    layout = build_layout(header, "Status Footer", 100, 30)
    console.print(layout)
    output = console.export_text()
    
    with open("tests/snapshot_main.txt", "w") as f:
        f.write(output)
        
    assert "MLX-Man" in output
    assert "Status Footer" in output

