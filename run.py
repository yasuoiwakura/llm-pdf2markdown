import os
import shutil
import base64
import httpx
from pathlib import Path
from dotenv import load_dotenv
import pypdfium2

load_dotenv()

URL = os.getenv("OLLAMA_URL")
MODEL = os.getenv("OLLAMA_MODEL")
INPUT_PDF = os.getenv("TEST_PDF")
SCALE = 2.0

def pdf_to_images(pdf_path: Path) -> list[Path]:
    pdf = pypdfium2.PdfDocument(str(pdf_path))
    images = []
    tmpdir = Path("temp_images")
    tmpdir.mkdir(exist_ok=True)
    for i, page in enumerate(pdf):
        image = page.render(pypdfium2.PdfBitmap.to_pil, scale=SCALE)
        path = tmpdir / f"page_{i+1:03d}.png"
        image.save(path, "PNG")
        images.append(path)
    return images

def ollama_generate(prompt: str) -> str:
    client = httpx.Client(timeout=120)
    resp = client.post(
        f"{URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False},
    )
    resp.raise_for_status()
    return resp.json()["response"]

def ollama_generate_with_image(image_path: Path, prompt: str) -> str:
    image_b64 = base64.b64encode(image_path.read_bytes()).decode()
    client = httpx.Client(timeout=120)
    resp = client.post(
        f"{URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "images": [image_b64], "stream": False},
    )
    resp.raise_for_status()
    return resp.json()["response"]

def main():
    print(f"URL: {URL}")
    print(f"Model: {MODEL}")
    print(f"Input: {INPUT_PDF}")

    input_path = Path(INPUT_PDF)
    output_path = input_path.with_suffix(".md")

    images = pdf_to_images(input_path)
    print(f"Converting {len(images)} page(s)...")

    parts = []
    for i, img in enumerate(images, 1):
        print(f"  Page {i}/{len(images)}...")
        md = ollama_generate_with_image(img, "Convert this image to Markdown.")
        parts.append(md)

    shutil.rmtree("temp_images")
    output_path.write_text("\n\n---\n\n".join(parts), encoding="utf-8")
    print(f"Created: {output_path}")

if __name__ == "__main__":
    main()