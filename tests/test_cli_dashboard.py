import pytest
from unittest.mock import patch, MagicMock
from rich.align import Align
from rich.panel import Panel

from mlx_man.cli_dashboard import (
    get_chip_name,
    get_total_ram_gb,
    get_free_ram_gb,
    get_current_gpu_limit,
    get_macos_version,
    get_banner,
    get_main_menu_panel,
    get_tip_line,
    get_system_status_footer,
    get_system_dashboard
)

@patch("subprocess.check_output")
def test_get_chip_name(mock_out):
    mock_out.return_value = b"Apple M3 Max\n"
    assert get_chip_name() == "Apple M3 Max"
    
    mock_out.side_effect = Exception("error")
    with patch("platform.processor", return_value="arm"):
        assert get_chip_name() == "arm"
    with patch("platform.processor", return_value=""):
        assert get_chip_name() == "Unknown"

@patch("psutil.virtual_memory")
def test_ram_functions(mock_vm):
    mock_mem = MagicMock()
    mock_mem.total = 32 * (1024**3)
    mock_mem.available = 16.5 * (1024**3)
    mock_vm.return_value = mock_mem
    
    assert get_total_ram_gb() == 32
    assert get_free_ram_gb() == 16.5

@patch("subprocess.check_output")
def test_get_current_gpu_limit(mock_out):
    mock_out.return_value = b"21504\n" # 21 GB
    assert get_current_gpu_limit() == "21 GB"
    
    mock_out.side_effect = Exception("error")
    assert get_current_gpu_limit() == "~21 GB"

def test_get_macos_version():
    with patch("platform.mac_ver", return_value=("14.4.1", (), "")):
        assert get_macos_version() == "14.4.1"
    with patch("platform.mac_ver", return_value=("", (), "")):
        assert get_macos_version() == "Unknown"

def test_renderables():
    assert isinstance(get_banner(), Align)
    assert isinstance(get_main_menu_panel(), Align)
    assert isinstance(get_tip_line(), Align)

@patch("mlx_man.cli_dashboard.get_free_ram_gb")
def test_get_system_status_footer(mock_free):
    mock_free.return_value = 5.0 # red
    assert "🔴" in get_system_status_footer()
    
    mock_free.return_value = 10.0 # yellow
    assert "🟡" in get_system_status_footer()
    
    mock_free.return_value = 20.0 # green
    assert "🟢" in get_system_status_footer()

@patch("mlx_man.cli_dashboard.get_free_ram_gb")
def test_get_system_dashboard(mock_free):
    mock_free.return_value = 5.0
    dash = get_system_dashboard()
    assert str(dash) # verify it builds
    
    mock_free.return_value = 10.0
    dash = get_system_dashboard()
    
    mock_free.return_value = 20.0
    dash = get_system_dashboard()
