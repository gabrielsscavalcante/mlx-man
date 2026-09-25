import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from mlx_man.opencode_sync import sync_opencode_config

@patch("mlx_man.opencode_sync.OPENCODE_CONFIG")
def test_sync_opencode_config_success(mock_config, tmp_path):
    conf = tmp_path / "opencode.json"
    mock_config.parent.mkdir = MagicMock()
    mock_config.exists.return_value = False
    
    # We must patch open specifically for this file
    with patch("builtins.open", MagicMock()) as mock_open:
        assert sync_opencode_config("org/model") == True
        mock_open.assert_called_with(mock_config, "w")

@patch("mlx_man.opencode_sync.OPENCODE_CONFIG")
def test_sync_opencode_config_read_existing(mock_config, tmp_path):
    mock_config.exists.return_value = True
    read_data = '{"provider": {"mlx": {"models": {"existing/model": {"name": "test"}}}}}'
    with patch("builtins.open", MagicMock()) as mock_open:
        # Mock file handle for read and write
        handle = MagicMock()
        handle.read.return_value = read_data
        handle.__enter__.return_value = handle
        mock_open.return_value = handle
        
        # We need to mock json.load to return dict since mock_open read string doesn't automatically load in json.load
        with patch("json.load", return_value=json.loads(read_data)):
            assert sync_opencode_config("org/model") == True

@patch("mlx_man.opencode_sync.OPENCODE_CONFIG")
def test_sync_opencode_config_read_error(mock_config):
    mock_config.exists.return_value = True
    with patch("builtins.open", side_effect=Exception("Read error")):
        # Read error should fall back to empty config, then try writing
        with patch("builtins.open", MagicMock()):
            assert sync_opencode_config() == True

@patch("mlx_man.opencode_sync.OPENCODE_CONFIG")
def test_sync_opencode_config_write_error(mock_config):
    mock_config.parent.mkdir.side_effect = Exception("Write error")
    assert sync_opencode_config() == False
