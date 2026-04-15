"""Ollama client for sending prompts and images."""
import base64
import httpx
from pathlib import Path


class OllamaClient:
    def __init__(self, url: str, model: str, timeout: float = 120.0):
        self.url = url.rstrip("/")
        self.model = model
        self._client = httpx.Client(timeout=timeout)

    def ping(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            return self._client.get(f"{self.url}/api/tags").status_code == 200
        except httpx.ConnectError:
            return False

    def generate(self, prompt: str) -> str:
        """Send text prompt, return response."""
        resp = self._client.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def generate_with_image(self, image_path: Path | list[Path], prompt: str) -> str:
        """Send single or multiple images + prompt, return response."""
        if isinstance(image_path, list):
            image_paths = image_path
        else:
            image_paths = [image_path]
        images_b64 = [base64.b64encode(img.read_bytes()).decode() for img in image_paths]
        resp = self._client.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": prompt, "images": images_b64, "stream": False},
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def close(self):
        self._client.close()
