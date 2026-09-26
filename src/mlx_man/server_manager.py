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

def get_running_servers():
    """Returns dict mapping port (str) to server info dict if running, else {}. Purges dead servers."""
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text())
        # Support migration from old format where data was a single object
        if "pid" in data:
            data = {str(data.get("port", "8080")): data}
            
        active_servers = {}
        changed = False
        
        for port_str, state in list(data.items()):
            if check_server_health(state):
                # Verify it's actually mlx_lm
                proc = psutil.Process(state["pid"])
                cmdline = " ".join(proc.cmdline())
                if "mlx_lm" in cmdline and "server" in cmdline:
                    active_servers[port_str] = state
                else:
                    changed = True
            else:
                changed = True
                
        if changed:
            if not active_servers:
                STATE_FILE.unlink(missing_ok=True)
            else:
                STATE_FILE.write_text(json.dumps(active_servers))
                
        return active_servers
    except Exception:
        STATE_FILE.unlink(missing_ok=True)
    return {}

def stop_server(port=None):
    """Stops the running server on a specific port, or all if port is None."""
    servers = get_running_servers()
    
    ports_to_stop = [str(port)] if port else list(servers.keys())
    
    for p in ports_to_stop:
        if p in servers:
            pid = servers[p]["pid"]
            try:
                os.kill(pid, signal.SIGTERM)
                for _ in range(10):
                    if not psutil.pid_exists(pid):
                        break
                    time.sleep(0.2)
                if psutil.pid_exists(pid):
                    os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            del servers[p]
            
    if not servers:
        STATE_FILE.unlink(missing_ok=True)
    else:
        STATE_FILE.write_text(json.dumps(servers))

def start_server(model_id, port=8080, adapter_path=None):
    """Starts a new server as a detached background daemon on the specified port."""
    # Stop existing server on this port if any
    stop_server(port)
    
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(LOG_FILE, "a") as f:
        f.write(f"\n--- Starting Server for {model_id} on port {port} ---\n")
    
    log_fd = open(LOG_FILE, "a")
    
    cmd = [sys.executable, "-m", "mlx_lm.server", "--model", model_id, "--port", str(port)]
    if adapter_path:
        cmd.extend(["--adapter-path", adapter_path])
        
    proc = subprocess.Popen(
        cmd,
        stdout=log_fd,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    
    servers = get_running_servers()
    
    data = {
        "pid": proc.pid,
        "model_id": model_id,
        "port": port,
        "adapter_path": adapter_path,
        "start_time": time.time()
    }
    
    servers[str(port)] = data
    STATE_FILE.write_text(json.dumps(servers))
    return data

def check_server_health(state: dict) -> bool:
    """Check if the server process in the state dictionary is actually running."""
    if not state or "pid" not in state:
        return False
    pid = state["pid"]
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False
