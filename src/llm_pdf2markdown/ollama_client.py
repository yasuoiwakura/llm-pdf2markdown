import base64
import httpx
from pathlib import Path
from dataclasses import dataclass


@dataclass
class OllamaResponse:
    success: bool
    markdown: str | None = None
    error: str | None = None


class OllamaClient:
    def __init__(self, url: str, model: str):
        self.url = url.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=120.0)

    def check_connection(self) -> bool:
        try:
            resp = self.client.get(f"{self.url}/api/tags")
            return resp.status_code == 200
        except httpx.ConnectError:
            return False

    def send_text(self, prompt: str) -> OllamaResponse:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            resp = self.client.post(f"{self.url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return OllamaResponse(success=True, markdown=data.get("response", ""))
        except httpx.HTTPError as e:
            return OllamaResponse(success=False, error=str(e))

    def send_image(self, image_path: Path, prompt: str) -> OllamaResponse:
        image_bytes = image_path.read_bytes()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }
        try:
            resp = self.client.post(f"{self.url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return OllamaResponse(success=True, markdown=data.get("response", ""))
        except httpx.HTTPError as e:
            return OllamaResponse(success=False, error=str(e))

    def close(self):
        self.client.close()
