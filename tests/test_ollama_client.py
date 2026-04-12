import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from llm_pdf2markdown.ollama_client import OllamaClient, OllamaResponse


class TestOllamaClient:
    def test_check_connection_success(self):
        with patch("httpx.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.get.return_value.status_code = 200
            mock_client.return_value = mock_instance

            client = OllamaClient("http://localhost:11434", "gemma3:4b")
            assert client.check_connection() is True

    def test_check_connection_failure(self):
        import httpx
        with patch("httpx.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client.return_value = mock_instance

            client = OllamaClient("http://localhost:11434", "gemma3:4b")
            assert client.check_connection() is False
