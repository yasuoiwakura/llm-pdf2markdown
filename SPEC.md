# llm-pdf2markdown

CLI tool to convert PDFs to Markdown using a local Ollama LLM.

## Requirements

- Python 3.14+
- Ollama running locally
- `.venv` virtual environment (created automatically)

## Installation

```bash
git clone <repo>
cd llm-pdf2markdown
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Configuration

Create `.env` (see `.env.example`):

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
TEST_PDF=exampledata/test.pdf
OUTPUT_DIR=
```

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `gemma3:4b` | Model for image-to-markdown |
| `TEST_PDF` | - | Path for manual testing |
| `OUTPUT_DIR` | `""` | Output directory (empty = next to PDF) |

## Usage

### Single file

```bash
python -m llm_pdf2markdown input.pdf
python -m llm_pdf2markdown input.pdf --model llama3.2-vision
```

### Directory (batch)

```bash
python -m llm_pdf2markdown ./pdfs/
```

Recursively converts all `.pdf` files in the directory tree.

### Output

- `OUTPUT_DIR` set: `<OUTPUT_DIR>/<original_name>.md`
- `OUTPUT_DIR` empty: `<original_dir>/<original_name>.md`

## Project Structure

```
llm-pdf2markdown/
├── src/llm_pdf2markdown/
│   ├── __init__.py
│   ├── __main__.py         # python -m entry
│   ├── cli.py              # Click CLI
│   ├── ollama_client.py    # Ollama API client
│   └── pdf_converter.py    # PDF → PNG converter
├── tests/
├── .gitignore
├── .env.example
├── pyproject.toml
└── README.md
```

## Dependencies

- `pypdfium2` - PDF rendering to images
- `httpx` - HTTP client for Ollama API
- `click` - CLI framework
- `python-dotenv` - Environment variable loading
- `pillow` - Image handling

## Development

### Phases

| Phase | Status | Description |
|-------|--------|-------------|
| PoC | todo | Connect to Ollama, send text prompt |
| MVP | todo | PDF → PNG, send image, save Markdown |
| Batch | todo | Directory recursion, batch processing |

### Testing

```bash
pytest tests/
```

## Notes

- KISS: Simple error handling, MVP scope
- `.md` extension replaces `.pdf` in output filename
- Model must support vision/images (e.g., `gemma3:4b`, `llama3.2-vision`, `llava`)
