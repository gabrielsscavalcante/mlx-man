import pytest
from unittest.mock import patch, MagicMock

from mlx_man.process_service import ProcessClassifier, ProcessService, ProcessInfo
from rich.console import Console


class TestProcessClassifier:
    def test_safe_processes(self):
        assert ProcessClassifier.classify("language_server")[0] == "Safe"
        assert ProcessClassifier.classify("MTLCompilerService")[0] == "Safe"

    def test_caution_processes(self):
        assert ProcessClassifier.classify("Siri AI")[0] == "Caution"
        assert ProcessClassifier.classify("AppleSpell")[0] == "Caution"
        assert ProcessClassifier.classify("UnknownApp123")[0] == "Caution"

    def test_danger_processes(self):
        assert ProcessClassifier.classify("ControlCenter")[0] == "Danger"
        assert ProcessClassifier.classify("NotificationCenter")[0] == "Danger"
        assert ProcessClassifier.classify("cloudd")[0] == "Danger"


class TestTerminationSafety:
    @patch('mlx_man.process_service.psutil.Process')
    def test_confirm_safe_process_issues_sigterm(self, mock_process):
        mock_p = MagicMock()
        mock_process.return_value = mock_p
        success = ProcessService.terminate_process(12345)
        assert success is True
        mock_process.assert_called_once_with(12345)
        mock_p.terminate.assert_called_once()
        mock_p.wait.assert_called_once_with(timeout=3)
        mock_p.kill.assert_not_called()

    @patch('mlx_man.process_service.psutil.Process')
    def test_sigkill_fallback_on_timeout(self, mock_process):
        import psutil
        mock_p = MagicMock()
        mock_p.wait.side_effect = psutil.TimeoutExpired(10)
        mock_process.return_value = mock_p
        success = ProcessService.terminate_process(12345)
        assert success is True
        mock_p.terminate.assert_called_once()
        mock_p.kill.assert_called_once()

    @patch('mlx_man.ram_manager_view.tui_table_select')
    @patch('mlx_man.ram_manager_view.ProcessService.terminate_process')
    @patch('mlx_man.ram_manager_view.ProcessService.get_system_memory_info')
    @patch('mlx_man.ram_manager_view.ProcessService.get_processes')
    @patch('mlx_man.ram_manager_view.tui_confirm')
    def test_cancel_confirmation_aborts(self, mock_confirm, mock_get_processes, mock_get_mem, mock_terminate, mock_select):
        from mlx_man.ram_manager_view import run_ram_manager
        mock_get_mem.return_value = {"used_gb": 10, "total_gb": 32, "wired_gb": 2}
        mock_get_processes.return_value = []
        safe_proc = ProcessInfo(123, "language_server", 100, "Safe", "Desc")
        mock_select.side_effect = [safe_proc, None]
        mock_confirm.return_value = False
        run_ram_manager(expert_mode=False)
        mock_terminate.assert_not_called()

    @patch('mlx_man.ram_manager_view.tui_table_select')
    @patch('mlx_man.ram_manager_view.ProcessService.terminate_process')
    @patch('mlx_man.ram_manager_view.ProcessService.get_system_memory_info')
    @patch('mlx_man.ram_manager_view.ProcessService.get_processes')
    @patch('mlx_man.ram_manager_view.tui_text_input')
    def test_danger_without_override_prevents_kill(self, mock_text, mock_get_processes, mock_get_mem, mock_terminate, mock_select):
        from mlx_man.ram_manager_view import run_ram_manager
        mock_get_mem.return_value = {"used_gb": 10, "total_gb": 32, "wired_gb": 2}
        mock_get_processes.return_value = []
        danger_proc = ProcessInfo(123, "ControlCenter", 100, "Danger", "Desc")
        mock_select.side_effect = [danger_proc, None]
        run_ram_manager(expert_mode=False)
        mock_text.assert_called_once()
        mock_terminate.assert_not_called()

    @patch('mlx_man.ram_manager_view.tui_table_select')
    @patch('mlx_man.ram_manager_view.ProcessService.terminate_process')
    @patch('mlx_man.ram_manager_view.ProcessService.get_system_memory_info')
    @patch('mlx_man.ram_manager_view.ProcessService.get_processes')
    @patch('mlx_man.ram_manager_view.tui_confirm')
    @patch('mlx_man.ram_manager_view.tui_text_input')
    def test_confirm_safe_process_kills_successfully(self, mock_text, mock_confirm, mock_get_processes, mock_get_mem, mock_terminate, mock_select):
        from mlx_man.ram_manager_view import run_ram_manager
        mock_get_mem.return_value = {"used_gb": 10, "total_gb": 32, "wired_gb": 2}
        mock_get_processes.return_value = []
        safe_proc = ProcessInfo(123, "language_server", 100, "Safe", "Desc")
        mock_select.side_effect = [safe_proc, None]
        mock_confirm.return_value = True
        mock_terminate.return_value = True
        run_ram_manager(expert_mode=False)
        mock_terminate.assert_called_once_with(123)
        mock_text.assert_called_once()


