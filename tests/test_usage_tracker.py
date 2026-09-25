import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from mlx_man.usage_tracker import get_config_dir, _migrate_legacy_history, load_data, save_data, record_usage

def test_get_config_dir(tmp_path):
    with patch("os.path.expanduser", return_value=tmp_path):
        d = get_config_dir()
        assert d == str(tmp_path / ".config" / "mlx-man")
        assert Path(d).exists()

@patch("mlx_man.usage_tracker.get_config_dir")
@patch("os.path.exists")
@patch("shutil.copy2")
def test_migrate_legacy_history(mock_copy, mock_exists, mock_config):
    mock_config.return_value = "/mock/config"
    # Return true for legacy, false for new
    mock_exists.side_effect = lambda path: "legacy" in str(path) or ".model_usage_history.json" in str(path)
    _migrate_legacy_history()
    mock_copy.assert_called_once()

@patch("mlx_man.usage_tracker.HISTORY_FILE", "/tmp/missing.json")
@patch("os.path.exists", return_value=False)
def test_load_data_missing(mock_exists):
    assert load_data() == {}

@patch("mlx_man.usage_tracker.HISTORY_FILE", "/tmp/bad.json")
@patch("os.path.exists", return_value=True)
def test_load_data_bad(mock_exists, tmp_path):
    with patch("builtins.open", MagicMock()) as mock_open:
        handle = MagicMock()
        handle.read.return_value = "{"
        handle.__enter__.return_value = handle
        mock_open.return_value = handle
        
        with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
            assert load_data() == {}

@patch("mlx_man.usage_tracker.HISTORY_FILE", "/tmp/good.json")
@patch("os.path.exists", return_value=True)
def test_load_data_good(mock_exists):
    with patch("builtins.open", MagicMock()) as mock_open:
        with patch("json.load", return_value={"test": {"count": 1}}):
            assert load_data() == {"test": {"count": 1}}

@patch("mlx_man.usage_tracker.HISTORY_FILE", "/tmp/save.json")
def test_save_data():
    with patch("builtins.open", MagicMock()) as mock_open:
        save_data({"test": {"count": 1}})
        mock_open.assert_called_once()

@patch("mlx_man.usage_tracker.load_data")
@patch("mlx_man.usage_tracker.save_data")
def test_record_usage(mock_save, mock_load):
    mock_load.return_value = {}
    record_usage("org/model")
    mock_save.assert_called_once()
    args = mock_save.call_args[0][0]
    assert "org/model" in args
    assert args["org/model"]["count"] == 1

    # Second time
    mock_load.return_value = {"org/model": {"count": 1}}
    record_usage("org/model")
    args = mock_save.call_args[0][0]
    assert args["org/model"]["count"] == 2
