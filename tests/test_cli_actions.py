import pytest
from unittest.mock import patch, MagicMock
import subprocess
from mlx_man.cli_actions import (
    run_memory_cleaner,
    run_model_inspector,
    run_insights_history,
    action_run_server
)

def test_run_memory_cleaner():
    with patch("mlx_man.ram_manager_view.run_ram_manager") as mock_run:
        run_memory_cleaner()
        mock_run.assert_called_once()
    
    with patch("mlx_man.ram_manager_view.run_ram_manager", side_effect=KeyboardInterrupt):
        run_memory_cleaner()

def test_run_model_inspector():
    with patch("mlx_man.model_inspector.run_model_inspector") as mock_run:
        run_model_inspector()
        mock_run.assert_called_once()
        
    with patch("mlx_man.model_inspector.run_model_inspector", side_effect=KeyboardInterrupt):
        run_model_inspector()

def test_run_insights_history():
    with patch("mlx_man.insights_view.run_insights_history") as mock_run:
        run_insights_history()
        mock_run.assert_called_once()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
def test_action_run_server_cancel_gpu(mock_confirm, mock_select, mock_run, mock_footer):
    mock_select.return_value = None
    action_run_server()
    mock_run.assert_not_called()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_full_flow_chat(mock_get_models, mock_confirm, mock_select, mock_run, mock_footer, tmp_path):
    mock_get_models.return_value = {
        "org/model": {"name": "Test Model", "ram_estimate_gb": 10, "best_for": ["Chat"]}
    }
    
    mock_select.side_effect = [
        ("26624", "desc"),
        ("reasoning", "desc"),
        ("org/model", "desc"),
        ("chat", "desc")
    ]
    
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        model_dir = tmp_path / ".cache" / "huggingface" / "hub" / "models--org--model"
        model_dir.mkdir(parents=True)
        
        with patch("mlx_man.usage_tracker.record_usage") as mock_record:
            action_run_server()
            mock_record.assert_called_with("org/model")
            
        mock_run.assert_any_call(["sudo", "sysctl", "iogpu.wired_limit_mb=26624"])
        # verify mlx_lm chat was called
        calls = mock_run.mock_calls
        assert any("chat" in call.args[0] for call in calls)
        
@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_full_flow_server_not_installed(mock_get_models, mock_confirm, mock_select, mock_run, mock_footer, tmp_path):
    mock_get_models.return_value = {
        "org/model": {"name": "Test Model"}
    }
    
    mock_select.side_effect = [
        ("skip", "desc"),
        ("reasoning", "desc"),
        ("org/model", "desc"),
        ("server", "desc")
    ]
    
    mock_confirm.return_value = True
    
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        with patch("mlx_man.model_downloader.download_model", return_value=True) as mock_dl:
            with patch("mlx_man.opencode_sync.sync_opencode_config"):
                with patch("mlx_man.usage_tracker.record_usage"):
                    action_run_server()
                    mock_dl.assert_called_with("org/model")
                    
        calls = mock_run.mock_calls
        assert any("server" in call.args[0] for call in calls)

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
def test_action_run_server_cancel_role(mock_select, mock_footer):
    mock_select.side_effect = [("skip", ""), None]
    action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role", return_value={})
