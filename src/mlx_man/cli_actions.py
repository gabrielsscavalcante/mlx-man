"""
cli_actions.py — Core action handlers for the main menu.
Routes to the server launcher, memory cleaner, model inspector, and insights.
"""

import os
import sys
import subprocess
from pathlib import Path
from rich.console import Group, Console
from rich.text import Text

from mlx_man.ui_components import create_header_panel, create_data_table, create_warning_panel
from mlx_man.tui_engine import tui_select, tui_confirm

console = Console()

def run_memory_cleaner():
    try:
        from mlx_man.ram_manager_view import run_ram_manager
        run_ram_manager()
    except KeyboardInterrupt:
        pass

def run_model_inspector():
    try:
        from mlx_man.model_inspector import run_model_inspector as _run
        _run()
    except KeyboardInterrupt:
        pass

def run_insights_history():
    from mlx_man.insights_view import run_insights_history as _run
    _run()

def action_run_server():
    """Interactive flow: GPU limit → Role → Model → Server/Chat."""
    from mlx_man.cli_dashboard import get_system_status_footer
    footer = get_system_status_footer()

    # 1. GPU Memory Limit
    gpu_header = create_header_panel(
        Group(
            Text("By default, macOS limits GPU memory to ~21 GB on a 32 GB Mac.", style="dim white"),
            Text("Large models (32B 4-bit) need more headroom.", style="dim white"),
            Text("⚠ This will prompt for your Mac password (sudo).", style="yellow"),
        ),
        "GPU Memory Limit (Optional)"
    )

    gpu_choices = [
        ("26624", "26 GB (Recommended for 32B and 27B-6bit models)"),
        ("28672", "28 GB (Maximum headroom — for long contexts)"),
        ("skip", "Skip (Keep the current limit)")
    ]

    gpu_choice = tui_select(
        title="Select GPU Limit:",
        choices=gpu_choices,
        format_func=lambda x: x[1],
        header=gpu_header,
        footer=footer
    )

    if not gpu_choice:
        return

    if gpu_choice[0] != "skip":
        subprocess.run(["sudo", "sysctl", f"iogpu.wired_limit_mb={gpu_choice[0]}"])

    # 2. Role Selection
    role_header = create_header_panel(Text("Choose the persona for your AI model.", style="dim white"), "Choose a Role")
    
    role_choices = [
        ("reasoning", "🧠 Reasoning (Plan, analyze, design)"),
        ("builder", "🔨 Builder (Implement, refactor, write code)"),
        ("general", "⚡ General Purpose (A bit of everything)"),
        ("cancel", "Cancel")
    ]

    role_choice = tui_select(
        title="What do you want to do right now?",
        choices=role_choices,
        format_func=lambda x: x[1],
        header=role_header,
        footer=footer
    )

    if not role_choice or role_choice[0] == "cancel":
        return

    from mlx_man.model_registry import get_models_by_role
    HF_CACHE = Path.home() / '.cache' / 'huggingface' / 'hub'
    models = get_models_by_role(role_choice[0])

    if not models:
        tui_confirm(prompt="No models registered for this role. Press Enter to go back.", header=role_header, footer=footer)
        return

    model_choices = []
    for model_id, entry in models.items():
        dir_name = 'models--' + model_id.replace('/', '--')
        installed = (HF_CACHE / dir_name).exists()
        status_tag = "●" if installed else "○"
        ram = entry.get('ram_estimate_gb', '?')
        tier = entry.get('performance_tier', 'Unknown')
        name = entry.get('name', model_id.split('/')[-1])
        short_desc = entry.get('best_for', [''])[0]
        
        display_text = f"{status_tag} {name} (RAM: ~{ram}GB) - {short_desc}"
        model_choices.append((model_id, display_text))
        
    model_choices.append(("cancel", "Cancel"))
    
    model_header = create_header_panel(Text("● = installed    ○ = not downloaded", style="dim white"), "Model Selection")

    model_choice = tui_select(
        title="Select a model to run:",
        choices=model_choices,
        format_func=lambda x: x[1],
        header=model_header,
        footer=footer,
        width=80
    )

    if not model_choice or model_choice[0] == "cancel":
        return

    model_id = model_choice[0]
    entry = models[model_id]

    # Check if installed
    dir_name = 'models--' + model_id.replace('/', '--')
    installed = (HF_CACHE / dir_name).exists()

    if not installed:
        dl_header = create_warning_panel(Text(f"Model '{entry['name']}' is not downloaded yet."), "Download Required")
        dl = tui_confirm("Download it now?", header=dl_header, footer=footer)
        if not dl:
            return

        print(f"\n  ℹ  Downloading: {model_id}")
        from mlx_man.model_downloader import download_model
        success = download_model(model_id)
        if not success:
            return

    # Action Selection
    action_header = create_header_panel(Text(f"Selected: {entry['name']}", style="bold white"), "Action")
    
    action_choices = [
        ("server", "Start API Server (localhost:8080)"),
        ("chat", "Chat in Terminal"),
        ("cancel", "Cancel")
    ]

    action_choice = tui_select(
        title="Select action:",
        choices=action_choices,
        format_func=lambda x: x[1],
        header=action_header,
        footer=footer
    )

    if not action_choice or action_choice[0] == "cancel":
        return

    from mlx_man.usage_tracker import record_usage
    record_usage(model_id)

    if action_choice[0] == "server":
        print(f"\n  ✔  Starting OpenAI-compatible server on http://localhost:8080")
        print("  ℹ  When done, press Ctrl+C to stop.\n")
        from mlx_man.opencode_sync import sync_opencode_config
        sync_opencode_config(model_id)
        try:
            subprocess.run([sys.executable, "-m", "mlx_lm", "server", "--model", model_id])
        except KeyboardInterrupt:
            pass
    elif action_choice[0] == "chat":
        print(f"\n  ✔  Starting interactive terminal chat...")
        print("  ℹ  Type 'quit' or 'exit' to end the session.\n")
        try:
            subprocess.run([sys.executable, "-m", "mlx_lm", "chat", "--model", model_id])
        except KeyboardInterrupt:
            pass
