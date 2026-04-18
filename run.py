import os
import shutil
import json
import base64
import argparse
from pathlib import Path
from dotenv import load_dotenv
import pypdfium2

load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description="Convert PDFs to Markdown using local LLM")
parser.add_argument("--verbose", "-v", type=int, default=None, help="Verbosity level (0-3)")
parser.add_argument("--test-pdf", type=str, default=None, help="Override TEST_PDF")
args = parser.parse_args()

# Debug config (early, with CLI override)
VERBOSE = args.verbose if args.verbose is not None else int(os.getenv("VERBOSE", "0"))

# Boolean parsing helper (idiotensicher)
def bool_from_env(env_name: str, default: bool = False) -> bool:
    """Parse boolean from environment variable (idiotensicher)."""
    TRUE_VALUES = ["1", "true"]
    FALSE_VALUES = ["0", "false"]
    
    value = str(os.getenv(env_name, "")).lower().strip()
    
    if value in TRUE_VALUES:
        return True
    elif value in FALSE_VALUES:
        return False
    else:
        return default

# LLM Provider config
USE_OLLAMA = bool_from_env("USE_OLLAMA", True)
USE_LMSTUDIO = bool_from_env("USE_LMSTUDIO", False)

# Config dictionary for LLMManager
CONFIG = {
    "USE_OLLAMA": USE_OLLAMA,
    "USE_LMSTUDIO": USE_LMSTUDIO,
    "OLLAMA_URL": os.getenv("OLLAMA_URL"),
    "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL"),
    "OLLAMA_KEEP_ALIVE": os.getenv("OLLAMA_KEEP_ALIVE", "30m"),
    "LMSTUDIO_URL": os.getenv("LMSTUDIO_URL"),
    "LMSTUDIO_MODEL": os.getenv("LMSTUDIO_MODEL"),
    "LMSTUDIO_CONTEXT_SIZE": os.getenv("LMSTUDIO_CONTEXT_SIZE", ""),
    "CONTEXT_SIZE_PER_REQUEST": os.getenv("CONTEXT_SIZE_PER_REQUEST", "0"),
    "CONTEXT_SIZE_BY_MODEL_LOAD": bool_from_env("CONTEXT_SIZE_BY_MODEL_LOAD", False),
}

# LM Studio config
LMSTUDIO_CONTEXT_SIZE = os.getenv("LMSTUDIO_CONTEXT_SIZE", "")
CONTEXT_SIZE_BY_MODEL_LOAD = bool_from_env("CONTEXT_SIZE_BY_MODEL_LOAD", False)

# Output config
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "")
OUTPUT_INTO_SAME_DIR = bool_from_env("OUTPUT_INTO_SAME_DIR", True)
OVERWRITE_OUTPUT_FILES = bool_from_env("OVERWRITE_OUTPUT_FILES", False)
KEEP_TEMP_FILES = bool_from_env("KEEP_TEMP_FILES", False)

# Prompt config
OCR_PROMPT = os.getenv("OCR_PROMPT", "")
OCR_PROMPT_FILE = os.getenv("OCR_PROMPT_FILE", "")

# Multi-page config
MAX_PAGES_PER_REQUEST = int(os.getenv("MAX_PAGES_PER_REQUEST", "4"))

# Step prompts (required for multi-step processing)
OCR_PROMPT_FILE_STEP1 = os.getenv("OCR_PROMPT_FILE_STEP1", "")
OCR_PROMPT_FILE_STEP2 = os.getenv("OCR_PROMPT_FILE_STEP2", "")
OCR_PROMPT_FILE_STEP3 = os.getenv("OCR_PROMPT_FILE_STEP3", "")

# Initialize LLM Manager
from clients import create_client
from clients.manager import LLMManager

llm_manager = LLMManager(CONFIG, verbose=VERBOSE)

# Determine provider
if USE_LMSTUDIO:
    PROVIDER = "LM Studio"
    URL = CONFIG["LMSTUDIO_URL"]
    MODEL = CONFIG.get("LMSTUDIO_MODEL", "")
elif USE_OLLAMA:
    PROVIDER = "Ollama"
    URL = CONFIG["OLLAMA_URL"]
    MODEL = CONFIG["OLLAMA_MODEL"]
else:
    print("[ERROR] No LLM provider enabled (set USE_OLLAMA=true or USE_LMSTUDIO=true)")
    exit(1)


