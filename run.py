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

# Input modes (mutually exclusive)
input_group = parser.add_mutually_exclusive_group()
input_group.add_argument("--test-pdf", type=str, default=None, help="Single PDF file")
input_group.add_argument("--input-dir", type=str, default=None, help="Directory containing PDFs")

# Batch options
parser.add_argument("--recursive", action="store_true", help="Process directories recursively")
parser.add_argument("--output-structure", choices=["preserve", "flat"], default=None, help="Output directory structure (preserve=keep subdirs, flat=all in one dir)")
parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")

# General options
parser.add_argument("--verbose", "-v", type=int, default=None, help="Verbosity level (0-3)")
parser.add_argument("--output-dir", type=str, default=None, help="Output directory")

args = parser.parse_args()

# Batch options override from CLI
if args.input_dir is not None:
    INPUT_DIR = args.input_dir
if args.recursive:
    RECURSIVE = True
if args.output_structure is not None:
    OUTPUT_STRUCTURE = args.output_structure
if args.overwrite:
    OVERWRITE_OUTPUT_FILES = True
if args.output_dir is not None:
    OUTPUT_DIR = args.output_dir

# Legacy: TEST_PDF from CLI
TEST_PDF = args.test_pdf if args.test_pdf else os.getenv("TEST_PDF")

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

# Multi-phase prompts - loaded from model_config.toml [prompts] section
def load_prompt_from_config(step: int) -> str:
    """Load prompt for a step from model_config.toml [prompts] section."""
    prompt_path = llm_manager.get_prompt_file_path(step)
    if prompt_path and prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return ""

OCR_PROMPT_STEP1 = load_prompt_from_config(1)
OCR_PROMPT_STEP2 = load_prompt_from_config(2)
OCR_PROMPT_STEP3 = load_prompt_from_config(3)

# Test config
TEST_PDF = os.getenv("TEST_PDF")
INPUT_DIR = os.getenv("INPUT_DIR")
RECURSIVE = bool_from_env("RECURSIVE", False)
OUTPUT_STRUCTURE = os.getenv("OUTPUT_STRUCTURE", "preserve")
SCALE = 2.0

# Batch mode detection
def is_batch_mode():
    """Check if batch processing mode is active."""
    return INPUT_DIR is not None

def collect_pdfs(input_dir: Path, recursive: bool = False) -> list[Path]:
    """Collect PDF files from directory.
    
    Args:
        input_dir: Directory to search
        recursive: If True, search subdirectories too
    
    Returns:
        List of PDF file paths
    """
    if recursive:
        return list(input_dir.rglob("*.pdf"))
    else:
        return list(input_dir.glob("*.pdf"))

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


def get_output_dir(input_path: Path) -> Path:
    """Determine output directory for a given input file."""
    if OUTPUT_INTO_SAME_DIR:
        return input_path.parent
    else:
        out_dir = Path(OUTPUT_DIR)
        if OUTPUT_STRUCTURE == "preserve":
            # Keep relative path structure
            pass  # Already handled in process_batch
        out_dir.mkdir(exist_ok=True)
        return out_dir


def process_single_pdf(pdf_path: Path, output_base_dir: Path) -> tuple[bool, str]:
    """Process a single PDF file.
    
    Returns:
        (success, error_message)
    """
    try:
        pdf_name = pdf_path.name
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_name}")
        print(f"{'='*60}")
        
        # PDF → Images
        print(f"[Preparing data] Converting PDF to images: {pdf_path}")
        images = pdf_to_images(pdf_path)
        
        # Determine output paths
        if OUTPUT_STRUCTURE == "preserve" and OUTPUT_DIR:
            # Preserve directory structure
            try:
                rel_path = pdf_path.resolve().relative_to(Path(INPUT_DIR).resolve())
                output_dir = output_base_dir / rel_path.parent
            except ValueError:
                output_dir = output_base_dir
        else:
            output_dir = output_base_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        input_stem = pdf_path.stem
        single_pages_path = output_dir / f"{input_stem}_single_pages.md"
        metadata_path = output_dir / f"{input_stem}_metadata.yaml"
        final_output_path = output_dir / f"{input_stem}.md"
        
        # Check if files already exist
        if single_pages_path.exists() and final_output_path.exists() and not OVERWRITE_OUTPUT_FILES:
            print(f"[SKIP] Output files already exist (use --overwrite to replace)")
            return True, "skipped"
        
        total_pages = len(images)
        source_file = pdf_path.name
        temp_filenames = [img.name for img in images]
        
        # ============ STEP 1: Plain OCR ============
        print(f"\n[Step 1/3] Plain OCR - Processing {total_pages} pages individually...")
        single_pages_md = step1_ocr_single_pages(images, OCR_PROMPT_STEP1, total_pages)
        
        # Speichere Step 1 Output
        single_pages_path.write_text(single_pages_md, encoding="utf-8")
        print(f"[OK] Saved: {single_pages_path}")
        
        # Cleanup Step 1 client if different from default
        debug(1, "Cleaning up Step 1 client...")
        llm_manager.cleanup_after_step1()
        
        # ============ STEP 2: Metadata ============
        print(f"\n[Step 2/3] Extracting metadata from all pages...")
        metadata_yaml = step2_extract_metadata(images, OCR_PROMPT_STEP2, total_pages)
        
        # Speichere Step 2 Output
        metadata_path.write_text(metadata_yaml, encoding="utf-8")
        print(f"[OK] Saved: {metadata_path}")
        
        # ============ STEP 3: Finalize ============
        print(f"\n[Step 3/3] Finalizing document with metadata...")
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
        
        # Cleanup temp images for this PDF
        if not KEEP_TEMP_FILES:
            temp_dir = pdf_path.parent / "temp_images"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        print(f"[OK] Completed: {pdf_name}")
        return True, ""
        
    except Exception as e:
        return False, str(e)


