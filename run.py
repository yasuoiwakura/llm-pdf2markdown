import os
import shutil
import json
import base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("OLLAMA_URL")
MODEL = os.getenv("OLLAMA_MODEL")
KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
TEST_PDF = os.getenv("TEST_PDF")
SCALE = 2.0

import httpx
import pypdfium2

def ping():
    client = httpx.Client(timeout=10)
    try:
        resp = client.get(f"{URL}/api/tags")
        return resp.status_code == 200
    except:
        return False

def get_models():
    client = httpx.Client(timeout=10)
    resp = client.get(f"{URL}/api/tags")
    resp.raise_for_status()
    return resp.json()["models"]

def get_running_models():
    client = httpx.Client(timeout=10)
    resp = client.get(f"{URL}/api/ps")
    resp.raise_for_status()
    return resp.json()["models"]

def send_prompt(prompt: str) -> str:
    client = httpx.Client(timeout=120)
    resp = client.post(
        f"{URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "keep_alive": KEEP_ALIVE, "stream": False},
    )
    resp.raise_for_status()
    return resp.json()["response"]

def send_prompt_with_image(image_path: Path, prompt: str) -> str:
    """Send image + text prompt, return response."""
    image_b64 = base64.b64encode(image_path.read_bytes()).decode()
    client = httpx.Client(timeout=120)
    resp = client.post(
        f"{URL}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "images": [image_b64],
            "keep_alive": KEEP_ALIVE,
            "stream": False
        },
    )
    resp.raise_for_status()
    return resp.json()["response"]

def pdf_to_images(pdf_path: Path) -> list[Path]:
    """Convert PDF pages to PNG images."""
    pdf = pypdfium2.PdfDocument(str(pdf_path))
    images = []
    tmpdir = Path("temp_images")
    if tmpdir.exists():
        shutil.rmtree(tmpdir)
    tmpdir.mkdir()
    
    n_pages = len(pdf)
    for page_number in range(n_pages):
        page = pdf.get_page(page_number)
        bitmap = page.render(scale=SCALE)
        pil_image = bitmap.to_pil()
        path = tmpdir / f"page_{page_number+1:03d}.png"
        pil_image.save(path, "PNG")
        images.append(path)
        print(f"  Saved: {path.name}")
    
    pdf.close()
    return images

# Step 1: Connection
print(f"URL: {URL}")
print(f"Model: {MODEL}")

if ping():
    print("[OK] Connected to Ollama")
else:
    print("[FAIL] Cannot connect to Ollama")
    exit(1)

# Check available models
print("\nAvailable models:")
models = get_models()
for m in models:
    name = m.get("name", "?")
    size = m.get("size", 0) // (1024*1024*1024)
    print(f"  - {name} ({size:.1f} GB)")

# Check if desired model is available
model_base = MODEL.split(":")[0]
available = any(m.get("name", "").startswith(model_base) for m in models)
if available:
    print(f"\n[OK] Model '{MODEL}' is available")
else:
    print(f"\n[WARN] Model '{MODEL}' not found")

# Check running models
print("\nRunning models (in memory):")
running = get_running_models()
if running:
    for m in running:
        name = m.get("name", "?")
        expires = m.get("expires_at", "?")
        print(f"  - {name} (until {expires})")
else:
    print("  (none)")

# Check if desired model is running
running_names = [m.get("name", "") for m in running]
running = any(model_base in name for name in running_names)
if running:
    print(f"\n[OK] Model '{MODEL}' is RUNNING")
else:
    print(f"\n[WARN] Model '{MODEL}' is NOT running (will be loaded on first prompt)")

# Step 2: Text prompt
print("\nSending prompt...")
response = send_prompt("Say 'Hello from Ollama and Python!' in exactly those words.")
print(f"Response: {response}")

# Step 3: PDF → Images
print(f"\nConverting PDF to images: {TEST_PDF}")
images = pdf_to_images(Path(TEST_PDF))
print(f"[OK] {len(images)} page(s) saved to temp_images/")

# Step 4: Image → Markdown (nur Seite 1)
print("\nSending image to LLM (page 1)...")
first_image = images[0]
md = send_prompt_with_image(first_image, "Convert this image to Markdown.")
print(f"\nMarkdown (page 1):\n{md}")

# # Step 5: Save Markdown
# # # Step 5: Images (MVP)
# # # Step 4: Text → Markdown
# # # Step 5: Images (MVP)