import datetime
from unittest.mock import patch, MagicMock

from mlx_man.insights_view import (
    categorize_model,
    ModelInfo,
    render_insights_view,
    run_insights_history
)
from mlx_man.model_manager import delete_model_from_disk
from rich.console import Console


def test_categorize_model():
    assert categorize_model("mlx-community/QwQ-32B-4bit") == "Reasoning"
    assert categorize_model("mlx-community/Devstral-Small-2507-4bit") == "Build"
    assert categorize_model("mlx-community/Qwen3.6-27B-4bit") == "General"

    assert categorize_model("unknown/super-R1-model") == "Reasoning"
    assert categorize_model("unknown/deepseek-coder-v2") == "Build"
    assert categorize_model("unknown/Llama-3-8b") == "General"


def test_rendering():
    models = [
        ModelInfo(
            name="Test Model 1",
            repo_id="test/model-1",
            size_gb=10.5,
            times_used=0,
            last_used=None,
            category="Reasoning"
        ),
        ModelInfo(
            name="Test Model 2",
            repo_id="test/model-2",
            size_gb=5.0,
            times_used=5,
            last_used=datetime.datetime(2023, 10, 1),
            category="General"
        )
    ]

    with patch("mlx_man.insights_view.console", Console(record=True)) as mock_console:
        render_insights_view(models)

        output = mock_console.export_text()

        assert "Test Model 1" in output
        assert "Test Model 2" in output
        assert "Reasoning" in output
        assert "General" in output
        assert "15.5 GB" in output
        assert "🏆 Most Used Model: Test Model 2" in output
        assert "Usage Distribution by Category" in output


@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.delete_model_from_disk")
@patch("mlx_man.insights_view.tui_select")
@patch("mlx_man.insights_view.tui_confirm")
def test_deletion_safety(mock_confirm, mock_select, mock_delete, mock_gather):
    mock_model = ModelInfo(
        name="To Delete",
        repo_id="test/delete",
        size_gb=1.0,
        times_used=0,
        last_used=None,
        category="General"
    )
    mock_gather.return_value = [mock_model]

    # Test 1: User cancels deletion
    mock_select.side_effect = ["remove", mock_model, "back"]
    mock_confirm.return_value = False

    run_insights_history()
    mock_delete.assert_not_called()

    # Test 2: User confirms deletion
    mock_select.side_effect = ["remove", mock_model, "continue", "back"]
    mock_confirm.return_value = True
    mock_delete.return_value = 1024 ** 3

    run_insights_history()
    mock_delete.assert_called_once_with("test/delete")


@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_select")
def test_filter_routing(mock_select, mock_gather):
    mock_gather.return_value = []
    # User selects filter -> Reason -> back
    mock_select.side_effect = ["filter", "Reasoning", "back"]

    run_insights_history()
    assert mock_select.call_count == 3


@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.delete_model_from_disk")
@patch("mlx_man.insights_view.tui_select")
@patch("mlx_man.insights_view.tui_confirm")
def test_deletion_error_handling(mock_confirm, mock_select, mock_delete, mock_gather):
    mock_model = ModelInfo(
        name="Error Model",
        repo_id="test/error",
        size_gb=2.0,
        times_used=1,
        last_used=None,
        category="General"
    )
    mock_gather.return_value = [mock_model]

    mock_select.side_effect = ["remove", mock_model, "continue", "back"]
    mock_confirm.return_value = True
    mock_delete.side_effect = RuntimeError("Disk permission denied")

    # Should not raise exception
    run_insights_history()
    mock_delete.assert_called_once_with("test/error")


def test_sorting_logic():
    models = [
        ModelInfo("Used 5 times", "repo1", 1.0, 5, datetime.datetime(2023, 10, 1), "General"),
        ModelInfo("Used 0 times", "repo2", 1.0, 0, None, "General"),
        ModelInfo("Used 2 times", "repo3", 1.0, 2, datetime.datetime(2023, 10, 5), "General"),
    ]

    sorted_models = sorted(models, key=lambda m: (m.times_used, m.last_used or datetime.datetime.min))

    assert sorted_models[0].name == "Used 0 times"
    assert sorted_models[1].name == "Used 2 times"
    assert sorted_models[2].name == "Used 5 times"


@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_select")
def test_cancel_model_selection(mock_select, mock_gather):
    mock_model = ModelInfo("M1", "repo1", 2.0, 0, None, "General")
    mock_gather.return_value = [mock_model]

    # Select remove, then cancel, then back
    mock_select.side_effect = ["remove", "cancel", "back"]
    run_insights_history()
    assert mock_select.call_count == 3

    # Select remove, then None (Esc), then back
    mock_select.side_effect = ["remove", None, "back"]
    run_insights_history()
    assert mock_select.call_count == 6


@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_select")
def test_empty_models_remove(mock_select, mock_gather):
    mock_gather.return_value = []
    # If no models, remove should skip and re-prompt
    mock_select.side_effect = ["remove", "back"]
    run_insights_history()
    assert mock_select.call_count == 2


@patch("mlx_man.insights_view.gather_models")
@patch("mlx_man.insights_view.tui_select")
def test_tui_select_format_funcs(mock_select, mock_gather):
    mock_model = ModelInfo("TestModel", "repo/test", 4.2, 3, None, "Build")
    mock_gather.return_value = [mock_model]

    calls_kwargs = []
    def capture_kwargs(*args, **kwargs):
        calls_kwargs.append(kwargs)
        if len(calls_kwargs) == 1:
            return "remove"
        elif len(calls_kwargs) == 2:
            return "cancel"
        return "back"

    mock_select.side_effect = capture_kwargs
    run_insights_history()

    # Verify first call (main menu action)
    first_call = calls_kwargs[0]
    assert first_call["title"] == "Select action:"
    assert first_call["choices"] == ["remove", "filter", "back"]
    assert "header" in first_call
    assert "footer" in first_call
    format_action = first_call["format_func"]
    assert "Remove" in format_action("remove")
    assert "Filter" in format_action("filter")
    assert "Back" in format_action("back")

    # Verify second call (model selection)
    second_call = calls_kwargs[1]
    assert second_call["title"] == "Select model to completely remove:"
    assert "header" in second_call
    assert "footer" in second_call
    format_model = second_call["format_func"]
    assert "TestModel" in format_model(mock_model)
    assert "4.2 GB" in format_model(mock_model)
    assert "3 uses" in format_model(mock_model)
    assert format_model("cancel") == "Cancel"

