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

# Step 1: Connection
print(f"URL: {URL}")
print(f"Model: {MODEL}")

if ping():
    print("[OK] Connected to Ollama")
else:
    print("[FAIL] Cannot connect to Ollama")

# # Step 2: Text prompt
# # # Step 3: PDF text extraction
# # # Step 4: Text → Markdown
# # # Step 5: Images (MVP)