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
    with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
                                action_run_server()
    mock_run.assert_not_called()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.native_chat_view.run_chat_session")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_full_flow_chat(mock_get_models, mock_confirm, mock_select, mock_run, mock_chat, mock_footer, tmp_path):
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
            with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
                                action_run_server()
            mock_record.assert_called_with("org/model")
            
        mock_run.assert_any_call(["sudo", "sysctl", "iogpu.wired_limit_mb=26624"])
        # verify mlx_lm chat was called
        calls = mock_run.mock_calls
        
        
@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role")
@patch("mlx_man.cli_actions.tui_text_input", return_value="8081")
def test_action_run_server_full_flow_server_not_installed(mock_text, mock_get_models, mock_confirm, mock_select, mock_run, mock_footer, tmp_path):
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
                    with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
                                action_run_server()
                    mock_dl.assert_called_with("org/model")
                    
        

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
def test_action_run_server_cancel_role(mock_select, mock_footer):
    mock_select.side_effect = [("skip", ""), None]
    with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
                                action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role", return_value={})
def test_action_run_server_no_models(mock_get, mock_confirm, mock_select, mock_footer):
    mock_select.side_effect = [("skip", ""), ("reasoning", "")]
    with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
                                action_run_server()
    mock_confirm.assert_called_once()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_cancel_model(mock_get, mock_select, mock_footer):
    mock_get.return_value = {"org/model": {}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("cancel", "Cancel")]
    with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
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
        with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
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
            with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
                                action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_cancel_action(mock_get, mock_select, mock_footer, tmp_path):
    mock_get.return_value = {"org/model": {"name": "M"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("cancel", "Cancel")]
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        (tmp_path / ".cache" / "huggingface" / "hub" / "models--org--model").mkdir(parents=True)
        with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
                                action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.native_chat_view.run_chat_session", side_effect=KeyboardInterrupt)
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
def test_action_run_server_keyboard_interrupt_chat(mock_get, mock_select, mock_chat, mock_run, mock_footer, tmp_path):
    mock_get.return_value = {"org/model": {"name": "M"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("chat", "")]
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        (tmp_path / ".cache" / "huggingface" / "hub" / "models--org--model").mkdir(parents=True)
        with patch("mlx_man.usage_tracker.record_usage"):
            with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
                                action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.subprocess.run", side_effect=KeyboardInterrupt)
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.model_registry.get_models_by_role")
@patch("mlx_man.cli_actions.tui_text_input", return_value="8080")
@patch("mlx_man.cli_actions.tui_confirm", return_value=True)
def test_action_run_server_keyboard_interrupt_server(mock_confirm, mock_text, mock_get, mock_select, mock_run, mock_footer, tmp_path):
    mock_get.return_value = {"org/model": {"name": "M"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("server", "")]
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        (tmp_path / ".cache" / "huggingface" / "hub" / "models--org--model").mkdir(parents=True)
        with patch("mlx_man.opencode_sync.sync_opencode_config"):
            with patch("mlx_man.usage_tracker.record_usage"):
                with patch("builtins.input"):
                            with patch("mlx_man.server_manager.start_server"):
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


@patch("mlx_man.server_manager.get_running_servers", return_value={})
def test_action_manage_server_no_server(mock_get):
    from mlx_man.cli_actions import action_manage_server
    action_manage_server()

@patch("mlx_man.tui_engine.tui_select", return_value=("back", ""))
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"model_id": "org/model", "port": 8080}})
def test_action_manage_server_back(mock_get, mock_select):
    from mlx_man.cli_actions import action_manage_server
    action_manage_server()

@patch("mlx_man.tui_engine.tui_select", return_value={})
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"model_id": "org/model", "port": 8080}})
def test_action_manage_server_none(mock_get, mock_select):
    from mlx_man.cli_actions import action_manage_server
    action_manage_server()

@patch("mlx_man.server_manager.stop_server")
@patch("mlx_man.tui_engine.tui_confirm", return_value=True)
@patch("mlx_man.tui_engine.tui_select", return_value=("stop_8080", ""))
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"model_id": "org/model", "port": 8080}})
def test_action_manage_server_stop(mock_get, mock_select, mock_confirm, mock_stop):
    from mlx_man.cli_actions import action_manage_server
    action_manage_server()
    mock_stop.assert_called_once()

