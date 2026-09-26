import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import datetime

from mlx_man.insights_view import (
    ModelInfo,
    gather_models,
    generate_bar,
    get_insights_view,
    render_insights_view,
    run_insights_history
)

@pytest.fixture
def dummy_model():
    return ModelInfo(
        name="Test",
        repo_id="org/test",
        size_gb=10.0,
        times_used=5,
        last_used=datetime.datetime(2023, 1, 1),
        category="Reasoning"
    )

@pytest.fixture
def models_list(dummy_model):
    return [dummy_model]

@patch("mlx_man.insights_view.get_installed_models")
@patch("mlx_man.insights_view.load_usage_data")
def test_gather_models(mock_load, mock_get):
    mock_get.return_value = [{"model_id": "org/test", "disk_bytes": 10**9}]
    mock_load.return_value = {
        "org/test": {"count": 3, "last_used": "2023-01-01T10:00:00"}
    }
    models = gather_models()
    assert len(models) == 1
    assert models[0].times_used == 3
    assert models[0].last_used.year == 2023

@patch("mlx_man.insights_view.get_installed_models")
@patch("mlx_man.insights_view.load_usage_data")
def test_gather_models_bad_date(mock_load, mock_get):
    mock_get.return_value = [{"model_id": "org/test", "disk_bytes": 10**9}]
    mock_load.return_value = {
        "org/test": {"count": 3, "last_used": "invalid-date"}
    }
    models = gather_models()
    assert models[0].last_used is None

def test_generate_bar():
    # zero total
    assert "░░░░░░░░░░░░░░░░░░░░" in generate_bar(5, 0, width=20)
    # normal
    bar = generate_bar(5, 10, width=10)
    assert bar.count("█") == 5
    assert bar.count("░") == 5
    # overflow
    bar = generate_bar(15, 10, width=10)
    assert bar.count("█") == 10
    
def test_get_insights_view(models_list):
    group = get_insights_view(models_list)
    assert group is not None
    
    # Test empty
    group_empty = get_insights_view([])
    assert group_empty is not None

def test_render_insights_view(models_list):
    with patch("mlx_man.insights_view.console.print") as mock_print:
        render_insights_view(models_list)
        mock_print.assert_called_once()

@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_select")
def test_run_insights_history_empty(mock_select, mock_gather):
    mock_gather.return_value = []
    mock_select.return_value = "back"
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_insights_history()
    
    mock_select.assert_called_once()

@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_table_select")
def test_run_insights_history_back(mock_select, mock_gather, models_list):
    mock_gather.return_value = models_list
    mock_select.return_value = "back"
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_insights_history()

@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_table_select")
@patch("mlx_man.insights_view.tui_select")
def test_run_insights_history_filter(mock_select_list, mock_select_table, mock_gather, models_list):
    mock_gather.return_value = models_list
    mock_select_table.side_effect = ["filter", None]
    mock_select_list.side_effect = ["Build", None]
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_insights_history()

@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_table_select")
@patch("mlx_man.insights_view.tui_confirm")
@patch("mlx_man.insights_view.delete_model_from_disk")
@patch("mlx_man.insights_view.tui_select")
def test_run_insights_history_delete(mock_select, mock_del, mock_confirm, mock_table, mock_gather, dummy_model):
    mock_gather.return_value = [dummy_model]
    mock_table.side_effect = [dummy_model, None]
    mock_confirm.return_value = True
    mock_del.return_value = 1000
    mock_select.return_value = "continue"
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_insights_history()

@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_table_select")
@patch("mlx_man.insights_view.tui_confirm")
@patch("mlx_man.insights_view.delete_model_from_disk", side_effect=Exception("Err"))
@patch("mlx_man.insights_view.tui_select")
def test_run_insights_history_delete_err(mock_select, mock_del, mock_confirm, mock_table, mock_gather, dummy_model):
    mock_gather.return_value = [dummy_model]
    mock_table.side_effect = [dummy_model, None]
    mock_confirm.return_value = True
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_insights_history()

@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_table_select")
def test_run_insights_history_get_row(mock_table, mock_gather, dummy_model):
    mock_gather.return_value = [dummy_model]
    
    def side_effect(*args, **kwargs):
        rf = kwargs["row_func"]
        d = kwargs["data"][0]
        rf(d)
        
        # Test edge case: zero times_used
        d_zero = ModelInfo(
            name="Zero",
            repo_id="org/zero",
            size_gb=1.0,
            times_used=0,
            last_used=None,
            category="Reasoning"
        )
        rf(d_zero)
        return None
        
    mock_table.side_effect = side_effect
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_insights_history()

from mlx_man.insights_view import categorize_model, get_category_color

@patch("mlx_man.insights_view.get_registry_entry")
def test_categorize_model_branches(mock_reg):
    mock_reg.return_value = {"role": "reasoning"}
    assert categorize_model("x") == "Reasoning"
    mock_reg.return_value = {"role": "builder"}
    assert categorize_model("x") == "Build"
    mock_reg.return_value = {"role": "general"}
    assert categorize_model("x") == "General"
    
    mock_reg.return_value = None
    assert categorize_model("mlx-community/QwQ-32B-4bit") == "Reasoning"
    assert categorize_model("mlx-community/Qwen2.5-Coder-32B-Instruct-4bit") == "Build"
    assert categorize_model("unknown/model") == "General"

def test_get_category_color_branches():
    assert get_category_color("Reasoning") == "magenta"
    assert get_category_color("Build") == "blue"
    assert get_category_color("General") == "green"

from mlx_man.insights_view import load_usage_data

@patch("mlx_man.insights_view.DATA_FILE", "/tmp/nonexistent.json")
def test_load_usage_data_missing():
    assert load_usage_data() == {}

@patch("mlx_man.insights_view.DATA_FILE", "/tmp/bad.json")
def test_load_usage_data_bad():
    Path("/tmp/bad.json").write_text("{invalid")
    assert load_usage_data() == {}
    
@patch("mlx_man.insights_view.DATA_FILE", "/tmp/good.json")
def test_load_usage_data_good():
    Path("/tmp/good.json").write_text('{"test": {"count": 1}}')
    assert load_usage_data() == {"test": {"count": 1}}

@patch("mlx_man.insights_view.Path.home")
def test_get_insights_view_with_benchmarks(mock_home, tmp_path):
    from mlx_man.insights_view import get_insights_view
    import json
    
    mock_home.return_value = tmp_path
    bench_dir = tmp_path / ".config" / "mlx-man"
    bench_dir.mkdir(parents=True)
    bench_file = bench_dir / "benchmarks.json"
    
    bench_data = [
        {"model_id": "org/model", "hardware": "M2 Max", "ttft_s": 0.5, "tps": 40.5, "date": "2026-09-26"}
    ]
    with open(bench_file, "w") as f:
        json.dump(bench_data, f)
        
    group = get_insights_view([])
    # Check that it didn't crash and returns a Group
    assert group is not None

@patch("mlx_man.insights_view.Path.home")
def test_get_insights_view_with_benchmarks_invalid_json(mock_home, tmp_path):
    from mlx_man.insights_view import get_insights_view
    
    mock_home.return_value = tmp_path
    bench_dir = tmp_path / ".config" / "mlx-man"
    bench_dir.mkdir(parents=True)
    bench_file = bench_dir / "benchmarks.json"
    bench_file.write_text("invalid json")
        
    group = get_insights_view([])
    assert group is not None