def load_prompt(env_key: str, file_key: str, default: str) -> str:
    """Load prompt from .env or from file."""
    prompt = os.getenv(env_key, "")
    file_path = os.getenv(file_key, "")
    
    if file_path and Path(file_path).exists():
        return Path(file_path).read_text(encoding="utf-8").strip()
    elif prompt:
        return prompt
    else:
        return default

# Prompt for OCR
OCR_PROMPT_TEXT = load_prompt("OCR_PROMPT", "OCR_PROMPT_FILE", "Convert this image to markdown")

# Multi-phase prompts
OCR_PROMPT_STEP1 = load_prompt("", "OCR_PROMPT_FILE_STEP1", "")
OCR_PROMPT_STEP2 = load_prompt("", "OCR_PROMPT_FILE_STEP2", "")
OCR_PROMPT_STEP3 = load_prompt("", "OCR_PROMPT_FILE_STEP3", "")

# Test config
TEST_PDF = os.getenv("TEST_PDF")
SCALE = 2.0

# Debug config
VERBOSE = int(os.getenv("VERBOSE", "0"))

def debug(level: int, *args):
    """Print debug message if VERBOSE >= level."""
    if VERBOSE >= level:
        print(f"[DEBUG:{level}]", *args)


def replace_prompt_vars(prompt: str, total_pages: int, current_page: int = 0, source_file: str = "", temp_filenames: list[str] = None) -> str:
    """Replace placeholders in prompt."""
    if temp_filenames is None:
        temp_filenames = []
    
    result = prompt
    result = result.replace("{total_pages}", str(total_pages))
    result = result.replace("{current_page}", str(current_page))
    result = result.replace("{source_file}", source_file)
    result = result.replace("{temp_filenames}", ", ".join(temp_filenames))
    return result

# Initialize LLM Manager
from clients import create_client
from clients.manager import LLMManager

llm_manager = LLMManager(CONFIG, verbose=VERBOSE)

# Initialize LLM clients through manager
llm_manager.init_clients("lmstudio" if USE_LMSTUDIO else "ollama")

# Get model from first active step for debug display
current_model = None
for step in [1, 2, 3]:
    client = llm_manager.get_client(step)
    if client:
        current_model = client.model
        break

# Zeige Konfiguration in einer Zeile bei verbose >= 1
debug(1, f"Provider: {PROVIDER} | URL: {URL} | Model: {current_model}")


def ping() -> bool:
    """Check if LLM is reachable using manager."""
    client = llm_manager.get_client(1)
    return client.ping()


def get_models() -> list:
    """Get available models."""
    if USE_LMSTUDIO:
        import httpx
        c = httpx.Client(timeout=10)
        resp = c.get(f"{URL}/v1/models")
        resp.raise_for_status()
        return resp.json()["data"]
    else:
        import httpx
        c = httpx.Client(timeout=10)
        resp = c.get(f"{URL}/api/tags")
        resp.raise_for_status()
        return resp.json()["models"]


def check_model_availability():
    """Prüfe ob alle in model_config.toml definierten Modelle beim Server verfügbar sind."""
    print("\n[Model Check] Checking availability of configured models...")
    
    # Get available models from server
    try:
        available_models = get_models()
    except Exception as e:
        print(f"[WARN] Could not fetch model list: {e}")
        return
    
    # Extract model IDs based on provider
    if USE_LMSTUDIO:
        available_ids = [m.get("id", "") for m in available_models]
    else:
        available_ids = [m.get("name", "") for m in available_models]
    
    # Get configured models from LLMManager
    configured_models = set()
    for step in [1, 2, 3]:
        client = llm_manager.get_client(step)
        if client and client.model:
            configured_models.add(client.model)
    
    # Check each configured model
    all_available = True
    for model in configured_models:
        # Check if model is available (partial match for quantized variants)
        found = any(model in available_id or available_id in model for available_id in available_ids)
        if found:
            debug(1, f"[OK] Model '{model}' is available")
        else:
            print(f"[WARN] Model '{model}' not found in available models")
            all_available = False
    
    if not configured_models:
        print("[WARN] No models configured")
    elif all_available:
        print(f"[OK] All {len(configured_models)} configured models available")
    
    return all_available


def find_loaded_model() -> str:
    """Legacy - now handled by LLMManager."""
    return ""


def load_model() -> None:
    """Load model with context_length before chat."""
    pass  # Legacy - now handled by LLMManager from model_config.toml