@patch("mlx_man.server_manager.stop_server")
@patch("mlx_man.tui_engine.tui_confirm", return_value=False)
@patch("mlx_man.tui_engine.tui_select", return_value=("stop_8080", ""))
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"model_id": "org/model", "port": 8080}})
def test_action_manage_server_stop_cancel(mock_get, mock_select, mock_confirm, mock_stop):
    from mlx_man.cli_actions import action_manage_server
    action_manage_server()
    mock_stop.assert_not_called()

@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.server_manager.LOG_FILE")
@patch("mlx_man.tui_engine.tui_select", return_value=("logs", ""))
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"model_id": "org/model", "port": 8080}})
def test_action_manage_server_logs(mock_get, mock_select, mock_log_file, mock_run):
    from mlx_man.cli_actions import action_manage_server
    mock_log_file.exists.return_value = True
    action_manage_server()
    mock_run.assert_called()
    assert "less" in str(mock_run.call_args)

@patch("mlx_man.cli_actions.subprocess.run")
@patch("mlx_man.server_manager.LOG_FILE")
@patch("mlx_man.tui_engine.tui_select", return_value=("logs", ""))
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"model_id": "org/model", "port": 8080}})
def test_action_manage_server_logs_no_file(mock_get, mock_select, mock_log_file, mock_run):
    from mlx_man.cli_actions import action_manage_server
    mock_log_file.exists.return_value = False
    action_manage_server()
    assert not any("less" in str(c) for c in mock_run.mock_calls)

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_text_input", return_value="8080")
@patch("mlx_man.cli_actions.tui_confirm", side_effect=[True, False]) # DL yes, RAM warning no
@patch("mlx_man.model_registry.get_models_by_role")
@patch("mlx_man.cli_dashboard.get_free_ram_gb", return_value=8.0)
def test_action_run_server_ram_warning_cancel(mock_free_ram, mock_get_models, mock_confirm, mock_text, mock_select, mock_footer, tmp_path):
    mock_get_models.return_value = {"org/model": {"name": "Test", "ram_estimate_gb": "15.0"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("server", "")]
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        with patch("mlx_man.model_downloader.download_model", return_value=True):
            with patch("mlx_man.opencode_sync.sync_opencode_config"):
                from mlx_man.cli_actions import action_run_server
                action_run_server()

@patch("mlx_man.cli_dashboard.get_system_status_footer", return_value="footer")
@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_text_input", return_value="8080")
@patch("mlx_man.cli_actions.tui_confirm", side_effect=[True, True]) # DL yes, RAM warning yes
@patch("mlx_man.model_registry.get_models_by_role")
@patch("mlx_man.cli_dashboard.get_free_ram_gb", return_value=8.0)
def test_action_run_server_ram_warning_proceed(mock_free_ram, mock_get_models, mock_confirm, mock_text, mock_select, mock_footer, tmp_path):
    mock_get_models.return_value = {"org/model": {"name": "Test", "ram_estimate_gb": ">invalid"}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("server", "")]
    with patch("mlx_man.cli_actions.Path.home", return_value=tmp_path):
        with patch("mlx_man.model_downloader.download_model", return_value=True):
            with patch("mlx_man.opencode_sync.sync_opencode_config"):
                with patch("mlx_man.usage_tracker.record_usage"):
                    with patch("builtins.input"):
                        with patch("mlx_man.server_manager.start_server"):
                            from mlx_man.cli_actions import action_run_server
                            action_run_server()

@patch("mlx_man.server_manager.stop_server")
@patch("mlx_man.tui_engine.tui_confirm", return_value=True)
@patch("mlx_man.tui_engine.tui_select", return_value=("stop_all", ""))
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"model_id": "a"}, "8081": {"model_id": "b"}})
def test_action_manage_server_stop_all(mock_get, mock_select, mock_confirm, mock_stop):
    from mlx_man.cli_actions import action_manage_server
    action_manage_server()

