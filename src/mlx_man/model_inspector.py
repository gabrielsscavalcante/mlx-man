#!/usr/bin/env python3
"""
model_inspector.py — Browse, inspect, download, and delete local MLX models.

Refactored to use rich and tui_engine for a modern TUI experience.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass

from rich.console import Group
from rich.text import Text

from mlx_man.tui_engine import tui_select, tui_confirm, tui_text_input, tui_table_select
from mlx_man.model_registry import MODEL_REGISTRY, get_registry_entry, ROLE_INFO
from mlx_man.model_manager import delete_model_from_disk, HF_CACHE_DIR, MODEL_DIR_PREFIX, calculate_model_disk_size
from mlx_man.cli_dashboard import get_total_ram_gb, get_current_gpu_limit, get_system_status_footer
from mlx_man.ui_components import create_header_panel, create_data_table, create_warning_panel


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
    if tier == "Light":
        return "green"
    if tier == "Medium":
        return "yellow"
    if tier == "Heavy":
        return "magenta"
    return "bold red"


def get_role_icon(role: str) -> str:
    """Return the semantic icon for a given role category."""
    if role == "Reasoning":
        return "🧠"
    if role == "Builder":
        return "⚒️"
    return "⚡"


def discover_models() -> List[dict]:
    """Scan the HuggingFace cache and return a list of installed model info dicts."""
    models = []
    if not HF_CACHE_DIR.exists():
        return models

    for model_dir in sorted(HF_CACHE_DIR.iterdir()):
        if not model_dir.is_dir() or not model_dir.name.startswith(MODEL_DIR_PREFIX):
            continue

        parts = model_dir.name[len(MODEL_DIR_PREFIX) :].split("--")
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
        raw_info=model_info,
    )


def render_model_manager(models: List[ModelMetadata], filter_role: str = "All") -> Group:
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

    return create_header_panel(summary_text, "Manage Models")


def run_model_inspector():
    current_filter = "All"
    while True:
        raw_models = discover_models()
        models = [build_model_metadata(m) for m in raw_models]
        
        filtered = [m for m in models if current_filter == "All" or m.role == current_filter]

        header_view = render_model_manager(models, current_filter)
        footer_text = get_system_status_footer()

        if not filtered:
            choice = tui_select(
                title="No models found.",
                choices=["download", "filter", "back"],
                format_func=lambda x: {"download": "📥 Download", "filter": "📊 Filter", "back": "⬅️ Back"}[x],
                header=header_view,
                footer=footer_text
            )
        else:
            columns = [
                {"header": "Model Name", "style": "bold white"},
                {"header": "Role", "justify": "center"},
                {"header": "Cost", "justify": "right"},
                {"header": "Tier", "justify": "center"},
                {"header": "Best For", "style": "dim"}
            ]
            
            def get_row(m: ModelMetadata):
                quant_pill = Text(m.quant_details, style="dim")
                name_cell = Text(m.name + "\n").append(quant_pill)
                
                role_icon = {"Reasoning": "🧠", "Builder": "⚒️", "General": "⚡"}.get(m.role, "📦")
                role_cell = f"{role_icon} {m.role}"
                
                cost_cell = Text(f"Disk: {m.disk_gb:.1f} GB\n").append(f"RAM: ~{m.ram_estimate_gb:.1f} GB", style="dim")
                
                tier_color = {"Light": "green", "Medium": "yellow", "Heavy": "red", "Very Heavy": "magenta"}.get(m.tier, "white")
                tier_badge = Text(f" {m.tier} ", style=f"{tier_color} reverse")
                
                return [name_cell, role_cell, cost_cell, tier_badge, m.best_for]
                
            choice = tui_table_select(
                title=f"Installed Models ({current_filter})",
                columns=columns,
                data=filtered,
                row_func=get_row,
                header=header_view,
                footer=footer_text,
                extra_hotkeys={"d": "download", "f": "filter"}
            )
            
        if not choice or choice == "back":
            break
            
        if choice == "download":
            download_model()
            continue
            
        if choice == "filter":
            filter_labels = {
                "All": "🌐 All",
                "Reasoning": "🧠 Reasoning",
                "Builder": "⚒️  Builder",
                "General": "⚡ General",
            }
            filter_choice = tui_select(
                title="Select category to view:",
                choices=["All", "Reasoning", "Builder", "General"],
                format_func=lambda x: filter_labels.get(x, str(x)),
                header=header_view,
                footer=get_system_status_footer(),
            )
            if filter_choice:
                current_filter = filter_choice
            continue
            
        if isinstance(choice, ModelMetadata):
            _model_action_menu(choice)


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
        footer_text = get_system_status_footer()

        action_labels = {
            "run": "▶️  Run Model (Chat)",
            "serve": "🌐 Serve Model (API)",
            "meta": "ℹ️  View Detailed Metadata",
            "delete": "🗑️  Delete Model",
            "back": "⬅️  Return to Model List",
        }

        action = tui_select(
            title=f"Actions for {model.name}:",
            choices=["run", "serve", "meta", "delete", "back"],
            format_func=lambda x: action_labels.get(x, str(x)),
            header=panel,
            footer=footer_text,
        )

        if not action or action == "back":
            break

        if action == "run":
            print("\nDirect MLX inference is launching...")
            subprocess.run([sys.executable, "-m", "mlx_lm.generate", "--model", model.repo_id, "--prompt", "Hello!"])
            input("\nPress Enter to return...")

        elif action == "serve":
            print("\nStarting OpenAI-compatible server on port 8080...")
            try:
                subprocess.run([sys.executable, "-m", "mlx_lm.server", "--model", model.repo_id, "--port", "8080"])
            except KeyboardInterrupt:
                print("\nServer stopped.")

        elif action == "meta":
            meta_text = Text()
            meta_text.append("Config extracted specs:\n", style="bold white")
            specs = model.raw_info.get("specs", {})
            if specs:
                for k, v in specs.items():
                    meta_text.append(f"  • {k}: ", style="cyan")
                    meta_text.append(f"{v}\n", style="white")
            else:
                meta_text.append("  (No extra specs found in config.json)\n", style="dim")
            meta_text.append(f"\nCache Path: {model.raw_info.get('model_dir')}", style="dim")

            meta_panel = create_header_panel(meta_text, f"Metadata: {model.name}")
            tui_confirm(
                prompt="Press Enter or Esc to return to model actions.",
                header=meta_panel,
                footer=footer_text,
            )

        elif action == "delete":
            confirm = tui_confirm(
                prompt=f"⚠️ Permanently delete {model.name} (reclaim {model.disk_gb:.1f} GB)?",
                header=panel,
                footer=footer_text,
            )

            if confirm:
                try:
                    freed = delete_model_from_disk(model.repo_id)
                    result_text = Text(f"✔ Successfully deleted. Reclaimed {freed / (1024**3):.1f} GB.", style="bold green")
                    result_panel = create_warning_panel(result_text, "Model Deleted")
                    tui_confirm(
                        prompt="Model deleted. Press Enter to continue.",
                        header=result_panel,
                        footer=footer_text,
                    )
                    break  # Go back after deletion
                except Exception as e:
                    err_text = Text(f"✖ Failed to delete: {e}", style="bold red")
                    err_panel = create_warning_panel(err_text, "Delete Failed")
                    tui_confirm(
                        prompt="Error occurred. Press Enter to return.",
                        header=err_panel,
                        footer=footer_text,
                    )


def download_model():
    prompt_text = Text("Enter a HuggingFace model ID (e.g., mlx-community/Qwen3.6-27B-4bit)", style="dim")
    panel = create_header_panel(prompt_text, "Download New Model")
    footer_text = get_system_status_footer()

    model_id = tui_text_input(
        prompt="Model ID:",
        header=panel,
        footer=footer_text,
    )
    if not model_id:
        return

    model_id = model_id.replace("https://huggingface.co/", "").strip("/")
    if "/" not in model_id:
        err_text = Text("Invalid format. Expected org/model-name", style="bold red")
        err_panel = create_warning_panel(err_text, "Invalid Format")
        tui_confirm(
            prompt="Invalid format. Press Enter to return.",
            header=err_panel,
            footer=footer_text,
        )
        return

    print(f"\nDownloading {model_id}...")
    try:
        from mlx_man.model_downloader import download_model as _download
        _download(model_id)
    except KeyboardInterrupt:
        print("\nDownload interrupted.")
    except Exception as e:
        print(f"\nDownload failed: {e}")

    input("\nPress Enter to continue...")


if __name__ == "__main__":  # pragma: no cover
    try:
        run_model_inspector()
    except KeyboardInterrupt:
        print("\n  \033[32m✔\033[0m  Goodbye! 👋\n")
