# llm-pdf2markdown

Convert PDFs to Markdown using a local LLM (Ollama or LM Studio).

## Status: PoC

## Run PoC

```bash
python poc.py
```

## Config

```env
# Enable/disable LLM providers (only one should be true)
USE_OLLAMA=true
USE_LMSTUDIO=false

# Ollama (used only if USE_OLLAMA=true)
# URL: http://localhost:11434, API: /api/generate
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_KEEP_ALIVE=30m

# LM Studio (used only if USE_LMSTUDIO=true)
# URL: http://localhost:1234, API: /v1/chat/completions (OpenAI-compatible)
LMSTUDIO_URL=http://localhost:1234
LMSTUDIO_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit

TEST_PDF=exampledata/test.pdf
```

## Supported LLM Providers

| Provider | Enable Flag | Default URL | API Endpoint |
|----------|-------------|-------------|--------------|
| Ollama | USE_OLLAMA | localhost:11434 | /api/generate |
| LM Studio | USE_LMSTUDIO | localhost:1234 | /v1/chat/completions |

## Structure

```
llm_pdf2markdown/
├── __init__.py   # LLM client (Ollama & LM Studio)
├── client.py     # LLM client implementation
└── pdf.py        # PDF converter
```

## Implementation Guidelines

ALWAYS start with the MINIMUM viable implementation:
- Begin with the smallest, simplest working code
- Verify it works before adding features
- NEVER implement multiple features at once

## Implementation Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Basic LLM connection + ping (Ollama & LM Studio) | ✓ done |
| 2 | Simple text prompt → response | ✓ done |
| 3 | PDF → PNG images (temp_images/) | ✓ done |
| 4 | Images → Markdown via LLM | pending |
| 5 | Save Markdown file | pending |

### Step 1: Connection
- [x] Connects to LLM_PROVIDER URL
- [x] Supports both Ollama and LM Studio
- [x] Check available models

### Step 2: Text Prompt
- [x] Send simple text prompt
- [x] Receive and return response
- [x] Set keep_alive from OLLAMA_KEEP_ALIVE

### Step 3: PDF → PNG Images
- [x] Convert PDF pages to PNG images
- [x] Save to temp_images/ directory

### Step 4: Images → Markdown
- [ ] Send image to LLM
- [ ] Get Markdown response

### Step 5: Save Markdown
- [ ] Combine page Markdowns
- [ ] Save .md file

## Critical Rules

1. NEVER skip steps or implement future steps
2. ALWAYS verify current step works before proceeding
3. Keep each step as small as possible
4. If stuck, ask user before implementing more
5. Only implement ONE step at a time

## Phases

| Phase | Status |
|-------|--------|
| PoC | ✓ active - connection + text prompt |
| MVP | pending - image → Markdown |
