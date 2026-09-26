import os
from collections import deque
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box
from mlx_man.server_manager import LOG_FILE

def tail_logs(n_lines=5):
    """Safely tail the last N lines of the log file."""
    if not LOG_FILE.exists():
        return "[dim]No logs available yet.[/dim]"
    try:
        with open(LOG_FILE, "r") as f:
            lines = deque(f, maxlen=n_lines)
            if not lines:
                return "[dim]Log file is empty.[/dim]"
            return "".join(lines).strip()
    except Exception as e:
        return f"[red]Error reading logs: {e}[/red]"

def _create_server_panel(port, state, is_healthy):
    if is_healthy:
        status = "[bold green]🟢 RUNNING[/bold green]"
        border = "green"
    else:
        status = "[bold red]🔴 STOPPED / CRASHED[/bold red]"
        border = "red"
        
    model = state.get("model_id", "Unknown") if state else "None"
    pid = state.get("pid", "N/A") if state else "N/A"
    
    metadata = f"Status: {status}\nModel: [bold white]{model}[/bold white]\nPort: {port}\nPID: {pid}"
    return Panel(metadata, title=f"Server (Port {port})", border_style=border, box=box.ROUNDED)

def render_server_dashboard(servers: dict):
    """
    Renders the multi-server Dashboard layout.
    """
    from mlx_man.cli_dashboard import get_total_ram_gb, get_free_ram_gb, get_current_gpu_limit
    from mlx_man.server_manager import check_server_health
    
    panels = []
    for port, state in servers.items():
        is_healthy = check_server_health(state)
        panels.append(_create_server_panel(port, state, is_healthy))
        
    if not panels:
        top_panel = _create_server_panel("N/A", None, False)
    elif len(panels) == 1:
        top_panel = panels[0]
    else:
        top_panel = Columns(panels, expand=True)
    
    # Hardware Context Panel
    try:
        total = get_total_ram_gb()
        free = get_free_ram_gb()
        used = total - free
        gpu_limit = get_current_gpu_limit()
    except:
        total = free = used = 0
        gpu_limit = "Unknown"
        
    hardware = f"Total RAM: {total} GB\nUsed RAM:  {used:.1f} GB\nFree RAM:  {free:.1f} GB\nGPU Limit: {gpu_limit}"
    hw_panel = Panel(hardware, title="Combined Hardware Context", border_style="blue", box=box.ROUNDED, width=40)
    
    # Recent Logs Panel
    logs = tail_logs(6)
    logs_panel = Panel(logs, title="Recent Global Logs", border_style="bright_black", box=box.ROUNDED, expand=True)
    
    bottom_row = Columns([hw_panel, logs_panel], expand=True)
    
    return Group(top_panel, bottom_row)
