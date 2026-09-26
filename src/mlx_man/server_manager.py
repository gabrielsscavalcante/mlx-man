import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import psutil

CONFIG_DIR = Path.home() / ".config" / "mlx-man"
STATE_FILE = CONFIG_DIR / "server_state.json"
LOG_FILE = CONFIG_DIR / "server.log"

def get_running_server():
    """Returns dict with server info if running, else None."""
    if not STATE_FILE.exists():
        return None
    try:
        data = json.loads(STATE_FILE.read_text())
        pid = data.get("pid")
        if pid and psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            cmdline = " ".join(proc.cmdline())
            if "mlx_lm" in cmdline and "server" in cmdline:
                return data
            
        # Stale state
        STATE_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    return None

def stop_server():
    """Stops the currently running server gracefully."""
    server = get_running_server()
    if server:
        pid = server["pid"]
        try:
            os.kill(pid, signal.SIGTERM)
            # Wait briefly for graceful shutdown
            for _ in range(10):
                if not psutil.pid_exists(pid):
                    break
                time.sleep(0.2)
            # Force kill if still lingering
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    STATE_FILE.unlink(missing_ok=True)

def start_server(model_id, port=8080):
    """Starts a new server as a detached background daemon, killing old ones."""
    stop_server()
    
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Append marker to log file
    with open(LOG_FILE, "a") as f:
        f.write(f"\n--- Starting Server for {model_id} on port {port} ---\n")
    
    log_fd = open(LOG_FILE, "a")
    
    # Use start_new_session to detach the process completely from the CLI session
    proc = subprocess.Popen(
        [sys.executable, "-m", "mlx_lm.server", "--model", model_id, "--port", str(port)],
        stdout=log_fd,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    
    data = {
        "pid": proc.pid,
        "model_id": model_id,
        "port": port,
        "start_time": time.time()
    }
    STATE_FILE.write_text(json.dumps(data))
    return data
