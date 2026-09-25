"""Tests for project setup, packaging, and configuration infrastructure."""

import importlib
import os

import pytest


class TestPackageStructure:
    """Verify the Python package is correctly structured."""

    def test_package_is_importable(self):
        """The mlx_man package can be imported."""
        import mlx_man
        assert hasattr(mlx_man, "__version__")

    def test_version_format(self):
        """Version string follows semver format."""
        import mlx_man
        parts = mlx_man.__version__.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_version_is_current(self):
        """Version matches the expected release."""
        import mlx_man
        assert mlx_man.__version__ == "0.4.0"

    def test_all_modules_importable(self):
        """All package modules can be imported without errors."""
        modules = [
            "mlx_man.main",
            "mlx_man.cli_actions",
            "mlx_man.cli_dashboard",
            "mlx_man.cli_layout",
            "mlx_man.cli_select",
            "mlx_man.insights_view",
            "mlx_man.model_downloader",
            "mlx_man.model_inspector",
            "mlx_man.model_manager",
            "mlx_man.model_registry",
            "mlx_man.opencode_sync",
            "mlx_man.process_service",
            "mlx_man.ram_manager_view",
            "mlx_man.usage_tracker",
        ]
        for mod_name in modules:
            mod = importlib.import_module(mod_name)
            assert mod is not None, f"Failed to import {mod_name}"

    def test_entry_point_function_exists(self):
        """The main() entry point function exists and is callable."""
        from mlx_man.main import main
        assert callable(main)


class TestConfigDirectory:
    """Verify XDG-compliant configuration directory handling."""

    def test_get_config_dir_creates_directory(self, tmp_path, monkeypatch):
        """get_config_dir() creates ~/.config/mlx-man if it doesn't exist."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        # Re-import to pick up the env change
        import importlib
        import mlx_man.usage_tracker as ut
        importlib.reload(ut)
        config_dir = ut.get_config_dir()
        assert os.path.isdir(config_dir)
        assert config_dir == str(tmp_path / "mlx-man")

    def test_get_config_dir_respects_xdg(self, tmp_path, monkeypatch):
        """get_config_dir() respects XDG_CONFIG_HOME environment variable."""
        custom_config = tmp_path / "custom_config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_config))
        import importlib
        import mlx_man.usage_tracker as ut
        importlib.reload(ut)
        config_dir = ut.get_config_dir()
        assert str(custom_config) in config_dir

    def test_history_file_in_config_dir(self, tmp_path, monkeypatch):
        """HISTORY_FILE is located inside the config directory."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        import importlib
        import mlx_man.usage_tracker as ut
        importlib.reload(ut)
        assert "mlx-man" in ut.HISTORY_FILE
        assert "usage_history.json" in ut.HISTORY_FILE

    def test_legacy_history_migration(self, tmp_path, monkeypatch):
        """Legacy .model_usage_history.json is migrated to new location."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        import importlib
        import mlx_man.usage_tracker as ut
        importlib.reload(ut)
        # Migration should not raise even if legacy file doesn't exist
        ut._migrate_legacy_history()

    def test_record_and_load_usage(self, tmp_path, monkeypatch):
        """record_usage writes data that load_data can read back."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        import importlib
        import mlx_man.usage_tracker as ut
        importlib.reload(ut)
        
        ut.record_usage("test/model-1")
        data = ut.load_data()
        assert "test/model-1" in data
        assert data["test/model-1"]["count"] == 1
        assert data["test/model-1"]["last_used"] is not None

        ut.record_usage("test/model-1")
        data = ut.load_data()
        assert data["test/model-1"]["count"] == 2


class TestStartLlmScript:
    """Verify the shell launcher script has no hardcoded user paths."""

    def test_no_hardcoded_user_paths(self):
        """start_llm.sh contains no hardcoded user-specific paths."""
        script_path = os.path.join(
            os.path.dirname(__file__), '..', 'start_llm.sh'
        )
        with open(script_path) as f:
            content = f.read()
        # Should not contain any /Users/username/ paths
        assert "/Users/gabrielcavalcante/" not in content
        assert "opencode_mlx_qwen" not in content

    def test_uses_python_m_mlx_man(self):
        """start_llm.sh invokes python -m mlx_man."""
        script_path = os.path.join(
            os.path.dirname(__file__), '..', 'start_llm.sh'
        )
        with open(script_path) as f:
            content = f.read()
        assert "-m mlx_man" in content
