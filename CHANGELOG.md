# Changelog

All notable changes to the MLX-Man project.

## [0.3.1] — 2026-09-24

### Changed
- **Project Renamed to MLX-Man** — Rebranded project as **MLX-Man** (Local MLX LLM Manager for Mac).
- **Clear Manager Positioning** — Updated main dashboard banner, subtitle, description, and rotating tips to explicitly clarify that MLX-Man is an Apple Silicon MLX model manager and runner (downloads and runs models, not an AI agent tool).
- **New ASCII Art Logo** — Designed a sleek, centered block-style ASCII art logo spelling **MLX-MAN**.

### Added
- **Role-Based Model Architecture** — Dedicated support for **🧠 Reasoning / Thinking** models (QwQ-32B, Qwen3-32B, DeepSeek-R1-Distill-32B, Phi-4-Reasoning+, Qwen3-14B) and **🔨 Builder / Coding** models (Qwen2.5-Coder-32B, Devstral-Small-24B, Codestral-22B, Qwen2.5-Coder-14B), while retaining existing models under **⚡ General Purpose**.
- **Role-First Server Workflow** — "Run LLM Server" now prompts for role first, then presents models filtered for that specific task with RAM estimates and recommendations.
- **Sequential Swap Guide** — Workflow pattern to run reasoning models for prompt/plan generation, then swap to builder models for code implementation within the 32 GB RAM budget.
- **Installation Status & In-Flow Downloads** — The server menu indicates which models are installed (`●`) vs not downloaded (`○`), with an option to download uninstalled models directly from the selection menu.
- **Model Inspector Role Indicators** — Model browse list and detail cards now show role tags (`🧠 Reasoning`, `🔨 Builder`, `⚡ General Purpose`).

### Changed
- `model_registry.py` expanded with 9 verified MLX model definitions, role tags, and helper functions (`get_models_by_role`, `ROLE_INFO`).
- `start_llm.sh` updated to dynamic role-based model listing and selection.
- Bumped `CLI_VERSION` to `0.3.0`.

### Fixed
- Bash 3.2 macOS compatibility: replaced bash 4+ case-conversion syntax with POSIX-compatible pattern matching.

## [0.2.0] — 2026-09-23

### Added
- **CLI Framework** — Professional terminal UI with branded header, ANSI colors, system dashboard (chip, RAM, GPU limit, macOS version), and `--help` flag.
- **Main Menu Loop** — Interactive command menu that returns to the home screen after each action (no need to relaunch the script).
- **Model Inspector** — Browse all installed MLX models with at-a-glance summary (disk size, RAM estimate, performance tier, quantization).
- **Model Detail Cards** — Full technical specs extracted from `config.json` (architecture, layers, hidden size, heads, vocabulary) plus curated descriptions, use cases, and configuration notes.
- **Model Download** — Download new models directly from a HuggingFace model ID or URL. Supports pasting full URLs or just the `org/model-name` format.
- **Model Deletion** — Safe deletion with confirmation, orphaned shared blob cleanup, and disk space reporting.
- **Model Registry** (`src/model_registry.py`) — Curated knowledge base for known models, serving as the single source of truth for descriptions, RAM estimates, and GPU requirements.
- **CLI UI Library** (`src/cli_ui.sh`) — Reusable shell functions for styled output, system info, and input validation.
- **Comprehensive Documentation** — Full rewrite of `Documentation.md` covering all commands, model management, and project structure.

### Changed
- `start_llm.sh` completely rewritten from sequential menu flow to command-based CLI with main menu loop.
- Model selection now uses color-coded tiers and descriptions.
- GPU memory limit selection improved with clearer descriptions per option.

### Fixed
- Script now validates the virtual environment and Python binary before starting.
- `set -euo pipefail` for safer shell execution.

## [0.1.0] — 2026-09-23

### Added
- Initial `start_llm.sh` launcher with sequential flow: RAM check → GPU limit → model selection → action.
- `memory_cleaner.py` for interactive process killing.
- Support for 4 models: Qwen 3.6 35B MoE, 27B 6-bit, 27B 4-bit, GPT-OSS 20B.
- OpenCode CLI integration via local OpenAI-compatible API server.
