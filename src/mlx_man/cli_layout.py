"""
cli_layout.py — Spotlight-style centered layout engine.

Renders the UI centered both horizontally and vertically in the terminal,
creating a floating macOS-native aesthetic (like Spotlight or Raycast).

Uses raw ANSI escape sequences for cursor positioning combined with
Rich's Align for horizontal centering to achieve pixel-perfect placement.
"""

import os
import sys
import shutil
import subprocess

from rich.console import Console, RenderableType
from rich.align import Align
from rich.text import Text


def get_real_terminal_size():
    """Robustly gets terminal size using tput to bypass pseudo-terminal bugs."""
    try:
        # Ask the OS directly via tput (bypasses Python's fd limitations)
        cols = int(subprocess.check_output(
            ['tput', 'cols'], stderr=subprocess.DEVNULL
        ).decode().strip())
        rows = int(subprocess.check_output(
            ['tput', 'lines'], stderr=subprocess.DEVNULL
        ).decode().strip())
        if cols > 0 and rows > 0:
            return shutil.os.terminal_size((cols, rows))
    except Exception:
        pass

    for stream in (sys.stdout, sys.stderr, sys.stdin):
        try:
            fd = stream.fileno()
            sz = os.get_terminal_size(fd)
            if sz.columns > 0 and sz.lines > 0:
                return sz
        except Exception:
            pass

    # Fallback
    return shutil.get_terminal_size((80, 24))


def get_project_path() -> str:
    """Returns the current working directory formatted like '~/Documents/...'"""
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    if cwd.startswith(home):
        return cwd.replace(home, "~", 1)
    return cwd


def get_renderable_height(console: Console, renderable: RenderableType) -> int:
    """Accurately measure the height of a Rich renderable in lines."""
    with console.capture() as capture:
        console.print(renderable)
    return len(capture.get().splitlines())


def draw_footer(status_text: str, version: str = "v0.3.0"):
    """
    Draws a discreet, persistent footer at the absolute bottom of the terminal.

    Left side:  project path (muted)
    Right side: compact system status + version
    """
    size = get_real_terminal_size()
    cols, rows = size.columns, size.lines

    left_text = get_project_path()

    # Muted gray ANSI color
    color_start = "\033[38;5;242m"
    color_end = "\033[0m"

    # Build right side: system status · version
    right_text = f"{status_text}  ·  {version}"

    # Truncate left text if terminal is too small
    max_left = cols - len(right_text) - 4
    if max_left > 0 and len(left_text) > max_left:
        left_text = left_text[:max_left - 3] + "..."
    elif max_left <= 0:
        left_text = ""

    # Build the footer line with space-padding between left and right
    padding = max(0, cols - len(left_text) - len(right_text) - 1)
    footer = f"{left_text}{' ' * padding}{right_text}"

    # Position at the absolute bottom row, print, then reset cursor to top
    sys.__stdout__.write(f"\033[{rows};1H")
    sys.__stdout__.write(f"{color_start}{footer}{color_end}")
    sys.__stdout__.write("\033[1;1H")
    sys.__stdout__.flush()


def render_centered_view(
    content_block: RenderableType,
    footer_status: str = "",
    prompt_lines: int = 8,
):
    """
    The main Spotlight-effect renderer.

    Clears the terminal, draws the footer, and positions the content block
    precisely at the vertical and horizontal center of the terminal.

    Args:
        content_block: The Rich renderable to center (logo + panel + tips).
        footer_status: Compact system status text for the bottom footer.
        prompt_lines: Estimated lines the questionary prompt will consume
                      below the rendered content (used for vertical calc).
    """
    # 1. Clear screen and reset cursor
    sys.__stdout__.write("\033[2J\033[1;1H")
    sys.__stdout__.flush()

    # 2. Draw sticky footer
    draw_footer(footer_status)

    # 3. Get terminal dimensions
    size = get_real_terminal_size()
    cols, rows = size.columns, size.lines

    # 4. Create a console with explicit dimensions for accurate measurement
    render_console = Console(width=cols, height=rows)

    # 5. Measure content height
    content_height = get_renderable_height(render_console, content_block)

    # 6. Calculate vertical padding for true center
    #    Account for: content + prompt lines below + 1 footer line
    total_used = content_height + prompt_lines + 1
    available = rows - total_used
    top_padding = max(0, available // 2)

    # 7. Apply vertical padding
    sys.__stdout__.write("\n" * top_padding)
    sys.__stdout__.flush()

    # 8. Render the content block, centered horizontally
    render_console.print(Align.center(content_block))


# Legacy compatibility alias
def render_page(renderable: RenderableType, top_padding: int = -1):
    """
    Legacy wrapper for backward compatibility with existing code.
    Renders centered content with the old interface signature.
    """
    from mlx_man.cli_dashboard import get_system_status_footer
    render_centered_view(
        content_block=renderable,
        footer_status=get_system_status_footer(),
    )