def send_prompt(prompt: str, step: int = 2) -> str:
    """Send text prompt using LLMManager."""
    client = llm_manager.get_client(step)
    return client.generate(prompt)


def send_prompt_with_image(image_path: Path, prompt: str, step: int = 1) -> str:
    """Send single image + text prompt using LLMManager."""
    client = llm_manager.get_client(step)
    return client.generate_with_image(image_path, prompt)


def send_prompt_with_multiple_images(image_paths: list[Path], prompt: str, step: int = 1) -> str:
    """Send multiple images + text prompt using LLMManager."""
    client = llm_manager.get_client(step)
    # Send all images in a single request
    return client.generate_with_image(image_paths, prompt)


def pdf_to_images(pdf_path: Path) -> list[Path]:
    """Convert PDF pages to PNG images."""
    pdf = pypdfium2.PdfDocument(str(pdf_path))
    images = []
    tmpdir = Path("temp_images")
    if tmpdir.exists():
        shutil.rmtree(tmpdir)
    tmpdir.mkdir()
    
    n_pages = len(pdf)
    page_names = []
    for page_number in range(n_pages):
        page = pdf.get_page(page_number)
        bitmap = page.render(scale=SCALE)
        pil_image = bitmap.to_pil()
        path = tmpdir / f"page_{page_number+1:03d}.png"
        pil_image.save(path, "PNG")
        images.append(path)
        page_names.append(path.name)
    
    pdf.close()
    print(f"[OK] Saved {n_pages} pages: {', '.join(page_names)}")
    return images


def step1_ocr_single_pages(images: list[Path], prompt: str, total_pages: int) -> str:
    """Step 1: Plain OCR - jede Seite einzeln.
    Returns: Markdown mit allen Seiteninhalten (ggf. redundant)
    Mit Page Markern: # page n/total + <!-- start/end content page n of t -->
    """
    client = llm_manager.get_client(1)
    print(f"\n=== Step 1: Plain OCR (single pages) ===")
    print(f"[INFO] Model: {client.model}")
    all_pages_md = []
    
    for i, img in enumerate(images, 1):
        print(f"  Page {i}/{total_pages}...")
        page_prompt = replace_prompt_vars(prompt, total_pages, i)
        md = send_prompt_with_image(img, page_prompt)
        
        # Entferne Code-Fences
        md = md.strip()
        if md.startswith("```markdown"):
            md = md[len("```markdown"):]
        elif md.startswith("```"):
            md = md[len("```"):]
        if md.endswith("```"):
            md = md[:-3]
        md = md.strip()
        
        # Füge Page Markers hinzu (SPEC-konform)
        # Python fügt # page n/t + <!-- start/end content --> ein
        page_section = f"""# page {i}/{total_pages}

<!-- start content page {i} of {total_pages} -->
{md}
<!-- end content page {i} of {total_pages} -->"""
        
        all_pages_md.append(page_section)
        print(f"    Done: {len(md)} chars")
    
    result = "\n\n".join(all_pages_md)
    print(f"[OK] Step 1 complete: {len(result)} chars total")
    return result


def step2_extract_metadata(images: list[Path], prompt: str, total_pages: int) -> str:
    """Step 2: Metadaten extrahieren.
    Returns: YAML-String mit Metadaten
    """
    client = llm_manager.get_client(2)
    print(f"\n=== Step 2: Metadata Extraction ===")
    print(f"[INFO] Model: {client.model}")
    
    page_prompt = replace_prompt_vars(prompt, total_pages)
    md = send_prompt_with_multiple_images(images, page_prompt, step=2)
    
    # Entferne Code-Fences
    md = md.strip()
    if md.startswith("```yaml"):
        md = md[len("```yaml"):]
    elif md.startswith("```"):
        md = md[len("```"):]
    if md.endswith("```"):
        md = md[:-3]
    md = md.strip()
    
    print(f"[OK] Step 2 complete: {len(md)} chars")
    return md


