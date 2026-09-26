#!/usr/bin/env python3
"""
model_downloader.py — Download HuggingFace MLX models with progress reporting.

Uses huggingface_hub.snapshot_download to download models into the standard
HuggingFace cache directory (~/.cache/huggingface/hub).

Usage:
    python3 model_downloader.py <model-id-or-url>
"""

import sys
import os

def download_model(model_id_or_url: str) -> bool:
    """Download a model from Hugging Face by repo ID or URL."""
    # Clean up model input
    model_id = model_id_or_url.strip()
    if model_id.startswith("https://huggingface.co/"):
        model_id = model_id.replace("https://huggingface.co/", "")
    model_id = model_id.strip("/")

    if "/" not in model_id:
        print(f"Error: Invalid model ID '{model_id}'. Expected format: organization/model-name", file=sys.stderr)
        return False

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        try:
            from mlx_lm.utils import get_model_path
            print(f"Starting download for {model_id} via mlx_lm...")
            get_model_path(model_id)
            return True
        except ImportError:
            print("Error: Neither huggingface_hub nor mlx_lm is installed in the current environment.", file=sys.stderr)
            return False

    print(f"Connecting to Hugging Face Hub...")
    print(f"Downloading model: {model_id}")
    print("Files will be cached in ~/.cache/huggingface/hub/\n")

    try:
        snapshot_download(
            repo_id=model_id,
            resume_download=True,
            allow_patterns=[
                "*.safetensors",
                "*.safetensors.index.json",
                "*.json",
                "*.model",
                "*.tiktoken",
                "*.txt",
                "*.md"
            ]
        )
        print(f"\n✔ Successfully downloaded '{model_id}'!")
        return True
    except KeyboardInterrupt:
        print(f"\n⚠ Download interrupted by user.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n✖ Download failed: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: model_downloader.py <model-id-or-url>")
        sys.exit(1)

    success = download_model(sys.argv[1])
    sys.exit(0 if success else 1)
