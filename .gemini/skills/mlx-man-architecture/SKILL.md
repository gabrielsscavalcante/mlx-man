---
name: mlx-man-architecture
description: >
  MLX-Man project architecture guide. Consult this skill whenever creating new features,
  modules, or tests for MLX-Man to ensure they follow the established patterns, import
  conventions, data storage locations, and layer boundaries.
---

# MLX-Man Architecture Skill

This skill defines the canonical architecture, conventions, and patterns for the
MLX-Man project. **Every new feature, module, or test must follow these rules.**

## Package Identity

- **Distribution name (PyPI):** `mlx-man`
- **Python package name:** `mlx_man`
- **CLI entry point:** `mlx-man` → `mlx_man.main:main`
- **Source location:** `src/mlx_man/`
- **Version:** Single source of truth at `src/mlx_man/__init__.py`

## 3-Layer Architecture

MLX-Man enforces strict separation of concerns across three layers.
**Never mix layers** — UI code must not touch the filesystem directly,
and domain logic must not render output.

```
src/mlx_man/
├── Presentation Layer (CLI / TUI)
│   ├── main.py               # Main CLI loop & alternate screen buffer
│   ├── tui_engine.py          # Centralized rich.live.Live TUI Engine and native input
│   ├── ui_components.py       # Reusable layout components (panels, tables)
│   ├── cli_dashboard.py       # ASCII logo, hardware detection, & rotating tips
│   ├── cli_actions.py         # Action handlers (server launcher, memory cleaner)
│   ├── ram_manager_view.py    # Memory cleaner UI with process termination
│   └── insights_view.py       # Historical usage analytics dashboard
│
├── Domain Layer (Models & Logic)
│   ├── model_registry.py      # Single source of truth for curated models & roles
│   ├── model_manager.py       # HF cache scanner, size calculator, safe deleter
│   └── usage_tracker.py       # Local usage recording and session statistics
│
└── Infrastructure Layer (Engine & OS)
    ├── model_downloader.py    # Dedicated HuggingFace model downloader
    ├── model_inspector.py     # Model browser, technical spec cards
    ├── process_service.py     # Process monitoring service (psutil)
    └── opencode_sync.py       # OpenCode CLI configuration sync
```

### Layer Rules

| Layer | Can import from | Cannot import from |
|---|---|---|
| Presentation | Domain, Infrastructure, third-party (`rich`). NO blocking libraries like `questionary`. | — |
| Domain | Standard library only | Presentation, Infrastructure |
| Infrastructure | Domain, standard library, third-party (`psutil`, `huggingface_hub`, `mlx_lm`) | Presentation |

## Import Convention

**Always use package-qualified imports.** Never use bare imports or `sys.path` hacks.

```python
# ✅ CORRECT
from mlx_man.model_registry import MODEL_REGISTRY, get_registry_entry
from mlx_man.cli_dashboard import get_system_status_footer
from mlx_man import __version__

# ❌ WRONG — bare import (will break outside src/)
from model_registry import MODEL_REGISTRY

# ❌ WRONG — sys.path manipulation
import sys
sys.path.insert(0, os.path.dirname(__file__))
```

## Data Storage Locations

All user data uses XDG-compliant paths. **Never store data in the project directory.**

| Data | Location | Module |
|---|---|---|
| Usage history | `~/.config/mlx-man/usage_history.json` | `usage_tracker.py` |
| HF model cache | `~/.cache/huggingface/hub/` | `model_manager.py` |
| OpenCode config | `~/.config/opencode/opencode.json` | `opencode_sync.py` |

To get the config directory:
```python
from mlx_man.usage_tracker import get_config_dir
config_dir = get_config_dir()  # Returns ~/.config/mlx-man/
```

## Version Management

The version string lives **only** in `src/mlx_man/__init__.py`:

```python
# src/mlx_man/__init__.py
__version__ = "0.4.0"
```

To read the version elsewhere:
```python
from mlx_man import __version__
```

