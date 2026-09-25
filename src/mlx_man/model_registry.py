"""
model_registry.py — Curated knowledge base for known MLX models.

This is the single source of truth for model metadata: descriptions,
use cases, RAM estimates, GPU requirements, performance tiers, and roles.

Roles:
  - "reasoning" : Thinking / planning models for prompts and architecture
  - "builder"   : Coding / implementation models for writing and refactoring code
  - "general"   : General-purpose models that do both reasonably well

To add a new model, simply add a new entry to MODEL_REGISTRY below.
"""

MODEL_REGISTRY = {

    # ─────────────────────────────────────────────────────────────────────────
    # REASONING / THINKING MODELS
    # ─────────────────────────────────────────────────────────────────────────

    "mlx-community/QwQ-32B-4bit": {
        "name": "QwQ 32B (4-bit)",
        "short_name": "QwQ 32B",
        "role": "reasoning",
        "role_icon": "🧠",
        "description": (
            "Alibaba's dedicated reasoning model with 32 billion parameters. "
            "Excels at deep chain-of-thought reasoning, multi-step problem "
            "decomposition, and planning. One of the strongest open-source "
            "reasoning models available. Quantized to 4-bit for Apple Silicon."
        ),
        "best_for": [
            "Complex multi-step reasoning and planning",
            "Project architecture and prompt design",
            "Mathematical and logical problem solving",
            "Understanding and analyzing codebases",
        ],
        "not_ideal_for": [
            "Quick one-shot code generation (use a builder model)",
            "Systems with less than 24 GB available RAM",
        ],
        "ram_estimate_gb": 18,
        "gpu_limit_required": "26 GB recommended (sudo sysctl iogpu.wired_limit_mb=26624)",
        "performance_tier": "Heavy",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — reasoning-optimized",
        "context_window": "Up to 32K tokens",
        "notes": (
            "The top recommendation for planning and reasoning. Use this model "
            "first to understand your project, create prompts, and design the "
            "implementation plan. Then swap to a builder model to implement."
        ),
    },

    "mlx-community/Qwen3-32B-4bit": {
        "name": "Qwen3 32B (4-bit)",
        "short_name": "Qwen3 32B",
        "role": "reasoning",
        "role_icon": "🧠",
        "description": (
            "A 32-billion parameter dense model from the Qwen3 series with a "
            "unique dual-mode capability: it can switch between a deep 'thinking' "
            "mode for complex reasoning and a fast 'non-thinking' mode for quick "
            "responses. Very versatile for planning tasks."
        ),
        "best_for": [
            "Planning with thinking/non-thinking toggle",
            "Multi-step reasoning and analysis",
            "Multilingual project understanding",
            "Architectural design and code review",
        ],
        "not_ideal_for": [
            "Systems with less than 24 GB available RAM",
            "Pure code generation (use Qwen2.5-Coder instead)",
        ],
        "ram_estimate_gb": 18,
        "gpu_limit_required": "26 GB recommended",
        "performance_tier": "Heavy",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — dual-mode (thinking + fast)",
        "context_window": "Up to 32K tokens (extendable to 131K with YaRN)",
        "notes": (
            "Great alternative to QwQ if you want flexibility between deep "
            "reasoning and quick answers within the same model. The thinking "
            "mode produces chain-of-thought traces similar to QwQ."
        ),
    },

    "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit": {
        "name": "DeepSeek R1 Distill 32B (4-bit)",
        "short_name": "DS-R1 Distill 32B",
        "role": "reasoning",
        "role_icon": "🧠",
        "description": (
            "DeepSeek's R1 reasoning capability distilled into a 32B Qwen-based "
            "model. Inherits the step-by-step chain-of-thought approach from the "
            "full DeepSeek R1 model while being small enough to run locally. "
            "Excellent at breaking down complex problems."
        ),
        "best_for": [
            "Step-by-step problem decomposition",
            "Detailed reasoning chains",
            "Code architecture planning",
            "Complex analysis and research",
        ],
        "not_ideal_for": [
            "Quick tasks (the reasoning chains add latency)",
            "Systems with less than 24 GB available RAM",
        ],
        "ram_estimate_gb": 18,
        "gpu_limit_required": "26 GB recommended",
        "performance_tier": "Heavy",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — R1 reasoning distillation",
        "context_window": "Up to 32K tokens",
        "notes": (
            "Produces very detailed, step-by-step reasoning traces. The "
            "distillation from DeepSeek R1 means it thinks through problems "
            "methodically. Good when you need thorough analysis before coding."
        ),
    },

    "mlx-community/Phi-4-reasoning-plus-4bit": {
        "name": "Phi-4 Reasoning Plus (4-bit)",
        "short_name": "Phi-4 Reasoning+",
        "role": "reasoning",
        "role_icon": "🧠",
        "description": (
            "Microsoft's 14B parameter reasoning model, punching well above its "
            "weight class. Surprisingly strong reasoning for its size, with fast "
            "inference and low memory footprint. Great when you want quick "
            "planning without loading a 32B model."
        ),
        "best_for": [
            "Fast reasoning when speed matters",
            "Planning alongside other apps (low RAM)",
            "Quick architectural decisions",
            "When you need a reasoning model that leaves RAM headroom",
        ],
        "not_ideal_for": [
            "The most complex multi-step reasoning (use 32B models)",
            "Long-context analysis",
        ],
        "ram_estimate_gb": 8,
        "gpu_limit_required": "Not required — fits within default macOS limits",
        "performance_tier": "Light",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — reasoning-optimized (14B)",
        "context_window": "Up to 16K tokens",
        "notes": (
            "The best 'lightweight reasoning' option. Only ~8 GB RAM means you "
            "can keep browsers and IDEs open. Good for a quick planning session "
            "before switching to a builder model."
        ),
    },

    "mlx-community/Qwen3-14B-4bit": {
        "name": "Qwen3 14B (4-bit)",
        "short_name": "Qwen3 14B",
        "role": "reasoning",
        "role_icon": "🧠",
        "description": (
            "A compact 14B model from the Qwen3 series with thinking mode "
            "support. Offers the same dual-mode (thinking/fast) capability as "
            "Qwen3-32B in a lighter package. Great for fast planning iterations."
        ),
        "best_for": [
            "Fast planning with thinking mode",
            "Quick project analysis",
            "Running alongside memory-heavy apps",
            "Rapid iteration on prompts and plans",
        ],
        "not_ideal_for": [
            "Deep reasoning on very complex problems (use 32B)",
        ],
        "ram_estimate_gb": 8,
        "gpu_limit_required": "Not required — fits within default macOS limits",
        "performance_tier": "Light",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — dual-mode (thinking + fast)",
        "context_window": "Up to 32K tokens (extendable to 131K with YaRN)",
        "notes": (
            "Pairs well with a 14B builder model for a fast, low-RAM workflow. "
            "Both can almost fit in memory simultaneously if needed (~16 GB total)."
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # BUILDER / CODING MODELS
    # ─────────────────────────────────────────────────────────────────────────

    "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit": {
        "name": "Qwen2.5 Coder 32B (4-bit)",
        "short_name": "Qwen2.5 Coder 32B",
        "role": "builder",
        "role_icon": "🔨",
        "description": (
            "The best open-source coding model available. 32 billion parameters "
            "fine-tuned specifically for code generation, refactoring, debugging, "
            "and multi-file editing. Rivals GPT-4 on coding benchmarks. "
            "Quantized to 4-bit for Apple Silicon."
        ),
        "best_for": [
            "Full code implementation from plans",
            "Multi-file refactoring and editing",
            "Debugging and fixing complex issues",
            "Code review and optimization",
        ],
        "not_ideal_for": [
            "High-level planning (use a reasoning model first)",
            "Systems with less than 24 GB available RAM",
        ],
        "ram_estimate_gb": 18,
        "gpu_limit_required": "26 GB recommended (sudo sysctl iogpu.wired_limit_mb=26624)",
        "performance_tier": "Heavy",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — code-specialized",
        "context_window": "Up to 128K tokens",
        "notes": (
            "The top recommendation for building and implementing code. Use this "
            "after planning with a reasoning model. The 128K context window means "
            "it can handle very large files and multi-file contexts."
        ),
    },

    "mlx-community/Devstral-Small-2507-4bit": {
        "name": "Devstral Small 24B (4-bit)",
        "short_name": "Devstral 24B",
        "role": "builder",
        "role_icon": "🔨",
        "description": (
            "Mistral AI's purpose-built agentic coding model (24B parameters), "
            "designed for autonomous software engineering: codebase exploration, "
            "multi-file editing, and powering coding agents. Fine-tuned from "
            "Mistral-Small-3.1 specifically for SWE tasks."
        ),
        "best_for": [
            "Agentic coding workflows",
            "Multi-file codebase editing",
            "Software engineering tasks",
            "Autonomous code implementation",
        ],
        "not_ideal_for": [
            "Non-coding tasks (it's specialized for code)",
        ],
        "ram_estimate_gb": 14,
        "gpu_limit_required": "Not required — fits within default macOS limits",
        "performance_tier": "Medium",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — agentic coding (24B)",
        "context_window": "Up to 128K tokens",
        "notes": (
            "Built specifically for agentic coding. Excels at SWE-bench tasks "
            "and autonomous multi-file editing. A great middle ground between "
            "the 32B Qwen Coder (more capable) and the 14B (faster)."
        ),
    },

    "mlx-community/Codestral-22B-v0.1-4bit": {
        "name": "Codestral 22B (4-bit)",
        "short_name": "Codestral 22B",
        "role": "builder",
        "role_icon": "🔨",
        "description": (
            "Mistral AI's dedicated code generation model with 22 billion "
            "parameters. Designed for code completion, generation, and "
            "fill-in-the-middle tasks. Strong multi-language support covering "
            "80+ programming languages."
        ),
        "best_for": [
            "Fast code completion and generation",
            "Multi-language projects",
            "Fill-in-the-middle code tasks",
            "Moderate memory environments",
        ],
        "not_ideal_for": [
            "Complex multi-step reasoning (use a reasoning model)",
        ],
        "ram_estimate_gb": 12,
        "gpu_limit_required": "Not required — fits within default macOS limits",
        "performance_tier": "Light",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — code-specialized (22B)",
        "context_window": "Up to 32K tokens",
        "notes": (
            "Good balance of capability and speed. Supports 80+ programming "
            "languages. The open-weights version of Mistral's Codestral line."
        ),
    },

    "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit": {
        "name": "Qwen2.5 Coder 14B (4-bit)",
        "short_name": "Qwen2.5 Coder 14B",
        "role": "builder",
        "role_icon": "🔨",
        "description": (
            "A 14B parameter coding model from the Qwen2.5 Coder family. "
            "Fast and very capable for its size, making it ideal for quick "
            "code generation when you don't want to load a 32B model. "
            "Excellent quality-to-speed ratio."
        ),
        "best_for": [
            "Fast code generation and editing",
            "Running alongside other applications",
            "Quick implementation iterations",
            "Paired with a 14B reasoning model for a lightweight workflow",
        ],
        "not_ideal_for": [
            "Very complex multi-file refactors (use the 32B version)",
        ],
        "ram_estimate_gb": 8,
        "gpu_limit_required": "Not required — fits within default macOS limits",
        "performance_tier": "Light",
        "quantization_summary": "4-bit quantization",
        "architecture": "Dense Transformer — code-specialized (14B)",
        "context_window": "Up to 128K tokens",
        "notes": (
            "Pairs perfectly with Qwen3-14B or Phi-4-Reasoning for a fast, "
            "low-RAM workflow. Both models use ~8 GB, leaving plenty of headroom "
            "for browsers and IDEs. Great for rapid iteration."
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # GENERAL PURPOSE MODELS
    # ─────────────────────────────────────────────────────────────────────────

    "mlx-community/Qwen3.6-35B-A3B-4bit": {
        "name": "Qwen 3.6 35B-A3B MoE (4-bit)",
        "short_name": "Qwen3.6 35B MoE",
        "role": "general",
        "role_icon": "⚡",
        "description": (
            "A 35-billion parameter Mixture-of-Experts (MoE) model that only "
            "activates ~3 billion parameters per token. This architecture gives "
            "you the reasoning depth of a 35B model with the speed of a much "
            "smaller one. Quantized to 4-bit for Apple Silicon."
        ),
        "best_for": [
            "Complex multi-step reasoning",
            "Large-scale code generation & refactoring",
            "Long-context document analysis",
            "Advanced mathematical and logical tasks",
        ],
        "not_ideal_for": [
            "Quick one-shot answers (overkill)",
            "Systems with less than 28 GB RAM",
        ],
        "ram_estimate_gb": 24,
        "gpu_limit_required": "26 GB recommended (sudo sysctl iogpu.wired_limit_mb=26624)",
        "performance_tier": "Very Heavy",
        "quantization_summary": "4-bit affine quantization, group size 64",
        "architecture": "Mixture-of-Experts (MoE) — sparse activation",
        "context_window": "Up to 32K tokens (depends on available RAM)",
        "notes": (
            "Requires raising the macOS GPU memory limit. Best used when you "
            "have closed other heavy applications. The MoE design means only a "
            "fraction of the 35B parameters are active per forward pass, keeping "
            "latency competitive with dense 7B models."
        ),
    },

    "mlx-community/Qwen3.6-27B-6bit": {
        "name": "Qwen 3.6 27B (6-bit)",
        "short_name": "Qwen3.6 27B 6-bit",
        "role": "general",
        "role_icon": "⚡",
        "description": (
            "A 27-billion parameter dense model quantized to 6-bit precision. "
            "This offers near-FP16 quality with significantly reduced memory "
            "usage. Excellent coding performance with minimal quality loss from "
            "quantization."
        ),
        "best_for": [
            "High-quality code generation & debugging",
            "Nuanced text analysis and summarization",
            "Tasks where quantization quality matters",
            "Professional coding assistance",
        ],
        "not_ideal_for": [
            "Systems with limited RAM (< 24 GB recommended)",
            "Running alongside other memory-heavy apps",
        ],
        "ram_estimate_gb": 22,
        "gpu_limit_required": "26 GB recommended if other apps are open",
        "performance_tier": "Heavy",
        "quantization_summary": "6-bit affine quantization, group size 64",
        "architecture": "Dense Transformer",
        "context_window": "Up to 32K tokens",
        "notes": (
            "The 6-bit quantization preserves more model quality than 4-bit. "
            "Recommended when you need the highest quality output and have "
            "enough RAM. Consider closing browsers and heavy apps before use."
        ),
    },

    "mlx-community/Qwen3.6-27B-4bit": {
        "name": "Qwen 3.6 27B (4-bit)",
        "short_name": "Qwen3.6 27B 4-bit",
        "role": "general",
        "role_icon": "⚡",
        "description": (
            "A 27-billion parameter dense model quantized to 4-bit precision. "
            "The best balance between quality, speed, and memory usage. Fits "
            "comfortably within macOS default GPU limits, making it the most "
            "practical choice for daily use."
        ),
        "best_for": [
            "Daily coding assistant",
            "General-purpose chat and Q&A",
            "Running alongside other applications",
            "Fast iteration and prototyping",
        ],
        "not_ideal_for": [
            "Tasks requiring maximum output quality (use 6-bit instead)",
        ],
        "ram_estimate_gb": 14,
        "gpu_limit_required": "Not required — fits within default macOS limits",
        "performance_tier": "Light",
        "quantization_summary": "4-bit affine quantization, group size 64",
        "architecture": "Dense Transformer",
        "context_window": "Up to 32K tokens",
        "notes": (
            "Highly recommended as the default daily driver. Fast inference, "
            "excellent coding ability, and low enough memory to leave room for "
            "browsers, IDEs, and other tools. No sudo required."
        ),
    },

    "mlx-community/gpt-oss-20b-MXFP4-Q8": {
        "name": "GPT-OSS 20B (MXFP4-Q8)",
        "short_name": "GPT-OSS 20B",
        "role": "general",
        "role_icon": "⚡",
        "description": (
            "A 20-billion parameter open-source model using mixed-precision "
            "MXFP4/Q8 quantization. Designed for efficiency on Apple Silicon "
            "with a very light memory footprint."
        ),
        "best_for": [
            "Lightweight local coding assistance",
            "Quick tasks when RAM is limited",
            "Running alongside memory-heavy workloads",
            "Testing and experimentation",
        ],
        "not_ideal_for": [
            "Complex multi-step reasoning (prefer 27B or 35B)",
            "Long-form document generation",
        ],
        "ram_estimate_gb": 12,
        "gpu_limit_required": "Not required — fits easily within default limits",
        "performance_tier": "Light",
        "quantization_summary": "Mixed precision MXFP4 with Q8 fallback",
        "architecture": "Dense Transformer",
        "context_window": "Up to 16K tokens",
        "notes": (
            "The lightest model in the collection. Great when you want local "
            "AI assistance but don't want to sacrifice RAM for other tasks. "
            "Pairs well with having browsers and IDEs open simultaneously."
        ),
    },
}


from typing import Dict, List, Optional


def get_registry_entry(model_id: str) -> Optional[dict]:
    """Look up a model by its full HuggingFace ID."""
    return MODEL_REGISTRY.get(model_id)


def get_registry_entry_fuzzy(model_name_fragment: str) -> Optional[dict]:
    """Look up a model by a partial name match (case-insensitive)."""
    fragment = model_name_fragment.lower()
    for model_id, entry in MODEL_REGISTRY.items():
        if fragment in model_id.lower() or fragment in entry["name"].lower():
            return entry
    return None


def get_all_known_model_ids() -> List[str]:
    """Return a list of all registered model IDs."""
    return list(MODEL_REGISTRY.keys())


def get_models_by_role(role: str) -> Dict[str, dict]:
    """Return all registry entries matching a given role."""
    return {
        model_id: entry
        for model_id, entry in MODEL_REGISTRY.items()
        if entry.get("role") == role
    }


def get_all_roles() -> List[str]:
    """Return a sorted list of unique roles in the registry."""
    roles = sorted(set(entry.get("role", "general") for entry in MODEL_REGISTRY.values()))
    return roles


# Role display metadata
ROLE_INFO = {
    "reasoning": {
        "icon": "🧠",
        "label": "Reasoning / Thinking",
        "description": "Plan, analyze, and design before coding",
    },
    "builder": {
        "icon": "🔨",
        "label": "Builder / Coding",
        "description": "Implement, refactor, and build code",
    },
    "general": {
        "icon": "⚡",
        "label": "General Purpose",
        "description": "Good at both reasoning and coding",
    },
}

import os
import json

def _get_config_dir() -> str:
    config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    config_dir = os.path.join(config_home, "mlx-man")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

CUSTOM_MODELS_FILE = os.path.join(_get_config_dir(), "custom_models.json")

def load_custom_models():
    """Load custom models from disk and inject them into MODEL_REGISTRY."""
    if os.path.exists(CUSTOM_MODELS_FILE):
        try:
            with open(CUSTOM_MODELS_FILE, "r") as f:
                custom_models = json.load(f)
                for mid, entry in custom_models.items():
                    entry["role"] = entry.get("role", "general")
                    entry["is_custom"] = True
                    MODEL_REGISTRY[mid] = entry
        except Exception:
            pass

def register_custom_model(model_id: str, name: str, role: str = "general"):
    """Persist a new model to custom_models.json and the active registry."""
    custom_models = {}
    if os.path.exists(CUSTOM_MODELS_FILE):
        try:
            with open(CUSTOM_MODELS_FILE, "r") as f:
                custom_models = json.load(f)
        except Exception:
            pass
            
    entry = {
        "name": name,
        "short_name": name,
        "role": role,
        "description": "Custom model added via Sync.",
        "performance_tier": "Custom",
        "is_custom": True
    }
    
    custom_models[model_id] = entry
    MODEL_REGISTRY[model_id] = entry
    
    with open(CUSTOM_MODELS_FILE, "w") as f:
        json.dump(custom_models, f, indent=4)

load_custom_models()
