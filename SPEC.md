# llm-pdf2markdown

Convert PDFs to Markdown using a local Ollama LLM.

## Status: PoC

## Run PoC

```bash
python poc.py
```

## Config

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

## Structure

```
llm_pdf2markdown/
├── __init__.py   # PoC: only OllamaClient
├── client.py     # Ollama client
└── pdf.py        # (MVP: PDF converter)
```

## Implementation Guidelines

ALWAYS start with the MINIMUM viable implementation:
- Begin with the smallest, simplest working code
- Verify it works before adding features
- NEVER implement multiple features at once

## Implementation Steps

| Step | Description | Status |
|------|-------------|--------|
| 1 | Basic Ollama connection + ping | pending |
| 2 | Simple text prompt → response | pending |
| 3 | PDF text extraction only | pending |
| 4 | Convert extracted text to Markdown | pending |
| 5 | Add image handling (MVP) | pending |

### Step 1: Connection
- [ ] Connects to OLLAMA_URL
- [ ] Can ping the model
- [ ] Returns version/info

### Step 2: Text Prompt
- [ ] Send simple text prompt
- [ ] Receive and return response

### Step 3: PDF Text Extraction
- [ ] Extract text from PDF file
- [ ] Return raw text

### Step 4: Text → Markdown
- [ ] Convert extracted text to Markdown format
- [ ] Save Markdown file

### Step 5: Image Handling (MVP)
- [ ] Extract images from PDF
- [ ] Process images with LLM
- [ ] Generate Markdown with embedded images

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
