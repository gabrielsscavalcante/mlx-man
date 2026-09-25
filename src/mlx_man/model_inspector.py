#!/usr/bin/env python3
"""
model_inspector.py — Browse, inspect, download, and delete local MLX models.

Refactored to use rich and questionary for a modern TUI experience.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass

from rich.console import Console, Group
from rich.text import Text
import questionary

from mlx_man.model_registry import MODEL_REGISTRY, get_registry_entry, ROLE_INFO
from mlx_man.model_manager import delete_model_from_disk, HF_CACHE_DIR, MODEL_DIR_PREFIX, calculate_model_disk_size
from mlx_man.cli_dashboard import get_total_ram_gb, get_current_gpu_limit
from mlx_man.ui_components import create_header_panel, create_data_table, create_warning_panel
from mlx_man.cli_layout import render_centered_view

console = Console()

@dataclass
class ModelMetadata:
    name: str
    repo_id: str
    disk_gb: float
    ram_estimate_gb: float
    tier: Literal["Light", "Medium", "Heavy", "Very Heavy"]
    role: Literal["Reasoning", "Builder", "General"]
    quant_details: str
    best_for: str
    raw_info: dict  # To keep raw specs and paths

def categorize_model(repo_id: str) -> Literal["Reasoning", "Builder", "General"]:
    """Categorize model based on registry role or heuristics."""
    entry = get_registry_entry(repo_id)
    if entry and "role" in entry:
        role = entry["role"]
        if role == "reasoning":
            return "Reasoning"
        elif role == "builder":
            return "Builder"
        elif role == "general":
            return "General"
    
    repo_lower = repo_id.lower()
    if any(x in repo_lower for x in ["qwq", "r1", "o1", "reasoning"]):
        return "Reasoning"
    if any(x in repo_lower for x in ["coder", "devstral", "build"]):
        return "Builder"
    
    return "General"

def get_tier(ram_gb: float) -> Literal["Light", "Medium", "Heavy", "Very Heavy"]:
    """Map RAM footprint to an intuitive performance tier."""
    if ram_gb < 10:
        return "Light"
    elif ram_gb <= 16:
        return "Medium"
    elif ram_gb <= 24:
        return "Heavy"
    else:
        return "Very Heavy"

def get_tier_color(tier: str) -> str:
    """Return the rich color corresponding to a given tier."""
    if tier == "Light": return "green"
    if tier == "Medium": return "yellow"
    if tier == "Heavy": return "magenta"
    return "bold red"

def get_role_icon(role: str) -> str:
    """Return the semantic icon for a given role category."""
    if role == "Reasoning": return "🧠"
    if role == "Builder": return "⚒️"
    return "⚡"

def discover_models() -> List[dict]:
    """Scan the HuggingFace cache and return a list of installed model info dicts."""
    models = []
    if not HF_CACHE_DIR.exists():
        return models

    for model_dir in sorted(HF_CACHE_DIR.iterdir()):
        if not model_dir.is_dir() or not model_dir.name.startswith(MODEL_DIR_PREFIX):
            continue

        parts = model_dir.name[len(MODEL_DIR_PREFIX):].split("--")
        if len(parts) < 2:
            continue
        model_id = "/".join(parts)

        snapshots_dir = model_dir / "snapshots"
        latest_snapshot = None
        if snapshots_dir.exists():
            snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
            if snapshot_dirs:
                latest_snapshot = max(snapshot_dirs, key=lambda d: d.stat().st_mtime)

        config = {}
        if latest_snapshot:
            config_path = latest_snapshot / "config.json"
            if config_path.exists():
                try:
                    with open(config_path.resolve()) as f:
                        config = json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass

        disk_bytes = calculate_model_disk_size(model_dir)
        specs = _extract_specs(config)
        registry = get_registry_entry(model_id)

        models.append({
            "model_id": model_id,
            "model_dir": model_dir,
            "snapshot_dir": latest_snapshot,
            "config": config,
            "specs": specs,
            "disk_bytes": disk_bytes,
            "registry": registry,
        })
    return models

def _extract_specs(config: dict) -> dict:
    """Extract human-readable specs from a model's config.json."""
    specs = {}
    archs = config.get("architectures", [])
    if archs:
        specs["architecture"] = archs[0]
    specs["model_type"] = config.get("model_type", "unknown")

    quant = config.get("quantization") or config.get("quantization_config") or {}
    if quant:
        bits = quant.get("bits", "?")
        group_size = quant.get("group_size", "?")
        mode = quant.get("mode", "?")
        specs["quantization"] = f"{bits}-bit g{group_size}"
    
    return specs

