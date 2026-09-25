import os
import sys
import time
from typing import Any
from rich.console import Console, Group
from rich.align import Align
from rich.text import Text

from mlx_man.process_service import ProcessService, ProcessInfo
from mlx_man.ui_components import create_header_panel, create_data_table, create_warning_panel
from mlx_man.cli_dashboard import get_system_status_footer
from mlx_man.tui_engine import tui_select, tui_confirm, tui_text_input

console = Console()

def get_header_group(mem_info: dict, reclaimable_mb: float) -> Group:
    used = f"{mem_info['used_gb']:.1f} GB"
    total = f"{mem_info['total_gb']:.1f} GB"
    wired = f"{mem_info.get('wired_gb', 0):.1f} GB"
    reclaimable = f"{reclaimable_mb / 1024:.1f} GB"
    
    header_text = Text()
    header_text.append(f"Total System RAM: ", style="bold white")
    header_text.append(f"{used} / {total}\n", style="dim")
    header_text.append(f"Memory Pressure / Wired RAM: ", style="bold white")
    header_text.append(f"{wired}\n", style="dim")
    header_text.append(f"Reclaimable Target: ", style="bold white")
    header_text.append(f"~{reclaimable}", style="dim")
    
    return create_header_panel(Align.center(header_text), title="Clean Up RAM")

def get_process_table(processes: list[ProcessInfo]):
    columns = [
        {"header": "PID", "style": "dim", "width": 8},
        {"header": "Process Name", "style": "bold white", "min_width": 20},
        {"header": "RAM Usage", "style": "white", "justify": "right", "width": 12},
        {"header": "Risk Level", "width": 12},
        {"header": "Description / Impact", "style": "dim"}
    ]
    table = create_data_table(title="Running Processes", columns=columns)

    for p in processes:
        if p.safety == "Safe":
            risk = "[green]Safe[/green]"
        elif p.safety == "Caution":
            risk = "[yellow]Caution[/yellow]"
        else:
            risk = "[red]Protected[/red]"
            
        table.add_row(
            str(p.pid),
            p.name,
            f"{int(p.memory_mb)} MB",
            risk,
            p.description
        )
        
    return table

def run_ram_manager(expert_mode: bool = False):
    while True:
        try:
            mem_info = ProcessService.get_system_memory_info()
            processes = ProcessService.get_processes()
        except Exception as e:
            console.print(f"[red]Error fetching system data: {e}[/red]")
            return

        reclaimable_mb = sum(p.memory_mb for p in processes if p.safety != "Danger")
        
        # Build header Group containing the header panel and the process table
        header_panel = get_header_group(mem_info, reclaimable_mb)
        table = get_process_table(processes)
        header = Group(header_panel, Text(""), table)
        
        choices = list(processes) + ["cancel"]
        
        try:
            selected = tui_select(
                title="Select a process to manage:",
                choices=choices,
                format_func=lambda x: "Exit" if x == "cancel" else f"{x.name} ({x.pid})",
                header=header,
                footer=get_system_status_footer(),
            )
        except KeyboardInterrupt:
            break
            
        if not selected or selected == "cancel":
            break
            
        p: ProcessInfo = selected
        
        if p.safety == "Danger" and not expert_mode:
            warning = Text(f"\n🚨 ERROR: '{p.name}' is a Protected macOS process.\nYou cannot terminate this process without the '--expert' override.")
            tui_text_input(
                prompt="Press Enter to continue...",
                header=create_warning_panel(warning, "Access Denied"),
                footer=get_system_status_footer(),
            )
            continue
            
        if p.safety == "Danger":
            warning = Text(f"\n🚨 DANGER: '{p.name}' is a critical system process.\nTerminating this may cause system instability or crash your session.")
            confirm = tui_confirm(
                prompt="Are you absolutely sure you want to FORCE KILL this process?",
                header=create_warning_panel(warning, "Critical Warning"),
                footer=get_system_status_footer(),
            )
            if not confirm:
                continue
        elif p.safety == "Caution":
            warning = Text(f"\n🚨 WARNING: '{p.name}' is a macOS background service.\nIt will restart automatically or cause minor UI disruption.")
            confirm = tui_confirm(
                prompt=f"Do you really want to kill '{p.name}'?",
                header=create_warning_panel(warning, "Caution"),
                footer=get_system_status_footer(),
            )
            if not confirm:
                continue
        else:
            warning = Text(f"\n⚠️ Terminate '{p.name}' (PID: {p.pid}, RAM: {int(p.memory_mb)} MB)?\nRisk Level: SAFE - {p.description}")
            confirm = tui_confirm(
                prompt="Are you sure you want to stop this process?",
                header=create_warning_panel(warning, "Confirm Action"),
                footer=get_system_status_footer(),
            )
            if not confirm:
                continue
                
        success = ProcessService.terminate_process(p.pid)
        result_text = Text()
        if success:
            result_text.append(f"✔ Successfully terminated {p.name}.", style="green")
        else:
            result_text.append(f"✖ Failed to terminate {p.name}.", style="red")
            
        tui_text_input(
            prompt="Press Enter to continue...",
            header=create_header_panel(result_text, "Execution Result"),
            footer=get_system_status_footer(),
        )

if __name__ == "__main__":
    expert = "--expert" in sys.argv
    run_ram_manager(expert_mode=expert)
