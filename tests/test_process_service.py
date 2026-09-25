import pytest
from unittest.mock import patch, MagicMock
import psutil
from mlx_man.process_service import ProcessClassifier, ProcessService, ProcessInfo

def test_process_classifier():
    assert ProcessClassifier.classify("WindowServer")[0] == "Danger"
    assert ProcessClassifier.classify("Safari")[0] == "Safe"
    assert ProcessClassifier.classify("siriactionsd")[0] == "Caution"
    assert ProcessClassifier.classify("RandomApp")[0] == "Caution"

@patch("mlx_man.process_service.psutil.virtual_memory")
def test_get_system_memory_info(mock_vm):
    mock_mem = MagicMock()
    mock_mem.total = 32 * (1024**3)
    mock_mem.used = 16 * (1024**3)
    mock_mem.available = 16 * (1024**3)
    mock_mem.percent = 50.0
    mock_mem.wired = 8 * (1024**3)
    mock_vm.return_value = mock_mem
    
    info = ProcessService.get_system_memory_info()
    assert info["total_gb"] == 32.0
    assert info["percent"] == 50.0

@patch("mlx_man.process_service.psutil.process_iter")
def test_get_processes(mock_iter):
    p1 = MagicMock()
    p1.info = {'pid': 100, 'name': 'Safari', 'memory_info': MagicMock(rss=100*1024*1024)}
    p2 = MagicMock()
    p2.info = {'pid': 200, 'name': 'TinyApp', 'memory_info': MagicMock(rss=10*1024*1024)} # skips because < 50MB
    p3 = MagicMock()
    p3.info = {'pid': 300, 'name': 'WindowServer', 'memory_info': MagicMock(rss=200*1024*1024)}
    
    p_err1 = MagicMock()
    type(p_err1).info = property(lambda self: (_ for _ in ()).throw(psutil.NoSuchProcess(400))) # triggers exception

    p_empty_mem = MagicMock()
    p_empty_mem.info = {'pid': 500, 'name': 'App', 'memory_info': None}
    
    mock_iter.return_value = [p1, p2, p3, p_err1, p_empty_mem]
    
    procs = ProcessService.get_processes()
    assert len(procs) == 2
    assert procs[0].name == "WindowServer" # Sorted by MB descending
    assert procs[1].name == "Safari"

@patch("mlx_man.process_service.psutil.Process")
def test_terminate_process_success_term(mock_proc_class):
    mock_proc = MagicMock()
    mock_proc_class.return_value = mock_proc
    assert ProcessService.terminate_process(123) is True
    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once_with(timeout=3)
    mock_proc.kill.assert_not_called()

@patch("mlx_man.process_service.psutil.Process")
def test_terminate_process_success_kill(mock_proc_class):
    mock_proc = MagicMock()
    mock_proc.wait.side_effect = psutil.TimeoutExpired(3)
    mock_proc_class.return_value = mock_proc
    assert ProcessService.terminate_process(123) is True
    mock_proc.kill.assert_called_once()

@patch("mlx_man.process_service.psutil.Process", side_effect=psutil.AccessDenied(123))
def test_terminate_process_access_denied(mock_proc_class):
    assert ProcessService.terminate_process(123) is False

@patch("mlx_man.process_service.psutil.Process", side_effect=Exception("Crash"))
def test_terminate_process_exception(mock_proc_class):
    assert ProcessService.terminate_process(123) is False
