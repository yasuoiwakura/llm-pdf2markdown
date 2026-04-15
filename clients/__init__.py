from .base import LLMClient
from .ollama import OllamaClient
from .lmstudio import LMStudioClient


def create_client(provider: str, model: str, config: dict) -> LLMClient:
    """Factory: Erstellt passenden Client basierend auf provider."""
    if provider == "ollama":
        return OllamaClient(
            url=config.get("OLLAMA_URL", "http://localhost:11434"),
            model=model,
            keep_alive=config.get("OLLAMA_KEEP_ALIVE", "30m")
        )
    elif provider == "lmstudio":
        return LMStudioClient(
            url=config.get("LMSTUDIO_URL", "http://localhost:1234"),
            model=model,
            context_size=config.get("LMSTUDIO_CONTEXT_SIZE"),
            context_size_per_request=config.get("CONTEXT_SIZE_PER_REQUEST") == "1",
            context_size_by_load=config.get("CONTEXT_SIZE_BY_MODEL_LOAD", False)
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


__all__ = ["LLMClient", "OllamaClient", "LMStudioClient", "create_client"]
