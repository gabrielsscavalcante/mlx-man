import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

HF_CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"
MODEL_DIR_PREFIX = "models--"

def get_model_cache_dir(model_id: str) -> Path:
    """Return the expected cache directory for a model ID or local absolute path."""
    if model_id.startswith("/"):
        return Path(model_id)
    dir_name = MODEL_DIR_PREFIX + model_id.replace("/", "--")
    return HF_CACHE_DIR / dir_name

def calculate_model_disk_size(model_dir: Path) -> int:
    """Calculate total disk usage for a model by following symlinks to real files."""
    if not model_dir.exists():
        return 0
    total = 0
    seen_inodes = set()
    for root, _dirs, files in os.walk(model_dir, followlinks=True):
        for fname in files:
            fpath = Path(root) / fname
            try:
                stat = fpath.stat()
                if stat.st_ino not in seen_inodes:
                    seen_inodes.add(stat.st_ino)
                    total += stat.st_size
            except OSError:
                pass
    return total

def _find_orphaned_shared_blobs(model_dir: Path) -> List[Path]:
    """Find shared blobs referenced ONLY by this model."""
    shared_blobs_dir = HF_CACHE_DIR / "blobs"
    if not shared_blobs_dir.exists():
        return []

    model_dir_name = model_dir.name
    orphaned = []

    for subdir in shared_blobs_dir.iterdir():
        if not subdir.is_dir():
            continue
        for item in subdir.iterdir():
            if not item.name.endswith(".refs"):
                continue
            try:
                refs_content = item.read_text().strip().splitlines()
                all_ours = all(
                    ref.strip().startswith(model_dir_name + "/")
                    for ref in refs_content
                    if ref.strip()
                )
                if all_ours and refs_content:
                    blob_file = item.with_suffix("")
                    if blob_file.exists():
                        orphaned.append(blob_file)
            except OSError:
                pass

    return orphaned

def delete_model_from_disk(model_id: str) -> int:
    """
    Deletes the model from the HF cache and cleans orphaned shared blobs.
    Returns the total bytes freed.
    """
    model_dir = get_model_cache_dir(model_id)
    if not model_dir.exists():
        return 0

    disk_size = calculate_model_disk_size(model_dir)
    orphaned_blobs = _find_orphaned_shared_blobs(model_dir)

    try:
        shutil.rmtree(model_dir)
    except OSError as e:
        raise RuntimeError(f"Failed to remove model directory: {e}")

    lock_dir = HF_CACHE_DIR / ".locks" / model_dir.name
    if lock_dir.exists():
        try:
            shutil.rmtree(lock_dir)
        except OSError:
            pass

    freed_shared = 0
    if orphaned_blobs:
        for blob_path in orphaned_blobs:
            try:
                blob_size = blob_path.stat().st_size
                blob_path.unlink()
                freed_shared += blob_size
                for suffix in [".lock", ".refs"]:
                    companion = blob_path.with_suffix(suffix)
                    if companion.exists():
                        companion.unlink()
                parent = blob_path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
            except OSError:
                pass

    return disk_size + freed_shared

def get_installed_models() -> List[Dict[str, Any]]:
    """Scan HF cache for installed MLX models and return basic info."""
    models = []
    if not HF_CACHE_DIR.exists():
        return models

    for model_dir in sorted(HF_CACHE_DIR.iterdir()):
        if not model_dir.is_dir() or not model_dir.name.startswith(MODEL_DIR_PREFIX):
            continue

        parts = model_dir.name[len(MODEL_DIR_PREFIX):].split("--")
        if len(parts) < 2:
            continue
        model_id = "/".join(parts)
        
        disk_bytes = calculate_model_disk_size(model_dir)
        models.append({
            "model_id": model_id,
            "model_dir": model_dir,
            "disk_bytes": disk_bytes
        })

    return models
