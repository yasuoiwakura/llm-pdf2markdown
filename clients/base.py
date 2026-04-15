from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class LLMClient(ABC):
    """Abstract base class for all LLM clients."""
    
    model: str
    provider: str
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Text-only prompt → response."""
        pass
    
    @abstractmethod
    def generate_with_image(self, image_path: Path, prompt: str) -> str:
        """Image + prompt → markdown response."""
        pass
    
    @abstractmethod
    def get_usage(self) -> Dict[str, int]:
        """Return: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}"""
        pass
    
    @abstractmethod
    def close(self):
        """Cleanup resources."""
        pass
    
    @abstractmethod
    def ping(self) -> bool:
        """Check connection."""
        pass
    
    @abstractmethod
    def load_model(self, context_length: int = None):
        """Load model with optional context_length (for LM Studio)."""
        pass
    
    @abstractmethod
    def unload_model(self):
        """Unload model (for LM Studio cleanup)."""
        pass
