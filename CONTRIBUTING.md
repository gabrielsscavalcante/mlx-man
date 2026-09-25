# Contributing to MLX-Man

Thank you for your interest in contributing to MLX-Man! This guide will help you get set up and understand the project.

## Prerequisites

- **macOS with Apple Silicon** (M-series chip)
- **Python 3.9+** (system Python or via Homebrew)
- **Git**

## Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/gabrielsscavalcante/mlx-man.git
cd mlx-man

# 2. Create a virtual environment and install with dev dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Or using uv (faster):
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. Verify the setup
make test
```

After setup, the `mlx-man` command should be available in your terminal.

## Project Architecture

MLX-Man follows a strict **3-layer architecture**:

```
src/mlx_man/
├── Presentation Layer (CLI / TUI)
│   ├── main.py               # Main CLI loop & alternate screen buffer
│   ├── cli_select.py          # Spotlight-style centered selector
│   ├── cli_layout.py          # Dynamic terminal centering & footer
│   ├── cli_dashboard.py       # ASCII logo, hardware detection, tips
│   └── cli_actions.py         # Action handlers (server, cleaner, etc.)
│
├── Domain Layer (Models & Logic)
│   ├── model_registry.py      # Curated model knowledge base
│   ├── model_manager.py       # HF cache scanner & size calculator
│   └── usage_tracker.py       # Session history & analytics data
│
└── Infrastructure Layer (Engine & OS)
    ├── model_downloader.py    # HuggingFace model downloads
    ├── model_inspector.py     # Model browser & detail cards
    ├── process_service.py     # Process monitoring (psutil)
    ├── ram_manager_view.py    # Memory cleaner UI
    ├── insights_view.py       # Usage analytics dashboard
    └── opencode_sync.py       # OpenCode CLI config sync
```

### Key Principles

1. **Package-qualified imports**: Always use `from mlx_man.module import ...`, never bare imports.
2. **Single source of truth**: Version lives in `src/mlx_man/__init__.py`. Usage data path lives in `usage_tracker.py`.
3. **XDG compliance**: User data goes to `~/.config/mlx-man/`, not the project directory.
4. **Safety first**: All destructive actions (model deletion, process killing) require confirmation prompts.

## Running Tests

```bash
# Run full test suite
make test

# Run with coverage
make test-cov

# Run a specific test file
pytest tests/test_setup.py -v

# Run a specific test
pytest tests/test_cli.py::test_banner_renders_without_error -v
```

## Adding a New Model to the Registry

1. Edit `src/mlx_man/model_registry.py`
2. Add a new entry to the `MODEL_REGISTRY` dict with all required fields
3. Add a corresponding test in `tests/test_cli.py` or `tests/test_models_view.py`
4. Update `README.md` and `Documentation.md` model tables

## Code Style

- Follow PEP 8
- Use type hints where practical
- Docstrings for all public functions
- Maximum line length: 100 characters

## Pull Request Guidelines

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Run `make test` and ensure all tests pass
4. Update documentation if needed
5. Keep commits atomic and well-described

## Data Directories

When developing, be aware of where MLX-Man stores data on a user's Mac:

| Directory | Purpose |
|---|---|
| `~/.config/mlx-man/` | App config & usage history |
| `~/.cache/huggingface/hub/` | Downloaded model weights |
| `~/.config/opencode/` | OpenCode CLI config (if used) |

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
