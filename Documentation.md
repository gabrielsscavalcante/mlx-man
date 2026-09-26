# MLX-Man — Local MLX LLM Manager for Mac

**MLX-Man** is a polished CLI tool for downloading, managing, and running local LLMs on macOS Apple Silicon using Apple's MLX framework. All models run **100% locally** — no code or prompts are ever sent to the internet.

> [!NOTE]
> **What is MLX-Man?** MLX-Man is an **MLX LLM manager and runner**, not an AI agent. It handles downloading models from HuggingFace, managing local disk storage and RAM optimization, and running models as interactive chat sessions or OpenAI-compatible local API servers (port 8080) that external coding tools and agents (such as OpenCode CLI) can connect to.

## Quick Start

```bash
cd mlx-man
mlx-man
```

> [!TIP]
> You can also launch MLX-Man using `./start_llm.sh` or `python -m mlx_man`.

---

## Recommended Workflow: Thinker → Builder Swap

On unified-memory Apple Silicon Macs (like 32 GB), running a large reasoning model and a large coding model simultaneously can exhaust unified memory. The optimal workflow runs one specialized model at a time:

```
┌─────────────────────────────────┐
│  Phase 1: Planning & Reasoning   │
│  Run 🧠 Reasoning Model (e.g. QwQ-32B)
│  - Understand project architecture
│  - Design implementation plans & prompts
└────────────────┬────────────────┘
                 │ (Ctrl+C to stop server)
                 ▼
┌─────────────────────────────────┐
│  Phase 2: Code Implementation   │
│  Run 🔨 Builder Model (e.g. Qwen2.5-Coder-32B)
│  - Feed the plan to OpenCode CLI
│  - Implement, refactor, and test
└─────────────────────────────────┘
```

---

## Commands

The CLI presents an interactive main menu with a system dashboard showing your chip, RAM, GPU limit, and macOS version.

### [1] Run LLM Server

Start a local model as an OpenAI-compatible API server or interactive chat session.

**Flow:**
1. **GPU Memory Limit** — Optionally raise the macOS GPU limit (e.g., 26 GB recommended for 32B models, or skip for lighter models).
2. **Choose a Role:**
   - **🧠 Reasoning / Thinking** — Models optimized for step-by-step reasoning, architectural planning, and prompt design.
   - **🔨 Builder / Coding** — Models specialized for code generation, multi-file refactoring, and SWE agent workflows.
   - **⚡ General Purpose** — Well-rounded models suitable for both coding and general dialogue.
3. **Model Selection** — Pick from curated models for that role. Models show installation status (`●` installed, `○` not downloaded). If not downloaded, you can trigger a download directly.
4. **Action** — Start the API server on `localhost:8080` (for OpenCode CLI) or launch an interactive terminal chat.

### [2] Clean Up RAM

Interactive memory cleaner that lists heavy running processes sorted by RAM usage. Select processes to forcefully close and free memory before running large models.

Aim for:
- ~8 GB free for 14B models (e.g. Qwen3-14B, Qwen2.5-Coder-14B, Phi-4)
- ~14–18 GB free for 24B–32B 4-bit models (e.g. QwQ-32B, Qwen2.5-Coder-32B)
- ~22–24 GB free for heavy models (e.g. 27B 6-bit, 35B MoE)

### [3] Manage Models

Full model management console:

- **Browse** — See all installed models with disk size, RAM estimate, performance tier, role tag, and quantization info at a glance.
- **Inspect** — Select a model to view its full detail card: architecture, quantization, hidden size, layers, vocabulary, curated description, role, use cases, and configuration notes.
- **Download** — Download new models from HuggingFace by pasting a model ID or URL.
- **Delete** — Remove models you no longer need. The CLI safely cleans up shared blob files and reports exact disk space freed. Requires typing the model name to confirm.

---

## Curated Models & Roles

### 🧠 Reasoning / Thinking Models
*Best for project planning, prompt engineering, multi-step problem solving, and architecture design.*

