"""
cli_select.py — Fully centered interactive menu selector.

Replaces questionary.select() for screens where the Spotlight/Raycast
centered aesthetic is required.  The ENTIRE screen — logo, floating
panel with highlighted menu items, shortcuts, and tips — is rendered
by Rich on every keypress, keeping everything perfectly centered.

Uses raw terminal mode (tty/termios) for zero-dependency keypress
capture and Rich Console for rendering.
"""

import io
import os
import sys
import tty
import termios
import select as _select
from typing import List, Optional, Tuple

from rich.console import Console, Group, RenderableType
from rich.text import Text
from rich.align import Align
from rich.panel import Panel
from rich import box

from mlx_man.cli_layout import get_real_terminal_size, get_project_path


# Type alias: a menu item is (display_label, return_value), or None for separator
MenuItem = Optional[Tuple[str, str]]


# ─────────────────────────────────────────────────────────────────────────────
# Raw keypress reader
# ─────────────────────────────────────────────────────────────────────────────

def _read_key() -> str:
    """
    Read a single keypress from stdin in raw terminal mode.

    Uses os.read(fd) on the raw file descriptor — NOT sys.stdin.read()
    — so that select.select() on the same fd correctly detects whether
    more bytes of an escape sequence are waiting.  (Python's buffered
    stdin would absorb the burst, making select report "nothing left".)

    Raises KeyboardInterrupt on Ctrl-C so the caller's try/finally
    can restore terminal state.
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)

        if ch == b'\x1b':  # Start of an escape sequence
            # Arrow keys send \x1b [ A/B/C/D as a rapid burst
            if _select.select([fd], [], [], 0.1)[0]:
                ch2 = os.read(fd, 1)
                if ch2 == b'[':
                    if _select.select([fd], [], [], 0.1)[0]:
                        ch3 = os.read(fd, 1)
                        if ch3 == b'A':
                            return 'up'
                        if ch3 == b'B':
                            return 'down'
                    # Drain remaining bytes of unrecognised sequences
                    while _select.select([fd], [], [], 0.01)[0]:
                        os.read(fd, 1)
            return 'escape'

        if ch in (b'\r', b'\n'):
            return 'enter'
        if ch == b'\x03':  # Ctrl-C
            raise KeyboardInterrupt

        return ch.decode('utf-8', errors='replace')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ─────────────────────────────────────────────────────────────────────────────
# Footer builder (returns an ANSI string for single-shot frame writes)
# ─────────────────────────────────────────────────────────────────────────────

def _build_footer_ansi(
    status_text: str,
    cols: int,
    rows: int,
    version: str = "v0.3.0",
) -> str:
    """Return an ANSI escape string that renders the footer at the terminal bottom."""
    left = get_project_path()
    right = f"{status_text}  ·  {version}"

    max_left = cols - len(right) - 4
    if max_left > 0 and len(left) > max_left:
        left = left[: max_left - 3] + "..."
    elif max_left <= 0:
        left = ""

    pad = max(0, cols - len(left) - len(right) - 1)
    footer_line = f"{left}{' ' * pad}{right}"

    gray = "\033[38;5;242m"
    reset = "\033[0m"

    # Move cursor to bottom row → print footer in gray → cursor home
    return f"\033[{rows};1H{gray}{footer_line}{reset}\033[1;1H"


# ─────────────────────────────────────────────────────────────────────────────
# Frame renderer (zero-flicker single-shot write)
# ─────────────────────────────────────────────────────────────────────────────

def _render_frame(content: RenderableType, footer_status: str):
    """
    Render one complete frame to the terminal.

    The Rich output is first captured to an in-memory buffer, then the
    entire frame (clear + footer + vertical-padding + content) is written
    in a single sys.__stdout__.write() call to eliminate flicker.
    """
    size = get_real_terminal_size()
    cols, rows = size.columns, size.lines

    # Render Rich content into a string buffer
    buf = io.StringIO()
    rc = Console(
        file=buf,
        width=cols,
        force_terminal=True,
        color_system="truecolor",
    )
    rc.print(content, end="")

    rendered = buf.getvalue()

    # Measure height from the rendered output
    content_height = rendered.count('\n') + 1

    # Vertical centering (1 line reserved for footer)
    available = rows - content_height - 1
    top_pad = max(0, available // 2)

    # Footer ANSI string
    footer = _build_footer_ansi(footer_status, cols, rows)

    # Write the entire frame in ONE shot → zero flicker
    frame = "\033[2J\033[1;1H"   # clear screen + cursor home
    frame += footer               # footer at bottom (resets cursor to top)
    frame += "\n" * top_pad       # vertical padding
    frame += rendered             # content

    sys.__stdout__.write(frame)
    sys.__stdout__.flush()


# ─────────────────────────────────────────────────────────────────────────────
# The main selector
# ─────────────────────────────────────────────────────────────────────────────

def centered_select(
    items: List[MenuItem],
    header: RenderableType,
    below_panel: RenderableType,
    footer_status: str = "",
    panel_width: int = 56,
) -> Optional[str]:
    """
    Fully centered interactive selector — the Spotlight effect.

    The ENTIRE terminal is rendered by Rich on every keypress: the logo,
    a floating rounded-border panel with highlighted menu items, and the
    shortcuts/tips underneath.  Everything is centered both vertically
    and horizontally.

    Args:
        items:         List of (label, value) tuples; ``None`` = separator.
        header:        Rich renderable above the panel (logo/banner).
        below_panel:   Rich renderable below the panel (shortcuts, tips).
        footer_status: Compact system status for the bottom-right footer.
        panel_width:   Width of the floating selection panel.

    Returns:
        The ``value`` string of the selected item, or ``None`` on Escape.
    """
    # Cap panel width to terminal
    size = get_real_terminal_size()
    panel_width = min(panel_width, size.columns - 4)

    # Indices of selectable (non-separator) items
    selectable = [i for i, item in enumerate(items) if item is not None]
    if not selectable:
        return None

    idx = 0  # pointer into `selectable`

    # Hide cursor for a clean look
    sys.__stdout__.write("\033[?25l")
    sys.__stdout__.flush()

    try:
        while True:
            current = selectable[idx]
            inner_width = panel_width - 6  # 2 border + 2×2 padding

            # ── Build menu lines ──────────────────────────────────────
            menu_lines: list = []
            for i, item in enumerate(items):
                if item is None:
                    sep = "─" * max(1, inner_width - 2)
                    menu_lines.append(
                        Text(f"  {sep}", style="bright_black")
                    )
                else:
                    label, _ = item
                    if i == current:
                        # Highlighted: solid background bar across full width
                        padded = f" ▸ {label}".ljust(inner_width)
                        menu_lines.append(
                            Text(padded, style="bold white on #3e4452")
                        )
                    else:
                        menu_lines.append(
                            Text(f"   {label}", style="dim white")
                        )

            # ── Floating panel ────────────────────────────────────────
            panel = Panel(
                Group(*menu_lines),
                box=box.ROUNDED,
                border_style="bright_black",
                width=panel_width,
                padding=(1, 1),
            )

            # ── Assemble full screen content ──────────────────────────
            full_content = Group(
                header,
                Text(""),
                Align.center(panel),
                Text(""),
                below_panel,
            )

            # ── Render ────────────────────────────────────────────────
            _render_frame(full_content, footer_status)

            # ── Read keypress ─────────────────────────────────────────
            key = _read_key()

            if key == 'up':
                idx = (idx - 1) % len(selectable)
            elif key == 'down':
                idx = (idx + 1) % len(selectable)
            elif key == 'enter':
                return items[selectable[idx]][1]
            elif key in ('escape', 'q'):
                return None
            # All other keys are silently ignored

    finally:
        # Always restore cursor visibility
        sys.__stdout__.write("\033[?25h")
        sys.__stdout__.flush()
