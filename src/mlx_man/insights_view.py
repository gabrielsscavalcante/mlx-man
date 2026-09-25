import os
import json
import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from mlx_man.model_registry import get_registry_entry, ROLE_INFO
from mlx_man.model_manager import get_installed_models, delete_model_from_disk
from mlx_man.cli_dashboard import console
from mlx_man.usage_tracker import HISTORY_FILE

console = Console()

DATA_FILE = HISTORY_FILE  # Single source of truth from usage_tracker

@dataclass
class ModelInfo:
    name: str
    repo_id: str
    size_gb: float
    times_used: int
    last_used: Optional[datetime.datetime]
    category: str

def format_bytes_gb(size_bytes: int) -> float:
    return round(size_bytes / (1024 ** 3), 1)

def categorize_model(repo_id: str) -> str:
    """Categorize model based on registry role or heuristics."""
    entry = get_registry_entry(repo_id)
    if entry and "role" in entry:
        role = entry["role"]
        if role == "reasoning":
            return "Reasoning"
        elif role == "builder":
            return "Build"
        elif role == "general":
            return "General"
    
    # Heuristic fallbacks
    repo_lower = repo_id.lower()
    if any(x in repo_lower for x in ["qwq", "r1", "o1", "reasoning"]):
        return "Reasoning"
    if any(x in repo_lower for x in ["coder", "devstral", "build"]):
        return "Build"
    
    return "General"

def get_category_color(category: str) -> str:
    if category == "Reasoning":
        return "magenta"
    elif category == "Build":
        return "blue"
    else:
        return "green"

def load_usage_data() -> Dict[str, Dict]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def gather_models() -> List[ModelInfo]:
    installed = get_installed_models()
    usage_data = load_usage_data()
    
    models = []
    for m in installed:
        repo_id = m["model_id"]
        size_gb = format_bytes_gb(m["disk_bytes"])
        
        # Get name from registry or use repo_id
        entry = get_registry_entry(repo_id)
        name = entry["name"] if entry else repo_id.split("/")[-1]
        
        # Get usage
        usage = usage_data.get(repo_id, {})
        times_used = usage.get("count", 0)
        last_used_str = usage.get("last_used")
        last_used = None
        if last_used_str:
            try:
                last_used = datetime.datetime.fromisoformat(last_used_str)
            except ValueError:
                pass
                
        category = categorize_model(repo_id)
        
        models.append(ModelInfo(
            name=name,
            repo_id=repo_id,
            size_gb=size_gb,
            times_used=times_used,
            last_used=last_used,
            category=category
        ))
        
    return models

from rich.console import Group
from mlx_man.cli_layout import render_page

def generate_bar(value: float, total: float, width: int = 20, color: str = "white") -> str:
    if total <= 0:
        return f"[{color}]" + "░" * width + "[/]"
    ratio = min(value / total, 1.0)
    filled = int(ratio * width)
    return f"[{color}]" + "█" * filled + "░" * (width - filled) + "[/]"