def build_model_metadata(model_info: dict) -> ModelMetadata:
    """Transform raw discovery info into structured ModelMetadata for rendering."""
    model_id = model_info["model_id"]
    disk_gb = model_info["disk_bytes"] / (1024**3)
    
    reg = model_info.get("registry")
    if reg:
        name = reg.get("name", model_id.split("/")[-1])
        ram_est = reg.get("ram_estimate_gb", disk_gb * 1.05)
        quant = model_info["specs"].get("quantization", reg.get("quantization_summary", "Unknown"))
        best_for = ", ".join(reg.get("best_for", ["General tasks"]))
    else:
        name = model_id.split("/")[-1]
        ram_est = disk_gb * 1.05
        quant = model_info["specs"].get("quantization", "Unknown")
        best_for = "General usage"
        
    role = categorize_model(model_id)
    tier = get_tier(ram_est)
    
    return ModelMetadata(
        name=name,
        repo_id=model_id,
        disk_gb=round(disk_gb, 1),
        ram_estimate_gb=round(ram_est, 1),
        tier=tier,
        role=role,
        quant_details=quant,
        best_for=best_for,
        raw_info=model_info
    )

def render_model_manager(models: List[ModelMetadata], filter_role: str = "All"):
    """
    Constructs and renders the full 'Manage Models' dashboard layout containing
    the system summary panel and the formatted tabular list of installed models.
    """
    total_models = len(models)
    total_disk_gb = sum(m.disk_gb for m in models)
    system_ram = get_total_ram_gb()
    gpu_limit = get_current_gpu_limit()

    summary_text = Text()
    summary_text.append("📦 Total Installed Models: ", style="bold white")
    summary_text.append(f"{total_models}\n", style="dim")
    summary_text.append("💾 Total Disk Footprint: ", style="bold white")
    summary_text.append(f"{total_disk_gb:.1f} GB\n", style="dim")
    summary_text.append("🖥️  System RAM Context: ", style="bold white")
    summary_text.append(f"{system_ram} GB Unified  |  Limit: {gpu_limit}", style="dim")

    header_panel = create_header_panel(summary_text, "Manage Models")

    columns = [
        {"header": "Model Name & Quant", "style": "bold white"},
        {"header": "Role / Category", "justify": "center"},
        {"header": "Resource Cost", "justify": "right"},
        {"header": "Tier Badge", "justify": "center"},
        {"header": "Best For", "style": "dim"},
    ]
    table = create_data_table(columns=columns)

    for m in models:
        if filter_role != "All" and m.role != filter_role:
            continue
            
        quant_pill = f"[dim]{m.quant_details}[/]"
        name_cell = f"{m.name}\n{quant_pill}"
        
        role_icon = get_role_icon(m.role)
        role_cell = f"{role_icon} {m.role}"
        
        cost_cell = f"Disk: {m.disk_gb:.1f} GB\n[dim]RAM: ~{m.ram_estimate_gb:.1f} GB[/]"
        
        tier_color = get_tier_color(m.tier)
        tier_badge = f"[{tier_color} reverse] {m.tier} [/]"
        
        table.add_row(name_cell, role_cell, cost_cell, tier_badge, m.best_for)
        table.add_row("", "", "", "", "") # Spacing

    components = [header_panel, Text("")]
    if total_models > 0:
        components.append(table)
    else:
        components.append(Text("No models found. Try downloading one!", style="yellow"))

    render_centered_view(Group(*components), prompt_lines=6)

def run_model_inspector():
    """Main interactive loop for discovering, filtering, and selecting models."""
    current_filter = "All"
    while True:
        raw_models = discover_models()
        models = [build_model_metadata(m) for m in raw_models]
        
        render_model_manager(models, current_filter)
        
        choices = [
            questionary.Choice("🔍 Select Model to Inspect/Manage", "inspect"),
            questionary.Choice("📊 Filter by Category", "filter"),
            questionary.Choice("📥 Download a new model", "download"),
            questionary.Choice("⬅️  Back to Main Menu", "back")
        ]
        
        choice = questionary.select(
            "Select action:",
            choices=choices
        ).ask()
        
        if not choice or choice == "back":
            break
            
        if choice == "filter":
            filter_choice = questionary.select(
                "Select category to view:",
                choices=["All", "Reasoning", "Builder", "General"]
            ).ask()
            if filter_choice:
                current_filter = filter_choice
                
        elif choice == "inspect":
            if not models:
                continue
                
            model_choices = []
            for m in models:
                if current_filter != "All" and m.role != current_filter: continue
                model_choices.append(questionary.Choice(f"{m.name} ({m.disk_gb:.1f} GB)", m))
            model_choices.append(questionary.Choice("⬅️ Cancel", "cancel"))
            
            selected_m = questionary.select(
                "Select a model:",
                choices=model_choices
            ).ask()
            
            if not selected_m or selected_m == "cancel":
                continue
                
            _model_action_menu(selected_m)

        elif choice == "download":
            download_model()

