import pytest
from unittest.mock import patch, MagicMock

import os
import sys
# Ensure src is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, '..', 'src'))

from process_service import ProcessClassifier, ProcessService, ProcessInfo
from ram_manager_view import render_process_table, render_header
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
    @patch('process_service.psutil.Process')
    def test_confirm_safe_process_issues_sigterm(self, mock_process):
        mock_p = MagicMock()
        mock_process.return_value = mock_p
        
        success = ProcessService.terminate_process(12345)
        
        assert success is True
        mock_process.assert_called_once_with(12345)
        mock_p.terminate.assert_called_once()
        mock_p.wait.assert_called_once_with(timeout=3)
        mock_p.kill.assert_not_called()

    @patch('process_service.psutil.Process')
    def test_sigkill_fallback_on_timeout(self, mock_process):
        import psutil
        mock_p = MagicMock()
        mock_p.wait.side_effect = psutil.TimeoutExpired(10)
        mock_process.return_value = mock_p
        
        success = ProcessService.terminate_process(12345)
        
        assert success is True
        mock_p.terminate.assert_called_once()
        mock_p.kill.assert_called_once()

    @patch('ram_manager_view.questionary.select')
    @patch('ram_manager_view.ProcessService.terminate_process')
    @patch('ram_manager_view.ProcessService.get_system_memory_info')
    @patch('ram_manager_view.ProcessService.get_processes')
    @patch('ram_manager_view.os.system')
    @patch('ram_manager_view.questionary.confirm')
    def test_cancel_confirmation_aborts(self, mock_confirm, mock_system, mock_get_processes, mock_get_mem, mock_terminate, mock_select):
        from ram_manager_view import run_ram_manager
        
        mock_get_mem.return_value = {"used_gb": 10, "total_gb": 32, "wired_gb": 2}
        mock_get_processes.return_value = []
        
        # User selects a Safe process
        safe_proc = ProcessInfo(123, "language_server", 100, "Safe", "Desc")
        
        # We need select() to return the process, then 'cancel' on the second loop to break out
        mock_select.return_value.ask.side_effect = [safe_proc, "cancel"]
        
        # User cancels the confirmation
        mock_confirm.return_value.ask.return_value = False
        
        run_ram_manager(expert_mode=False)
        
        # Terminate should not have been called
        mock_terminate.assert_not_called()

    @patch('ram_manager_view.questionary.select')
    @patch('ram_manager_view.ProcessService.terminate_process')
    @patch('ram_manager_view.ProcessService.get_system_memory_info')
    @patch('ram_manager_view.ProcessService.get_processes')
    @patch('ram_manager_view.os.system')
    @patch('ram_manager_view.questionary.text')
    def test_danger_without_override_prevents_kill(self, mock_text, mock_system, mock_get_processes, mock_get_mem, mock_terminate, mock_select):
        from ram_manager_view import run_ram_manager
        
        mock_get_mem.return_value = {"used_gb": 10, "total_gb": 32, "wired_gb": 2}
        mock_get_processes.return_value = []
        
        danger_proc = ProcessInfo(123, "ControlCenter", 100, "Danger", "Desc")
        
        mock_select.return_value.ask.side_effect = [danger_proc, "cancel"]
        
        run_ram_manager(expert_mode=False)
        
        # Should show error and ask to press Enter
        mock_text.return_value.ask.assert_called_once()
        mock_terminate.assert_not_called()


class TestUIRendering:
    def test_render_table_no_truncation(self):
        console = Console(record=True, width=120)
        
        processes = [
            ProcessInfo(1001, "language_server", 244.5, "Safe", "Safe process desc"),
            ProcessInfo(1002, "Siri AI", 150.0, "Caution", "Caution process desc"),
            ProcessInfo(1003, "ControlCenter", 50.2, "Danger", "Danger process desc")
        ]
        
        render_process_table(processes, console_obj=console)
        
        output = console.export_text()
        
        # Check that badges are rendered (without markup, they are just text)
        assert "Safe" in output
        assert "Caution" in output
        assert "Protected" in output
        assert "language_server" in output
        assert "244 MB" in output
