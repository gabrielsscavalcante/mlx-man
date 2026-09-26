import os
from pathlib import Path
from datetime import datetime

def read_file(path: str) -> str:
    """Reads the contents of a local file."""
    try:
        p = Path(path).resolve()
        if not p.exists():
            return f"Error: File '{path}' does not exist."
        if not p.is_file():
            return f"Error: '{path}' is not a file."
        # Safety check: limit size
        if p.stat().st_size > 1024 * 1024: # 1MB limit
            return f"Error: File '{path}' is too large to read (max 1MB)."
        return p.read_text(errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"

def list_directory(path: str = ".") -> str:
    """Lists files and folders in a given directory."""
    try:
        p = Path(path).resolve()
        if not p.exists():
            return f"Error: Directory '{path}' does not exist."
        if not p.is_dir():
            return f"Error: '{path}' is not a directory."
        
        entries = []
        for entry in p.iterdir():
            prefix = "[DIR] " if entry.is_dir() else "[FILE]"
            entries.append(f"{prefix} {entry.name}")
            
        if not entries:
            return "Directory is empty."
        return "\n".join(sorted(entries))
    except Exception as e:
        return f"Error listing directory: {e}"

def get_time() -> str:
    """Returns the current local time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

AVAILABLE_TOOLS = {
    "read_file": read_file,
    "list_directory": list_directory,
    "get_time": get_time
}
