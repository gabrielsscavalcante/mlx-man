from typing import Optional
from rich.console import Group
from rich.text import Text
from rich.panel import Panel
from rich import box
from pathlib import Path
import os

from mlx_man.ui_components import create_header_panel, create_warning_panel
from mlx_man.tui_engine import tui_text_input, tui_table_select, tui_confirm, tui_select
from mlx_man.cli_dashboard import get_system_status_footer
from mlx_man.chat_manager import get_all_sessions, load_session, delete_session, export_session, ChatSession

def action_chat_history():
    """Interactive flow to view, resume, export, and delete past chats."""
    while True:
        sessions = get_all_sessions()
        
        if not sessions:
            tui_text_input(
                prompt="Press Enter to return to main menu...",
                header=create_header_panel("No chat history found.", "Chat History"),
                footer=get_system_status_footer()
            )
            return

        columns = [
            {"header": "Date", "style": "bold white"},
            {"header": "Model", "style": "cyan"},
            {"header": "Msgs", "justify": "right", "style": "dim"},
            {"header": "Excerpt", "style": "dim"},
        ]
        
        def format_row(s: ChatSession):
            excerpt = s.messages[0]['content'][:40] + "..." if s.messages else "Empty"
            excerpt = excerpt.replace("\n", " ")
            date_str = s.start_time.split("T")[0] + " " + s.start_time.split("T")[1][:5]
            return [
                date_str,
                s.model_id.split("/")[-1],
                str(len(s.messages)),
                excerpt
            ]
            
        header = create_header_panel(Text(f"{len(sessions)} Past Sessions", style="green"), "Chat History")
        
        choice = tui_table_select(
            title="Select a chat:",
            columns=columns,
            data=sessions,
            row_func=format_row,
            header=header,
            footer=get_system_status_footer()
        )
        
        if not choice:
            break
            
        # Sub-menu for the selected chat
        action_header = create_header_panel(Text(f"Model: {choice.model_id}", style="cyan"), f"Chat: {choice.start_time}")
        action = tui_select(
            title="What would you like to do?",
            choices=[
                ("resume", "▶️ Resume Chat"),
                ("export", "💾 Export Chat (.md / .json)"),
                ("delete", "🗑️ Delete Chat"),
                ("back", "↩ Back")
            ],
            format_func=lambda x: x[1],
            header=action_header,
            footer=get_system_status_footer()
        )
        
        if not action or action[0] == "back":
            continue
            
        if action[0] == "delete":
            confirm = tui_confirm(
                prompt="Are you sure you want to delete this chat?",
                header=create_warning_panel("This action cannot be undone.", "Confirm Deletion"),
                footer=get_system_status_footer(),
                default=False
            )
            if confirm:
                delete_session(choice.session_id)
        elif action[0] == "resume":
            from mlx_man.native_chat_view import run_chat_session
            run_chat_session(choice.model_id, choice.session_id)
        elif action[0] == "export":
            # Prompt for export path
            default_path = str(Path.home() / "Documents" / f"mlx_chat_{choice.session_id}.md")
            
            format_choice = tui_select(
                title="Select Export Format:",
                choices=[("markdown", "📝 Markdown (.md) - Recommended"), ("json", "⚙️ JSON (.json)")],
                format_func=lambda x: x[1],
                header=action_header,
                footer=get_system_status_footer()
            )
            
            if not format_choice:
                continue
                
            fmt = format_choice[0]
            default_path = str(Path.home() / "Documents" / f"mlx_chat_{choice.session_id}.{'md' if fmt == 'markdown' else 'json'}")
            
            custom_path = tui_text_input(
                prompt=f"Enter export path (default: {default_path}):",
                header=create_header_panel("Export Chat", "Export Destination"),
                footer=get_system_status_footer()
            )
            
            final_path = custom_path.strip() if custom_path and custom_path.strip() else default_path
            
            try:
                export_session(choice, final_path, format_type=fmt)
                tui_text_input(
                    prompt="Press Enter to continue...",
                    header=create_header_panel(Text(f"Successfully exported to:\n{final_path}", style="green"), "Export Success"),
                    footer=get_system_status_footer()
                )
            except Exception as e:
                tui_text_input(
                    prompt="Press Enter to continue...",
                    header=create_warning_panel(f"Export failed:\n{e}", "Export Error"),
                    footer=get_system_status_footer()
                )