def process_batch():
    """Process multiple PDFs from a directory."""
    input_dir = Path(INPUT_DIR)
    
    if not input_dir.exists():
        print(f"[ERROR] Input directory does not exist: {input_dir}")
        exit(1)
    
    # Collect PDFs
    pdfs = collect_pdfs(input_dir, RECURSIVE)
    
    if not pdfs:
        print(f"[ERROR] No PDF files found in: {input_dir}")
        exit(1)
    
    print(f"\n{'='*60}")
    print(f"BATCH MODE: {len(pdfs)} PDF(s) found")
    print(f"Input: {input_dir}")
    print(f"Recursive: {RECURSIVE}")
    print(f"Output structure: {OUTPUT_STRUCTURE}")
    print(f"{'='*60}")
    
    # Determine output base directory
    if OUTPUT_DIR:
        output_base_dir = Path(OUTPUT_DIR)
    elif OUTPUT_INTO_SAME_DIR:
        output_base_dir = input_dir
    else:
        output_base_dir = Path("output")
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each PDF
    results = []
    for i, pdf_path in enumerate(pdfs, 1):
        success, error = process_single_pdf(pdf_path, output_base_dir)
        results.append((pdf_path.name, success, error))
    
    # Summary
    success_count = sum(1 for _, s, _ in results if s)
    error_count = len(results) - success_count
    
    print(f"\n{'='*60}")
    print(f"BATCH SUMMARY")
    print(f"{'='*60}")
    print(f"Total: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    
    if error_count > 0:
        print("\nFailed files:")
        for name, success, error in results:
            if not success:
                print(f"  - {name}: {error}")
    
    # Cleanup all LLM clients
    debug(1, "Closing all LLM clients...")
    llm_manager.close_all()


def process_single():
    """Process a single PDF file."""
    if not TEST_PDF:
        print("[ERROR] No PDF specified. Set TEST_PDF or use --test-pdf")
        exit(1)
    
    pdf_path = Path(TEST_PDF)
    if not pdf_path.exists():
        print(f"[ERROR] PDF file does not exist: {pdf_path}")
        exit(1)
    
    success, error = process_single_pdf(pdf_path, get_output_dir(pdf_path))
    
    if not success:
        print(f"[ERROR] Processing failed: {error}")
        exit(1)
    
    # Cleanup all LLM clients
    debug(1, "Closing all LLM clients...")
    llm_manager.close_all()


# Main entry point
if __name__ == "__main__":
    # Check if prompts are loaded
    if not OCR_PROMPT_STEP1 or not OCR_PROMPT_STEP2 or not OCR_PROMPT_STEP3:
        print("[ERROR] All 3 step prompts are required (set in model_config.toml [prompts] section):")
        print(f"  - step1_file: {'SET' if OCR_PROMPT_STEP1 else 'MISSING'}")
        print(f"  - step2_file: {'SET' if OCR_PROMPT_STEP2 else 'MISSING'}")
        print(f"  - step3_file: {'SET' if OCR_PROMPT_STEP3 else 'MISSING'}")
        exit(1)
    
    # Step 1: Connection check
    if ping():
        print(f"[OK] Connected to {PROVIDER}")
    else:
        print(f"[FAIL] Cannot connect to {PROVIDER}")
        exit(1)
    
    # Step 2: Check model availability (before any processing)
    check_model_availability()
    
    # Choose processing mode
    if is_batch_mode():
        process_batch()
    else:
        process_single()