**Do not** hardcode version strings anywhere else. `pyproject.toml` defines the
version statically (keep it in sync with `__init__.py`).

## Adding a New Module

1. Create the file at `src/mlx_man/new_module.py`
2. Use package-qualified imports for all sibling dependencies
3. Place it in the correct architectural layer
4. Add corresponding tests at `tests/test_new_module.py`
5. Ensure it's importable by adding to `test_setup.py::test_all_modules_importable`

## Adding a New Model to the Registry

1. Edit `src/mlx_man/model_registry.py` → `MODEL_REGISTRY` dict
2. Include all required fields: `name`, `role`, `ram_estimate_gb`, `performance_tier`,
   `quantization_summary`, `best_for`, `description`
3. Add the model to the README.md and Documentation.md tables
4. Run `make test` to verify

## Testing Patterns

### File location
All tests go in `tests/`. No `sys.path` manipulation needed — `pyproject.toml`
sets `pythonpath = ["src"]` for pytest.

### Imports in tests
```python
# ✅ CORRECT — package-qualified, no sys.path
from mlx_man.model_manager import get_installed_models
from mlx_man.usage_tracker import record_usage, load_data
```

### Mock patch targets
Always patch using the full `mlx_man.module.symbol` path:
```python
# ✅ CORRECT
@patch('mlx_man.model_inspector.questionary.select')
@patch('mlx_man.main.centered_select')

# ❌ WRONG — bare module path
@patch('model_inspector.questionary.select')
```

### Shared fixtures
Use fixtures from `tests/conftest.py`:
- `mock_hf_cache(tmp_path)` — temporary HuggingFace cache directory
- `mock_config_dir(tmp_path)` — temporary MLX-Man config directory
- `rich_console()` — Rich Console with `record=True` for output assertions

### Rendering tests
Use `Console(record=True)` to assert UI renders without exceptions:
```python
def test_my_view_renders():
    from rich.console import Console
    c = Console(record=True, width=120)
    c.print(my_renderable)
    output = c.export_text()
    assert "Expected Text" in output
```

### Safety tests
All destructive actions must be tested with both confirmed and cancelled paths:
```python
def test_delete_cancelled_does_not_delete():
    # Mock questionary.confirm to return False
    # Assert delete_model_from_disk was NOT called

def test_delete_confirmed_removes_model():
    # Mock questionary.confirm to return True
    # Assert delete_model_from_disk WAS called with correct args
```

## CLI Entry Points

There are three equivalent ways to run MLX-Man:

```bash
mlx-man              # Installed CLI entry point
python -m mlx_man    # Package invocation
./start_llm.sh       # Shell launcher (legacy compat)
```

## UX Safety Rules

1. **Destructive actions** (model deletion, process killing) → mandatory confirmation prompt
2. **Model deletion** → must clean orphaned shared blobs, report exact disk space freed
3. **Process killing** → 3-tier safety classification (Safe/Caution/Danger)
4. **Long operations** (model downloads) → progress indicators to prevent stall perception
5. **GPU memory** → offer `sudo sysctl iogpu.wired_limit_mb=N` when running heavy models

## UI/UX & Design

For all rules regarding the presentation layer, visual aesthetics, color palettes, and reusable UI components (`mlx_man.ui_components`), you MUST refer strictly to the **`mlx-man-design`** skill. The architecture strictly mandates that the Presentation Layer logic contains no business logic and relies on the central layout engine for rendering.

### UI Snapshot Testing
All TUI layout components MUST be backed by deterministic snapshot tests in `tests/test_ui_snapshots.py`.
- Mocks: Always mock dynamic inputs like RAM amount, chip names, and process lists before taking a snapshot.
- Generation: Run `UPDATE_SNAPSHOTS=1 pytest` to regenerate the `.txt` baseline and `.svg` visual artifact.
- CI: The GitHub Actions CI pipeline will automatically upload the `.svg` snapshots as artifacts on every run.
