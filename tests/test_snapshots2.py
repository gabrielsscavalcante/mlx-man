import pytest
from rich.console import Console, Group
from mlx_man.tui_engine import main_menu_select
from mlx_man.main import MENU_ITEMS
from mlx_man.cli_dashboard import get_banner, get_shortcuts_line, get_tip_line, get_system_status_footer

def test_main_menu_full():
    console = Console(width=100, height=30, record=True, force_terminal=True)
    
    below_panel = Group(
        get_shortcuts_line(),
        "\n",
        get_tip_line(),
    )
    # Patch tui_engine to just render one frame to our console and exit
    import mlx_man.tui_engine
    
    # We will just call build_layout directly to see what the layout looks like
    from mlx_man.tui_engine import build_layout
    from rich.panel import Panel
    from rich.text import Text
    
    inner_width = 50
    menu_lines = []
    selectable = [i for i, item in enumerate(MENU_ITEMS) if item is not None]
    idx = 0
    
    for i, item in enumerate(MENU_ITEMS):
        if item is None:
            sep = "─" * max(1, inner_width - 2)
            menu_lines.append(Text(f"  {sep}", style="bright_black"))
        else:
            label, val = item
            if i == selectable[idx]:
                padded = f" ▸ {label}".ljust(inner_width)
                menu_lines.append(Text(padded, style="bold black on white"))
            else:
                menu_lines.append(Text(f"   {label}", style="dim white"))
                
    panel = Panel(
        Group(*menu_lines),
        width=inner_width + 4,
    )
    
    body = Group(get_banner(), Text(""), panel, Text(""), below_panel)
    layout = build_layout(body, get_system_status_footer(), 100, 30)
    
    console.print(layout)
    with open("tests/snapshot_full.txt", "w") as f:
        f.write(console.export_text())

test_main_menu_full()
