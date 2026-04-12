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

## Phases

| Phase | Status |
|-------|--------|
| PoC | ✓ active - connection + text prompt |
| MVP | pending - image → Markdown |
