"""
cli_actions.py — Action handlers for the main menu.

Routes user selections to the appropriate subsystem:
server launcher, memory cleaner, model inspector, and insights.
"""

import os
import sys
import subprocess
import questionary
from rich.console import Console

console = Console()


def run_memory_cleaner():
    """Launch the interactive RAM cleanup view."""
    try:
        from mlx_man.ram_manager_view import run_ram_manager
        run_ram_manager()
    except KeyboardInterrupt:
        pass


def run_model_inspector():
    """Launch the model management and inspection view."""
    try:
        from mlx_man.model_inspector import run_model_inspector as _run
        _run()
    except KeyboardInterrupt:
        pass


def run_insights_history():
    """Launch the usage insights and history dashboard."""
    from mlx_man.insights_view import run_insights_history as _run
    _run()


def action_run_server():
    """Interactive flow: GPU limit → Role → Model → Server/Chat."""
    # 1. GPU Memory Limit
    console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print("[bold cyan]  GPU Memory Limit (Optional)[/]")
    console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n")
    console.print("  [cyan]ℹ[/]  By default, macOS limits GPU memory to ~21 GB on a 32 GB Mac.")
    console.print("  [cyan]ℹ[/]  Large models (32B 4-bit) need more headroom.")
    console.print("  [yellow]⚠  This will prompt for your Mac password (sudo).[/]\n")

    gpu_choice = questionary.select(
        "Select GPU Limit:",
        choices=[
            questionary.Choice("26 GB (Recommended for 32B and 27B-6bit models)", "26624"),
            questionary.Choice("28 GB (Maximum headroom — for long contexts on heavy models)", "28672"),
            questionary.Choice("Skip (Keep the current limit. Fine for 14B models)", "skip")
        ]
    ).ask()

    if not gpu_choice:
        return

    if gpu_choice != "skip":
        console.print(f"  [cyan]ℹ[/]  Requesting sudo to set GPU limit...")
        subprocess.run(["sudo", "sysctl", f"iogpu.wired_limit_mb={gpu_choice}"])
        console.print(f"  [green]✔[/]  GPU limit updated.")

    # 2. Role Selection
    console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print("[bold cyan]  Choose a Role[/]")
    console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n")

    role_choice = questionary.select(
        "What do you want to do right now?",
        choices=[
            questionary.Choice("🧠 Reasoning / Thinking (Plan, analyze, design prompts)", "reasoning"),
            questionary.Choice("🔨 Builder / Coding (Implement, refactor, write code)", "builder"),
            questionary.Choice("⚡ General Purpose (A bit of everything)", "general"),
            questionary.Choice("Cancel", "cancel")
        ]
    ).ask()

    if not role_choice or role_choice == "cancel":
        return

    from mlx_man.model_registry import get_models_by_role
    from pathlib import Path

    HF_CACHE = Path.home() / '.cache' / 'huggingface' / 'hub'
    models = get_models_by_role(role_choice)

    if not models:
        console.print("  [yellow]⚠  No models registered for this role.[/]")
        return

    choices = []
    for model_id, entry in models.items():
        dir_name = 'models--' + model_id.replace('/', '--')
        installed = (HF_CACHE / dir_name).exists()
        status_tag = "●" if installed else "○"
        ram = entry.get('ram_estimate_gb', '?')
        tier = entry.get('performance_tier', 'Unknown')
        name = entry.get('name', model_id.split('/')[-1])
        desc_parts = entry.get('best_for', [])
        short_desc = desc_parts[0] if desc_parts else ''

        display_text = f"{status_tag} {name} (RAM: ~{ram} GB | Tier: {tier}) - {short_desc}"
        choices.append(questionary.Choice(display_text, model_id))

    choices.append(questionary.Choice("Cancel", "cancel"))

    console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print(f"[bold cyan]  Model Selection[/]")
    console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n")
    console.print("  [dim]● = installed    ○ = not downloaded[/]")

    model_choice = questionary.select(
        "Select a model to run:",
        choices=choices
    ).ask()

    if not model_choice or model_choice == "cancel":
        return

    model_id = model_choice
    entry = models[model_id]

    # Check if installed
    dir_name = 'models--' + model_id.replace('/', '--')
    installed = (HF_CACHE / dir_name).exists()

    if not installed:
        console.print(f"\n  [yellow]⚠  Model '{entry['name']}' is not downloaded yet.[/]")
        dl = questionary.confirm("Download it now?").ask()
        if not dl:
            console.print("  [cyan]ℹ[/]  Cancelled.")
            return

        console.print(f"\n  [cyan]ℹ[/]  Downloading: [bold white]{model_id}[/]")
        from mlx_man.model_downloader import download_model
        success = download_model(model_id)
        if not success:
            console.print("  [red]✖  Download failed.[/]")
            return
        console.print("  [green]✔  Model downloaded successfully![/]")

    # Action Selection
    console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    console.print("[bold cyan]  Action[/]")
    console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n")

    action_choice = questionary.select(
        "Select action:",
        choices=[
            questionary.Choice("Start API Server (OpenAI-compatible on localhost:8080)", "server"),
            questionary.Choice("Chat in Terminal (Interactive CLI chat)", "chat"),
            questionary.Choice("Cancel", "cancel")
        ]
    ).ask()

    if not action_choice or action_choice == "cancel":
        return

    # Track usage (direct function call instead of subprocess)
    from mlx_man.usage_tracker import record_usage
    record_usage(model_id)

    # Run Server or Chat
    if action_choice == "server":
        console.print(f"\n  [green]✔[/]  Starting OpenAI-compatible server on [bold]http://localhost:8080[/]")
        console.print("  [cyan]ℹ[/]  💡 When done, press [bold]Ctrl+C[/] to stop.\n")
        from mlx_man.opencode_sync import sync_opencode_config
        sync_opencode_config(model_id)
        try:
            subprocess.run([sys.executable, "-m", "mlx_lm", "server", "--model", model_id])
        except KeyboardInterrupt:
            pass
    elif action_choice == "chat":
        console.print(f"\n  [green]✔[/]  Starting interactive terminal chat...")
        console.print("  [cyan]ℹ[/]  Type [bold]'quit'[/] or [bold]'exit'[/] to end the session.\n")
        try:
            subprocess.run([sys.executable, "-m", "mlx_lm", "chat", "--model", model_id])
        except KeyboardInterrupt:
            pass