@patch("mlx_man.server_manager.stop_server")
@patch("mlx_man.tui_engine.tui_confirm", return_value=True)
@patch("mlx_man.tui_engine.tui_select", return_value=("stop_8081", ""))
@patch("mlx_man.server_manager.get_running_servers", return_value={"8080": {"model_id": "a"}, "8081": {"model_id": "b"}})
def test_action_manage_server_stop_specific(mock_get, mock_select, mock_confirm, mock_stop):
    from mlx_man.cli_actions import action_manage_server
    action_manage_server()

@patch("mlx_man.cli_actions.tui_text_input")
@patch("mlx_man.cli_actions.tui_select")
@patch("subprocess.run")
@patch("mlx_man.model_registry.register_custom_model")
def test_action_quantize_model_success(mock_register, mock_run, mock_select, mock_input):
    from mlx_man.cli_actions import action_quantize_model
    from pathlib import Path
    import sys
    
    mock_input.side_effect = ["my_org/my_model", ""]
    mock_select.side_effect = ["4"]
    
    action_quantize_model()
    
    dest_path = Path.home() / ".config" / "mlx-man" / "quantized" / "my_model-4bit"
    
    # Check that subprocess.run was called with the right args
    called_args = mock_run.call_args[0][0]
    assert called_args == [
        sys.executable, "-m", "mlx_lm.convert",
        "--hf-path", "my_org/my_model",
        "--mlx-path", str(dest_path),
        "-q", "--q-bits", "4"
    ]
    
    mock_register.assert_called_once_with(str(dest_path), "my_model (4-bit Quantized)")

@patch("mlx_man.cli_actions.tui_text_input")
def test_action_quantize_model_cancel_repo(mock_input):
    from mlx_man.cli_actions import action_quantize_model
    mock_input.return_value = ""
    action_quantize_model()

@patch("mlx_man.cli_actions.tui_text_input")
@patch("mlx_man.cli_actions.tui_select")
def test_action_quantize_model_cancel_bits(mock_select, mock_input):
    from mlx_man.cli_actions import action_quantize_model
    mock_input.return_value = "org/model"
    mock_select.return_value = "back"
    action_quantize_model()

@patch("mlx_man.cli_actions.tui_text_input")
@patch("mlx_man.cli_actions.tui_select")
@patch("subprocess.run")
def test_action_quantize_model_subprocess_error(mock_run, mock_select, mock_input):
    from mlx_man.cli_actions import action_quantize_model
    import subprocess
    
    mock_input.side_effect = ["org/model", ""]
    mock_select.return_value = "8"
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
    
    action_quantize_model()
    
@patch("mlx_man.cli_actions.tui_text_input")
@patch("mlx_man.cli_actions.tui_select")
@patch("subprocess.run")
def test_action_quantize_model_exception(mock_run, mock_select, mock_input):
    from mlx_man.cli_actions import action_quantize_model
    
    mock_input.side_effect = ["org/model", ""]
    mock_select.return_value = "8"
    mock_run.side_effect = Exception("boom")
    
    action_quantize_model()

@patch("mlx_lm.load")
@patch("mlx_lm.stream_generate")
@patch("subprocess.run")
def test_action_run_benchmark_success(mock_sub_run, mock_stream, mock_load):
    from mlx_man.cli_actions import action_run_benchmark
    import time
    
    mock_model, mock_tokenizer = MagicMock(), MagicMock()
    mock_tokenizer.apply_chat_template = MagicMock(return_value="formatted_prompt")
    mock_tokenizer.chat_template = "exists"
    mock_load.return_value = (mock_model, mock_tokenizer)
    
    # Simulate 50 tokens
    def mock_stream_gen(*args, **kwargs):
        for _ in range(50):
            time.sleep(0.001)
            yield "tok"
    
    mock_stream.side_effect = mock_stream_gen
    
    # Mock subprocess.run for sysctl
    mock_proc1 = MagicMock()
    mock_proc1.stdout = "Apple M2 Max"
    mock_proc2 = MagicMock()
    mock_proc2.stdout = str(32 * (1024**3))
    mock_sub_run.side_effect = [mock_proc1, mock_proc2]
    
    action_run_benchmark("org/model")

