import re
from typing import Tuple
from mlx_man.cli_dashboard import get_total_ram_gb

def estimate_ram(model_id: str) -> float:
    """Estimates the RAM needed to run a model based on its ID string."""
    params = 0
    bits = 16 # Default to bf16
    
    match_params = re.search(r'([\d\.]+)B', model_id, re.IGNORECASE)
    if match_params:
        params = float(match_params.group(1))
        
    match_bits = re.search(r'(\d+)-?bit', model_id, re.IGNORECASE)
    if match_bits:
        bits = int(match_bits.group(1))
        
    if params == 0:
        return 0
        
    return (params * bits / 8) * 1.2

def get_hardware_recommendation(model_id: str) -> Tuple[str, str]:
    """Returns a recommendation badge and its color style based on the system's total RAM."""
    ram_needed = estimate_ram(model_id)
    if ram_needed == 0:
        return "❓ Unknown", "dim"
        
    total_ram = get_total_ram_gb()
    
    if ram_needed < total_ram * 0.7:
        return "🟢 Great Match", "bold green"
    elif ram_needed < total_ram:
        return "🟡 Paging Risk", "bold yellow"
    else:
        return "🔴 Will OOM", "bold red"
