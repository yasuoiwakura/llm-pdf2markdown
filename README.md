# llm-pdf2markdown

> **Bleeding Edge** — v0.1.0 — Local PDF-to-Markdown via LLM vision.

Convert PDFs to Markdown using a local LLM (LM Studio or Ollama).  
Documents stay on your machine.

## Limitations

- **Only LM Studio** was properly tested. Ollama support exists but is **not verified**.
- **Context size** is not reliably enforced — loaded models may ignore `LMSTUDIO_CONTEXT_SIZE`.
- **Always review output** — check for hallucinations, dropped content, and OCR errors.

## Quickstart

```bash
copy .env.example .env
python run.py --USE_LMSTUDIO 1 --TEST_PDF doc.pdf

# Multi-phase (better quality for complex docs)
python run.py --MULTIPHASE_MODE 1 --TEST_PDF doc.pdf

# Batch mode
python run.py --INPUT_DIR ./pdfs
```

## Prerequisites

- Python 3.11+
- [LM Studio](https://lmstudio.ai) (recommended) or [Ollama](https://ollama.com)
- A vision-capable model loaded (e.g., `gemma3-4b`)

## Docs

- [SPEC.md](SPEC.md) — Specification & configuration reference
- [AGENTS.md](AGENTS.md) — AI-assisted development rules
