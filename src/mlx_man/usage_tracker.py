#!/usr/bin/env python3
"""
usage_tracker.py — Record and query model usage history.

Stores session data in ~/.config/mlx-man/usage_history.json (XDG-compliant).
Legacy data from the old project-root location is auto-migrated on first run.
"""

import json
import os
import datetime


# ─────────────────────────────────────────────────────────────────────────────
# XDG-compliant config directory
# ─────────────────────────────────────────────────────────────────────────────

def get_config_dir() -> str:
    """Return the MLX-Man config directory (~/.config/mlx-man on macOS).

    Respects XDG_CONFIG_HOME if set, otherwise defaults to ~/.config.
    Creates the directory if it doesn't exist.
    """
    config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    config_dir = os.path.join(config_home, "mlx-man")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def _migrate_legacy_history() -> None:
    """One-time migration: copy legacy .model_usage_history.json to new location.

    The old location was <project_root>/.model_usage_history.json.
    If that file exists and the new location doesn't, copy it over.
    """
    # Walk up from this file to find the project root (src/mlx_man/ -> src/ -> root)
    legacy_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', '..', '.model_usage_history.json'
    )
    legacy_path = os.path.normpath(legacy_path)
    new_path = os.path.join(get_config_dir(), "usage_history.json")
    if os.path.exists(legacy_path) and not os.path.exists(new_path):
        import shutil
        shutil.copy2(legacy_path, new_path)


# Resolve paths at module load time
HISTORY_FILE = os.path.join(get_config_dir(), "usage_history.json")
_migrate_legacy_history()


# ─────────────────────────────────────────────────────────────────────────────
# Data access
# ─────────────────────────────────────────────────────────────────────────────

def load_data() -> dict:
    """Load the usage history JSON file, returning an empty dict on any error."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_data(data: dict) -> None:
    """Persist the usage history dict to disk as formatted JSON."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)


def record_usage(model_id: str) -> None:
    """Record a single usage event for the given model."""
    data = load_data()
    if model_id not in data:
        data[model_id] = {"count": 0, "last_used": None}
    data[model_id]["count"] += 1
    data[model_id]["last_used"] = datetime.datetime.now().isoformat()
    save_data(data)


if __name__ == "__main__":  # pragma: no cover
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "record" and len(sys.argv) > 2:
            record_usage(sys.argv[2])
