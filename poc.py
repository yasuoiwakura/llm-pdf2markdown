"""PoC: Test Ollama connection and text prompt."""
import os
from dotenv import load_dotenv

from llm_pdf2markdown import OllamaClient

load_dotenv()

url = os.getenv("OLLAMA_URL", "http://localhost:11434")
model = os.getenv("OLLAMA_MODEL", "gemma3:4b")

print(f"URL: {url}")
print(f"Model: {model}")

client = OllamaClient(url, model)

print("\n1. Checking connection...")
if client.ping():
    print("   [OK] Connected")
else:
    print("   [FAIL] Connection failed - is Ollama running?")
    exit(1)

print("\n2. Sending text prompt...")
response = client.generate("Say 'Hello from Ollama!' in exactly those words.")
print(f"   Response: {response}")

print("\n[OK] PoC successful")
