import pytest
import os
from unittest.mock import patch
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from mlx_man.tui_engine import build_layout
from mlx_man.cli_dashboard import get_banner, get_tip_line
from mlx_man.main import MENU_ITEMS
from mlx_man.ram_manager_view import get_header_group, get_process_row
from mlx_man.process_service import ProcessInfo

UPDATE_SNAPSHOTS = os.environ.get("UPDATE_SNAPSHOTS") == "1"

def assert_snapshot(console: Console, base_name: str):
    output_txt = console.export_text(clear=False)
    
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

@patch('mlx_man.cli_dashboard.random.choice', return_value="Connect external coding tools or agents to MLX-Man's local server on port 8080")
@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_main_menu_snapshot(m1, m2, m3, m4, m5):
    from mlx_man.cli_dashboard import get_system_status_footer
    
    console = Console(width=100, height=30, record=True, force_terminal=True)
    
    below_panel = Group(
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
    layout = build_layout(body, get_system_status_footer(), 100, 30, shortcuts={"↑↓": "navigate", "enter": "select", "esc/q": "quit"})
    
    console.print(layout)
    assert_snapshot(console, "main_menu")

@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=8.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
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
    layout = build_layout(body, get_system_status_footer(), 120, 30, shortcuts={"↑↓": "navigate", "enter": "select", "esc/q": "back"})
    
    console.print(layout)
    assert_snapshot(console, "ram_manager")


@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
@patch('mlx_man.model_inspector.get_total_ram_gb', return_value=32)
@patch('mlx_man.model_inspector.get_current_gpu_limit', return_value="24 GB")
def test_model_inspector_snapshot(m1, m2, m3, m4, m5, m6):
    from mlx_man.cli_dashboard import get_system_status_footer
    from mlx_man.model_inspector import render_model_manager, ModelMetadata
    console = Console(width=120, height=35, record=True, force_terminal=True)
    
    models = [
        ModelMetadata(
            name="QwQ 32B",
            repo_id="mlx-community/QwQ-32B-4bit",
            disk_gb=18.0,
            ram_estimate_gb=19.0,
            tier="Heavy",
            role="Reasoning",
            quant_details="4-bit",
            best_for="Reasoning",
            raw_info={}
        ),
        ModelMetadata(
            name="Devstral Small 24B",
            repo_id="mlx-community/Devstral-Small-2507-4bit",
            disk_gb=14.0,
            ram_estimate_gb=15.0,
            tier="Medium",
            role="Builder",
            quant_details="4-bit",
            best_for="Coding",
            raw_info={}
        ),
        ModelMetadata(
            name="Qwen 3.6 27B",
            repo_id="mlx-community/Qwen3.6-27B-4bit",
            disk_gb=14.0,
            ram_estimate_gb=15.0,
            tier="Medium",
            role="General",
            quant_details="4-bit",
            best_for="General usage",
            raw_info={}
        )
    ]
    
    header_view = render_model_manager(models, "All")
    
    columns = [
        {"header": "Model Name", "style": "bold white"},
        {"header": "Role", "justify": "center"},
        {"header": "Cost", "justify": "right"},
        {"header": "Tier", "justify": "center"},
        {"header": "Best For", "style": "dim"}
    ]
    
    table = Table(
        title="Installed Models (All)",
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
        
    for i, m in enumerate(models):
        quant_pill = Text(m.quant_details, style="dim")
        name_cell = Text(m.name + "\\n").append(quant_pill)
        
        role_icon = {"Reasoning": "🧠", "Builder": "⚒️", "General": "⚡"}.get(m.role, "📦")
        role_cell = f"{role_icon} {m.role}"
        
        cost_cell = Text(f"Disk: {m.disk_gb:.1f} GB\\n").append(f"RAM: ~{m.ram_estimate_gb:.1f} GB", style="dim")
        
        tier_color = {"Light": "green", "Medium": "yellow", "Heavy": "red", "Very Heavy": "magenta"}.get(m.tier, "white")
        tier_badge = Text(f" {m.tier} ", style=f"{tier_color} reverse")
        
        row = [name_cell, role_cell, cost_cell, tier_badge, m.best_for]
        
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
                else:
                    styled_row.append(cell)
            table.add_row(*styled_row, style="bold black on white")
        else:
            table.add_row(*row)
            
    from rich import box
    panel = Panel(table, box=box.ROUNDED, border_style="bright_black", width=100, padding=(1,1))
    body = Group(header_view, Text(""), panel)
    
    footer_text = get_system_status_footer()
    layout = build_layout(body, footer_text, 120, 35, shortcuts={"↑↓": "navigate", "enter": "select", "esc/q": "back", "d": "download", "f": "filter"})
    
    console.print(layout)
    assert_snapshot(console, "model_inspector")

@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_insights_snapshot(m1, m2, m3, m4):
    from mlx_man.cli_dashboard import get_system_status_footer
    from mlx_man.insights_view import get_insights_view, ModelInfo, get_category_color
    import datetime
    console = Console(width=120, height=45, record=True, force_terminal=True)
    
    models = [
        ModelInfo(
            name="QwQ 32B",
            repo_id="test/QwQ",
            size_gb=18.0,
            times_used=42,
            last_used=datetime.datetime(2026, 9, 25, 14, 30),
            category="Reasoning"
        ),
        ModelInfo(
            name="Devstral Small",
            repo_id="test/Devstral",
            size_gb=14.0,
            times_used=120,
            last_used=datetime.datetime(2026, 9, 24, 10, 00),
            category="Build"
        ),
        ModelInfo(
            name="Qwen 3.6",
            repo_id="test/Qwen",
            size_gb=14.0,
            times_used=5,
            last_used=datetime.datetime(2026, 9, 20, 8, 15),
            category="General"
        )
    ]
    
    header_view = get_insights_view(models, "All")
    
    columns = [
        {"header": "Model Name", "style": "bold white"},
        {"header": "Category", "justify": "center"},
        {"header": "Size", "justify": "right", "style": "dim"},
        {"header": "Uses", "justify": "right"},
        {"header": "Last Used", "style": "dim"},
    ]
    
    table = Table(
        title="Installed Models (All)",
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
        
    for i, m in enumerate(models):
        cat_color = get_category_color(m.category)
        cat_badge = Text(f" {m.category} ", style=f"{cat_color} reverse")
        
        uses_style = "bold red" if m.times_used == 0 else "white"
        uses_text = Text(str(m.times_used), style=uses_style)
        
        last_used_str = m.last_used.strftime('%Y-%m-%d %H:%M') if m.last_used else "Never"
        
        row = [m.name, cat_badge, f"{m.size_gb:.1f} GB", uses_text, last_used_str]
        
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
                else:
                    styled_row.append(cell)
            table.add_row(*styled_row, style="bold black on white")
        else:
            table.add_row(*row)
            
    from rich import box
    panel = Panel(table, box=box.ROUNDED, border_style="bright_black", width=100, padding=(1,1))
    body = Group(header_view, Text(""), panel)
    
    footer_text = get_system_status_footer()
    layout = build_layout(body, footer_text, 120, 45, shortcuts={"↑↓": "navigate", "enter": "select", "esc/q": "back", "f": "filter"})
    
    console.print(layout)
    assert_snapshot(console, "insights")

@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_download_model_snapshot(m1, m2, m3, m4):
    from mlx_man.cli_dashboard import get_system_status_footer
    from mlx_man.ui_components import create_header_panel
    from mlx_man.tui_engine import build_layout
    from rich.console import Console, Group
    from rich.text import Text
    from rich.panel import Panel
    from rich import box
    
    console = Console(width=120, height=30, record=True, force_terminal=True)
    
    prompt_text = Text("Enter a HuggingFace model ID (e.g., mlx-community/Qwen3.6-27B-4bit)", style="dim")
    panel_header = create_header_panel(prompt_text, "Download New Model")
    
    buf = "mlx-community/Llama-3-8B-Instruct-4bit"
    content = Group(
        Text("Model ID:", style="bold white"),
        Text(""),
        Text(buf + "█", style="white")
    )
    
    panel = Panel(
        content,
        box=box.ROUNDED,
        border_style="bright_black",
        width=60,
        padding=(1, 1),
    )
    
    body = Group(panel_header, Text(""), panel)
    layout = build_layout(body, get_system_status_footer(), 120, 30, shortcuts={"enter": "submit", "esc": "cancel"})
    
    console.print(layout)
    assert_snapshot(console, "download_model")


@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_model_action_menu_snapshot(m1, m2, m3, m4):
    from mlx_man.cli_dashboard import get_system_status_footer
    from mlx_man.ui_components import create_header_panel
    from mlx_man.tui_engine import build_layout
    from rich.console import Console, Group
    from rich.text import Text
    from rich.panel import Panel
    from rich import box
    
    console = Console(width=120, height=35, record=True, force_terminal=True)
    
    details = Text()
    details.append("Model ID: ", style="bold white")
    details.append("mlx-community/QwQ-32B-4bit\n", style="dim")
    details.append("Disk Size: ", style="bold white")
    details.append("18.0 GB\n", style="dim")
    details.append("RAM Est: ", style="bold white")
    details.append("19.0 GB\n", style="dim")
    details.append("Quant: ", style="bold white")
    details.append("4-bit\n", style="dim")

    header = create_header_panel(details, "QwQ 32B")
    
    choices = [
        ("▶️  Run Model (Chat)", "run"),
        ("🌐 Serve Model (API)", "serve"),
        ("ℹ️  View Detailed Metadata", "meta"),
        ("🗑️  Delete Model", "delete"),
        ("⬅️  Return to Model List", "back")
    ]
    
    menu_lines = []
    for i, (label, val) in enumerate(choices):
        if i == 0:
            t = Text(f" ▸ {label}")
            t.pad_right(40)
            t.stylize("bold black on white")
            menu_lines.append(t)
        else:
            menu_lines.append(Text(f"   {label}", style="dim white"))
            
    panel = Panel(
        Group(*menu_lines),
        box=box.ROUNDED,
        border_style="bright_black",
        width=46,
        padding=(1, 1),
    )
    
    body = Group(header, Text(""), panel)
    layout = build_layout(body, get_system_status_footer(), 120, 35, shortcuts={"↑↓": "navigate", "enter": "select", "esc/q": "back"})
    
    console.print(layout)
    assert_snapshot(console, "model_action_menu")


@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_model_delete_confirm_snapshot(m1, m2, m3, m4):
    from mlx_man.cli_dashboard import get_system_status_footer
    from mlx_man.ui_components import create_header_panel
    from mlx_man.tui_engine import build_layout
    from rich.console import Console, Group
    from rich.text import Text
    from rich.panel import Panel
    from rich import box
    
    console = Console(width=120, height=30, record=True, force_terminal=True)
    
    details = Text()
    details.append("Model ID: ", style="bold white")
    details.append("mlx-community/QwQ-32B-4bit\n", style="dim")
    header = create_header_panel(details, "QwQ 32B")
    
    choices = [("No", False), ("Yes", True)]
    
    menu_lines = [Text("⚠️ Permanently delete QwQ 32B (reclaim 18.0 GB)?", style="bold yellow"), Text("")]
    for i, (label, val) in enumerate(choices):
        if i == 0:
            t = Text(f" {label}"); t.pad_right(40); t.stylize("bold black on white"); menu_lines.append(t)
        else:
            menu_lines.append(Text(f" {label}", style="dim white"))
            
    panel = Panel(
        Group(*menu_lines),
        box=box.ROUNDED,
        border_style="yellow",
        width=46,
        padding=(1, 1),
    )
    
    body = Group(header, Text(""), panel)
    layout = build_layout(body, get_system_status_footer(), 120, 30, shortcuts={"↑↓": "toggle", "enter": "confirm", "esc/q": "cancel"})
    
    console.print(layout)
    assert_snapshot(console, "model_delete_confirm")

@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_sync_models_snapshot(m1, m2, m3, m4):
    from mlx_man.cli_dashboard import get_system_status_footer, get_banner
    from mlx_man.tui_engine import build_layout
    from rich.console import Console, Group
    from rich.text import Text
    from rich.panel import Panel
    from rich import box
    
    console = Console(width=120, height=35, record=True, force_terminal=True)
    
    header = get_banner()
    
    options = [
        ("🔍  Search Hugging Face Cache", "search"),
        ("📁  Add Custom Local Path", "custom"),
        ("↩   Back", "back")
    ]
    
    menu_lines = []
    for i, (label, val) in enumerate(options):
        if i == 0:
            t = Text(f" ▸ {label}")
            t.pad_right(40)
            t.stylize("bold black on white")
            menu_lines.append(t)
        else:
            menu_lines.append(Text(f"   {label}", style="dim white"))
            
    panel = Panel(
        Group(*menu_lines),
        title="Sync Models to MLX-Man & OpenCode",
        box=box.ROUNDED,
        border_style="bright_black",
        width=46,
        padding=(1, 1),
    )
    
    body = Group(header, Text(""), panel)
    layout = build_layout(body, get_system_status_footer(), 120, 35, shortcuts={"↑↓": "navigate", "enter": "select", "esc/q": "back"})
    
    console.print(layout)
    assert_snapshot(console, "sync_models")

@patch('mlx_man.cli_dashboard.get_chip_name', return_value="Apple M-Mock")
@patch('mlx_man.cli_dashboard.get_free_ram_gb', return_value=16.0)
@patch('mlx_man.cli_dashboard.get_total_ram_gb', return_value=32)
@patch('mlx_man.cli_dashboard.get_current_gpu_limit', return_value="24 GB")
def test_search_hub_results_snapshot(m1, m2, m3, m4):
    from mlx_man.cli_dashboard import get_system_status_footer
    from mlx_man.ui_components import create_header_panel
    from mlx_man.tui_engine import build_layout
    from rich.console import Console, Group
    from rich.text import Text
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    
    console = Console(width=120, height=35, record=True, force_terminal=True)
    
    header = create_header_panel(Text("Found 2 matching MLX models.", style="green"), "Hub Search Results")
    
    table = Table(
        title="Hub Search Results",
        title_style="bold white",
        title_justify="left",
        box=None,
        header_style="dim white",
        expand=True,
        padding=(0, 2)
    )
    
    table.add_column("Model ID", style="bold white")
    table.add_column("Downloads", justify="right", style="dim")
    table.add_column("RAM Needed", justify="right")
    table.add_column("Hardware Match", justify="center")
    
    # Selected row
    row1 = [
        Text("mlx-community/Qwen2.5-7B-Instruct-4bit", style="bold black on white"),
        Text("1,234,567", style="bold black on white"),
        Text("~4.2 GB", style="bold black on white"),
        Text("🟢 Great Match", style="bold black on white")
    ]
    table.add_row(*row1, style="bold black on white")
    
    row2 = [
        "mlx-community/QwQ-32B-4bit",
        "500,000",
        "~19.2 GB",
        Text("🟡 Paging Risk", style="bold yellow")
    ]
    table.add_row(*row2)
    
    panel = Panel(table, box=box.ROUNDED, border_style="bright_black", width=110, padding=(1,1))
    body = Group(header, Text(""), panel)
    
    layout = build_layout(body, get_system_status_footer(), 120, 35, shortcuts={"↑↓": "navigate", "enter": "select", "esc/q": "back"})
    
    console.print(layout)
    assert_snapshot(console, "search_hub_results")
