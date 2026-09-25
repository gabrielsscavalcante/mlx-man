import pytest
from unittest.mock import patch, MagicMock

from mlx_man.ram_manager_view import run_ram_manager, get_process_row
from mlx_man.process_service import ProcessInfo

@pytest.fixture
def mock_processes():
    return [
        ProcessInfo(1, "SafeApp", 100, "Safe", "Desc"),
        ProcessInfo(2, "CautApp", 200, "Caution", "Desc"),
        ProcessInfo(3, "DangApp", 300, "Danger", "Desc"),
    ]

def test_get_process_row():
    p = ProcessInfo(1, "App", 100, "Safe", "Desc")
    row = get_process_row(p)
    assert row[0] == "1"
    
    p2 = ProcessInfo(2, "App2", 200, "Caution", "Desc")
    assert "Caution" in str(get_process_row(p2)[3])
    
    p3 = ProcessInfo(3, "App3", 300, "Danger", "Desc")
    assert "Protected" in str(get_process_row(p3)[3])

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
def test_run_ram_manager_error(mock_mem):
    mock_mem.side_effect = Exception("System error")
    run_ram_manager()
    # just testing it doesn't crash and returns

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
@patch("mlx_man.ram_manager_view.ProcessService.get_processes")
@patch("mlx_man.ram_manager_view.tui_table_select")
def test_run_ram_manager_interrupt(mock_select, mock_get_p, mock_mem, mock_processes):
    mock_get_p.return_value = mock_processes
    mock_mem.return_value = {"used_gb": 10, "total_gb": 16, "wired_gb": 2}
    mock_select.side_effect = KeyboardInterrupt
    run_ram_manager()

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
@patch("mlx_man.ram_manager_view.ProcessService.get_processes")
@patch("mlx_man.ram_manager_view.tui_table_select")
def test_run_ram_manager_empty(mock_select, mock_get_p, mock_mem):
    mock_get_p.return_value = []
    mock_mem.return_value = {"used_gb": 10, "total_gb": 16, "wired_gb": 2}
    mock_select.return_value = None
    run_ram_manager()

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
@patch("mlx_man.ram_manager_view.ProcessService.get_processes")
@patch("mlx_man.ram_manager_view.tui_table_select")
@patch("mlx_man.ram_manager_view.tui_text_input")
def test_run_ram_manager_danger_no_expert(mock_input, mock_select, mock_get_p, mock_mem, mock_processes):
    mock_get_p.return_value = mock_processes
    mock_mem.return_value = {"used_gb": 10, "total_gb": 16, "wired_gb": 2}
    mock_select.side_effect = [mock_processes[2], None] # Danger app
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_ram_manager(expert_mode=False)

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
@patch("mlx_man.ram_manager_view.ProcessService.get_processes")
@patch("mlx_man.ram_manager_view.tui_table_select")
@patch("mlx_man.ram_manager_view.tui_confirm")
@patch("mlx_man.ram_manager_view.ProcessService.terminate_process")
@patch("mlx_man.ram_manager_view.tui_text_input")
def test_run_ram_manager_danger_expert_yes(mock_input, mock_term, mock_confirm, mock_select, mock_get_p, mock_mem, mock_processes):
    mock_get_p.return_value = mock_processes
    mock_mem.return_value = {"used_gb": 10, "total_gb": 16, "wired_gb": 2}
    mock_select.side_effect = [mock_processes[2], None] # Danger app
    mock_confirm.return_value = True
    mock_term.return_value = True
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_ram_manager(expert_mode=True)
    mock_term.assert_called_once_with(3)

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
@patch("mlx_man.ram_manager_view.ProcessService.get_processes")
@patch("mlx_man.ram_manager_view.tui_table_select")
@patch("mlx_man.ram_manager_view.tui_confirm")
def test_run_ram_manager_danger_expert_no(mock_confirm, mock_select, mock_get_p, mock_mem, mock_processes):
    mock_get_p.return_value = mock_processes
    mock_mem.return_value = {"used_gb": 10, "total_gb": 16, "wired_gb": 2}
    mock_select.side_effect = [mock_processes[2], None] # Danger app
    mock_confirm.return_value = False
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_ram_manager(expert_mode=True)

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
@patch("mlx_man.ram_manager_view.ProcessService.get_processes")
@patch("mlx_man.ram_manager_view.tui_table_select")
@patch("mlx_man.ram_manager_view.tui_confirm")
@patch("mlx_man.ram_manager_view.ProcessService.terminate_process")
@patch("mlx_man.ram_manager_view.tui_text_input")
def test_run_ram_manager_safe_fail(mock_input, mock_term, mock_confirm, mock_select, mock_get_p, mock_mem, mock_processes):
    mock_get_p.return_value = mock_processes
    mock_mem.return_value = {"used_gb": 10, "total_gb": 16, "wired_gb": 2}
    mock_select.side_effect = [mock_processes[0], None] # Safe app
    mock_confirm.return_value = True
    mock_term.return_value = False
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_ram_manager()

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
@patch("mlx_man.ram_manager_view.ProcessService.get_processes")
@patch("mlx_man.ram_manager_view.tui_table_select")
@patch("mlx_man.ram_manager_view.tui_confirm")
def test_run_ram_manager_caut_no(mock_confirm, mock_select, mock_get_p, mock_mem, mock_processes):
    mock_get_p.return_value = mock_processes
    mock_mem.return_value = {"used_gb": 10, "total_gb": 16, "wired_gb": 2}
    mock_select.side_effect = [mock_processes[1], None] # Caut app
    mock_confirm.return_value = False
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_ram_manager()

@patch("mlx_man.ram_manager_view.ProcessService.get_system_memory_info")
@patch("mlx_man.ram_manager_view.ProcessService.get_processes")
@patch("mlx_man.ram_manager_view.tui_table_select")
@patch("mlx_man.ram_manager_view.tui_confirm")
def test_run_ram_manager_safe_no(mock_confirm, mock_select, mock_get_p, mock_mem, mock_processes):
    mock_get_p.return_value = mock_processes
    mock_mem.return_value = {"used_gb": 10, "total_gb": 16, "wired_gb": 2}
    mock_select.side_effect = [mock_processes[0], None] # Safe app
    mock_confirm.return_value = False
    
    with patch("mlx_man.cli_dashboard.get_system_status_footer", return_value=""):
        run_ram_manager()