def test_action_run_server_no_models(mock_get, mock_confirm, mock_select, mock_footer):
    mock_select.side_effect = [("skip", ""), ("reasoning", "")]
    action_run_server()
    mock_confirm.assert_called_once()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_cancel_model(mock_get, mock_select, mock_footer):
    mock_get.return_value = {"org/model": {}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("cancel", "Cancel")]
    action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_refuse_download(mock_get, mock_confirm, mock_select, mock_footer, tmp_path):
    mock_get.return_value = {"org/model": {"name": "M"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", "")]
    mock_confirm.return_value = False
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_download_fails(mock_get, mock_confirm, mock_select, mock_footer, tmp_path):
    mock_get.return_value = {"org/model": {"name": "M"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", "")]
    mock_confirm.return_value = True
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        with patch("mlx_man.model_downloader.download_model", return_value=False):
            action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_cancel_action(mock_get, mock_select, mock_footer, tmp_path):
    mock_get.return_value = {"org/model": {"name": "M"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("cancel", "Cancel")]
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        (tmp_path / ".cache" / "huggingface" / "hub" / "models--org--model").mkdir(parents=True)
        action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run", side_effect=KeyboardInterrupt)
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_keyboard_interrupt_chat(mock_get, mock_select, mock_run, mock_footer, tmp_path):
    mock_get.return_value = {"org/model": {"name": "M"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("chat", "")]
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        (tmp_path / ".cache" / "huggingface" / "hub" / "models--org--model").mkdir(parents=True)
        with patch("mlx_man.usage_tracker.record_usage"):
            action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run", side_effect=KeyboardInterrupt)
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_keyboard_interrupt_server(mock_get, mock_select, mock_run, mock_footer, tmp_path):
    mock_get.return_value = {"org/model": {"name": "M"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("server", "")]
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        (tmp_path / ".cache" / "huggingface" / "hub" / "models--org--model").mkdir(parents=True)
        with patch("mlx_man.opencode_sync.sync_opencode_config"):
            with patch("mlx_man.usage_tracker.record_usage"):
                action_run_server()

from mlx_man.cli_actions import action_sync_models
from mlx_man.model_registry import MODEL_REGISTRY

@patch("mlx_man.cli_actions.tui_select")
def test_action_sync_models_back(mock_select):
    mock_select.return_value = "back"
    action_sync_models()
    
    mock_select.return_value = None
    action_sync_models()

@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_manager.get_installed_models")
@patch("mlx_man.cli_actions.tui_text_input")
def test_action_sync_models_search_empty(mock_input, mock_get, mock_select):
    mock_select.return_value = "search"
    mock_get.return_value = []
    action_sync_models()
    mock_input.assert_called_once()
    assert "already synced" in mock_input.call_args[1]["header"].renderable

@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_manager.get_installed_models")
@patch("mlx_man.cli_actions.tui_text_input")
@patch("mlx_man.model_registry.register_custom_model")
@patch("mlx_man.opencode_sync.sync_opencode_config")
def test_action_sync_models_search_found(mock_sync, mock_reg, mock_input, mock_get, mock_select):
    mock_get.return_value = [{"id": "unregistered/model"}]
    # First select "search", then select the model "unregistered/model"
    mock_select.side_effect = ["search", "unregistered/model"]
    
    action_sync_models()
    mock_reg.assert_called_once_with("unregistered/model", "model")
    mock_sync.assert_called_once()
    
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_manager.get_installed_models")
def test_action_sync_models_search_back(mock_get, mock_select):
    mock_get.return_value = [{"id": "unregistered/model"}]
    mock_select.side_effect = ["search", "back"]
    action_sync_models()
    
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_text_input")
def test_action_sync_models_custom_empty_path(mock_input, mock_select):
    mock_select.return_value = "custom"
    mock_input.return_value = None
    action_sync_models()
    
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_text_input")
@patch("pathlib.Path.exists")
def test_action_sync_models_custom_bad_path(mock_exists, mock_input, mock_select):
    mock_select.return_value = "custom"
    mock_input.side_effect = ["/bad/path", None]
    mock_exists.return_value = False
    action_sync_models()
    assert "does not exist" in mock_input.call_args[1]["header"].renderable

@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_text_input")
@patch("pathlib.Path.exists")
@patch("mlx_man.model_registry.register_custom_model")
@patch("mlx_man.opencode_sync.sync_opencode_config")
def test_action_sync_models_custom_success(mock_sync, mock_reg, mock_exists, mock_input, mock_select):
    mock_select.return_value = "custom"
    mock_input.side_effect = ["/good/path", "My Model", None]
    mock_exists.return_value = True
    action_sync_models()
    mock_reg.assert_called_once_with("/good/path", "My Model")
    mock_sync.assert_called_once()

