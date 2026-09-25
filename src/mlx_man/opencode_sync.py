#!/usr/bin/env python3
"""
opencode_sync.py — Synchronize MLX-Man models with OpenCode CLI configuration.

Updates ~/.config/opencode/opencode.json so OpenCode always recognizes all installed
and registered MLX models, and sets the active model when the server starts.
"""

import json
import os
import sys
from pathlib import Path

from mlx_man.model_registry import MODEL_REGISTRY

OPENCODE_CONFIG = Path.home() / ".config" / "opencode" / "opencode.json"


def sync_opencode_config(active_model_id: str = None) -> bool:
    """Sync model registry into OpenCode configuration."""
    try:
        OPENCODE_CONFIG.parent.mkdir(parents=True, exist_ok=True)

        config = {}
        if OPENCODE_CONFIG.exists():
            try:
                with open(OPENCODE_CONFIG, "r") as f:
                    config = json.load(f)
            except Exception:
                config = {}

        config.setdefault("$schema", "https://opencode.ai/config.json")
        provider = config.setdefault("provider", {})
        mlx = provider.setdefault("mlx", {
            "npm": "@ai-sdk/openai-compatible",
            "name": "MLX (local)"
        })
        
        options = mlx.setdefault("options", {})
        options["baseURL"] = options.get("baseURL", "http://127.0.0.1:8080/v1")
        # Explicitly set 10-minute timeout (600,000 ms) for OpenCode/AI-SDK
        # This prevents BrokenPipeError during long prompt processing on 32B models
        options["timeout"] = 600000

        models = mlx.setdefault("models", {})
        # Ensure all registered models are present in OpenCode config
        for mid, entry in MODEL_REGISTRY.items():
            if mid not in models:
                models[mid] = {"name": entry.get("name", mid.split("/")[-1])}

        if active_model_id:
            config["model"] = f"mlx:{active_model_id}"

        with open(OPENCODE_CONFIG, "w") as f:
            json.dump(config, f, indent=2)
            f.write("\n")

        return True
    except Exception as e:
        print(f"Warning: Could not sync OpenCode config: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":  # pragma: no cover
    active = sys.argv[1] if len(sys.argv) > 1 else None
    sync_opencode_config(active)
