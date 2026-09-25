from mlx_man.model_registry import (
    get_registry_entry_fuzzy,
    get_all_known_model_ids,
    get_models_by_role,
    get_all_roles,
    get_registry_entry
)

def test_get_registry_entry_fuzzy():
    # Test valid
    entry = get_registry_entry_fuzzy("qwq")
    assert entry is not None
    assert "QwQ" in entry["name"]
    
    # Test invalid
    assert get_registry_entry_fuzzy("doesnotexist999") is None

def test_get_all_known_model_ids():
    ids = get_all_known_model_ids()
    assert len(ids) > 10
    assert "mlx-community/QwQ-32B-4bit" in ids

def test_get_models_by_role():
    reasoning = get_models_by_role("reasoning")
    assert len(reasoning) > 0
    assert "mlx-community/QwQ-32B-4bit" in reasoning
    
    empty = get_models_by_role("nonexistent_role")
    assert len(empty) == 0

def test_get_all_roles():
    roles = get_all_roles()
    assert "reasoning" in roles
    assert "builder" in roles
    assert "general" in roles

def test_get_registry_entry():
    assert get_registry_entry("mlx-community/QwQ-32B-4bit") is not None
    assert get_registry_entry("invalid") is None

import os
import json
from unittest.mock import patch, MagicMock
from mlx_man.model_registry import load_custom_models, register_custom_model, MODEL_REGISTRY, CUSTOM_MODELS_FILE

@patch("os.path.exists", return_value=True)
def test_load_custom_models(mock_exists, tmp_path):
    custom_models = {
        "custom/model": {"name": "Custom Model"}
    }
    with patch("builtins.open", MagicMock()) as mock_open:
        handle = MagicMock()
        handle.read.return_value = json.dumps(custom_models)
        handle.__enter__.return_value = handle
        mock_open.return_value = handle
        
        with patch("json.load", return_value=custom_models):
            load_custom_models()
            
    assert "custom/model" in MODEL_REGISTRY
    assert MODEL_REGISTRY["custom/model"]["is_custom"] is True
    assert MODEL_REGISTRY["custom/model"]["role"] == "general"

@patch("os.path.exists", return_value=True)
def test_register_custom_model(mock_exists):
    custom_models = {}
    with patch("builtins.open", MagicMock()) as mock_open:
        with patch("json.load", return_value=custom_models):
            with patch("json.dump") as mock_dump:
                register_custom_model("new/model", "New Model")
                assert "new/model" in MODEL_REGISTRY
                
                # Check dump was called
                mock_dump.assert_called_once()
                args, _ = mock_dump.call_args
                dumped_dict = args[0]
                assert "new/model" in dumped_dict
                assert dumped_dict["new/model"]["name"] == "New Model"

@patch("os.path.exists", return_value=True)
def test_load_custom_models_exception(mock_exists):
    with patch("builtins.open", MagicMock()) as mock_open:
        with patch("json.load", side_effect=Exception("error")):
            load_custom_models()

@patch("os.path.exists", return_value=True)
def test_register_custom_model_exception(mock_exists):
    with patch("builtins.open", MagicMock()) as mock_open:
        with patch("json.load", side_effect=Exception("error")):
            with patch("json.dump"):
                register_custom_model("new", "new")
