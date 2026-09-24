import os
import time
from dataclasses import dataclass
from typing import Literal, List, Tuple
import psutil

SafetyTier = Literal["Safe", "Caution", "Danger"]

@dataclass
class ProcessInfo:
    pid: int
    name: str
    memory_mb: float
    safety: SafetyTier
    description: str
    can_kill: bool = True

class ProcessClassifier:
    """
    Classifies processes into safety tiers based on their name.
    """
    
    SAFE_PROCESSES = {
        "Safari": "Web browser.",
        "Google Chrome": "Web browser.",
        "Antigravity IDE": "Coding environment.",
        "VS Code": "Code editor.",
        "Code Helper": "Code editor.",
        "Electron": "Electron framework app.",
        "opencode-cli": "AI agent.",
        "Spotify": "Music player.",
        "Slack": "Team communication app.",
        "Discord": "Chat application.",
        "Docker Desktop": "Container virtualization.",
        "Notes": "Apple Notes.",
        "Messages": "Apple Messages (iMessage).",
        "Mail": "Apple Mail client.",
        "language_server": "Code analysis tool used by your IDE.",
        "MTLCompilerService": "Metal compiler service.",
        "Activity Monitor": "Task manager app.",
    }

    CAUTION_PROCESSES = {
        "Siri AI": "macOS Siri / Apple Intelligence background process.",
        "siriactionsd": "macOS Siri background process.",
        "AppleSpell": "macOS spell checker.",
        "com.apple.weather.menu": "macOS Weather widget.",
        "cloudphotod": "macOS Cloud Photos daemon.",
        "corespotlightd": "macOS Search indexing (restarts automatically).",
    }
    
    DANGER_PROCESSES = {
        "ControlCenter": "macOS Control Center UI.",
        "NotificationCenter": "macOS Notification UI.",
        "cloudd": "macOS Cloud sync daemon.",
        "sharingd": "macOS Sharing daemon.",
        "routined": "macOS Routine daemon.",
        "WindowServer": "macOS Core UI server.",
        "kernel_task": "macOS Kernel.",
        "sysmond": "System monitor daemon.",
        "loginwindow": "macOS Login Window."
    }

    @classmethod
    def classify(cls, name: str) -> Tuple[SafetyTier, str]:
        for dang_name, desc in cls.DANGER_PROCESSES.items():
            if dang_name in name:
                return "Danger", desc
                
        for safe_name, desc in cls.SAFE_PROCESSES.items():
            if safe_name in name:
                return "Safe", desc
                
        for caut_name, desc in cls.CAUTION_PROCESSES.items():
            if caut_name in name:
                return "Caution", desc

        return "Caution", "Unknown background process."

class ProcessService:
    @staticmethod
    def get_system_memory_info() -> dict:
        """
        Returns a dictionary with memory information in GB.
        """
        mem = psutil.virtual_memory()
        return {
            "total_gb": mem.total / (1024 ** 3),
            "used_gb": mem.used / (1024 ** 3),
            "free_gb": mem.available / (1024 ** 3),
            "percent": mem.percent,
            "wired_gb": getattr(mem, 'wired', 0) / (1024 ** 3)
        }

    @staticmethod
    def get_processes() -> List[ProcessInfo]:
        """
        Retrieves a list of running processes and their memory usage.
        """
        processes = []
        for p in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                mem_info = p.info['memory_info']
                if not mem_info:
                    continue
                rss = mem_info.rss / (1024 * 1024)
                if rss < 50:
                    continue
                name = p.info['name']
                pid = p.info['pid']
                
                safety, desc = ProcessClassifier.classify(name)
                can_kill = safety != "Danger"
                
                processes.append(ProcessInfo(
                    pid=pid,
                    name=name,
                    memory_mb=rss,
                    safety=safety,
                    description=desc,
                    can_kill=can_kill
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return sorted(processes, key=lambda x: x.memory_mb, reverse=True)

    @staticmethod
    def terminate_process(pid: int) -> bool:
        """
        Terminates a process safely using SIGTERM then SIGKILL.
        """
        try:
            p = psutil.Process(pid)
            p.terminate()
            try:
                p.wait(timeout=3)
            except psutil.TimeoutExpired:
                p.kill()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            import sys
            print(f"Notice: Could not terminate process {pid}: {e}", file=sys.stderr)
            return False
        except Exception as e:
            import sys
            print(f"Notice: Unexpected error when terminating process {pid}: {e}", file=sys.stderr)
            return False
