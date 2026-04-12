import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("OLLAMA_URL")
MODEL = os.getenv("OLLAMA_MODEL")

import httpx

def ping():
    client = httpx.Client(timeout=10)
    try:
        resp = client.get(f"{URL}/api/tags")
        return resp.status_code == 200
    except:
        return False

def send_prompt(prompt: str) -> str:
    client = httpx.Client(timeout=120)
    resp = client.post(
        f"{URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False},
    )
    resp.raise_for_status()
    return resp.json()["response"]

# Step 1: Connection
print(f"URL: {URL}")
print(f"Model: {MODEL}")

if ping():
    print("[OK] Connected to Ollama")
else:
    print("[FAIL] Cannot connect to Ollama")
    exit(1)

# Step 2: Text prompt
print("\nSending prompt...")
response = send_prompt("Say 'Hello from Ollama and Python!' in exactly those words.")
print(f"Response: {response}")

# # Step 3: PDF text extraction
# # # Step 4: Text → Markdown
# # # Step 5: Images (MVP)