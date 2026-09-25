"""
test_cli.py — Tests for the main menu routing and action dispatching.

All tests mock the centered_select() selector and the rendering layers
to verify that user selections route to the correct action handlers
without side effects or actual terminal I/O.
"""

from unittest.mock import patch, MagicMock

from mlx_man.main import main
from mlx_man.cli_actions import action_run_server


# ─────────────────────────────────────────────────────────────────────────────
# Main Menu Routing Tests
# ─────────────────────────────────────────────────────────────────────────────

@patch('mlx_man.main.action_run_server')
@patch('mlx_man.main.centered_select')
@patch('builtins.input', return_value='')
def test_main_menu_routing_run_server(mock_input, mock_select, mock_run_server):
    """Selecting 'run' routes to action_run_server."""
    mock_select.side_effect = ['run', 'exit']
    main()
    mock_run_server.assert_called_once()


@patch('mlx_man.main.run_memory_cleaner')
@patch('mlx_man.main.centered_select')
@patch('builtins.input', return_value='')
def test_main_menu_routing_clean_ram(mock_input, mock_select, mock_clean):
    """Selecting 'clean' routes to run_memory_cleaner."""
    mock_select.side_effect = ['clean', 'exit']
    main()
    mock_clean.assert_called_once()


@patch('mlx_man.main.run_model_inspector')
@patch('mlx_man.main.centered_select')
@patch('builtins.input', return_value='')
def test_main_menu_routing_manage_models(mock_input, mock_select, mock_manage):
    """Selecting 'manage' routes to run_model_inspector."""
    mock_select.side_effect = ['manage', 'exit']
    main()
    mock_manage.assert_called_once()


@patch('mlx_man.main.run_insights_history')
@patch('mlx_man.main.centered_select')
@patch('builtins.input', return_value='')
def test_main_menu_routing_insights(mock_input, mock_select, mock_insights):
    """Selecting 'insights' routes to run_insights_history."""
    mock_select.side_effect = ['insights', 'exit']
    main()
    mock_insights.assert_called_once()


@patch('mlx_man.main.centered_select')
def test_main_menu_exit_on_none(mock_select):
    """Returning None from the selector (Escape) exits gracefully."""
    mock_select.return_value = None
    main()  # Should not raise


@patch('mlx_man.main.centered_select')
def test_main_menu_exit_on_exit_choice(mock_select):
    """Selecting 'exit' exits gracefully."""
    mock_select.return_value = 'exit'
    main()  # Should not raise


# ─────────────────────────────────────────────────────────────────────────────
# UI Rendering Tests (no-crash assertions using Console(record=True))
# ─────────────────────────────────────────────────────────────────────────────

def test_banner_renders_without_error():
    """The banner component renders without raising exceptions."""
    from rich.console import Console
    from mlx_man.cli_dashboard import get_banner

    c = Console(record=True, width=100)
    c.print(get_banner())
    output = c.export_text()
    assert "MLX" in output or "██" in output
    assert "not an AI agent" in output


def test_shortcuts_renders_without_error():
    """The shortcuts line renders without raising exceptions."""
    from rich.console import Console
    from mlx_man.cli_dashboard import get_shortcuts_line

    c = Console(record=True, width=100)
    c.print(get_shortcuts_line())
    output = c.export_text()
    assert "navigate" in output


def test_tip_renders_without_error():
    """The tip line renders without raising exceptions."""
    from rich.console import Console
    from mlx_man.cli_dashboard import get_tip_line

    c = Console(record=True, width=100)
    c.print(get_tip_line())
    output = c.export_text()
    assert "Tip" in output


def test_system_status_footer_returns_string():
    """System status footer returns a non-empty string with RAM info."""
    from mlx_man.cli_dashboard import get_system_status_footer

    result = get_system_status_footer()
    assert isinstance(result, str)
    assert len(result) > 0
    assert "GB RAM" in result


def test_legacy_get_system_dashboard():
    """Legacy get_system_dashboard() still returns a renderable Table."""
    from rich.console import Console
    from rich.table import Table
    from mlx_man.cli_dashboard import get_system_dashboard

    result = get_system_dashboard()
    assert isinstance(result, Table)

    c = Console(record=True, width=100)
    c.print(result)
    output = c.export_text()
    assert "System Status" in output


def test_menu_panel_renders_inside_centered_frame():
    """
    Simulate what centered_select renders: menu items inside a Panel,
    wrapped in a Group with header and footer content.
    """
    from rich.console import Console, Group
    from rich.text import Text
    from rich.panel import Panel
    from rich.align import Align
    from rich import box
    from mlx_man.cli_dashboard import get_banner, get_shortcuts_line, get_tip_line

    items = [
        ("🚀  Run LLM Server", "run"),
        ("🧹  Clean Up RAM", "clean"),
        None,
        ("⏻   Exit", "exit"),
    ]

    menu_lines = []
    for i, item in enumerate(items):
        if item is None:
            menu_lines.append(Text("  ──────────────────", style="bright_black"))
        else:
            label, _ = item
            if i == 0:
                menu_lines.append(Text(f" ▸ {label}", style="bold white"))
            else:
                menu_lines.append(Text(f"   {label}", style="dim white"))

    panel = Panel(
        Group(*menu_lines),
        box=box.ROUNDED,
        border_style="bright_black",
        width=50,
        padding=(1, 1),
    )

    full = Group(
        get_banner(),
        Text(""),
        Align.center(panel),
        Text(""),
        get_shortcuts_line(),
        Text(""),
        get_tip_line(),
    )

    c = Console(record=True, width=100)
    c.print(full)
    output = c.export_text()

    assert "╭" in output
    assert "╰" in output
    assert "Run LLM Server" in output
    assert "Exit" in output
    assert "navigate" in output
