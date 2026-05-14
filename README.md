# llm-pdf2markdown

> Convert PDFs to Markdown using a local LLM with multi-phase OCR processing.

## Features

- **3-Phase Processing**: OCR → Metadata → Finalize for high-quality output
- **Batch Mode**: Process entire directories of PDFs
- **Model Flexibility**: Configure different models per processing step via TOML
- **Local Processing**: Documents stay on your machine (LM Studio or Ollama)

## Quickstart

```bash
# Single PDF
python run.py --test-pdf document.pdf

# Directory (all PDFs)
python run.py --input-dir ./pdfs

# Recursive (include subfolders)
python run.py --input-dir ./pdfs --recursive

# With output directory
python run.py --input-dir ./pdfs --output-dir ./output

# Verbose output (0-3)
python run.py --test-pdf document.pdf -v 2

# Overwrite existing files
python run.py --input-dir ./pdfs --overwrite
```

## CLI Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--test-pdf <file>` | Single PDF file (mutually exclusive with `--input-dir`) | `--test-pdf doc.pdf` |
| `--input-dir <dir>` | Directory containing PDFs | `--input-dir ./pdfs` |
| `--recursive` | Process directories recursively (include subfolders) | `--recursive` |
| `--output-dir <dir>` | Output directory for results | `--output-dir ./output` |
| `--output-structure` | Output structure: `preserve` (keep folder structure) or `flat` (all in one dir) | `--output-structure flat` |
| `--overwrite` | Overwrite existing output files | `--overwrite` |
| `--verbose, -v <0-3>` | Verbosity level: 0=errors, 1=info, 2=debug, 3=full API logs | `-v 3` |
| `--help, -h` | Show all available options | `--help` |

## Input Modes

| Mode | Usage | Output |
|------|-------|--------|
| Single | `--test-pdf doc.pdf` | `doc.md` in same directory as PDF |
| Directory | `--input-dir ./pdfs` | `*.md` files in `OUTPUT_DIR` |
| Recursive | `--input-dir ./pdfs --recursive` | `*.md` files preserving folder structure |

## Output Files

For each PDF, three files are generated:

| File | Description |
|------|-------------|
| `[name].md` | Final document (metadata embedded) |
| `[name]_single_pages.md` | Raw OCR output (Step 1) |
| `[name]_metadata.yaml` | Extracted metadata (Step 2) |

## Configuration

### Environment Variables (.env)

```env
# LLM Provider
USE_OLLAMA=true
USE_LMSTUDIO=false

# LM Studio
LMSTUDIO_URL=http://localhost:1234
LMSTUDIO_MODEL=your-model

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=your-model
OLLAMA_KEEP_ALIVE=30m

# Output
OUTPUT_DIR=output
OUTPUT_INTO_SAME_DIR=true
OVERWRITE_OUTPUT_FILES=false
```

### Model Configuration (model_config.toml)

Per-step model configuration:

```toml
[step1]
model = "glm-ocr@f16"
CONTEXT_SIZE_BY_MODEL_LOAD = false

[step_2_and_3]
model = "gemma-3-12b"
CONTEXT_SIZE_BY_MODEL_LOAD = true
context_size = 16384

[prompts]
step1_file = "prompts/multiphase_step1_ocr.md"
step2_file = "prompts/multiphase_step2_metadata.md"
step3_file = "prompts/multiphase_step3_finalize.md"
```

## Processing Phases

| Phase | Input | Output | Purpose |
|-------|-------|--------|---------|
| 1 | Single page images | `[name]_single_pages.md` | Raw OCR, verbatim extraction |
| 2 | All pages as images | `[name]_metadata.yaml` | Structure extraction (sender, recipient, type) |
| 3 | Step 1 + Step 2 outputs | `[name].md` | Clean document, deduplicated |

## Verbose Levels

| Level | Output |
|-------|--------|
| 0 | Errors only |
| 1 | + Info messages, configuration display |
| 2 | + Debug info (client lifecycle, model loading) |
| 3 | + Full API requests/responses (JSON) |

## Prerequisites

- Python 3.11+
- [LM Studio](https://lmstudio.ai) or [Ollama](https://ollama.com)
- Vision-capable LLM model loaded in your provider

## Files

- `run.py` - Main entry point
- `model_config.toml` - Per-step model configuration
- `prompts/` - Processing prompts for each phase
- `SPEC.md` - Full specification
- `AGENTS.md` - Development rules