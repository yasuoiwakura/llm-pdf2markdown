import httpx
import base64
from pathlib import Path
from typing import Dict, Any

from .base import LLMClient


class LMStudioClient(LLMClient):
    """LM Studio LLM client implementation."""
    
    def __init__(self, url: str, model: str, context_size: int = None, 
                 context_size_per_request: bool = False, context_size_by_load: bool = False):
        self.url = url
        self.model = model
        self.provider = "lmstudio"
        self.context_size = context_size
        self.context_size_per_request = context_size_per_request
        self.context_size_by_load = context_size_by_load
        self._client = httpx.Client(timeout=180)
        self._last_usage = {}
        self._instance_id = ""
    
    def ping(self) -> bool:
        try:
            resp = self._client.get(f"{self.url}/v1/models")
            return resp.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str) -> str:
        model_to_use = self._instance_id if self._instance_id else self.model
        payload = {
            "model": model_to_use,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        if self.context_size and self.context_size_per_request:
            payload["max_tokens"] = self.context_size
        
        resp = self._client.post(f"{self.url}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        self._last_usage = data.get("usage", {})
        return data["choices"][0]["message"]["content"]
    
    def generate_with_image(self, image_path: Path | list[Path], prompt: str) -> str:
        # Support single image or multiple images
        if isinstance(image_path, list):
            image_paths = image_path
        else:
            image_paths = [image_path]
        
        # Build content: text + multiple images
        content = [{"type": "text", "text": prompt}]
        for img in image_paths:
            image_b64 = base64.b64encode(img.read_bytes()).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}})
        
        model_to_use = self._instance_id if self._instance_id else self.model
        payload = {
            "model": model_to_use,
            "messages": [{"role": "user", "content": content}],
            "stream": False
        }
        if self.context_size and self.context_size_per_request:
            payload["max_tokens"] = self.context_size
        
        resp = self._client.post(f"{self.url}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        self._last_usage = data.get("usage", {})
        return data["choices"][0]["message"]["content"]
    
    def get_usage(self) -> Dict[str, int]:
        return self._last_usage
    
    def load_model(self, context_length: int = None):
        """Load model with context_length."""
        if not self.context_size_by_load:
            return
        
        ctx = context_length or self.context_size
        if not ctx:
            return
        
        resp = self._client.post(
            f"{self.url}/api/v1/models/load",
            json={"model": self.model, "context_length": int(ctx)}
        )
        
        if resp.status_code == 200:
            data = resp.json()
            self._instance_id = data.get("instance_id", "")
            self._was_explicitly_loaded = True
        elif resp.status_code == 409:
            # Already loaded, get instance info
            self._instance_id = self.model  # Fall back to model name
            self._was_explicitly_loaded = True
    
    def unload_model(self):
        """Unload model from memory."""
        if not self._instance_id:
            return
        
        try:
            self._client.post(
                f"{self.url}/api/v1/models/unload",
                json={"instance_id": self._instance_id}
            )
        except:
            pass
        finally:
            self._instance_id = ""
            self._was_explicitly_loaded = False
    
    def close(self):
        # NUR entladen wenn Modell explizit geladen wurde
        if getattr(self, '_was_explicitly_loaded', False):
            self.unload_model()
        self._client.close()
