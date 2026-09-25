import re

def estimate_ram(model_id: str) -> float:
    params = 0
    bits = 16 # default bf16/fp16
    
    match_params = re.search(r'([\d\.]+)B', model_id, re.IGNORECASE)
    if match_params:
        params = float(match_params.group(1))
        
    match_bits = re.search(r'(\d+)-?bit', model_id, re.IGNORECASE)
    if match_bits:
        bits = int(match_bits.group(1))
        
    if params == 0:
        return 0 # Unknown
        
    return (params * bits / 8) * 1.2

test_cases = [
    "mlx-community/Qwen2.5-7B-Instruct-4bit",
    "mlx-community/QwQ-32B-4bit",
    "mlx-community/Llama-3-70B-Instruct-8bit",
    "lmstudio-community/Meta-Llama-3-8B-Instruct-bf16"
]

for t in test_cases:
    print(f"{t}: {estimate_ram(t):.1f} GB")
