"""
tui_engine.py — Centralized TUI Engine using rich.live.Live
Replaces blocking input libraries (like questionary) with native state machines.
"""

import sys
import termios
import tty
from typing import List, Optional, Any, Callable, Tuple, Dict

from rich.console import Group, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box

def _read_key() -> str:
    """Reads a single keypress from stdin in raw mode."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1).encode('utf-8')
        
        if ch == b'\x1b':
            ch2 = sys.stdin.read(1)
            ch3 = sys.stdin.read(1)
            if ch2 == '[':
                if ch3 == 'A': return 'up'
                if ch3 == 'B': return 'down'
                if ch3 == 'C': return 'right'
                if ch3 == 'D': return 'left'
            return 'escape'
            
        if ch in (b'\r', b'\n'):
            return 'enter'
        if ch == b'\x03':
            raise KeyboardInterrupt
        if ch in (b'\x7f', b'\b'):
            return 'backspace'

        return ch.decode('utf-8', errors='replace')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def build_layout(content: RenderableType, footer: str, width: int, height: int) -> Layout:
    if width < 40 or height < 12:
        return Layout(Align.center(Text("Terminal too small", style="red"), vertical="middle"))
        
    layout = Layout()
    layout.split_column(
        Layout(name="body"),
        Layout(name="footer", size=2)
    )
    layout["body"].update(Align.center(content, vertical="middle"))
    layout["footer"].update(Align(Text(f" {footer}", style="dim white", justify="right"), vertical="bottom"))
    return layout

def tui_select(
    title: str,
    choices: List[Any],  # can be list of strings, or list of objects
    format_func: Callable[[Any], str],
    header: RenderableType,
    footer: str,
    width: int = 60
) -> Optional[Any]:
    """State machine for UP/DOWN selection."""
    idx = 0
    
    with Live(screen=True, refresh_per_second=10) as live:
        while True:
            # Render
            menu_lines = []
            inner_width = width - 6
            
            menu_lines.append(Text(title, style="bold white"))
            menu_lines.append(Text(""))
            
            for i, choice in enumerate(choices):
                label = format_func(choice)
                if i == idx:
                    t = Text(f" {label}"); t.pad_right(inner_width); menu_lines.append(t); t.stylize("bold black on white")

                else:
                    menu_lines.append(Text(f" {label}", style="dim white"))
                    
            panel = Panel(
                Group(*menu_lines),
                box=box.ROUNDED,
                border_style="bright_black",
                width=width,
                padding=(1, 1),
            )
            
            body = Group(header, Text(""), panel)
            live.update(build_layout(body, footer, live.console.width, live.console.height))
            
            key = _read_key()
            if key == 'up':
                idx = (idx - 1) % len(choices)
            elif key == 'down':
                idx = (idx + 1) % len(choices)
            elif key == 'enter':
                return choices[idx]
            elif key in ('escape', 'q'):
                return None

def tui_confirm(
    prompt: str,
    header: RenderableType,
    footer: str,
) -> bool:
    """State machine for Yes/No confirmation."""
    choices = [("Yes", True), ("No", False)]
    idx = 1 # Default to No
    
    with Live(screen=True, refresh_per_second=10) as live:
        while True:
            menu_lines = [Text(prompt, style="bold yellow"), Text("")]
            
            for i, (label, val) in enumerate(choices):
                if i == idx:
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
            live.update(build_layout(body, footer, live.console.width, live.console.height))
            
            key = _read_key()
            if key == 'up':
                idx = (idx - 1) % len(choices)
            elif key == 'down':
                idx = (idx + 1) % len(choices)
            elif key == 'enter':
                return choices[idx][1]
            elif key == 'escape':
                return False

def tui_text_input(
    prompt: str,
    header: RenderableType,
    footer: str,
) -> Optional[str]:
    """State machine for typing text."""
    buf = ""
    
    with Live(screen=True, refresh_per_second=10) as live:
        while True:
            content = Group(
                Text(prompt, style="bold white"),
                Text(""),
                Text(buf + "█", style="white") # fake cursor
            )
            
            panel = Panel(
                content,
                box=box.ROUNDED,
                border_style="bright_black",
                width=60,
                padding=(1, 1),
            )
            
            body = Group(header, Text(""), panel)
            live.update(build_layout(body, footer, live.console.width, live.console.height))
            
            key = _read_key()
            if key == 'enter':
                return buf
            elif key == 'escape':
                return None
            elif key == 'backspace':
                buf = buf[:-1]
            elif len(key) == 1:
                buf += key

def main_menu_select(
    items: List[Any],
    header: RenderableType,
    below_panel: RenderableType,
    footer: str,
) -> Optional[str]:
    selectable = [i for i, item in enumerate(items) if item is not None]
    if not selectable: return None
    idx = 0
    
    with Live(screen=True, refresh_per_second=10) as live:
        while True:
            inner_width = 50
            menu_lines = []
            
            for i, item in enumerate(items):
                if item is None:
                    sep = "─" * max(1, inner_width - 2)
                    menu_lines.append(Text(f"  {sep}", style="bright_black"))
                else:
                    label, val = item
                    if i == selectable[idx]:
                        t = Text(f" ▸ {label}"); t.pad_right(inner_width); t.stylize("bold black on white"); menu_lines.append(t)

                    else:
                        menu_lines.append(Text(f"   {label}", style="dim white"))
                        
            panel = Panel(
                Group(*menu_lines),
                box=box.ROUNDED,
                border_style="bright_black",
                width=inner_width + 4,
                padding=(1, 1),
            )
            
            body = Group(header, Text(""), panel, Text(""), below_panel)
            live.update(build_layout(body, footer, live.console.width, live.console.height))
            
            key = _read_key()
            if key == 'up':
                idx = (idx - 1) % len(selectable)
            elif key == 'down':
                idx = (idx + 1) % len(selectable)
            elif key == 'enter':
                return items[selectable[idx]][1]
            elif key in ('escape', 'q'):
                return None

from rich.table import Table

def tui_table_select(
    title: str,
    columns: List[dict],
    data: List[Any],
    row_func: Callable[[Any], List[Any]],
    header: RenderableType,
    footer: str,
    page_size: int = 15,
    extra_hotkeys: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """State machine for UP/DOWN selection inside a paginated Rich Table."""
    if not data:
        return None
        
    idx = 0
    
    with Live(screen=True, refresh_per_second=10) as live:
        while True:
            # Pagination
            start_idx = max(0, idx - page_size // 2)
            end_idx = min(len(data), start_idx + page_size)
            if end_idx - start_idx < page_size:
                start_idx = max(0, end_idx - page_size)
                
            page_data = data[start_idx:end_idx]
            
            table_title = f"{title} (Showing {start_idx+1}-{end_idx} of {len(data)})" if len(data) > page_size else title
            
            table = Table(
                title=table_title,
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
                
            for i, item in enumerate(page_data):
                actual_idx = start_idx + i
                row = row_func(item)
                
                # If selected, wrap each cell in the highlight style
                if actual_idx == idx:
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
            
            panel = Panel(table, box=box.ROUNDED, border_style="bright_black", width=100, padding=(1,1))
            body = Group(header, Text(""), panel)
            live.update(build_layout(body, footer, live.console.width, live.console.height))
            
            key = _read_key()
            if key == 'up':
                idx = (idx - 1) % len(data)
            elif key == 'down':
                idx = (idx + 1) % len(data)
            elif key == 'enter':
                return data[idx]
            elif key in ('escape', 'q'):
                return None
            elif extra_hotkeys and key in extra_hotkeys:
                return extra_hotkeys[key]
