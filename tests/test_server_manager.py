import pytest
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from mlx_man.server_manager import get_running_server, stop_server, start_server, STATE_FILE, LOG_FILE

@pytest.fixture(autouse=True)
def mock_dirs(tmp_path, monkeypatch):
    import mlx_man.server_manager
    monkeypatch.setattr(mlx_man.server_manager, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(mlx_man.server_manager, "STATE_FILE", tmp_path / "server_state.json")
    monkeypatch.setattr(mlx_man.server_manager, "LOG_FILE", tmp_path / "server.log")

@patch("mlx_man.server_manager.psutil.pid_exists", return_value=True)
@patch("mlx_man.server_manager.psutil.Process")
def test_get_running_server_valid(mock_process, mock_exists, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text(json.dumps({"pid": 1234, "model_id": "test"}))
    
    mock_proc = MagicMock()
    mock_proc.cmdline.return_value = ["python", "-m", "mlx_lm.server"]
    mock_process.return_value = mock_proc
    
    res = get_running_server()
    assert res["pid"] == 1234
    assert res["model_id"] == "test"

@patch("mlx_man.server_manager.psutil.pid_exists", return_value=True)
@patch("mlx_man.server_manager.psutil.Process")
def test_get_running_server_invalid_cmdline(mock_process, mock_exists, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text(json.dumps({"pid": 1234, "model_id": "test"}))
    
    mock_proc = MagicMock()
    mock_proc.cmdline.return_value = ["python", "other_script.py"]
    mock_process.return_value = mock_proc
    
    assert get_running_server() is None
    assert not state.exists() # Should unlink

@patch("mlx_man.server_manager.psutil.pid_exists", return_value=False)
def test_get_running_server_dead_pid(mock_exists, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text(json.dumps({"pid": 1234}))
    assert get_running_server() is None
    assert not state.exists()

def test_get_running_server_no_file(tmp_path):
    assert get_running_server() is None

def test_get_running_server_corrupt_file(tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text("invalid json")
    assert get_running_server() is None

@patch("mlx_man.server_manager.os.kill")
@patch("mlx_man.server_manager.psutil.pid_exists", side_effect=[False, False]) # running, then dies
@patch("mlx_man.server_manager.get_running_server", return_value={"pid": 1234})
def test_stop_server_graceful(mock_get, mock_exists, mock_kill):
    stop_server()
    mock_kill.assert_called_once_with(1234, signal.SIGTERM)

import signal
@patch("mlx_man.server_manager.os.kill")
@patch("mlx_man.server_manager.psutil.pid_exists", return_value=True) # refuses to die
@patch("mlx_man.server_manager.get_running_server", return_value={"pid": 1234})
def test_stop_server_force_kill(mock_get, mock_exists, mock_kill):
    # mock_exists always true -> kill is called with SIGTERM then SIGKILL
    stop_server()
    assert mock_kill.call_count == 2
    mock_kill.assert_any_call(1234, signal.SIGTERM)
    mock_kill.assert_any_call(1234, signal.SIGKILL)

@patch("mlx_man.server_manager.os.kill", side_effect=ProcessLookupError)
@patch("mlx_man.server_manager.get_running_server", return_value={"pid": 1234})
def test_stop_server_lookup_error(mock_get, mock_kill):
    stop_server() # shouldn't crash

@patch("mlx_man.server_manager.subprocess.Popen")
@patch("mlx_man.server_manager.stop_server")
def test_start_server(mock_stop, mock_popen, tmp_path):
    mock_proc = MagicMock()
    mock_proc.pid = 9999
    mock_popen.return_value = mock_proc
    
    data = start_server("org/model")
    
    assert data["pid"] == 9999
    assert data["model_id"] == "org/model"
    mock_stop.assert_called_once()
    
    log_file = tmp_path / "server.log"
    assert log_file.exists()
    assert "Starting Server for org/model" in log_file.read_text()
    
    state_file = tmp_path / "server_state.json"
    assert state_file.exists()
