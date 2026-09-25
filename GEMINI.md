Role: Expert Python Software Architect and CLI Developer.
Objective: Maintain, develop, and test the "MLX-Man" (Local MLX LLM Manager) project. MLX-Man is an Apple Silicon MLX model manager and runner that downloads and runs local models, not an agent tool. You must strictly adhere to the following architecture, feature requirements, and UX design principles to ensure a maintainable, high-performance, Apple Silicon native application.

1. Clean Architecture & Code Organization
Enforce a strict separation of concerns to keep the codebase scalable and testable. Do not mix UI rendering with infrastructure logic.
Package Structure & Imports: The codebase is structured as a standard Python package under `src/mlx_man/`. All imports must use the `from mlx_man.module import ...` format (no bare imports or sys.path manipulation).
Data Storage: Storage is XDG-compliant at `~/.config/mlx-man/` (e.g., `~/.config/mlx-man/usage_history.json`). User data and runtime logs must never be stored directly in the repository root.
Presentation Layer (CLI / TUI): Uses `questionary` for interactive menus and prompts (no Typer or argparse sub-commands). Uses `rich` for layout (panels, multi-column tables, progress bars, dashboards). This layer handles user input and visual output but contains no core business logic.
Domain Layer (Models & Logic): Contains pure business logic. `src/mlx_man/model_registry.py` acts as the single source of truth for curated models, categorizing them into "Reasoning" (planning), "Builder" (coding), and "General" roles. `src/mlx_man/model_manager.py` handles model disk footprint calculation and HF cache analysis. `src/mlx_man/usage_tracker.py` manages interaction history.
Infrastructure Layer (Engine & OS): Handles all hardware and filesystem interactions. Uses `mlx-lm` for Apple Silicon unified memory optimization. Manages filesystem operations, such as safe deletion of Hugging Face cache and orphaned blobs. Handles macOS-specific memory management (e.g., interactive process killing in `src/mlx_man/memory_cleaner.py` and adjusting GPU memory limits via `sysctl`).

2. Core Features & Command Reference
The CLI runs as an interactive loop via `src/mlx_man/main.py` (accessible via `mlx-man`, `python -m mlx_man`, or `start_llm.sh`). The agent must understand and support the following core capabilities:
Run LLM Server: Users select a role (🧠 Reasoning, 🔨 Builder, ⚡ General), choose a curated model, and can start an OpenAI-compatible API server (port 8080) for tools like OpenCode, or an interactive chat session.
Clean Up RAM: An interactive memory cleaner that lists heavy running processes and allows users to forcefully close them to free up unified memory before running large models.
Manage Models: A model management console to browse installed models, inspect their detailed metadata (architecture, quantization, RAM estimate), download new models from HuggingFace, and delete models to reclaim disk space.
Insights & History: A dashboard view displaying historical model usage and session tracking.

3. UX Rules & Safety Guardrails
Destructive Actions: Any deletion request (e.g., removing a model or killing a process) must trigger a mandatory confirmation prompt before making system changes. Deleting models must safely clean up orphaned shared blobs and report exact disk space freed.
Interactive Navigation: Rely on `questionary` for menu selection and inputs rather than raw numeric inputs or command-line arguments. Use an Alternate Screen Buffer for the main UI to keep the terminal clean.
System Feedback: Use entertaining and informative progress indicators for long-running tasks like model pulling to prevent the user from thinking the process has stalled.
Apple Silicon Optimizations: Recommend and implement commands to increase the system's wired memory limit (`sudo sysctl iogpu.wired_limit_mb=N`) to maximize performance on macOS for models requiring more than the default ~21 GB limit.

4. Testing Requirements
Every feature requires comprehensive `pytest` coverage:
Domain Logic Tests: Verify cache scanning, size calculations, and orphaned blob detection in `src/mlx_man/model_manager.py`.
Safety Tests: Mock filesystem deletions and process kills to strictly verify that unconfirmed prompts abort safely and confirmed actions target the correct resources.
Rendering Tests: Use `rich.console.Console(record=True)` to assert that UI views (dashboards, tables) render without raising exceptions and that text formatting respects standard terminal widths.
Test Environment: Tests no longer need `sys.path` hacks thanks to `pyproject.toml` (which declares `pythonpath = ["src"]` and allows editable installation via `pip install -e '.[dev]'`).
