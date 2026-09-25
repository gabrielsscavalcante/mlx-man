import pytest
import os
from unittest.mock import patch
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from mlx_man.tui_engine import build_layout
from mlx_man.cli_dashboard import get_banner, get_shortcuts_line, get_tip_line
from mlx_man.main import MENU_ITEMS
from mlx_man.ram_manager_view import get_header_group, get_process_row
from mlx_man.process_service import ProcessInfo

UPDATE_SNAPSHOTS = os.environ.get("UPDATE_SNAPSHOTS") == "1"

def assert_snapshot(console: Console, base_name: str):
    output_txt = console.export_text()
    
    txt_path = os.path.join(os.path.dirname(__file__), "snapshots", f"{base_name}.txt")
    svg_path = os.path.join(os.path.dirname(__file__), "snapshots", f"{base_name}.svg")
    
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    
    if UPDATE_SNAPSHOTS:
        with open(txt_path, "w") as f:
            f.write(output_txt)
        console.save_svg(svg_path, title=base_name)
        return
        
    if not os.path.exists(txt_path):
        pytest.fail(f"Snapshot file not found: {txt_path}. Run with UPDATE_SNAPSHOTS=1 to create it.")
        
    with open(txt_path, "r") as f:
        expected = f.read()
        
    assert output_txt == expected, f"Snapshot mismatch for {txt_path}"
    
    # Also save the SVG so the CI produces it as an artifact, but don't strictly assert SVG bytes
    console.save_svg(svg_path, title=base_name)

@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32.0)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_main_menu_snapshot(m1, m2, m3, m4):
    from mlx_man.cli_dashboard import get_system_status_footer
    
    console = Console(width=100, height=30, record=True, force_terminal=True)
    
    below_panel = Group(
        get_shortcuts_line(),
        "\n",
        get_tip_line(),
    )
    
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
                t = Text(f" ▸ {label}")
                t.pad_right(inner_width)
                t.stylize("bold black on white")
                menu_lines.append(t)
            else:
                menu_lines.append(Text(f"   {label}", style="dim white"))
                
    panel = Panel(
        Group(*menu_lines),
        width=inner_width + 4,
    )
    
    body = Group(get_banner(), Text(""), panel, Text(""), below_panel)
    layout = build_layout(body, get_system_status_footer(), 100, 30)
    
    console.print(layout)
    assert_snapshot(console, "main_menu")

@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=8.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32.0)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_ram_manager_snapshot(m1, m2, m3, m4):
    from mlx_man.cli_dashboard import get_system_status_footer
    console = Console(width=120, height=30, record=True, force_terminal=True)
    
    mem_info = {"used_gb": 24.0, "total_gb": 32.0, "wired_gb": 4.0}
    reclaimable_mb = 2048.0
    header_panel = get_header_group(mem_info, reclaimable_mb)
    
    processes = [
        ProcessInfo(1001, "Safari", 1024, "Safe", "Web browser"),
        ProcessInfo(1002, "kernel_task", 500, "Danger", "Critical"),
        ProcessInfo(1003, "Spotlight", 200, "Caution", "Index"),
    ]
    
    columns = [
        {"header": "PID", "style": "dim", "width": 8},
        {"header": "Process Name", "style": "bold white", "min_width": 20},
        {"header": "RAM Usage", "style": "white", "justify": "right", "width": 12},
        {"header": "Risk Level", "width": 12},
        {"header": "Description / Impact", "style": "dim"}
    ]
    
    table = Table(
        title="Running Processes",
        title_style="bold white",
        title_justify="left",
        box=None,
        header_style="dim white",
        expand=True,
        padding=(0, 2)
    )
    for col in columns:
        table.add_column(
            col["header"],
            style=col.get("style", ""),
            justify=col.get("justify", "left"),
            width=col.get("width", None),
            min_width=col.get("min_width", None)
        )
        
    for i, item in enumerate(processes):
        row = get_process_row(item)
        if i == 0:
            styled_row = []
            for cell in row:
                if isinstance(cell, str):
                    t = Text(cell)
                    t.stylize("bold black on white")
                    styled_row.append(t)
                elif isinstance(cell, Text):
                    cell.style = "bold black on white"
                    styled_row.append(cell)
            table.add_row(*styled_row, style="bold black on white")
        else:
            table.add_row(*row)
            
    from rich import box
    panel = Panel(table, box=box.ROUNDED, border_style="bright_black", width=100, padding=(1,1))
    body = Group(header_panel, Text(""), panel)
    layout = build_layout(body, get_system_status_footer(), 120, 30)
    
    console.print(layout)
    assert_snapshot(console, "ram_manager")

