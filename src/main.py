"""
main.py — MLX-Man entry point.

MLX-Man is an Apple Silicon native MLX LLM manager and runner.
Downloads, manages, and serves local models via MLX (standalone runner, not an AI agent).
"""

import sys

from rich.console import Group
from rich.text import Text

from cli_dashboard import (
    get_banner,
    get_shortcuts_line,
    get_tip_line,
    get_system_status_footer,
    console,
)
from cli_select import centered_select

from cli_actions import (
    action_run_server,
    run_memory_cleaner,
    run_model_inspector,
    run_insights_history,
)


# ─────────────────────────────────────────────────────────────────────────────
# Menu items:  (display_label, return_value)  or  None = separator
# ─────────────────────────────────────────────────────────────────────────────
MENU_ITEMS = [
    ("🚀  Run LLM Server",      "run"),
    ("🧹  Clean Up RAM",         "clean"),
    ("📦  Manage Models",        "manage"),
    ("📊  Insights & History",   "insights"),
    None,                        # visual separator
    ("⏻   Exit",                 "exit"),
]


def main():
    """Main interactive loop with Spotlight-style fully centered UI."""
    # Enter Alternate Screen Buffer
    sys.__stdout__.write("\033[?1049h")
    sys.__stdout__.flush()

    goodbye = False

    try:
        while True:
            # Fix the tip for this menu cycle (so it doesn't change per keypress)
            below_panel = Group(
                get_shortcuts_line(),
                Text(""),
                get_tip_line(),
            )

            choice = centered_select(
                items=MENU_ITEMS,
                header=get_banner(),
                below_panel=below_panel,
                footer_status=get_system_status_footer(),
            )

            if not choice or choice == "exit":
                goodbye = True
                break

            if choice == "run":
                action_run_server()
            elif choice == "clean":
                run_memory_cleaner()
            elif choice == "manage":
                run_model_inspector()
            elif choice == "insights":
                run_insights_history()

            if choice != "exit":
                console.print(
                    "\n  [dim]Press Enter to return to the main menu...[/]",
                    end="",
                )
                input()

    except KeyboardInterrupt:
        goodbye = True

    finally:
        # Exit Alternate Screen Buffer cleanly — no artifacts left behind
        sys.__stdout__.write("\033[?1049l")
        sys.__stdout__.flush()

    # Print goodbye AFTER exiting alt screen so the user actually sees it
    if goodbye:
        console.print("\n  [green]✔[/]  Goodbye! 👋\n")


if __name__ == "__main__":
    main()
