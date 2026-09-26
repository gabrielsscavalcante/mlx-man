"""
cli_actions.py — Core action handlers for the main menu.
Routes to the server launcher, memory cleaner, model inspector, and insights.
"""

import os
import sys
import subprocess
from pathlib import Path
from rich.text import Text
from mlx_man.ui_components import create_warning_panel
from mlx_man.tui_engine import tui_text_input, tui_confirm
from rich.console import Group, Console
from rich.text import Text
from mlx_man.ui_components import create_warning_panel
from mlx_man.tui_engine import tui_text_input, tui_confirm

from mlx_man.ui_components import create_header_panel, create_data_table, create_warning_panel
from mlx_man.tui_engine import tui_select, tui_confirm, tui_text_input
from mlx_man.cli_dashboard import get_banner, get_system_status_footer


console = Console()

def run_memory_cleaner():
    try:
        from mlx_man.ram_manager_view import run_ram_manager
        run_ram_manager()
    except KeyboardInterrupt:
        pass

def run_model_inspector():
    try:
        from mlx_man.model_inspector import run_model_inspector as _run
        _run()
    except KeyboardInterrupt:
        pass

def run_insights_history():
    from mlx_man.insights_view import run_insights_history as _run
    _run()

def action_run_server():
    """Interactive flow: GPU limit → Role → Model → Server/Chat."""
    from mlx_man.cli_dashboard import get_system_status_footer
    footer = get_system_status_footer()

    # 1. GPU Memory Limit
    gpu_header = create_header_panel(
        Group(
            Text("By default, macOS limits GPU memory to ~21 GB on a 32 GB Mac.", style="dim white"),
            Text("Large models (32B 4-bit) need more headroom.", style="dim white"),
            Text("⚠ This will prompt for your Mac password (sudo).", style="yellow"),
        ),
        "GPU Memory Limit (Optional)"
    )

    gpu_choices = [
        ("26624", "26 GB (Recommended for 32B and 27B-6bit models)"),
        ("28672", "28 GB (Maximum headroom — for long contexts)"),
        ("skip", "Skip (Keep the current limit)")
    ]

    gpu_choice = tui_select(
        title="Select GPU Limit:",
        choices=gpu_choices,
        format_func=lambda x: x[1],
        header=gpu_header,
        footer=footer
    )

    if not gpu_choice:
        return

    if gpu_choice[0] != "skip":
        subprocess.run(["sudo", "sysctl", f"iogpu.wired_limit_mb={gpu_choice[0]}"])

    # 2. Role Selection
    role_header = create_header_panel(Text("Choose the persona for your AI model.", style="dim white"), "Choose a Role")
    
    role_choices = [
        ("reasoning", "🧠 Reasoning (Plan, analyze, design)"),
        ("builder", "🔨 Builder (Implement, refactor, write code)"),
        ("general", "⚡ General Purpose (A bit of everything)"),
        ("cancel", "Cancel")
    ]

    role_choice = tui_select(
        title="What do you want to do right now?",
        choices=role_choices,
        format_func=lambda x: x[1],
        header=role_header,
        footer=footer
    )

    if not role_choice or role_choice[0] == "cancel":
        return

    from mlx_man.model_registry import get_models_by_role
    HF_CACHE = Path.home() / '.cache' / 'huggingface' / 'hub'
    models = get_models_by_role(role_choice[0])

    if not models:
        tui_confirm(prompt="No models registered for this role. Press Enter to go back.", header=role_header, footer=footer)
        return

    model_choices = []
    for model_id, entry in models.items():
        dir_name = 'models--' + model_id.replace('/', '--')
        installed = (HF_CACHE / dir_name).exists()
        status_tag = "●" if installed else "○"
        ram = entry.get('ram_estimate_gb', '?')
        tier = entry.get('performance_tier', 'Unknown')
        name = entry.get('name', model_id.split('/')[-1])
        short_desc = entry.get('best_for', [''])[0]
        
        display_text = f"{status_tag} {name} (RAM: ~{ram}GB) - {short_desc}"
        model_choices.append((model_id, display_text))
        
    model_choices.append(("cancel", "Cancel"))
    
    model_header = create_header_panel(Text("● = installed    ○ = not downloaded", style="dim white"), "Model Selection")

    model_choice = tui_select(
        title="Select a model to run:",
        choices=model_choices,
        format_func=lambda x: x[1],
        header=model_header,
        footer=footer,
        width=80
    )

    if not model_choice or model_choice[0] == "cancel":
        return

    model_id = model_choice[0]
    entry = models[model_id]

    # Check if installed
    dir_name = 'models--' + model_id.replace('/', '--')
    installed = (HF_CACHE / dir_name).exists()

    if not installed:
        dl_header = create_warning_panel(Text(f"Model '{entry['name']}' is not downloaded yet."), "Download Required")
        dl = tui_confirm("Download it now?", header=dl_header, footer=footer)
        if not dl:
            return

        print(f"\n  ℹ  Downloading: {model_id}")
        from mlx_man.model_downloader import download_model
        success = download_model(model_id)
        if not success:
            return

    # Action Selection
    action_header = create_header_panel(Text(f"Selected: {entry['name']}", style="bold white"), "Action")
    
    action_choices = [
        ("server", "Start API Server (localhost:8080)"),
        ("chat", "Chat in Terminal"),
        ("benchmark", "⚡ Run Hardware Benchmark"),
        ("cancel", "Cancel")
    ]

    action_choice = tui_select(
        title="Select action:",
        choices=action_choices,
        format_func=lambda x: x[1],
        header=action_header,
        footer=footer
    )

    if not action_choice or action_choice[0] == "cancel":
        return

    from mlx_man.usage_tracker import record_usage
    record_usage(model_id)
    
    adapter_path = None
    if action_choice[0] in ("server", "chat"):
        use_lora = tui_confirm("Do you want to attach a LoRA adapter to this model?", header=action_header, footer=footer)
        if use_lora:
            adapter_path = tui_text_input(
                prompt="Enter Absolute Path or HuggingFace Repo ID of the adapter:", 
                header=action_header, 
                footer=footer
            )
            if not adapter_path:
                return

    if action_choice[0] == "server":
        from mlx_man.server_manager import get_running_servers, start_server
        from mlx_man.cli_dashboard import get_free_ram_gb
        from mlx_man.opencode_sync import sync_opencode_config
        import time
        
        servers = get_running_servers()
        default_port = "8080" if "8080" not in servers else "8081"
        
        port_str = tui_text_input(prompt=f"Enter port to run on (default: {default_port}):", header=action_header, footer=footer)
        port = int(port_str) if port_str and port_str.isdigit() else int(default_port)
        
        ram_needed_str = entry.get('ram_estimate_gb', '0')
        if isinstance(ram_needed_str, str):
            ram_needed_str = ram_needed_str.replace('>', '').replace('<', '')
        try:
            ram_needed = float(ram_needed_str)
        except:
            ram_needed = 0
            
        free_ram = get_free_ram_gb()
        if ram_needed > free_ram:
            warn = create_warning_panel(
                Text(f"WARNING: Model needs ~{ram_needed}GB but only {free_ram:.1f}GB is free.\nRunning this may cause severe system swapping or crashes.", style="red"),
                "RAM Safety Alert"
            )
            if not tui_confirm("Are you sure you want to proceed?", header=warn, footer=footer):
                return
                
        print(f"\n  ✔  Starting OpenAI-compatible server on http://localhost:{port} in background...")
        sync_opencode_config(model_id)
        start_server(model_id, port, adapter_path)
        time.sleep(1)
        print("\n  ℹ  Server is running in the background. You can view logs or stop it from the Main Menu.\n")
        input("Press Enter to return to menu...")
    elif action_choice[0] == "chat":
        print(f"\n  ✔  Starting interactive terminal chat...")
        print("\n  ℹ  Type 'quit' or 'exit' to end the session.\n")
        try:
            from mlx_man.native_chat_view import run_chat_session
            run_chat_session(model_id, adapter_path=adapter_path)
        except KeyboardInterrupt:
            pass
    elif action_choice[0] == "benchmark":
        print(f"\n  ⚡ Starting Hardware Benchmark for {model_id}...")
        try:
            action_run_benchmark(model_id)
        except Exception as e:
            print(f"\n  ❌ Benchmark failed: {e}")
        input("\nPress Enter to return to menu...")

