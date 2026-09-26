"""
main.py — MLX-Man entry point.

MLX-Man is an Apple Silicon native MLX LLM manager and runner.
Downloads, manages, and serves local models via MLX (standalone runner, not an AI agent).
"""

import sys

from rich.console import Group
from rich.text import Text

from mlx_man.cli_dashboard import (
    get_banner,
    get_tip_line,
    get_system_status_footer,
    console,
)

from mlx_man.hub_search_view import action_search_hub
from mlx_man.chat_history_view import action_chat_history
from mlx_man.cli_actions import (
    action_run_server,
    run_memory_cleaner,
    run_model_inspector,
    run_insights_history,
    action_sync_models,
    action_manage_server,
)


def get_menu_items():
    from mlx_man.server_manager import get_running_server
    items = [
        ("🚀  Run LLM Server",      "run"),
    ]
    
    server = get_running_server()
    if server:
        model_short = server["model_id"].split("/")[-1]
        items.append((f"🟢  Active Server: {model_short}", "server_manage"))
        
    items.extend([
        ("🧹  Clean Up RAM",         "clean"),
        ("📦  Manage Models",        "manage"),
        ("📊  Insights & History",   "insights"),
        ("💬  Chat History",         "history"),
        ("🔄  Sync Models",          "sync"),
        None,                        # visual separator
        ("⏻   Exit",                 "exit"),
    ])
    return items


from mlx_man.tui_engine import main_menu_select

def main():
    """Main interactive loop with Spotlight-style fully centered UI."""
    goodbye = False

    try:
        while True:
            below_panel = Group(
                get_tip_line(),
            )

            choice = main_menu_select(
                items=get_menu_items(),
                header=get_banner(),
                below_panel=below_panel,
                footer=get_system_status_footer(),
            )

            if not choice or choice == "exit":
                goodbye = True
                break

            if choice == "run":
                action_run_server()
            elif choice == "server_manage":
                action_manage_server()
            elif choice == "clean":
                run_memory_cleaner()
            elif choice == "manage":
                run_model_inspector()
            elif choice == "insights":
                run_insights_history()
            elif choice == "history":
                action_chat_history()
            elif choice == "sync":
                action_sync_models()

    except KeyboardInterrupt:
        goodbye = True

    if goodbye:
        print("\n  \033[32m✔\033[0m  Goodbye! 👋\n")

if __name__ == "__main__":  # pragma: no cover
    main()
