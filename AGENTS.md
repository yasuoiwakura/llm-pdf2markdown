# llm-pdf2markdown

Convert PDFs to Markdown using a local LLM (Ollama or LM Studio).

## Stack
Python 3.x, Ollama, LM Studio, pdf2image, httpx, python-dotenv

## Critical Rules
1. NEVER skip steps or implement future steps
2. ALWAYS verify current step works before proceeding
3. Keep each step as small as possible
4. Only implement ONE step at a time
5. **Step 1 is the MVP** - must be complete and verbatim
6. If stuck, ask user before implementing more

## Implementation Guidelines
- Start with minimum viable implementation
- Never implement multiple features at once
- Single Responsibility: jede Klasse hat eine Aufgabe
- Rückwärtskompatibilität: `client.py` bleibt als Alias

## Implementation Order
1. clients/base.py (ABC)
2. clients/ollama.py + clients/lmstudio.py
3. clients/__init__.py (Factory)
4. manager.py (LLMManager)
5. run.py refaktorieren

## Virtual Environment
```
.venv\Scripts\activate
pip install -r requirements.txt
```

## Spec
See [SPEC.md](SPEC.md)