def action_sync_models():
    """Interactive flow to sync unregistered or custom models."""
    from mlx_man.model_registry import register_custom_model, MODEL_REGISTRY
    from mlx_man.model_manager import get_installed_models
    from mlx_man.opencode_sync import sync_opencode_config
    from pathlib import Path
    
    options = [
        ("🔍  Search Hugging Face Cache", "search"),
        ("📁  Add Custom Local Path", "custom"),
        ("↩   Back", "back")
    ]
    
    choice = tui_select(
        title="Sync Models to MLX-Man & OpenCode",
        items=options,
        header=get_banner(),
        footer=get_system_status_footer()
    )
    
    if not choice or choice == "back":
        return
        
    if choice == "search":
        installed = get_installed_models()
        unregistered = [m["id"] for m in installed if m["id"] not in MODEL_REGISTRY]
        
        if not unregistered:
            tui_text_input(
                prompt="Press Enter to return...",
                header=create_header_panel("✔ All cached models are already synced!", "Sync Complete"),
                footer=get_system_status_footer()
            )
            return
            
        items = [(f"Add {mid}", mid) for mid in unregistered] + [("↩ Back", "back")]
        selected_id = tui_select(
            title="Found Unregistered Models",
            items=items,
            header=get_banner(),
            footer=get_system_status_footer()
        )
        
        if selected_id and selected_id != "back":
            name = selected_id.split("/")[-1]
            register_custom_model(selected_id, name)
            sync_opencode_config()
            tui_text_input(
                prompt="Press Enter to continue...",
                header=create_header_panel(f"✔ Successfully synced {name}!", "Sync Complete"),
                footer=get_system_status_footer()
            )
            
    elif choice == "custom":
        path_str = tui_text_input(
            prompt="Enter absolute path to the model directory:",
            header=get_banner(),
            footer=get_system_status_footer()
        )
        if not path_str:
            return
            
        if not Path(path_str).exists():
            tui_text_input(
                prompt="Press Enter to return...",
                header=create_warning_panel(f"Path does not exist: {path_str}", "Error"),
                footer=get_system_status_footer()
            )
            return
            
        name = tui_text_input(
            prompt="Enter a display name for this model:",
            header=get_banner(),
            footer=get_system_status_footer()
        )
        if name:
            register_custom_model(path_str, name)
            sync_opencode_config()
            tui_text_input(
                prompt="Press Enter to continue...",
                header=create_header_panel(f"✔ Successfully synced {name}!", "Sync Complete"),
                footer=get_system_status_footer()
            )


