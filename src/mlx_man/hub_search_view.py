import subprocess
import sys
from rich.console import Group, Console
from rich.text import Text
from rich.panel import Panel
from rich import box

from mlx_man.ui_components import create_header_panel, create_warning_panel
from mlx_man.tui_engine import tui_text_input, tui_table_select, tui_confirm
from mlx_man.cli_dashboard import get_banner, get_system_status_footer
from mlx_man.hardware_recommender import get_hardware_recommendation, estimate_ram

def action_search_hub():
    """Interactive flow to search HuggingFace Hub for MLX models."""
    try:
        from huggingface_hub import HfApi
    except ImportError:
        tui_text_input(
            prompt="Press Enter to return...",
            header=create_warning_panel("huggingface_hub is not installed.", "Error"),
            footer=get_system_status_footer()
        )
        return

    api = HfApi()
    
    query = tui_text_input(
        prompt="Enter search query (e.g. 'Llama 3', or empty for Top MLX Models):",
        header=create_header_panel("🔍 Search HuggingFace Hub", "Hub Search"),
        footer=get_system_status_footer()
    )
    
    if query is None: # Escape pressed
        return
        
    loading_text = Text(f"Searching HuggingFace Hub for '{query}'..." if query else "Fetching top MLX models...", style="bold yellow")
    header = create_header_panel(loading_text, "Hub Search")
    
    # We can't really show a loading spinner with blocking IO, so we just let it block.
    # It takes ~1 second.
    try:
        models_gen = api.list_models(search=query if query else None, filter="mlx", sort="downloads", limit=30)
        models = list(models_gen)
    except Exception as e:
        tui_text_input(
            prompt="Press Enter to return...",
            header=create_warning_panel(f"Failed to fetch from Hub: {e}", "Error"),
            footer=get_system_status_footer()
        )
        return

    if not models:
        tui_text_input(
            prompt="Press Enter to return...",
            header=create_warning_panel(f"No MLX models found for '{query}'.", "No Results"),
            footer=get_system_status_footer()
        )
        return
        
    columns = [
        {"header": "Model ID", "style": "bold white"},
        {"header": "Downloads", "justify": "right", "style": "dim"},
        {"header": "RAM Needed", "justify": "right"},
        {"header": "Hardware Match", "justify": "center"},
    ]
    
    def format_row(m):
        badge, style = get_hardware_recommendation(m.id)
        ram_val = estimate_ram(m.id)
        ram_str = f"~{ram_val:.1f} GB" if ram_val > 0 else "Unknown"
        
        return [
            m.id,
            f"{m.downloads:,}",
            ram_str,
            Text(badge, style=style)
        ]

    while True:
        header = create_header_panel(Text(f"Found {len(models)} matching MLX models.", style="green"), "Hub Search Results")
        
        choice = tui_table_select(
            title=f"Hub Search Results",
            columns=columns,
            data=models,
            row_func=format_row,
            header=header,
            footer=get_system_status_footer()
        )
        
        if not choice:
            break
            
        badge, _ = get_hardware_recommendation(choice.id)
        
        confirm = tui_confirm(
            prompt=f"Download {choice.id}?",
            header=create_header_panel(f"Hardware Match: {badge}", choice.id),
            footer=get_system_status_footer(),
            default=True
        )
        
        if confirm:
            console = Console(force_terminal=True)
            console.clear()
            print(f"\n🚀 Launching downloader for {choice.id}...\n")
            
            downloader_path = __file__.replace("hub_search_view.py", "model_downloader.py")
            subprocess.run([sys.executable, downloader_path, choice.id])
            
            tui_text_input(
                prompt="Press Enter to continue...",
                header=create_header_panel("Download process completed.", "Download Complete"),
                footer=get_system_status_footer()
            )
            break
