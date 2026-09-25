"""Shared test fixtures for MLX-Man test suite."""

import pytest


@pytest.fixture
def mock_hf_cache(tmp_path):
    """Create a temporary HuggingFace cache directory structure for testing."""
    cache_dir = tmp_path / "huggingface" / "hub"
    cache_dir.mkdir(parents=True)
    return cache_dir


@pytest.fixture
def mock_config_dir(tmp_path):
    """Create a temporary MLX-Man config directory for testing."""
    config_dir = tmp_path / "mlx-man"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def rich_console():
    """Create a Rich console that records output for assertions."""
    from rich.console import Console
    return Console(record=True, width=120, force_terminal=True)