def get_insights_view(models: List[ModelInfo], category_filter: str = "All") -> Group:
    total_size_gb = sum(m.size_gb for m in models)
    total_uses = sum(m.times_used for m in models)
    num_models = len(models)
    
    most_used = None
    if models:
        most_used = max(models, key=lambda m: m.times_used)

    # 1. Summary Bar
    summary_text = Text()
    if most_used and most_used.times_used > 0:
        last_used_str = most_used.last_used.strftime('%Y-%m-%d') if most_used.last_used else "Unknown"
        summary_text.append("🏆 Most Used Model: ", style="bold yellow")
        summary_text.append(f"{most_used.name} ", style="bold white")
        summary_text.append(f"({most_used.times_used} uses, last active {last_used_str})\n", style="dim")
    else:
        summary_text.append("🏆 Most Used Model: ", style="bold yellow")
        summary_text.append("No usage data yet\n", style="dim")
        
    summary_text.append("📊 Total Inferences: ", style="bold magenta")
    summary_text.append(f"{total_uses}\n", style="bold white")
    
    summary_text.append("💾 Total Disk Usage: ", style="bold cyan")
    summary_text.append(f"{total_size_gb:.1f} GB ", style="bold white")
    summary_text.append(f"across {num_models} installed models", style="dim")
    
    panel = Panel(
        summary_text,
        title="[bold cyan]Insights & History[/]",
        border_style="cyan",
        expand=False,
        padding=(1, 4)
    )
    
    components = [panel, Text("")]

    # 2. Category Breakdown Chart
    if models:
        cat_stats = {"Reasoning": {"uses": 0, "size": 0.0}, "Build": {"uses": 0, "size": 0.0}, "General": {"uses": 0, "size": 0.0}}
        for m in models:
            cat = m.category if m.category in cat_stats else "General"
            cat_stats[cat]["uses"] += m.times_used
            cat_stats[cat]["size"] += m.size_gb
        
        breakdown_table = Table(title="[bold white]Usage Distribution by Category[/]", box=None, padding=(0, 2), expand=False)
        breakdown_table.add_column("Category", style="bold")
        breakdown_table.add_column("Usage Chart", justify="left")
        breakdown_table.add_column("Total Uses", justify="right")
        breakdown_table.add_column("Disk Space", justify="right", style="dim")
        
        for cat in ["Reasoning", "Build", "General"]:
            stats = cat_stats[cat]
            color = get_category_color(cat)
            pct = (stats["uses"] / total_uses * 100) if total_uses > 0 else 0
            bar = generate_bar(stats["uses"], total_uses, width=25, color=color)
            
            breakdown_table.add_row(
                f"[{color}]{cat}[/]",
                f"{bar} {pct:4.1f}%",
                f"{stats['uses']} uses",
                f"{stats['size']:.1f} GB"
            )
        components.append(breakdown_table)
        components.append(Text(""))

    # 3. Table of Models
    table = Table(title=f"[bold white]Installed Models[/] [dim]({category_filter})[/]", box=None, padding=(0, 2), expand=False)
    table.add_column("Model Name", style="bold white")
    table.add_column("Category", justify="center")
    table.add_column("Size", justify="right", style="dim")
    table.add_column("Uses", justify="right")
    table.add_column("Last Used", style="dim")

    # Sort models: least used first (0 usage at top) to encourage deletion of unused models
    sorted_models = sorted(models, key=lambda m: (m.times_used, m.last_used or datetime.datetime.min))
    
    displayed_count = 0
    for m in sorted_models:
        if category_filter != "All" and m.category != category_filter:
            continue
            
        cat_color = get_category_color(m.category)
        cat_badge = f"[{cat_color} reverse] {m.category} [/]"
        
        uses_style = "red" if m.times_used == 0 else "white"
        uses_text = f"[{uses_style}]{m.times_used}[/]"
        
        last_used_str = m.last_used.strftime('%Y-%m-%d %H:%M') if m.last_used else "Never"
        
        table.add_row(
            m.name,
            cat_badge,
            f"{m.size_gb:.1f} GB",
            uses_text,
            last_used_str
        )
        displayed_count += 1

    if displayed_count == 0:
        components.append(Text(f"  No installed models found for category '{category_filter}'.", style="dim"))
    else:
        components.append(table)
        
    return Group(*components)

def render_insights_view(models: List[ModelInfo], category_filter: str = "All") -> None:
    """Legacy function to appease old tests that mocked console."""
    console.clear()
    console.print(get_insights_view(models, category_filter))

def run_insights_history():
    current_filter = "All"
    while True:
        models = gather_models()
        view = get_insights_view(models, current_filter)
        
        render_page(view, top_padding=-1)
        
        choice = questionary.select(
            "Select action:",
            choices=[
                questionary.Choice("🗑️  Remove Model(s)", "remove"),
                questionary.Choice("📊 Filter by Category", "filter"),
                questionary.Choice("⬅️  Back to Main Menu", "back")
            ]
        ).ask()

        if not choice or choice == "back":
            break
            
        if choice == "filter":
            filter_choice = questionary.select(
                "Select category to view:",
                choices=["All", "Reasoning", "Build", "General"]
            ).ask()
            if filter_choice:
                current_filter = filter_choice
                
        elif choice == "remove":
            # Show list of models to delete
            if not models:
                continue
                
            model_choices = []
            for m in sorted(models, key=lambda x: x.times_used):
                display = f"{m.name} ({m.size_gb:.1f} GB) - {m.times_used} uses"
                model_choices.append(questionary.Choice(display, m))
            model_choices.append(questionary.Choice("Cancel", "cancel"))
            
            selected_model = questionary.select(
                "Select model to completely remove:",
                choices=model_choices
            ).ask()
            
            if not selected_model or selected_model == "cancel":
                continue
                
            confirm = questionary.confirm(
                f"⚠️ Are you sure you want to permanently delete {selected_model.name} (reclaiming {selected_model.size_gb:.1f} GB)?"
            ).ask()
            
            if confirm:
                try:
                    freed = delete_model_from_disk(selected_model.repo_id)
                    freed_gb = format_bytes_gb(freed)
                    console.print(f"\n  [green]✔  Successfully deleted {selected_model.name}. Reclaimed {freed_gb:.1f} GB.[/]")
                except Exception as e:
                    console.print(f"\n  [red]✖  Failed to delete: {e}[/]")
                
                # Pause before refreshing
                console.print("\n  [dim]Press Enter to continue...[/]", end="")
                input()