| Model | HuggingFace Repo | RAM | Tier | Highlights |
|-------|------------------|-----|------|------------|
| **QwQ 32B (4-bit)** | `mlx-community/QwQ-32B-4bit` | ~18 GB | Heavy | ⭐ Top open reasoning model; deep chain-of-thought |
| **Qwen3 32B (4-bit)** | `mlx-community/Qwen3-32B-4bit` | ~18 GB | Heavy | Dual-mode thinking/fast toggle; 32K–131K context |
| **DeepSeek R1 Distill 32B (4-bit)** | `mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit` | ~18 GB | Heavy | Methodical step-by-step problem breakdown |
| **Phi-4 Reasoning Plus (4-bit)** | `mlx-community/Phi-4-reasoning-plus-4bit` | ~8 GB | Light | Fast reasoning with low memory footprint |
| **Qwen3 14B (4-bit)** | `mlx-community/Qwen3-14B-4bit` | ~8 GB | Light | Lightweight thinking mode, fast planning |

### 🔨 Builder / Coding Models
*Best for code generation, multi-file refactoring, debugging, and implementation.*

| Model | HuggingFace Repo | RAM | Tier | Highlights |
|-------|------------------|-----|------|------------|
| **Qwen2.5 Coder 32B (4-bit)** | `mlx-community/Qwen2.5-Coder-32B-Instruct-4bit` | ~18 GB | Heavy | ⭐ Top open coding model; 128K context |
| **Devstral Small 24B (4-bit)** | `mlx-community/Devstral-Small-2507-4bit` | ~14 GB | Medium | Mistral agentic coder fine-tuned for SWE tasks |
| **Codestral 22B (4-bit)** | `mlx-community/Codestral-22B-v0.1-4bit` | ~12 GB | Light | 80+ programming languages, code completion |
| **Qwen2.5 Coder 14B (4-bit)** | `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` | ~8 GB | Light | Fast implementation, low RAM |

### ⚡ General Purpose Models
*Balanced models that perform well across both reasoning and implementation.*

| Model | HuggingFace Repo | RAM | Tier | Highlights |
|-------|------------------|-----|------|------------|
| **Qwen 3.6 35B-A3B MoE (4-bit)** | `mlx-community/Qwen3.6-35B-A3B-4bit` | ~24 GB | Very Heavy | 35B reasoning depth with sparse 3B latency |
| **Qwen 3.6 27B (6-bit)** | `mlx-community/Qwen3.6-27B-6bit` | ~22 GB | Heavy | Near-FP16 quality coding & analysis |
| **Qwen 3.6 27B (4-bit)** | `mlx-community/Qwen3.6-27B-4bit` | ~14 GB | Light | Excellent daily driver balance |
| **GPT-OSS 20B (MXFP4-Q8)** | `mlx-community/gpt-oss-20b-MXFP4-Q8` | ~12 GB | Light | Efficient mixed-precision, low footprint |

---

## OpenCode CLI Integration

When you select "Start API Server", the model hosts an OpenAI-compatible endpoint at `http://127.0.0.1:8080/v1`. Your `~/.config/opencode/opencode.json` is configured to automatically detect this local server.

Just open a new terminal tab and run `opencode` while the server is running.

### [4] Run Benchmark
Benchmark any installed model on-device to measure real-world Tokens Per Second (t/s) and Time to First Token (TTFT) on your specific Apple Silicon chip. Results are automatically recorded and displayed on the Insights Speed Leaderboard.

### [5] Quantize Model
Compress and convert any standard Hugging Face model directly on-device using MLX quantization (4-bit, 6-bit, or 8-bit), optimizing it for your available RAM.

### [6] Native Chat (Agentic & RAG)
Interactive terminal chat with full local history:
- **Agentic Mode**: The model can use built-in tools (`read_file`, `list_directory`, `get_time`) to examine your workspace, always gated by an explicit security permission prompt (`Allow? [Y/n]`).
- **Local RAG Mode**: Index local folders and codebases with zero external vector database dependencies to automatically inject relevant file chunks into conversation context.
- **LoRA Adapter Support**: Attach custom fine-tuned weights directly when launching chat or servers.

---

## Release & Distribution Guide

