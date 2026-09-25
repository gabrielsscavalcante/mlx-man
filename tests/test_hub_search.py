import pytest
from unittest.mock import patch, MagicMock
from mlx_man.hub_search_view import action_search_hub

class MockModelInfo:
    def __init__(self, id, downloads):
        self.id = id
        self.downloads = downloads

@patch("mlx_man.hub_search_view.tui_text_input", return_value=None)
def test_search_hub_cancel(mock_input):
    action_search_hub()
    mock_input.assert_called_once()

@patch("mlx_man.hub_search_view.tui_text_input", return_value="query")
@patch("huggingface_hub.HfApi")
def test_search_hub_no_results(mock_hf, mock_input):
    mock_api_instance = mock_hf.return_value
    mock_api_instance.list_models.return_value = iter([])
    
    with patch("mlx_man.hub_search_view.create_warning_panel") as mock_warning:
        action_search_hub()
        mock_warning.assert_called_once()
        assert "No MLX models found" in mock_warning.call_args[0][0]

@patch("mlx_man.hub_search_view.tui_text_input", return_value="query")
@patch("huggingface_hub.HfApi")
def test_search_hub_exception(mock_hf, mock_input):
    mock_api_instance = mock_hf.return_value
    mock_api_instance.list_models.side_effect = Exception("API error")
    
    with patch("mlx_man.hub_search_view.create_warning_panel") as mock_warning:
        action_search_hub()
        mock_warning.assert_called_once()
        assert "API error" in mock_warning.call_args[0][0]

@patch("mlx_man.hub_search_view.tui_text_input", return_value="query")
@patch("huggingface_hub.HfApi")
@patch("mlx_man.hub_search_view.tui_table_select", return_value=None)
def test_search_hub_table_back(mock_select, mock_hf, mock_input):
    mock_api_instance = mock_hf.return_value
    mock_api_instance.list_models.return_value = iter([MockModelInfo("model-id", 100)])
    action_search_hub()
    mock_select.assert_called_once()

@patch("mlx_man.hub_search_view.tui_text_input")
@patch("huggingface_hub.HfApi")
@patch("mlx_man.hub_search_view.tui_table_select", return_value=None)
@patch("mlx_man.hub_search_view.tui_confirm")
@patch("mlx_man.hub_search_view.subprocess.run")
def test_search_hub_download_success(mock_run, mock_confirm, mock_select, mock_hf, mock_input):
    mock_input.side_effect = ["query", None] # first for query, then for continue
    mock_api_instance = mock_hf.return_value
    mock_api_instance.list_models.return_value = iter([MockModelInfo("model-id", 100)])
    
    # Return a model, then return None to break the loop
    mock_select.side_effect = [MockModelInfo("model-id", 100), None]
    mock_confirm.return_value = True
    
    with patch("mlx_man.hub_search_view.Console"):
        action_search_hub()
        
    assert any('model_downloader.py' in str(call_args) for call_args in mock_run.call_args_list)

@patch("mlx_man.hub_search_view.tui_text_input")
@patch("huggingface_hub.HfApi")
@patch("mlx_man.hub_search_view.tui_table_select", return_value=None)
@patch("mlx_man.hub_search_view.tui_confirm")
def test_search_hub_download_cancel(mock_confirm, mock_select, mock_hf, mock_input):
    mock_input.return_value = "query"
    mock_api_instance = mock_hf.return_value
    mock_api_instance.list_models.return_value = iter([MockModelInfo("model-id", 100)])
    
    mock_select.side_effect = [MockModelInfo("model-id", 100), None]
    mock_confirm.return_value = False
    
    action_search_hub()

def test_search_hub_no_huggingface_hub():
    import sys
    with patch.dict(sys.modules, {'huggingface_hub': None}):
        with patch("mlx_man.hub_search_view.tui_text_input") as mock_input:
            action_search_hub()
            mock_input.assert_called_once()


@patch("mlx_man.hub_search_view.tui_text_input", return_value="query")
@patch("huggingface_hub.HfApi")
@patch("mlx_man.hub_search_view.tui_table_select", return_value=None)
def test_search_hub_format_row(mock_select, mock_hf, mock_input):
    mock_api_instance = mock_hf.return_value
    mock_api_instance.list_models.return_value = iter([MockModelInfo("model-id", 100)])
    
    action_search_hub()
    
    # Get the format_row function passed to tui_table_select
    kwargs = mock_select.call_args.kwargs
    format_row = kwargs["row_func"]
    
    row = format_row(MockModelInfo("mlx-community/Qwen2.5-7B-Instruct-4bit", 100))
    assert row[0] == "mlx-community/Qwen2.5-7B-Instruct-4bit"
    assert row[1] == "100"
