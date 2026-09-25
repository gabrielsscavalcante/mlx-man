import re

with open('tests/test_hub_search.py', 'r') as f:
    content = f.read()

# Fix mock_run assertion
content = content.replace("mock_run.assert_called_once()", "assert any('model_downloader.py' in str(call_args) for call_args in mock_run.call_args_list)")

# Add a test that calls format_row
test_format_row = """
@patch("mlx_man.hub_search_view.tui_text_input", return_value="query")
@patch("huggingface_hub.HfApi")
@patch("mlx_man.hub_search_view.tui_table_select")
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
"""

content += "\n" + test_format_row

with open('tests/test_hub_search.py', 'w') as f:
    f.write(content)