MLX-Man uses standard Semantic Versioning (`vMAJOR.MINOR.PATCH`) and automated release delivery:

### 1. Release Automation (`scripts/release.sh`)
Releases must be cut exclusively on the `main` branch with clean working trees:
```bash
# Validate, bump version, run tests, and create git tag:
./scripts/release.sh patch   # or minor, major, or specific version x.y.z
```

### 2. GitHub Release Delivery (`.github/workflows/release.yml`)
When a tag (e.g. `v0.5.0`) is pushed to GitHub:
1. GitHub Actions runs verification on Python 3.12.
2. Builds the source distribution (`.tar.gz`) and binary wheel (`.whl`).
3. Publishes an official GitHub Release with release notes and downloadable assets.

### 3. User Installation Channels
- **Instant (zero install)**: `uvx mlx-man`
- **Global isolated install**: `pipx install mlx-man`
- **Local editable install**: `pip install -e '.[dev]'`

---

## Project Structure

```
mlx-man/
├── pyproject.toml            # Modern Python packaging configuration (Hatchling)
├── Makefile                  # Developer workflow targets (install, test, lint, run)
├── start_llm.sh              # Shell launcher script (resolves Python & .venv)
├── scripts/
│   └── release.sh            # Automated release & tagging script
├── Documentation.md          # In-depth architectural & usage documentation
├── CONTRIBUTING.md           # Contributor guidelines
├── CHANGELOG.md              # Version history
├── LICENSE                   # MIT License
├── src/
│   └── mlx_man/
│       ├── __init__.py       # Centralized package version string
│       ├── __main__.py       # Direct execution via `python -m mlx_man`
│       ├── main.py           # Main CLI loop & alternate screen buffer
│       ├── tui_engine.py     # Spotlight-style raw terminal TUI engine
│       ├── cli_dashboard.py  # Hardware detection, status badges, & rotating tips
│       ├── cli_actions.py    # Subsystem action handlers (quantize, benchmark, chat)
│       ├── model_registry.py # Single source of truth for models & roles
│       ├── model_manager.py  # HF cache scanner, size calculator, safe deleter
│       ├── model_inspector.py # Model browser, spec cards, downloader
│       ├── model_downloader.py # Dedicated secure Hugging Face downloader
│       ├── rag_engine.py     # Pure-Python zero-dependency BM25 RAG indexer
│       ├── tools.py          # Safe read-only agentic tools for native chat
│       ├── native_chat_view.py # Terminal chat, agentic loop, and RAG integration
│       ├── server_manager.py # Background multi-server lifecycle manager
│       ├── server_dashboard_view.py # Multi-server monitoring dashboard
│       ├── process_service.py # Process monitoring service for RAM management
│       ├── ram_manager_view.py # Memory cleaner UI with process termination
│       ├── usage_tracker.py  # Local usage recording and session statistics
│       └── insights_view.py  # Historical analytics & Benchmark Speed Leaderboard
└── tests/
    ├── conftest.py           # Shared test fixtures & mocks
    ├── test_setup.py         # Packaging, importability, & XDG compliance tests
    ├── test_tools.py         # Agentic tools unit tests
    ├── test_rag_engine.py    # BM25 RAG indexer tests
    ├── test_server_manager.py # Multi-server lifecycle tests
    ├── test_ui_snapshots.py  # 15 Rich console UI snapshot tests
    └── ...                   # Full 320-test 100% coverage suite
```

---

## GPU Memory Limit Reference

| Setting | Limit | Command |
|---------|-------|---------|
| Default | ~21 GB | *(no action needed)* |
| 26 GB (recommended) | 26 GB | `sudo sysctl iogpu.wired_limit_mb=26624` |
| 28 GB (max) | 28 GB | `sudo sysctl iogpu.wired_limit_mb=28672` |

> **Note:** The GPU limit resets after reboot. The CLI offers to set it each time you run a server.

---

## Requirements

- macOS with Apple Silicon (M-series chip: M1 through M6 tested)
- Python 3.9+ (system Python or Homebrew)
- Dependencies managed via `pyproject.toml` (install via `pip install -e .` or `uv pip install -e .`)
