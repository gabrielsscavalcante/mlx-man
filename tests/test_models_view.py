import pytest
from unittest.mock import patch, MagicMock
from rich.console import Console

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from model_inspector import (
    ModelMetadata,
    categorize_model,
    get_tier,
    build_model_metadata,
    render_model_manager,
    run_model_inspector,
)

def test_tier_assignment():
    assert get_tier(8.0) == "Light"
    assert get_tier(9.9) == "Light"
    assert get_tier(10.0) == "Medium"
    assert get_tier(15.0) == "Medium"
    assert get_tier(16.0) == "Medium"
    assert get_tier(17.0) == "Heavy"
    assert get_tier(24.0) == "Heavy"
    assert get_tier(25.0) == "Very Heavy"

def test_category_heuristics():
    # Test Devstral
    assert categorize_model("mlx-community/Devstral-Small-2507-4bit") == "Builder"
    # Test QwQ
    assert categorize_model("mlx-community/QwQ-32B-4bit") == "Reasoning"
    # Test Qwen 3.6
    assert categorize_model("mlx-community/Qwen3.6-27B-4bit") == "General"

@patch('model_inspector.questionary.select')
@patch('model_inspector._model_action_menu')
@patch('model_inspector.download_model')
@patch('model_inspector.discover_models')
def test_interactive_action_routing(mock_discover, mock_download, mock_action_menu, mock_select):
    # Mocking discover_models to return a dummy model
    mock_discover.return_value = [{
        "model_id": "dummy/model",
        "disk_bytes": 1024 * 1024 * 1024 * 5, # 5 GB
        "specs": {},
    }]
    
    # Simulate selecting a model to inspect, then back
    mock_select.return_value.ask.side_effect = ["inspect", "cancel", "download", "back"]
    
    # We also mock questionary inside the 'inspect' option
    # Actually, the 'inspect' option triggers another questionary.select
    with patch('model_inspector.questionary.select') as mock_inner_select:
        # 1. Main menu: 'inspect'
        # 2. Inner menu (model selection): returns a ModelMetadata
        # 3. Then it continues the main loop
        # 4. Main menu: 'cancel' doesn't exist, we mapped 'inspect' inner 'cancel', wait.
        pass

    # Let's simplify the mock side effects specifically for run_model_inspector
    mock_select.return_value.ask.side_effect = [
        "inspect", # main menu
        "cancel",  # inner model select menu (wait, they both use questionary.select, so the same mock is called)
        "download",# main menu
        "back"     # main menu
    ]
    
    run_model_inspector()
    
    assert mock_download.called
    assert not mock_action_menu.called
    
    # Let's test actual model routing
    mock_select.return_value.ask.side_effect = [
        "inspect",
        "dummy_model", # inner select
        "back"
    ]
    
    # we need the inner select to return something truthy for model, but we mocked questionary.select entirely
    # which returns a mock whose ask() returns strings. If we return a ModelMetadata object, it goes to action_menu
    dummy_meta = build_model_metadata(mock_discover.return_value[0])
    mock_select.return_value.ask.side_effect = [
        "inspect",
        dummy_meta,
        "back"
    ]
    
    run_model_inspector()
    mock_action_menu.assert_called_with(dummy_meta)

def test_table_and_badge_rendering():
    console = Console(record=True, width=120)
    
    models = [
        ModelMetadata(
            name="QwQ 32B (4-bit)",
            repo_id="mlx-community/QwQ-32B-4bit",
            disk_gb=18.0,
            ram_estimate_gb=19.0,
            tier="Heavy",
            role="Reasoning",
            quant_details="4-bit",
            best_for="Reasoning",
            raw_info={}
        ),
        ModelMetadata(
            name="Devstral Small 24B",
            repo_id="mlx-community/Devstral-Small-2507-4bit",
            disk_gb=14.0,
            ram_estimate_gb=15.0,
            tier="Medium",
            role="Builder",
            quant_details="4-bit",
            best_for="Coding",
            raw_info={}
        ),
        ModelMetadata(
            name="Qwen 3.6 27B",
            repo_id="mlx-community/Qwen3.6-27B-4bit",
            disk_gb=14.0,
            ram_estimate_gb=15.0,
            tier="Medium",
            role="General",
            quant_details="4-bit",
            best_for="General usage",
            raw_info={}
        )
    ]
    
    with patch('model_inspector.render_page') as mock_render:
        render_model_manager(models)
        
    group = mock_render.call_args[0][0]
    console.print(group)
    output = console.export_text()
    
    # Check no exceptions and text rendered correctly
    assert "QwQ 32B" in output
    assert "Devstral Small 24B" in output
    assert "Qwen 3.6 27B" in output
    
    # Check Role emojis
    assert "🧠" in output
    assert "⚒️" in output
    assert "⚡" in output
    
    # Check Tier labels
    assert "Heavy" in output
    assert "Medium" in output
