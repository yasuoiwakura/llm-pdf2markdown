import httpx
import base64
from pathlib import Path
from typing import Dict, Any

from .base import LLMClient


class OllamaClient(LLMClient):
    """Ollama LLM client implementation."""
    
    def __init__(self, url: str, model: str, keep_alive: str = "30m"):
        self.url = url
        self.model = model
        self.provider = "ollama"
        self.keep_alive = keep_alive
        self._client = httpx.Client(timeout=120)
        self._last_usage = {}
    
    def ping(self) -> bool:
        try:
            resp = self._client.get(f"{self.url}/api/tags")
            return resp.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str) -> str:
        resp = self._client.post(
            f"{self.url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "keep_alive": self.keep_alive,
                "stream": False
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._last_usage = {}
        return data.get("response", "")
    
    def generate_with_image(self, image_path: Path, prompt: str) -> str:
        image_b64 = base64.b64encode(image_path.read_bytes()).decode()
        resp = self._client.post(
            f"{self.url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "images": [image_b64],
                "keep_alive": self.keep_alive,
                "stream": False
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._last_usage = {}
        return data.get("response", "")
    
    def get_usage(self) -> Dict[str, int]:
        return self._last_usage
    
    def load_model(self, context_length: int = None):
        """Ollama loads models automatically on first use."""
        pass
    
    def unload_model(self):
        """Ollama uses keep_alive for cleanup."""
        pass
    
    def close(self):
        self._client.close()