def action_manage_server():
    from mlx_man.server_manager import get_running_servers, stop_server, LOG_FILE
    from mlx_man.server_dashboard_view import render_server_dashboard
    from mlx_man.cli_dashboard import get_system_status_footer
    from mlx_man.tui_engine import tui_select, tui_confirm
    import subprocess
    import time
    
    servers = get_running_servers()
    if not servers:
        return
        
    header = render_server_dashboard(servers)
    
    choices = []
    for port in sorted(servers.keys()):
        choices.append((f"stop_{port}", f"🛑  Stop Server on Port {port}"))
    
    if len(servers) > 1:
        choices.append(("stop_all", "🛑  Stop ALL Servers"))
        
    choices.append(("logs", "📄  View Full Server Logs (less)"))
    choices.append(("back", "⬅️   Back to Menu"))
    
    choice = tui_select(
        title="Server Actions:",
        choices=choices,
        format_func=lambda x: x[1],
        header=header,
        footer=get_system_status_footer()
    )
    
    if not choice or choice[0] == "back":
        return
        
    if choice[0] == "stop_all":
        if tui_confirm("Are you sure you want to stop all servers?", header=header, footer=get_system_status_footer()):
            stop_server()
            print("\n  ✔  All servers stopped.")
            time.sleep(1)
            
    elif choice[0].startswith("stop_"):
        port = choice[0].split("_")[1]
        if tui_confirm(f"Are you sure you want to stop the server on port {port}?", header=header, footer=get_system_status_footer()):
            stop_server(port)
            print(f"\n  ✔  Server on port {port} stopped.")
            time.sleep(1)
            
    elif choice[0] == "logs":
        if LOG_FILE.exists():
            subprocess.run(["less", "+G", str(LOG_FILE)])

