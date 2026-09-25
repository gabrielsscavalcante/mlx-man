import pytest
from unittest.mock import patch
from mlx_man.hardware_recommender import estimate_ram, get_hardware_recommendation

def test_estimate_ram():
    assert round(estimate_ram("mlx-community/Qwen2.5-7B-Instruct-4bit"), 1) == 4.2
    assert round(estimate_ram("mlx-community/QwQ-32B-4bit"), 1) == 19.2
    assert estimate_ram("unknown-model-without-params") == 0

@patch("mlx_man.hardware_recommender.get_total_ram_gb", return_value=16)
def test_get_hardware_recommendation(mock_ram):
    badge, style = get_hardware_recommendation("mlx-community/Qwen2.5-7B-Instruct-4bit")
    assert "Great Match" in badge
    assert style == "bold green"
    
    badge, style = get_hardware_recommendation("mlx-community/QwQ-14B-6bit")
    assert "Paging Risk" in badge
    assert style == "bold yellow"
    
    badge, style = get_hardware_recommendation("mlx-community/QwQ-32B-4bit")
    assert "Will OOM" in badge
    assert style == "bold red"
    
    badge, style = get_hardware_recommendation("unknown")
    assert "Unknown" in badge
