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
@patch("mlx_man.insights_view.questionary.select")
@patch("mlx_man.insights_view.questionary.confirm")
@patch("mlx_man.insights_view.console")
@patch("builtins.input", return_value="")
def test_deletion_safety(mock_input, mock_console, mock_confirm, mock_select, mock_delete, mock_gather):
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
    mock_select_ask = MagicMock()
    mock_select_ask.side_effect = ["remove", mock_model, "back"]
    mock_select.return_value.ask = mock_select_ask

    mock_confirm_ask = MagicMock()
    mock_confirm_ask.return_value = False
    mock_confirm.return_value.ask = mock_confirm_ask

    run_insights_history()
    mock_delete.assert_not_called()

    # Test 2: User confirms deletion
    mock_select_ask.side_effect = ["remove", mock_model, "back"]
    mock_select.return_value.ask = mock_select_ask

    mock_confirm_ask.return_value = True
    mock_confirm.return_value.ask = mock_confirm_ask
    mock_delete.return_value = 1024 ** 3

    run_insights_history()
    mock_delete.assert_called_once_with("test/delete")


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