def step3_finalize(single_pages_md: str, metadata_yaml: str, prompt: str, total_pages: int) -> str:
    """Step 3: Zusammenführen und bereinigen.
    Returns: Sauberes, zusammenhängendes Markdown mit eingebetteten Metadaten
    """
    client = llm_manager.get_client(3)
    print(f"\n=== Step 3: Finalization ===")
    print(f"[INFO] Model: {client.model}")
    
    # Baue Prompt mit Inhalten
    final_prompt = f"""{prompt}

SINGLE_PAGES_MARKDOWN:
{single_pages_md}

METADATA_YAML:
{metadata_yaml}
"""
    page_prompt = replace_prompt_vars(final_prompt, total_pages)
    md = send_prompt(page_prompt)
    
    # Entferne Code-Fences
    md = md.strip()
    if md.startswith("```markdown"):
        md = md[len("```markdown"):]
    elif md.startswith("```"):
        md = md[len("```"):]
    if md.endswith("```"):
        md = md[:-3]
    md = md.strip()
    
    print(f"[OK] Step 3 complete: {len(md)} chars")
    return md


# Step 1: Connection
if ping():
    print(f"[OK] Connected to {PROVIDER}")
else:
    print(f"[FAIL] Cannot connect to {PROVIDER}")
    exit(1)

# Step 2: Check model availability (before any processing)
check_model_availability()

# Step 3: PDF → Images
print(f"\n[Preparing data] Converting PDF to images: {TEST_PDF}")
images = pdf_to_images(Path(TEST_PDF))

# Bestimme Output-Pfad
input_path = Path(TEST_PDF)
if OUTPUT_INTO_SAME_DIR:
    output_dir = input_path.parent
else:
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

single_pages_path = output_dir / f"{input_path.stem}_single_pages.md"
metadata_path = output_dir / f"{input_path.stem}_metadata.yaml"
final_output_path = output_dir / f"{input_path.stem}.md"

# Prüfe ob Dateien bereits existieren
if single_pages_path.exists() and final_output_path.exists() and not OVERWRITE_OUTPUT_FILES:
    print(f"[ERROR] Output files already exist: {single_pages_path}, {final_output_path}")
    exit(1)

total_pages = len(images)
source_file = input_path.name
temp_filenames = [img.name for img in images]

# Check if prompts are loaded
if not OCR_PROMPT_STEP1 or not OCR_PROMPT_STEP2 or not OCR_PROMPT_STEP3:
    print("[ERROR] All 3 step prompts are required:")
    print(f"  - OCR_PROMPT_FILE_STEP1: {'SET' if OCR_PROMPT_FILE_STEP1 else 'MISSING'}")
    print(f"  - OCR_PROMPT_FILE_STEP2: {'SET' if OCR_PROMPT_FILE_STEP2 else 'MISSING'}")
    print(f"  - OCR_PROMPT_FILE_STEP3: {'SET' if OCR_PROMPT_FILE_STEP3 else 'MISSING'}")
    exit(1)

# ============ STEP 1: Plain OCR ============
print(f"\n[Step 1/{3}] Plain OCR - Processing {total_pages} pages individually...")
single_pages_md = step1_ocr_single_pages(images, OCR_PROMPT_STEP1, total_pages)

# Speichere Step 1 Output
single_pages_path.write_text(single_pages_md, encoding="utf-8")
print(f"[OK] Saved: {single_pages_path}")

# Cleanup Step 1 client if different from default
debug(1, "Cleaning up Step 1 client...")
llm_manager.cleanup_after_step1()

# ============ STEP 2: Metadata ============
print(f"\n[Step 2/{3}] Extracting metadata from all pages...")
metadata_yaml = step2_extract_metadata(images, OCR_PROMPT_STEP2, total_pages)

# Speichere Step 2 Output
metadata_path.write_text(metadata_yaml, encoding="utf-8")
print(f"[OK] Saved: {metadata_path}")

# ============ STEP 3: Finalize ============
print(f"\n[Step 3/{3}] Finalizing document with metadata...")
final_md = step3_finalize(single_pages_md, metadata_yaml, OCR_PROMPT_STEP3, total_pages)

# Entferne Code-Fences
final_md = final_md.strip()
if final_md.startswith("```markdown"):
    final_md = final_md[len("```markdown"):]
elif final_md.startswith("```"):
    final_md = final_md[len("```"):]
if final_md.endswith("```"):
    final_md = final_md[:-3]
final_md = final_md.strip()

final_output_path.write_text(final_md, encoding="utf-8")
print(f"[OK] Saved: {final_output_path}")

output_path = final_output_path

# Cleanup temp images
if not KEEP_TEMP_FILES:
    shutil.rmtree("temp_images")
    print("[OK] Cleaned up temp_images/")
else:
    print(f"[INFO] Kept temp_images/")

# Cleanup all LLM clients
debug(1, "Closing all LLM clients...")
llm_manager.close_all()
print("[OK] All LLM clients closed")