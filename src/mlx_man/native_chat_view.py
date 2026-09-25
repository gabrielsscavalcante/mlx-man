import sys
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from mlx_man.chat_manager import ChatSession, save_session, load_session

def run_chat_session(model_id: str, resume_session_id: Optional[str] = None):
    try:
        import mlx_lm
    except ImportError:
        print("Error: mlx_lm is not installed.")
        return

    console = Console()
    console.clear()
    console.print(Panel(f"Loading [bold cyan]{model_id}[/bold cyan] into memory...", title="MLX Native Chat", border_style="blue"))
    
    try:
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
            print()
        except KeyboardInterrupt:
            print("\n[dim][Interrupted by user][/dim]")
            
        session.messages.append({"role": "assistant", "content": response})
        save_session(session)
        
    console.print("\n[dim]Session saved. Returning to menu...[/dim]")
