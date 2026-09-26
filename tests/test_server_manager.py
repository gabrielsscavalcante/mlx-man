import pytest
import os
import signal
import json
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def setup_state_file(tmp_path):
    with patch("mlx_man.server_manager.STATE_FILE", tmp_path / "server_state.json"):
        with patch("mlx_man.server_manager.LOG_FILE", tmp_path / "server.log"):
            yield

from mlx_man.server_manager import get_running_servers, stop_server, start_server

def test_get_running_servers_no_file():
    assert get_running_servers() == {}

@patch("mlx_man.server_manager.psutil.pid_exists", return_value=True)
@patch("mlx_man.server_manager.psutil.Process")
def test_get_running_servers_valid(mock_process, mock_exists, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text(json.dumps({"pid": 1234, "model_id": "test"})) # old format
    
    mock_proc = MagicMock()
    mock_proc.cmdline.return_value = ["python", "-m", "mlx_lm.server"]
    mock_proc.is_running.return_value = True
    mock_proc.status.return_value = "running"
    mock_process.return_value = mock_proc
    
    res = get_running_servers()
    assert "8080" in res
    assert res["8080"]["pid"] == 1234

@patch("mlx_man.server_manager.psutil.pid_exists", return_value=True)
@patch("mlx_man.server_manager.psutil.Process")
def test_get_running_servers_stale_cmd(mock_process, mock_exists, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text(json.dumps({"8080": {"pid": 1234, "model_id": "test"}}))
    
    mock_proc = MagicMock()
    mock_proc.cmdline.return_value = ["bash"]
    mock_proc.is_running.return_value = True
    mock_proc.status.return_value = "running"
    mock_process.return_value = mock_proc
    
    res = get_running_servers()
    assert res == {}

@patch("mlx_man.server_manager.get_running_servers", return_value={})
def test_stop_server_not_running(mock_get):
    stop_server()
    mock_get.assert_called_once()

@patch("mlx_man.server_manager.os.kill")
@patch("mlx_man.server_manager.psutil.pid_exists", side_effect=[False, False])
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"pid": 1234}})
def test_stop_server_graceful(mock_get, mock_exists, mock_kill, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text("{}")
    stop_server("8080")
    mock_kill.assert_called_with(1234, signal.SIGTERM)

@patch("mlx_man.server_manager.os.kill")
@patch("mlx_man.server_manager.psutil.pid_exists", return_value=True)
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"pid": 1234}})
def test_stop_server_force_kill(mock_get, mock_exists, mock_kill, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text("{}")
    stop_server()
    mock_kill.assert_called_with(1234, signal.SIGKILL)

@patch("mlx_man.server_manager.os.kill", side_effect=ProcessLookupError)
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"pid": 1234}})
def test_stop_server_lookup_error(mock_get, mock_kill, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text("{}")
    stop_server()

@patch("mlx_man.server_manager.subprocess.Popen")
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"pid": 1234}})
@patch("mlx_man.server_manager.stop_server")
def test_start_server(mock_stop, mock_get, mock_popen):
    mock_proc = MagicMock()
    mock_proc.pid = 9999
    mock_popen.return_value = mock_proc
    
    res = start_server("test/model", 8081)
    
    mock_stop.assert_called_once_with(8081)
    assert res["pid"] == 9999
    assert res["port"] == 8081
    assert res["model_id"] == "test/model"

def test_check_server_health_no_state():
    from mlx_man.server_manager import check_server_health
    assert not check_server_health(None)
    assert not check_server_health({})

@patch("mlx_man.server_manager.psutil.Process")
def test_check_server_health_running(mock_process):
    from mlx_man.server_manager import check_server_health, psutil
    mock_instance = mock_process.return_value
    mock_instance.is_running.return_value = True
    mock_instance.status.return_value = psutil.STATUS_RUNNING
    assert check_server_health({"pid": 1234})

@patch("mlx_man.server_manager.psutil.Process")
def test_check_server_health_zombie(mock_process):
    from mlx_man.server_manager import check_server_health, psutil
    mock_instance = mock_process.return_value
    mock_instance.is_running.return_value = True
    mock_instance.status.return_value = psutil.STATUS_ZOMBIE
    assert not check_server_health({"pid": 1234})

@patch("mlx_man.server_manager.psutil.Process")
def test_check_server_health_not_running(mock_process):
    from mlx_man.server_manager import check_server_health, psutil
    mock_instance = mock_process.return_value
    mock_instance.is_running.return_value = False
    assert not check_server_health({"pid": 1234})

@patch("mlx_man.server_manager.psutil.Process", side_effect=__import__('psutil').NoSuchProcess(1234))
def test_check_server_health_no_process(mock_process):
    from mlx_man.server_manager import check_server_health
    assert not check_server_health({"pid": 1234})

@patch("mlx_man.server_manager.check_server_health", return_value=False)
def test_get_running_servers_dead_removes_file(mock_health, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text(json.dumps({"8080": {"pid": 1234}}))
    res = get_running_servers()
    assert res == {}
    assert not state.exists()

def test_get_running_servers_exception(tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text("invalid json")
    res = get_running_servers()
    assert res == {}
    assert not state.exists()

@patch("mlx_man.server_manager.os.kill")
@patch("mlx_man.server_manager.psutil.pid_exists", return_value=True)
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"pid": 1234}})
def test_stop_server_removes_file_when_empty(mock_get, mock_exists, mock_kill, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text("dummy")
    stop_server() # removes 8080, leaves it empty
    assert not state.exists()

@patch("mlx_man.server_manager.os.kill")
@patch("mlx_man.server_manager.psutil.pid_exists", return_value=True)
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"pid": 1234}, "8081": {"pid": 5678}})
def test_stop_server_keeps_file_if_not_empty(mock_get, mock_exists, mock_kill, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text("dummy")
    stop_server("8080")
    assert state.exists()

@patch("mlx_man.server_manager.check_server_health", side_effect=[False, True])
@patch("mlx_man.server_manager.psutil.Process")
def test_get_running_servers_partial_dead(mock_process, mock_health, tmp_path):
    state = tmp_path / "server_state.json"
    state.write_text(json.dumps({"8080": {"pid": 1234}, "8081": {"pid": 5678}}))
    
    mock_proc = MagicMock()
    mock_proc.cmdline.return_value = ["python", "-m", "mlx_lm.server"]
    mock_process.return_value = mock_proc
    
    res = get_running_servers()
    assert "8081" in res
    assert "8080" not in res
