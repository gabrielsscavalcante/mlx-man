import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from mlx_man.model_inspector import (
    run_model_inspector,
    _model_action_menu,
    download_model as dl_model,
    categorize_model,
    get_tier,
    get_tier_color,
    get_role_icon,
    discover_models,
    _extract_specs,
    ModelMetadata,
    build_model_metadata
)

@pytest.fixture
def dummy_meta():
    return ModelMetadata(
        name="model",
        repo_id="org/model",
        disk_gb=10.5,
        ram_estimate_gb=11.0,
        tier="Heavy",
        role="Reasoning",
        quant_details="4-bit",
        best_for="Testing",
        raw_info={}
    )

@patch("mlx_man.model_inspector.get_registry_entry")
def test_categorize_model(mock_get):
    # Registry overrides
    mock_get.return_value = {"role": "reasoning"}
    assert categorize_model("x/y") == "Reasoning"
    mock_get.return_value = {"role": "builder"}
    assert categorize_model("x/y") == "Builder"
    mock_get.return_value = {"role": "general"}
    assert categorize_model("x/y") == "General"
    
    # Fallback to string matching
    mock_get.return_value = None
    assert categorize_model("mlx-community/QwQ-32B-4bit") == "Reasoning"
    assert categorize_model("mlx-community/Qwen2.5-Coder-32B-Instruct-4bit") == "Builder"
    assert categorize_model("unknown/model") == "General"

def test_get_tier():
    assert get_tier(5) == "Light"
    assert get_tier(10) == "Medium"
    assert get_tier(20) == "Heavy"
    assert get_tier(35) == "Very Heavy"

def test_get_tier_color():
    assert get_tier_color("Light") == "green"
    assert get_tier_color("Medium") == "yellow"
    assert get_tier_color("Heavy") == "magenta"
    assert get_tier_color("Very Heavy") == "bold red"

def test_get_role_icon():
    assert get_role_icon("Reasoning") == "🧠"
    assert get_role_icon("Builder") == "⚒️"
    assert get_role_icon("General") == "⚡"

def test_extract_specs():
    config = {"architectures": ["LlamaForCausalLM"], "quantization_config": {"bits": 4, "group_size": 64}}
    specs = _extract_specs(config)
    assert specs["quantization"] == "4-bit g64"
    assert specs["architecture"] == "LlamaForCausalLM"
    assert specs["model_type"] == "unknown"

@patch("mlx_man.model_inspector.HF_CACHE_DIR")
def test_discover_models(mock_cache, tmp_path):
    mock_cache.exists.return_value = True
    model_dir = tmp_path / "models--org--model"
    model_dir.mkdir(parents=True)
    mock_cache.iterdir.return_value = [model_dir]
    models = discover_models()
    assert len(models) == 1
    assert models[0]["model_id"] == "org/model"
    assert "specs" in models[0]

