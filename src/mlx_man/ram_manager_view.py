import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
import questionary

from mlx_man.process_service import ProcessService, ProcessInfo

console = Console()

def render_header(mem_info: dict, reclaimable_mb: float):
    used = f"{mem_info['used_gb']:.1f} GB"
    total = f"{mem_info['total_gb']:.1f} GB"
    wired = f"{mem_info.get('wired_gb', 0):.1f} GB"
    reclaimable = f"{reclaimable_mb / 1024:.1f} GB"
    
    header_text = (
        f"[bold white]Total System RAM:[/] {used} / {total}\n"
        f"[bold white]Memory Pressure / Wired RAM:[/] {wired}\n"
        f"[bold white]Reclaimable Target:[/] ~{reclaimable}"
    )
    
    panel = Panel(
        Align.center(header_text),
        title="[bold cyan]Clean Up RAM[/]",
        border_style="cyan"
    )
    console.print(panel)

def render_process_table(processes: list[ProcessInfo], console_obj=console):
    table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
    table.add_column("PID", style="dim", width=8)
    table.add_column("Process Name", style="bold white", min_width=20)
    table.add_column("RAM Usage", justify="right", style="cyan", width=12)
    table.add_column("Risk Level", width=12)
    table.add_column("Description / Impact", style="dim")

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
        
    console_obj.print(table)

def run_ram_manager(expert_mode: bool = False):
    filter_safe_only = False
    while True:
        # Clear the visible screen without destroying the scrollback buffer (\x1b[3J)
        console.print("\033[H\033[2J", end="")
        
        try:
            mem_info = ProcessService.get_system_memory_info()
            processes = ProcessService.get_processes()
        except Exception as e:
            console.print(f"[red]Error fetching system data: {e}[/red]")
            return

        reclaimable_mb = sum(p.memory_mb for p in processes if p.safety != "Danger")
        
        render_header(mem_info, reclaimable_mb)
        
        filtered_processes = [p for p in processes if (p.safety == "Safe" or not filter_safe_only)]
        # Show all processes so the user can scroll through them
        render_process_table(filtered_processes)
        
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
        
        console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
        console.print("[dim] [↑/↓] Navigate | [Enter] Select | [Esc/Q] Back to Dashboard[/dim]")
        
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
            console.print(f"\n[red]🚨 ERROR: '{p.name}' is a Protected macOS process.[/red]")
            console.print("You cannot terminate this process without the '--expert' override.")
            questionary.text("Press Enter to continue...").ask()
            continue
            
        if p.safety == "Danger":
            console.print(f"\n[bold red]🚨 DANGER: '{p.name}' is a critical system process.[/bold red]")
            console.print("Terminating this may cause system instability or crash your session.")
            confirm = questionary.confirm("Are you absolutely sure you want to FORCE KILL this process?", default=False).ask()
            if not confirm:
                continue
        elif p.safety == "Caution":
            console.print(f"\n[bold yellow]🚨 WARNING: '{p.name}' is a macOS background service.[/bold yellow]")
            console.print("It will restart automatically or cause minor UI disruption.")
            confirm = questionary.confirm(f"Do you really want to kill '{p.name}'?", default=False).ask()
            if not confirm:
                continue
        else:
            console.print(f"\n[bold green]⚠️ Terminate '{p.name}' (PID: {p.pid}, RAM: {int(p.memory_mb)} MB)?[/bold green]")
            console.print(f"Risk Level: SAFE - {p.description}")
            confirm = questionary.confirm("Are you sure you want to stop this process?", default=False).ask()
            if not confirm:
                continue
                
        console.print(f"[cyan]ℹ[/] Terminating {p.name}...")
        success = ProcessService.terminate_process(p.pid)
        if success:
            console.print(f"[green]✔[/] Successfully terminated {p.name}.")
        else:
            console.print(f"[red]✖[/] Failed to terminate {p.name}.")
            
        import time
        time.sleep(1.5)

if __name__ == "__main__":
    expert = "--expert" in sys.argv
    run_ram_manager(expert_mode=expert)
