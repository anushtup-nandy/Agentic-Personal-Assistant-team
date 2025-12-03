"""
Centralized LLM Configuration
All Gemini and Ollama model settings in one place.
"""

# Default LLM Provider Settings
DEFAULT_LLM_PROVIDER = "gemini"  # Options: "gemini" or "ollama"

# Gemini Settings
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS = 500

# Ollama Settings  
OLLAMA_DEFAULT_MODEL = "gemma3:4b"
OLLAMA_TEMPERATURE = 0.7
OLLAMA_MAX_TOKENS = 500

# Model choices for UI
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2-pro",
]

OLLAMA_MODELS = [
    "gemma3:4b",
    "qwen3:8b",
]

# Agent-specific defaults (can be overridden per agent)
AGENT_DEFAULTS = {
    "model_provider": DEFAULT_LLM_PROVIDER,
    "model_name": GEMINI_DEFAULT_MODEL,
    "temperature": GEMINI_TEMPERATURE,
    "max_tokens": GEMINI_MAX_TOKENS,
}

def get_model_config(provider: str = None, model_name: str = None):
    """Get model configuration with defaults."""
    provider = provider or DEFAULT_LLM_PROVIDER
    
    if provider == "gemini":
        return {
            "provider": "gemini",
            "model": model_name or GEMINI_DEFAULT_MODEL,
            "temperature": GEMINI_TEMPERATURE,
            "max_tokens": GEMINI_MAX_TOKENS,
        }
    elif provider == "ollama":
        return {
            "provider": "ollama",
            "model": model_name or OLLAMA_DEFAULT_MODEL,
            "temperature": OLLAMA_TEMPERATURE,
            "max_tokens": OLLAMA_MAX_TOKENS,
        }
    else:
        raise ValueError(f"Unknown provider: {provider}")