@patch("mlx_man.model_inspector.HF_CACHE_DIR")
def test_discover_models_branches(mock_cache, tmp_path):
    mock_cache.exists.return_value = True
    
    # 1. not a dir
    f = tmp_path / "file"
    f.touch()
    
    # 2. invalid prefix
    d2 = tmp_path / "other--dir"
    d2.mkdir()
    
    # 3. parts < 2
    d3 = tmp_path / "models--org"
    d3.mkdir()
    
    # 4. JSON error
    d4 = tmp_path / "models--org--error"
    d4.mkdir(parents=True)
    sn4 = d4 / "snapshots" / "abc"
    sn4.mkdir(parents=True)
    cfg = sn4 / "config.json"
    cfg.write_text("{invalid")
    
    mock_cache.iterdir.return_value = [f, d2, d3, d4]
    models = discover_models()
    assert len(models) == 1  # only d4 is valid structure
    assert models[0]["model_id"] == "org/error"

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.model_inspector.discover_models")
def test_run_model_inspector_empty(mock_discover, mock_select, mock_foot):
    mock_discover.return_value = []
    mock_select.side_effect = ["back", None]
    run_model_inspector()
    mock_select.assert_called_once()

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_table_select")
@patch("mlx_man.model_inspector.discover_models")
@patch("mlx_man.model_inspector.download_model")
def test_run_model_inspector_download(mock_dl, mock_discover, mock_select, mock_foot):
    mock_discover.return_value = [{"model_id": "org/model", "disk_bytes": 100, "specs": {}}]
    mock_select.side_effect = ["download", None]
    run_model_inspector()
    mock_dl.assert_called_once()

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_table_select")
@patch("mlx_man.model_inspector.discover_models")
@patch("mlx_man.model_inspector._model_action_menu")
def test_run_model_inspector_select_model(mock_menu, mock_discover, mock_select, mock_foot):
    mock_discover.return_value = [{"model_id": "org/model", "disk_bytes": 100, "specs": {}}]
    def side_effect(*args, **kwargs):
        if mock_select.call_count == 1:
            return kwargs['data'][0]
        return None
    mock_select.side_effect = side_effect
    run_model_inspector()
    mock_menu.assert_called_once()

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
def test_model_action_menu_back(mock_select, mock_foot, dummy_meta):
    mock_select.return_value = None
    _model_action_menu(dummy_meta)

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.model_inspector.subprocess.run")
@patch("builtins.input", return_value="")
def test_model_action_menu_run(mock_input, mock_run, mock_select, mock_foot, dummy_meta):
    mock_select.side_effect = ["run", None]
    with patch("mlx_man.usage_tracker.record_usage"):
        _model_action_menu(dummy_meta)
    mock_run.assert_called_once()

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.server_manager.start_server")
@patch("builtins.input", return_value="")
def test_model_action_menu_serve(mock_input, mock_start, mock_select, mock_foot, dummy_meta):
    mock_select.side_effect = ["serve", None]
    with patch("mlx_man.usage_tracker.record_usage"):
        with patch("mlx_man.opencode_sync.sync_opencode_config"):
            _model_action_menu(dummy_meta)
    mock_start.assert_called_once_with('org/model')

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.model_inspector.tui_confirm")
@patch("mlx_man.model_inspector.delete_model_from_disk")
@patch("builtins.input", return_value="")
def test_model_action_menu_delete(mock_input, mock_del, mock_confirm, mock_select, mock_foot, dummy_meta):
    mock_select.side_effect = ["delete", None]
    mock_confirm.return_value = True
    mock_del.return_value = 1000
    _model_action_menu(dummy_meta)
    mock_del.assert_called_once()

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_text_input")
@patch("mlx_man.model_downloader.download_model")
@patch("builtins.input", return_value="")
def test_download_new_model(mock_input, mock_dl_core, mock_tui, mock_foot):
    mock_tui.return_value = "org/new"
    mock_dl_core.return_value = True
    dl_model()

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_text_input")
def test_download_new_model_cancel(mock_tui, mock_foot):
    mock_tui.return_value = None
    dl_model()

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.model_inspector.tui_confirm")
def test_model_action_menu_meta_no_specs(mock_confirm, mock_select, mock_foot, dummy_meta):
    mock_select.side_effect = ["meta", "back", None]
    _model_action_menu(dummy_meta)

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.model_inspector.tui_confirm")
def test_model_action_menu_meta_with_specs(mock_confirm, mock_select, mock_foot, dummy_meta):
    dummy_meta.raw_info = {"specs": {"architecture": "Llama", "hidden_size": 4096}}
    mock_select.side_effect = ["meta", "back", None]
    _model_action_menu(dummy_meta)

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.model_inspector.tui_confirm")
@patch("mlx_man.model_inspector.delete_model_from_disk", side_effect=Exception("Disk error"))
def test_model_action_menu_delete_error(mock_del, mock_confirm, mock_select, mock_foot, dummy_meta):
    mock_select.side_effect = ["delete", None]
    mock_confirm.return_value = True
    _model_action_menu(dummy_meta)

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_text_input")
@patch("mlx_man.model_inspector.tui_confirm")
@patch("builtins.input", return_value="")
def test_download_new_model_invalid(mock_input, mock_confirm, mock_tui, mock_foot):
    mock_tui.return_value = "invalid"
    dl_model()

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_text_input")
@patch("mlx_man.model_downloader.download_model", return_value=False)
@patch("mlx_man.model_inspector.tui_confirm")
@patch("builtins.input", return_value="")
def test_download_new_model_failed(mock_input, mock_confirm, mock_dl, mock_tui, mock_foot):
    mock_tui.return_value = "org/new"
    dl_model()

