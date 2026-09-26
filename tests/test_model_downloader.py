import pytest
from unittest.mock import patch, MagicMock
import sys
try:
    import mlx_lm.utils
except ImportError:
    pass

from mlx_man.model_downloader import download_model

def test_download_model_invalid_id():
    assert download_model("invalid") is False

def test_download_model_url():
    with patch("huggingface_hub.snapshot_download") as mock_dl:
        assert download_model("https://huggingface.co/org/model") is True
        mock_dl.assert_called_once_with(repo_id="org/model", resume_download=True, allow_patterns=["*.safetensors", "*.safetensors.index.json", "*.json", "*.model", "*.tiktoken", "*.txt", "*.md"])

def test_download_model_keyboard_interrupt():
    with patch("huggingface_hub.snapshot_download", side_effect=KeyboardInterrupt):
        assert download_model("org/model") is False

def test_download_model_exception():
    with patch("huggingface_hub.snapshot_download", side_effect=ValueError("Test")):
        assert download_model("org/model") is False

def test_download_model_import_error_mlx_fallback():
    with patch.dict("sys.modules", {"huggingface_hub": None}):
        with patch("mlx_lm.utils.get_model_path", create=True) as mock_mlx:
            assert download_model("org/model") is True
            mock_mlx.assert_called_once_with("org/model")

def test_download_model_import_error_both():
    with patch.dict("sys.modules", {"huggingface_hub": None, "mlx_lm.utils": None}):
        assert download_model("org/model") is False

def test_download_model_main_success():
    with patch("sys.argv", ["script", "org/model"]):
        with patch("huggingface_hub.snapshot_download") as mock_dl:
            with pytest.raises(SystemExit) as e:
                import runpy
                runpy.run_module("mlx_man.model_downloader", run_name="__main__")
            assert e.value.code == 0
            mock_dl.assert_called_once()

def test_download_model_main_fail():
    with patch("sys.argv", ["script", "invalid"]):
        with pytest.raises(SystemExit) as e:
            import runpy
            runpy.run_module("mlx_man.model_downloader", run_name="__main__")
        assert e.value.code == 1

def test_download_model_main_no_args():
    with patch("sys.argv", ["script"]):
        with pytest.raises(SystemExit) as e:
            import runpy
            runpy.run_module("mlx_man.model_downloader", run_name="__main__")
        assert e.value.code == 1
