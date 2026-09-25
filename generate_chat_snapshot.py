from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from mlx_man.ui_components import create_header_panel
from mlx_man.cli_dashboard import get_system_status_footer

console = Console(record=True, width=100)

table = Table(
    box=box.SIMPLE,
    show_header=True,
    header_style="bold magenta",
    expand=True,
    border_style="bright_black",
    padding=(0, 1),
)

table.add_column("Date", style="bold white")
table.add_column("Model", style="cyan")
table.add_column("Msgs", justify="right", style="dim")
table.add_column("Excerpt", style="dim")

table.add_row("2024-01-02 15:30", "Llama-3.1-8B-Instruct", "8", "Write a fast inverse square root func...")
table.add_row("2024-01-01 12:00", "Qwen2.5-7B-Instruct", "2", "How do I reverse a string in python?... ")

header = create_header_panel(Text("2 Past Sessions", style="green"), "Chat History")

table_panel = Panel(
    table,
    title="Select a chat:",
    title_align="left",
    box=box.ROUNDED,
    border_style="bright_black",
    padding=(1, 2)
)

footer_panel = Panel(
    Text("[↑↓] navigate  [enter] view/resume  [e] export  [d] delete  [esc/q] back", justify="left"),
    box=box.ROUNDED,
    border_style="bright_black"
)

console.print(header)
console.print(table_panel)
console.print(footer_panel)
console.save_svg("/Users/gabrielcavalcante/.gemini/antigravity/brain/00fad3be-7805-4371-9e06-0ff0d1b2d3a5/snapshots/chat_history.svg", title="Chat History")
