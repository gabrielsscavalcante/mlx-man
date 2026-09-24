# Manage Models View

## Overview
The "Manage Models" view provides a modern Terminal User Interface (TUI) for inspecting, organizing, and interacting with downloaded MLX models. It has been redesigned to align with the Dashboard and Insights modules, offering a cleaner categorized tabular presentation.

## Layout Components

1. **System Header Panel**
   - Displays real-time context about the system's memory constraints to help the user choose appropriately sized models.
   - Shows: `Total Installed Models`, `Total Disk Footprint`, and `System RAM Context` (Unified RAM + Wired GPU Limit).
   - Rendered using a `rich.panel.Panel` in cyan style.

2. **Model Inventory Table**
   - Replaces the legacy multi-line list with an aligned `rich.table.Table`.
   - **Model Name & Quant:** Distinct labels separating the underlying model from its quantization format (e.g., `4-bit g64`).
   - **Role / Category:** Categorized heuristically and mapped to `🧠 Reasoning`, `⚒️ Builder`, or `⚡ General`.
   - **Resource Cost:** Size on Disk and estimated Unified RAM requirements.
   - **Tier Badge:** High-visibility pills (`Light`, `Medium`, `Heavy`, `Very Heavy`) directly tied to RAM thresholds.
   - **Best For:** Quick actionable insight directly from the model registry.

## State Flow & Architecture

The view is orchestrated via `src/model_inspector.py`.

* **Discovery Phase:** `discover_models()` scans `~/.cache/huggingface/hub/models--*`, extracts paths and `config.json` specs.
* **Enrichment Phase:** `build_model_metadata()` merges raw filesystem discovery with curated `MODEL_REGISTRY` entries to populate the `ModelMetadata` dataclass schema. Unknown models are categorized using intelligent heuristics and RAM estimations.
* **Rendering Phase:** `render_model_manager()` builds a `rich.console.Group` and renders it via `cli_layout.render_page()` for perfect centering and a sticky footer.
* **Interaction Loop:** `questionary.select()` creates an interactive action bar to filter models, download new ones, or select a model.

### Action Menu
Selecting a model from the list enters the `_model_action_menu()` loop, exposing direct operations:
1. `▶️ Run Model`: Launches an interactive MLX prompt loop.
2. `🌐 Serve Model`: Spawns the OpenAI-compatible API on port 8080.
3. `ℹ️ View Detailed Metadata`: Extracts internal affine and grouping shapes.
4. `🗑️ Delete Model`: Invokes the safe cache deletion logic, reporting freed disk space.

## Keybindings
The UI leverages `questionary`, affording robust key-based navigation:
* **`↑/↓` Arrow Keys** or **`j/k`**: Navigate the option lists.
* **`Enter`**: Execute the selected action or inspect the selected model.
* **`Esc` or `Ctrl+C`**: Gracefully back out of current menus or cancel inputs without crashing the application.
