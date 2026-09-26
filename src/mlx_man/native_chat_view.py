import sys
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

import json
import re
from mlx_man.chat_manager import ChatSession, save_session, load_session
from mlx_man.tools import AVAILABLE_TOOLS
from mlx_man.tui_engine import tui_confirm

def run_chat_session(model_id: str, resume_session_id: Optional[str] = None, adapter_path: Optional[str] = None):
    try:
        import mlx_lm
    except ImportError:
        print("Error: mlx_lm is not installed.")
        return

    console = Console()
    console.clear()
    
    if adapter_path:
        console.print(Panel(f"Loading [bold cyan]{model_id}[/bold cyan] with adapter [bold magenta]{adapter_path}[/bold magenta]...", title="MLX Native Chat", border_style="blue"))
    else:
        console.print(Panel(f"Loading [bold cyan]{model_id}[/bold cyan] into memory...", title="MLX Native Chat", border_style="blue"))
    
    try:
        if adapter_path:
            model, tokenizer = mlx_lm.load(model_id, adapter_path=adapter_path)
        else:
            model, tokenizer = mlx_lm.load(model_id)
    except Exception as e:
        console.print(f"[bold red]Failed to load model:[/bold red] {e}")
        input("Press Enter to return...")
        return
        
    if resume_session_id:
        session = load_session(resume_session_id)
        if not session:
            console.print("[bold red]Failed to load session.[/bold red]")
            input("Press Enter to return...")
            return
        
        console.clear()
        console.print(Panel(f"Resumed Chat: [bold cyan]{model_id}[/bold cyan]\n[dim]History loaded. Type 'quit' or 'exit' to end.[/dim]", title="MLX Native Chat", border_style="green"))
        
        # Render history
        for msg in session.messages:
            if msg["role"] == "user":
                console.print(Panel(Text(msg["content"], style="blue"), title="👤 You", border_style="blue", title_align="left"))
            elif msg["role"] == "assistant":
                console.print(Panel(Markdown(msg["content"]), title="🤖 Assistant", border_style="green", title_align="left"))
    else:
        session_id = datetime.now().isoformat()
        session = ChatSession(session_id=session_id, model_id=model_id, start_time=session_id)
        session.messages.append({"role": "system", "content": 'You are an AI assistant. You can use tools to answer questions.\nAvailable tools:\n- read_file: {"path": "string"}\n- list_directory: {"path": "string"}\n- get_time: {}\n\nTo call a tool, output EXACTLY this XML format and wait for the result:\n<tool_call>\n{"name": "tool_name", "arguments": {"arg1": "val1"}}\n</tool_call>\n'})
        console.clear()
        console.print(Panel(f"Started Chat: [bold cyan]{model_id}[/bold cyan]\n[dim]Type your message below. Type 'quit' or 'exit' to end.[/dim]", title="MLX Native Chat", border_style="green"))
        
    while True:
        try:
            console.print()
            user_input = console.input("[bold blue]👤 You:[/bold blue]\n")
        except (KeyboardInterrupt, EOFError):
            break
            
        if user_input.strip().lower() in ['quit', 'exit']:
            break
            
        if not user_input.strip():
            continue
            
        session.messages.append({"role": "user", "content": user_input})
        save_session(session)
        
        while True:
            # Build prompt
            try:
                prompt = tokenizer.apply_chat_template(session.messages, tokenize=False, add_generation_prompt=True)
            except Exception:
                # Fallback if tokenizer doesn't support chat templates easily
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in session.messages]) + "\nassistant:"
            
            console.print("\n[bold green]🤖 Assistant:[/bold green]")
            
            response = ""
            try:
                for response_obj in mlx_lm.stream_generate(model, tokenizer, prompt=prompt, max_tokens=2048):
                    token = response_obj.text
                    print(token, end="", flush=True)
                    response += token
                    if "</tool_call>" in response:
                        break
                print()
            except KeyboardInterrupt:
                print("\n[dim][Interrupted by user][/dim]")
                session.messages.append({"role": "assistant", "content": response})
                save_session(session)
                break
                
            session.messages.append({"role": "assistant", "content": response})
            save_session(session)
            
            tool_match = re.search(r'<tool_call>(.*?)</tool_call>', response, re.DOTALL)
            if tool_match:
                try:
                    tool_data = json.loads(tool_match.group(1).strip())
                    tool_name = tool_data.get("name")
                    tool_args = tool_data.get("arguments", {})
                    
                    if tool_name in AVAILABLE_TOOLS:
                        # Security Check
                        console.print(f"\n[bold yellow]⚠️  Security Permission:[/bold yellow] The model wants to execute [bold]{tool_name}[/bold]({tool_args})")
                        allow = console.input("[bold yellow]Allow? [Y/n]: [/bold yellow]").strip().lower()
                        if allow in ['', 'y', 'yes']:
                            console.print(Panel(f"Executing [bold]{tool_name}[/bold]...", title="🛠️ Agent Tool", border_style="yellow"))
                            if tool_name == "get_time":
                                result = AVAILABLE_TOOLS[tool_name]()
                            else:
                                result = AVAILABLE_TOOLS[tool_name](**tool_args)
                        else:
                            result = "Error: User denied permission to run this tool."
                    else:
                        result = f"Error: Tool '{tool_name}' not found."
                except Exception as e:
                    result = f"Error parsing tool call: {e}"
                
                console.print(f"[dim]Tool Result: {result[:100]}...[/dim]")
                session.messages.append({"role": "user", "content": f"<tool_result>\n{result}\n</tool_result>"})
                save_session(session)
                # Loop back and let model generate final response based on tool_result
            else:
                # No tool called, we are done with this turn
                break

        
    console.print("\n[dim]Session saved. Returning to menu...[/dim]")
