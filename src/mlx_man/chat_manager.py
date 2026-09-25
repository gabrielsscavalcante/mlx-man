import json
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

CONFIG_DIR = Path.home() / '.config' / 'mlx-man'
CHATS_DIR = CONFIG_DIR / 'chats'

@dataclass
class ChatSession:
    session_id: str
    model_id: str
    start_time: str
    messages: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "model_id": self.model_id,
            "start_time": self.start_time,
            "messages": self.messages
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            session_id=data.get("session_id", ""),
            model_id=data.get("model_id", ""),
            start_time=data.get("start_time", ""),
            messages=data.get("messages", [])
        )

def get_all_sessions() -> List[ChatSession]:
    """Retrieve all saved chat sessions."""
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    sessions = []
    for file in CHATS_DIR.glob("*.json"):
        try:
            with open(file, "r") as f:
                data = json.load(f)
                sessions.append(ChatSession.from_dict(data))
        except Exception:
            pass
    return sorted(sessions, key=lambda s: s.start_time, reverse=True)

def save_session(session: ChatSession):
    """Save a chat session to disk."""
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = CHATS_DIR / f"{session.session_id}.json"
    with open(file_path, "w") as f:
        json.dump(session.to_dict(), f, indent=2)

def load_session(session_id: str) -> Optional[ChatSession]:
    """Load a specific chat session."""
    file_path = CHATS_DIR / f"{session_id}.json"
    if file_path.exists():
        with open(file_path, "r") as f:
            return ChatSession.from_dict(json.load(f))
    return None

def delete_session(session_id: str):
    """Delete a chat session."""
    file_path = CHATS_DIR / f"{session_id}.json"
    if file_path.exists():
        os.remove(file_path)

def export_session(session: ChatSession, export_path: str, format_type: str = "markdown"):
    """Export a session to the specified path in Markdown or JSON format."""
    path = Path(export_path).expanduser().resolve()
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        
    if format_type == "json":
        with open(path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
    else:
        with open(path, "w") as f:
            f.write(f"# MLX-Man Chat Session\n")
            f.write(f"**Date:** {session.start_time}\n")
            f.write(f"**Model:** `{session.model_id}`\n\n")
            f.write(f"---\n\n")
            for msg in session.messages:
                role = "👤 You" if msg["role"] == "user" else "🤖 Assistant"
                f.write(f"### {role}\n\n")
                f.write(f"{msg['content']}\n\n")
