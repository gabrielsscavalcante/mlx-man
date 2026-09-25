"""
ui_components.py — Reusable UI components for MLX-Man.

This module provides standardized Rich components (Panels, Tables) to ensure
a unified, muted "Spotlight-style" aesthetic across the entire application.
"""

from typing import Iterable, Optional

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import RenderableType
from rich.align import Align


def create_header_panel(content: RenderableType, title: Optional[str] = None, expand: bool = False) -> Panel:
    """
    Creates a standard rounded panel used for headers and primary info blocks.
    Uses the muted bright_black aesthetic.
    """
    return Panel(
        content,
        title=f"[bold white]{title}[/]" if title else None,
        box=box.ROUNDED,
        border_style="bright_black",
        expand=expand,
        padding=(1, 4)
    )


def create_data_table(title: Optional[str] = None, columns: Iterable[dict] = ()) -> Table:
    """
    Creates a standard table with no outer box, suitable for data lists.
    
    Args:
        title: Optional table title.
        columns: Iterable of dicts defining columns, e.g.,
                 [{"header": "Name", "style": "bold white", "justify": "left"}, ...]
    """
    table_title = f"[bold white]{title}[/]" if title else None
    table = Table(
        title=table_title,
        box=None,
        padding=(0, 2),
        expand=False,
        show_header=True,
        header_style="dim white"
    )
    
    for col in columns:
        table.add_column(
            col.get("header", ""),
            style=col.get("style", ""),
            justify=col.get("justify", "left"),
            width=col.get("width", None),
            min_width=col.get("min_width", None)
        )
        
    return table


def create_warning_panel(content: RenderableType, title: str = "Warning") -> Panel:
    """
    Creates a standardized warning panel for dangerous actions.
    Uses yellow or red accents depending on the severity, but keeps the
    overall structure consistent.
    """
    return Panel(
        content,
        title=f"[bold yellow]⚠️ {title}[/]",
        box=box.ROUNDED,
        border_style="yellow",
        expand=False,
        padding=(1, 4)
    )