def _model_action_menu(model: ModelMetadata):
    """Interactive submenu for performing actions on a selected model."""
    while True:
        details = Text()
        details.append("Model ID: ", style="bold white")
        details.append(f"{model.repo_id}\n", style="dim")
        details.append("Disk Size: ", style="bold white")
        details.append(f"{model.disk_gb:.1f} GB\n", style="dim")
        details.append("RAM Est: ", style="bold white")
        details.append(f"{model.ram_estimate_gb:.1f} GB\n", style="dim")
        details.append("Quant: ", style="bold white")
        details.append(f"{model.quant_details}\n", style="dim")
        
        panel = create_header_panel(details, model.name)
        
        render_centered_view(panel, prompt_lines=7)
        
        action = questionary.select(
            f"Actions for {model.name}:",
            choices=[
                questionary.Choice("▶️  Run Model (Chat)", "run"),
                questionary.Choice("🌐 Serve Model (API)", "serve"),
                questionary.Choice("ℹ️  View Detailed Metadata", "meta"),
                questionary.Choice("🗑️  Delete Model", "delete"),
                questionary.Choice("⬅️  Return to Model List", "back")
            ]
        ).ask()
        
        if not action or action == "back":
            break
            
        if action == "run":
            console.print("\n[yellow]Direct MLX inference is launching...[/]")
            subprocess.run(["python3", "-m", "mlx_lm.generate", "--model", model.repo_id, "--prompt", "Hello!"])
            console.print("\n[dim]Press Enter to return...[/]", end="")
            input()
            
        elif action == "serve":
            console.print("\n[yellow]Starting OpenAI-compatible server on port 8080...[/]")
            try:
                subprocess.run(["python3", "-m", "mlx_lm.server", "--model", model.repo_id, "--port", "8080"])
            except KeyboardInterrupt:
                console.print("\n[green]Server stopped.[/]")
                
        elif action == "meta":
            console.print("\n[bold white]Config.json extracted specs:[/]")
            import pprint
            pprint.pprint(model.raw_info.get("specs", {}))
            console.print(f"\n[dim]Cache Path: {model.raw_info.get('model_dir')}[/]")
            console.print("\n[dim]Press Enter to return...[/]", end="")
            input()
            
        elif action == "delete":
            confirm = questionary.confirm(
                f"⚠️ Are you sure you want to permanently delete {model.name} (reclaiming {model.disk_gb:.1f} GB)?"
            ).ask()
            
            if confirm:
                try:
                    freed = delete_model_from_disk(model.repo_id)
                    result_text = Text(f"✔ Successfully deleted. Reclaimed {freed / (1024**3):.1f} GB.", style="bold green")
                    render_centered_view(create_warning_panel(result_text, "Model Deleted"), prompt_lines=0)
                    time.sleep(1.5)
                    break # Go back after deletion
                except Exception as e:
                    err_text = Text(f"✖ Failed to delete: {e}", style="bold red")
                    render_centered_view(create_warning_panel(err_text, "Delete Failed"), prompt_lines=0)
                    time.sleep(2)

def download_model():
    prompt_text = Text("Enter a HuggingFace model ID (e.g., mlx-community/Qwen3.6-27B-4bit)", style="dim")
    panel = create_header_panel(prompt_text, "Download New Model")
    render_centered_view(panel, prompt_lines=2)
    
    model_id = questionary.text("Model ID:").ask()
    if not model_id:
        return
        
    model_id = model_id.replace("https://huggingface.co/", "").strip("/")
    if "/" not in model_id:
        err_text = Text("Invalid format. Expected org/model-name", style="bold red")
        render_centered_view(create_warning_panel(err_text, "Invalid Format"), prompt_lines=0)
        time.sleep(1.5)
        return

    console.print(f"\n[yellow]Downloading {model_id}...[/]")
    try:
        from mlx_man.model_downloader import download_model as _download
        _download(model_id)
    except KeyboardInterrupt:
        console.print("\n[yellow]Download interrupted.[/]")
    except Exception as e:
        console.print(f"\n[red]Download failed: {e}[/]")

    console.print("\n[dim]Press Enter to continue...[/]", end="")
    input()

if __name__ == "__main__":
    try:
        run_model_inspector()
    except KeyboardInterrupt:
        console.print("\n[green]✔ Goodbye![/]")
