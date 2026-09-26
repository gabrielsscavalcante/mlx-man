import pytest
from unittest.mock import patch, mock_open
from mlx_man.server_dashboard_view import tail_logs, render_server_dashboard

@patch("mlx_man.server_dashboard_view.LOG_FILE")
def test_tail_logs_no_file(mock_log):
    mock_log.exists.return_value = False
    assert "No logs available" in tail_logs()

@patch("mlx_man.server_dashboard_view.LOG_FILE")
def test_tail_logs_empty(mock_log):
    mock_log.exists.return_value = True
    with patch("builtins.open", mock_open(read_data="")):
        assert "empty" in tail_logs()

@patch("mlx_man.server_dashboard_view.LOG_FILE")
def test_tail_logs_success(mock_log):
    mock_log.exists.return_value = True
    data = "line1\nline2\nline3\nline4\nline5\nline6"
    with patch("builtins.open", mock_open(read_data=data)):
        res = tail_logs(2)
        assert "line5" in res
        assert "line6" in res
        assert "line1" not in res

@patch("mlx_man.server_dashboard_view.LOG_FILE")
def test_tail_logs_error(mock_log):
    mock_log.exists.return_value = True
    with patch("builtins.open", side_effect=Exception("mocked error")):
        assert "Error reading logs: mocked error" in tail_logs()

@patch("mlx_man.cli_dashboard.get_total_ram_gb", return_value=32.0)
@patch("mlx_man.cli_dashboard.get_free_ram_gb", return_value=16.0)
@patch("mlx_man.cli_dashboard.get_current_gpu_limit", return_value="24 GB")
@patch("mlx_man.server_dashboard_view.tail_logs", return_value="some log")
def test_render_server_dashboard_healthy(mock_tail, m1, m2, m3):
    state = {"model_id": "test", "port": 8080, "pid": 1234}
    grp = render_server_dashboard(state, True)
    assert grp is not None

@patch("mlx_man.cli_dashboard.get_total_ram_gb", side_effect=Exception("hw error"))
@patch("mlx_man.server_dashboard_view.tail_logs", return_value="some log")
def test_render_server_dashboard_hw_error(mock_tail, m1):
    state = {"model_id": "test", "port": 8080, "pid": 1234}
    grp = render_server_dashboard(state, False)
    assert grp is not None

def test_render_server_dashboard_none_state():
    with patch("mlx_man.cli_dashboard.get_total_ram_gb", return_value=32.0):
        with patch("mlx_man.cli_dashboard.get_free_ram_gb", return_value=16.0):
            with patch("mlx_man.cli_dashboard.get_current_gpu_limit", return_value="24 GB"):
                with patch("mlx_man.server_dashboard_view.tail_logs", return_value=""):
                    grp = render_server_dashboard(None, False)
                    assert grp is not None