def action_quantize_model():
    """Interactive flow to quantize a Hugging Face model locally."""
    from mlx_man.cli_dashboard import get_banner, get_system_status_footer
    from mlx_man.ui_components import create_header_panel, create_warning_panel
    from mlx_man.model_registry import register_custom_model
    import subprocess
    import sys
    from pathlib import Path
    
    header = get_banner()
    footer = get_system_status_footer()
    
    repo_id = tui_text_input(
        prompt="Enter HuggingFace Repo ID (e.g. meta-llama/Llama-3.2-1B):",
        header=header,
        footer=footer
    )
    if not repo_id or "/" not in repo_id:
        return
        
    bits_choice = tui_select(
        title="Select Quantization Precision:",
        items=[("4-bit (Recommended, ~25% size)", "4"), ("8-bit (~50% size)", "8"), ("Cancel", "back")],
        header=header,
        footer=footer
    )
    if not bits_choice or bits_choice == "back":
        return
        
    repo_name = repo_id.split("/")[-1]
    dest_path = Path.home() / ".config" / "mlx-man" / "quantized" / f"{repo_name}-{bits_choice}bit"
    
    print(f"\n  ℹ  Preparing to quantize {repo_id} to {bits_choice}-bit...")
    print(f"  ℹ  Output directory: {dest_path}\n")
    print("  (This will download the full model if not cached, then quantize it. This may take a while.)\n")
    
    try:
        dest_path.mkdir(parents=True, exist_ok=True)
        # Using mlx_lm.convert via subprocess
        subprocess.run([
            sys.executable, "-m", "mlx_lm.convert",
            "--hf-path", repo_id,
            "--mlx-path", str(dest_path),
            "-q", "--q-bits", bits_choice
        ], check=True)
        
        print("\n  ✔  Quantization complete!")
        # Register the local model
        name = f"{repo_name} ({bits_choice}-bit Quantized)"
        register_custom_model(str(dest_path), name)
        
        tui_text_input(
            prompt="Press Enter to return to menu...",
            header=create_header_panel(f"✔ Successfully quantized and registered {name}!", "Success"),
            footer=footer
        )
    except subprocess.CalledProcessError as e:
        tui_text_input(
            prompt="Press Enter to return...",
            header=create_warning_panel(f"Quantization failed with error code {e.returncode}.", "Error"),
            footer=footer
        )
    except Exception as e:
        tui_text_input(
            prompt="Press Enter to return...",
            header=create_warning_panel(f"An unexpected error occurred: {e}", "Error"),
            footer=footer
        )

def action_run_benchmark(model_id: str):
    import mlx_lm
    import time
    import json
    import subprocess
    from pathlib import Path
    from datetime import datetime
    
    print("  [1/3] Loading model into unified memory...")
    try:
        model, tokenizer = mlx_lm.load(model_id)
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}")
        
    prompt = "Write a comprehensive Python script that implements a merge sort algorithm, including detailed comments and test cases."
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        try:
            prompt = tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True)
        except Exception:
            pass
            
    print("  [2/3] Warming up and generating tokens...")
    start_time = time.time()
    first_token_time = None
    tokens_generated = 0
    
    for _ in mlx_lm.stream_generate(model, tokenizer, prompt, max_tokens=100):
        if first_token_time is None:
            first_token_time = time.time()
        tokens_generated += 1
        print("█", end="", flush=True)
        if tokens_generated >= 50:
            break
            
    print("\n  [3/3] Calculating metrics...")
    end_time = time.time()
    
    if first_token_time is None or tokens_generated <= 1:
        raise RuntimeError("Model failed to generate tokens.")
        
    prompt_time = first_token_time - start_time
    gen_time = end_time - first_token_time
    tps = (tokens_generated - 1) / gen_time if gen_time > 0 else 0.0
    
    # Attempt to get hardware info
    try:
        hw_info = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, check=True).stdout.strip()
        mem_bytes = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=True).stdout.strip())
        mem_gb = round(mem_bytes / (1024**3))
        hardware_str = f"{hw_info} ({mem_gb}GB)"
    except Exception:
        hardware_str = "Apple Silicon Mac"
        
    print(f"\n  📊 Results:")
    print(f"     - Hardware: {hardware_str}")
    print(f"     - Time to First Token (TTFT): {prompt_time:.2f}s")
    print(f"     - Generation Speed: {tps:.1f} tokens/sec")
    
    # Save to benchmarks.json
    bench_file = Path.home() / ".config" / "mlx-man" / "benchmarks.json"
    benchmarks = []
    if bench_file.exists():
        try:
            with open(bench_file, "r") as f:
                benchmarks = json.load(f)
        except json.JSONDecodeError:
            pass
            
    # Remove old benchmark for this model if exists
    benchmarks = [b for b in benchmarks if b.get("model_id") != model_id]
    
    benchmarks.append({
        "model_id": model_id,
        "hardware": hardware_str,
        "ttft_s": round(prompt_time, 2),
        "tps": round(tps, 1),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    bench_file.parent.mkdir(parents=True, exist_ok=True)
    with open(bench_file, "w") as f:
        json.dump(benchmarks, f, indent=4)
        
    print(f"\n  ✔  Benchmark saved to Leaderboard!")
