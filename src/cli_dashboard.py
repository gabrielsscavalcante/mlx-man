"""
cli_dashboard.py — Branding, system info, and visual components.

Provides the centered logo, system status (as a compact footer string),
and styled tip/shortcut renderables for the main menu.

Design: macOS Dark Mode aesthetic — muted grays, clean whites, minimal accents.
"""

import platform
import subprocess
import datetime
import random

import psutil
from rich.console import Console, Group
from rich.text import Text
from rich.align import Align
from rich.panel import Panel
from rich import box

console = Console()

CLI_VERSION = "0.3.0"

# ─────────────────────────────────────────────────────────────────────────────
# Sleek ASCII Logo — OpenCode-inspired muted aesthetic
# ─────────────────────────────────────────────────────────────────────────────

LOGO = """\
[bold white]███╗   ███╗ ██╗      ██╗  ██╗           ███╗   ███╗  █████╗  ███╗   ██╗[/bold white]
[white]████╗ ████║ ██║      ╚██╗██╔╝           ████╗ ████║ ██╔══██╗ ████╗  ██║[/white]
[bright_white]██╔████╔██║ ██║       ╚███╔╝   ██████╗  ██╔████╔██║ ███████║ ██╔██╗ ██║[/bright_white]
[white]██║╚██╔╝██║ ██║       ██╔██╗   ╚═════╝  ██║╚██╔╝██║ ██╔══██║ ██║╚██╗██║[/white]
[dim white]██║ ╚═╝ ██║ ███████╗ ██╔╝ ██╗           ██║ ╚═╝ ██║ ██║  ██║ ██║ ╚████║[/dim white]
[dim]╚═╝     ╚═╝ ╚══════╝ ╚═╝  ╚═╝           ╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚═╝  ╚═══╝[/dim]"""


# ─────────────────────────────────────────────────────────────────────────────
# System Info Helpers (domain layer — no rendering)
# ─────────────────────────────────────────────────────────────────────────────

def get_chip_name() -> str:
    """Returns the Apple Silicon chip name (e.g. 'Apple M6')."""
    try:
        return subprocess.check_output(
            ['sysctl', '-n', 'machdep.cpu.brand_string'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
    except Exception:
        return platform.processor() or "Unknown"


def get_total_ram_gb() -> int:
    return round(psutil.virtual_memory().total / (1024 ** 3))


def get_free_ram_gb() -> float:
    return round(psutil.virtual_memory().available / (1024 ** 3), 1)


def get_current_gpu_limit() -> str:
    try:
        limit_mb = int(subprocess.check_output(
            ['sysctl', '-n', 'iogpu.wired_limit_mb'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip())
        return f"{limit_mb // 1024} GB"
    except Exception:
        return "~21 GB"


def get_macos_version() -> str:
    mac_ver = platform.mac_ver()[0]
    return mac_ver if mac_ver else "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Renderable Components (presentation layer — return RenderableType only)
# ─────────────────────────────────────────────────────────────────────────────

def get_banner() -> Align:
    """Returns the centered logo + subtitle + description as a single renderable block."""
    subtitle = Text.from_markup(
        "[bold white]MLX-Man[/bold white] [dim]— Local MLX LLM Manager for Mac[/dim]"
    )
    description = Text.from_markup(
        "[dim]Download & run local AI models on Apple Silicon · Model runner, not an AI agent[/dim]"
    )
    banner_group = Group(
        Text.from_markup(LOGO),
        Align.center(subtitle),
        Align.center(description),
    )
    return Align.center(banner_group)


def get_main_menu_panel() -> Align:
    """
    Returns a Rich Panel styled as the central 'floating window' for the
    main command selection. The actual questionary prompt is rendered BELOW
    this panel in the terminal — this panel provides the visual context.
    """
    content = Text.from_markup(
        "[dim]Select a command below to get started.[/dim]"
    )
    panel = Panel(
        Align.center(content),
        box=box.ROUNDED,
        border_style="bright_black",
        width=60,
        padding=(1, 2),
    )
    return Align.center(panel)


def get_shortcuts_line() -> Align:
    """Returns the OpenCode-style muted keyboard shortcuts line."""
    shortcuts = Text.from_markup(
        "[dim]↑↓[/dim] navigate    "
        "[dim]enter[/dim] select    "
        "[dim]ctrl+c[/dim] quit"
    )
    return Align.center(shortcuts)


# Rotating tips for visual interest
_TIPS = [
    "MLX-Man downloads & runs MLX models locally — standalone runner, not an agent",
    "Connect external coding tools or agents to MLX-Man's local server on port 8080",
    "Use [bold]--print-logs[/bold] flag to see detailed logs in stderr",
    "32B models need [bold]sudo sysctl iogpu.wired_limit_mb=26624[/bold] for best perf",
    "Close heavy apps before running Heavy-tier models to free unified memory",
    "14B models only use ~8 GB — great for multitasking with browsers and IDEs",
    "Use [bold]Clean Up RAM[/bold] to interactively kill memory-heavy processes",
    "The MoE model activates only ~3B params per token — fast despite 35B total",
]


def get_tip_line() -> Align:
    """Returns a centered, softly-colored tip."""
    tip = random.choice(_TIPS)
    tip_text = Text.from_markup(f"[yellow]●[/yellow] [dim]Tip[/dim]  [dim italic]{tip}[/dim italic]")
    return Align.center(tip_text)


def get_system_status_footer() -> str:
    """
    Returns a compact, single-line system status string for the footer.
    Replaces the old prominent System Status table.
    """
    chip = get_chip_name()
    free_ram = get_free_ram_gb()
    total_ram = get_total_ram_gb()
    gpu_limit = get_current_gpu_limit()

    # RAM color indicator
    if free_ram < 8:
        ram_indicator = "🔴"
    elif free_ram < 16:
        ram_indicator = "🟡"
    else:
        ram_indicator = "🟢"

    return (
        f"{chip}  ·  {ram_indicator} {free_ram}/{total_ram} GB RAM  "
        f"·  GPU: {gpu_limit}"
    )


def get_system_dashboard():
    """
    Legacy-compatible function that returns a Table renderable.
    Kept for backward compatibility with tests and other modules that
    import it. The main menu no longer uses this directly.
    """
    from rich.table import Table
    table = Table(
        title="[bold white]System Status[/]",
        show_header=False, box=None, padding=(0, 4)
    )
    table.add_column("Hardware", justify="right", style="dim")
    table.add_column("HW Value", justify="left", style="white bold")
    table.add_column("Software", justify="right", style="dim")
    table.add_column("SW Value", justify="left", style="white bold")

    total_ram = get_total_ram_gb()
    free_ram = get_free_ram_gb()

    # RAM Color logic
    ram_style = "green"
    if free_ram < 8:
        ram_style = "red"
    elif free_ram < 16:
        ram_style = "yellow"

    table.add_row(
        "Chip:", get_chip_name(),
        "macOS:", get_macos_version()
    )
    table.add_row(
        "Total RAM:", f"{total_ram} GB",
        "Date:", datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    )
    table.add_row(
        "Free RAM:", f"[{ram_style}]{free_ram} GB[/]",
        "GPU Limit:", get_current_gpu_limit()
    )

    return table