@patch("mlx_lm.load", side_effect=Exception("Load failed"))
def test_action_run_benchmark_load_failure(mock_load):
    from mlx_man.cli_actions import action_run_benchmark
    import pytest
    with pytest.raises(RuntimeError, match="Failed to load model"):
        action_run_benchmark("org/model")

@patch("mlx_lm.load")
@patch("mlx_lm.stream_generate")
def test_action_run_benchmark_no_tokens(mock_stream, mock_load):
    from mlx_man.cli_actions import action_run_benchmark
    import pytest
    
    mock_load.return_value = (MagicMock(), MagicMock())
    
    # Simulate 0 tokens
    def mock_stream_gen(*args, **kwargs):
        return []
        yield
    
    mock_stream.side_effect = mock_stream_gen
    
    with pytest.raises(RuntimeError, match="Model failed to generate tokens."):
        action_run_benchmark("org/model")

@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_text_input")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role")
@patch("mlx_man.cli_dashboard.get_free_ram_gb", return_value=32.0)
@patch("mlx_man.cli_actions.Path.home")
@patch("builtins.input")
@patch("mlx_man.cli_actions.action_run_benchmark")
def test_action_run_server_benchmark_success(mock_bench, mock_input, mock_home, mock_ram, mock_get_models, mock_confirm, mock_text, mock_select, tmp_path):
    from mlx_man.cli_actions import action_run_server
    mock_get_models.return_value = {"org/model": {"name": "Test", "ram_estimate_gb": 8.0}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("benchmark", "")]
    mock_home.return_value = tmp_path
    
    with patch("mlx_man.model_downloader.download_model", return_value=True):
        with patch("mlx_man.opencode_sync.sync_opencode_config"):
            with patch("mlx_man.usage_tracker.record_usage"):
                action_run_server()
                mock_bench.assert_called_once_with("org/model")

@patch("mlx_man.cli_actions.tui_select")
@patch("mlx_man.cli_actions.tui_text_input")
@patch("mlx_man.cli_actions.tui_confirm")
@patch("mlx_man.model_registry.get_models_by_role")
@patch("mlx_man.cli_dashboard.get_free_ram_gb", return_value=32.0)
@patch("mlx_man.cli_actions.Path.home")
@patch("builtins.input")
@patch("mlx_man.cli_actions.action_run_benchmark", side_effect=Exception("Bench Error"))
def test_action_run_server_benchmark_fail(mock_bench, mock_input, mock_home, mock_ram, mock_get_models, mock_confirm, mock_text, mock_select, tmp_path):
    from mlx_man.cli_actions import action_run_server
    mock_get_models.return_value = {"org/model": {"name": "Test", "ram_estimate_gb": 8.0}}
    mock_select.side_effect = [("skip", ""), ("reasoning", ""), ("org/model", ""), ("benchmark", "")]
    mock_home.return_value = tmp_path
    
    with patch("mlx_man.model_downloader.download_model", return_value=True):
        with patch("mlx_man.opencode_sync.sync_opencode_config"):
            with patch("mlx_man.usage_tracker.record_usage"):
                action_run_server()
                mock_bench.assert_called_once_with("org/model")

@patch("mlx_lm.load")
@patch("mlx_lm.stream_generate")
@patch("subprocess.run")
@patch("mlx_man.cli_actions.Path.home")
def test_action_run_benchmark_exceptions(mock_home, mock_sub_run, mock_stream, mock_load, tmp_path):
    from mlx_man.cli_actions import action_run_benchmark
    import time
    
    mock_model, mock_tokenizer = MagicMock(), MagicMock()
    mock_tokenizer.chat_template = "exists"
    mock_tokenizer.apply_chat_template.side_effect = Exception("Template fail")
    mock_load.return_value = (mock_model, mock_tokenizer)
    
    def mock_stream_gen(*args, **kwargs):
        for _ in range(50):
            yield "tok"
    
    mock_stream.side_effect = mock_stream_gen
    
    mock_sub_run.side_effect = Exception("Sysctl fail")
    
    mock_home.return_value = tmp_path
    bench_dir = tmp_path / ".config" / "mlx-man"
    bench_dir.mkdir(parents=True)
    bench_file = bench_dir / "benchmarks.json"
    bench_file.write_text("invalid json")
    
    action_run_benchmark("org/model")