def test_extract_specs_branches():
    assert _extract_specs({}) == {"model_type": "unknown"}
    assert _extract_specs({"quantization": {"bits": 8, "group_size": 128}}) == {"quantization": "8-bit g128", "model_type": "unknown"}
    assert _extract_specs({"architectures": ["LlamaForCausalLM"]}) == {"architecture": "LlamaForCausalLM", "model_type": "unknown"}

def test_build_model_metadata():
    m = build_model_metadata({
        "model_id": "org/model",
        "disk_bytes": 1024**3 * 10,
        "registry": {"name": "Test", "best_for": ["Testing"]},
        "specs": {"quantization": "4-bit"}
    })
    assert m.name == "Test"
    
    m2 = build_model_metadata({
        "model_id": "org/unregistered",
        "disk_bytes": 1024**3 * 5,
        "specs": {}
    })
    assert m2.name == "unregistered"
    assert m2.quant_details == "Unknown"

@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.model_inspector.tui_table_select")
@patch("mlx_man.model_inspector.discover_models")
def test_run_model_inspector_filter(mock_discover, mock_select_table, mock_select_list):
    # org/model is "General" by default fallback
    mock_discover.return_value = [{"model_id": "org/model", "disk_bytes": 100, "specs": {}}]
    
    mock_select_table.side_effect = ["filter", "filter", None] 
    # Return "Reasoning", which filters it out -> empty! Then it returns "All", then shows table again
    mock_select_list.side_effect = ["Reasoning", "All", None]
    
    with patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer"):
        run_model_inspector()
    
    assert mock_select_list.call_count >= 1

@patch("mlx_man.model_inspector.tui_table_select")
@patch("mlx_man.model_inspector.discover_models")
def test_run_model_inspector_get_row(mock_discover, mock_select, dummy_meta):
    mock_discover.return_value = [{"model_id": "org/model", "disk_bytes": 100, "specs": {}}]
    
    def mock_table_select(*args, **kwargs):
        # Call get_row to test it
        row_func = kwargs["row_func"]
        data = kwargs["data"]
        row_func(data[0])
        return None

    mock_select.side_effect = mock_table_select
    with patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer"):
        run_model_inspector()

@patch("mlx_man.model_inspector.HF_CACHE_DIR")
def test_discover_models_branches(mock_cache, tmp_path):
    mock_cache.exists.return_value = True
    
    f = tmp_path / "file"
    f.touch()
    
    d2 = tmp_path / "other--dir"
    d2.mkdir()
    
    d3 = tmp_path / "models--org"
    d3.mkdir()
    
    d4 = tmp_path / "models--org--error"
    d4.mkdir(parents=True)
    sn4 = d4 / "snapshots" / "abc"
    sn4.mkdir(parents=True)
    cfg = sn4 / "config.json"
    cfg.write_text("{invalid")
    
    mock_cache.iterdir.return_value = [f, d2, d3, d4]
    models = discover_models()
    assert len(models) == 1

@patch("mlx_man.model_inspector.get_system_status_footer", return_value="footer")
@patch("mlx_man.model_inspector.tui_select")
@patch("mlx_man.model_inspector.subprocess.run", side_effect=KeyboardInterrupt)
@patch("builtins.input", return_value="")
def test_model_action_menu_serve_interrupt(mock_input, mock_run, mock_select, mock_foot, dummy_meta):
    mock_select.side_effect = ["serve", None]
    with patch("mlx_man.usage_tracker.record_usage"):
        with patch("mlx_man.opencode_sync.sync_opencode_config"):
            _model_action_menu(dummy_meta)

@patch("mlx_man.model_inspector.tui_text_input")
@patch("mlx_man.model_downloader.download_model", side_effect=KeyboardInterrupt)
@patch("builtins.input", return_value="")
def test_download_new_model_interrupt(mock_input, mock_dl, mock_tui):
    mock_tui.return_value = "org/model"
    dl_model()

@patch("mlx_man.model_inspector.tui_text_input")
@patch("mlx_man.model_downloader.download_model", side_effect=Exception("network err"))
@patch("builtins.input", return_value="")
def test_download_new_model_error(mock_input, mock_dl, mock_tui):
    mock_tui.return_value = "org/model"
    dl_model()

@patch("mlx_man.model_inspector.HF_CACHE_DIR")
def test_discover_models_no_cache(mock_cache):
    mock_cache.exists.return_value = False
    assert discover_models() == []
