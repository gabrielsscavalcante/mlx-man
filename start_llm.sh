#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# MLX-Man — start_llm.sh
# Minimal wrapper to launch the Python-based Terminal UI.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 1. Check repo-local .venv
if [ -f "$SCRIPT_DIR/.venv/bin/python3" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python3"
# 2. Check MLX_VENV custom environment variable
elif [ -n "${MLX_VENV:-}" ] && [ -f "$MLX_VENV/bin/python3" ]; then
    PYTHON="$MLX_VENV/bin/python3"
# 3. Check currently active virtual environment
elif [ -n "${VIRTUAL_ENV:-}" ] && [ -f "$VIRTUAL_ENV/bin/python3" ]; then
    PYTHON="$VIRTUAL_ENV/bin/python3"
# 4. Fallback to legacy path if present
elif [ -f "/Users/gabrielcavalcante/opencode_mlx_qwen/.venv/bin/python3" ]; then
    PYTHON="/Users/gabrielcavalcante/opencode_mlx_qwen/.venv/bin/python3"
# 5. Check if system python3 has required dependencies
elif command -v python3 &>/dev/null && python3 -c "import mlx_lm, rich, questionary, psutil" &>/dev/null; then
    PYTHON="python3"
else
    echo "================================================================="
    echo "  MLX-Man — Local MLX LLM Manager for Apple Silicon"
    echo "================================================================="
    echo "Error: No Python environment with MLX-Man dependencies was found."
    echo ""
    echo "To set up a virtual environment in this directory, run:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    echo "Or set MLX_VENV to point to an existing venv:"
    echo "  export MLX_VENV=/path/to/your/venv"
    echo "================================================================="
    exit 1
fi

# Pass control completely to the Python UI
exec "$PYTHON" "$SCRIPT_DIR/src/main.py" "$@"
