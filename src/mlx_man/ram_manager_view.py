import os
import sys
import time
from rich.console import Console
from rich.console import Group
from rich.align import Align
from rich.text import Text
import questionary

from mlx_man.process_service import ProcessService, ProcessInfo
from mlx_man.ui_components import create_header_panel, create_data_table, create_warning_panel
from mlx_man.cli_layout import render_centered_view
from mlx_man.cli_dashboard import get_system_status_footer

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
    filter_safe_only = False
    while True:
        try:
            mem_info = ProcessService.get_system_memory_info()
            processes = ProcessService.get_processes()
        except Exception as e:
            console.print(f"[red]Error fetching system data: {e}[/red]")
            return

        reclaimable_mb = sum(p.memory_mb for p in processes if p.safety != "Danger")
        
        filtered_processes = [p for p in processes if (p.safety == "Safe" or not filter_safe_only)]
        
        # Build layout
        header_panel = get_header_group(mem_info, reclaimable_mb)
        table = get_process_table(filtered_processes)
        
        layout = Group(
            header_panel,
            Text(""),
            table,
            Text(""),
            Align.center(Text("[dim] [↑/↓] Navigate | [Enter] Select | [Esc/Q] Back to Dashboard[/dim]"))
        )
        
        # Determine choices count for dynamic prompt height
        choices_count = len(filtered_processes) + 2
        
        render_centered_view(
            layout, 
            footer_status=get_system_status_footer(), 
            prompt_lines=min(choices_count + 3, 15)
        )
        
        choices = []
        for p in filtered_processes:
            if p.safety == "Safe":
                risk_tag = "🟢 [SAFE]"
            elif p.safety == "Caution":
                risk_tag = "🟡 [CAUTION]"
            else:
                risk_tag = "🔴 [DANGEROUS]"
                
            display_text = f"{p.name} (PID: {p.pid}, {int(p.memory_mb)} MB) - {risk_tag}"
            choices.append(questionary.Choice(display_text, p))
            
        choices.append(questionary.Choice(f"Toggle Filter (Safe Only: {filter_safe_only})", "filter"))
        choices.append(questionary.Choice("Cancel / Back to Dashboard", "cancel"))
        
        try:
            prompt = questionary.select(
                "Select a process to manage:",
                choices=choices
            )
            
            from prompt_toolkit.keys import Keys
            @prompt.application.key_bindings.add("q", eager=True)
            @prompt.application.key_bindings.add("Q", eager=True)
            @prompt.application.key_bindings.add(Keys.Escape, eager=True)
            def _(event):
                event.app.exit(result="cancel")
                
            selected = prompt.ask()
        except KeyboardInterrupt:
            break
            
        if not selected or selected == "cancel":
            break
            
        if selected == "filter":
            filter_safe_only = not filter_safe_only
            continue
            
        p: ProcessInfo = selected
        
        if p.safety == "Danger" and not expert_mode:
            warning = Text(f"\n🚨 ERROR: '{p.name}' is a Protected macOS process.\nYou cannot terminate this process without the '--expert' override.")
            render_centered_view(create_warning_panel(warning, "Access Denied"), prompt_lines=3)
            questionary.text("Press Enter to continue...").ask()
            continue
            
        if p.safety == "Danger":
            warning = Text(f"\n🚨 DANGER: '{p.name}' is a critical system process.\nTerminating this may cause system instability or crash your session.")
            render_centered_view(create_warning_panel(warning, "Critical Warning"), prompt_lines=3)
            confirm = questionary.confirm("Are you absolutely sure you want to FORCE KILL this process?", default=False).ask()
            if not confirm:
                continue
        elif p.safety == "Caution":
            warning = Text(f"\n🚨 WARNING: '{p.name}' is a macOS background service.\nIt will restart automatically or cause minor UI disruption.")
            render_centered_view(create_warning_panel(warning, "Caution"), prompt_lines=3)
            confirm = questionary.confirm(f"Do you really want to kill '{p.name}'?", default=False).ask()
            if not confirm:
                continue
        else:
            warning = Text(f"\n⚠️ Terminate '{p.name}' (PID: {p.pid}, RAM: {int(p.memory_mb)} MB)?\nRisk Level: SAFE - {p.description}")
            render_centered_view(create_warning_panel(warning, "Confirm Action"), prompt_lines=3)
            confirm = questionary.confirm("Are you sure you want to stop this process?", default=False).ask()
            if not confirm:
                continue
                
        # We need a small layout to show the result
        result_text = Text(f"Terminating {p.name}...\n")
        render_centered_view(create_header_panel(result_text, "Executing..."), prompt_lines=0)
        success = ProcessService.terminate_process(p.pid)
        if success:
            result_text.append(f"✔ Successfully terminated {p.name}.", style="green")
        else:
            result_text.append(f"✖ Failed to terminate {p.name}.", style="red")
            
        render_centered_view(create_header_panel(result_text, "Execution Result"), prompt_lines=0)
        time.sleep(1.5)

if __name__ == "__main__":
    expert = "--expert" in sys.argv
    run_ram_manager(expert_mode=expert)
