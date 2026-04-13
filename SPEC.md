# llm-pdf2markdown

Convert PDFs to Markdown using a local LLM (Ollama or LM Studio).

## Status: PoC → MVP (Multi-page support)

## Run PoC

```bash
python run.py
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
LMSTUDIO_CONTEXT_SIZE=16384

# Context size strategy
# NOT RECOMMENDED: Langsam + kein Query der geladenen Modelle möglich
CONTEXT_SIZE_BY_MODEL_LOAD=0
# Ungetestet: Funktioniert möglicherweise
CONTEXT_SIZE_PER_REQUEST=0

# LLM Parameters
MAX_PAGES_PER_REQUEST=4
# Pages <= 4: All pages in single request
# Pages > 4: 2-phase approach (NOT YET IMPLEMENTED)

# Prompts (optional: use file instead of inline)
# If OCR_PROMPT_FILE is set, file content overwrites OCR_PROMPT
OCR_PROMPT=Convert this image to markdown
OCR_PROMPT_FILE=prompts/ocr_prompt_detailed.md

# Output
OUTPUT_DIR=output
OUTPUT_INTO_SAME_DIR=true
OVERWRITE_OUTPUT_FILES=0
KEEP_TEMP_FILES=0

# Output-Tagging für Tuning-Vergleich
FILENAME_INCLUDE_MODEL_TAG=0    # 1 = [model_name] im Dateinamen, z.B. test[gemma3-4b].md
OUTPUT_INCLUDE_METADATA=0       # 1 = Metadata-Kommentar am Dateianfang (siehe unten)

TEST_PDF=exampledata/test.pdf
```

## CLI Parameters

Alle ENV-Variablen können per CLI überschrieben werden. Parameter-Namen sind identisch mit ENV-Variablen (inkl. Capslock).

```bash
python run.py --OLLAMA_MODEL gemma3:4b --OUTPUT_INCLUDE_METADATA 1
```

**Beispiel für Testreihe:**
```bash
for model in gemma3:4b qwen2.5:7b llama3.1:8b; do
  python run.py --OLLAMA_MODEL $model --FILENAME_INCLUDE_MODEL_TAG 1
done
```

| CLI-Parameter | Überschreibt ENV |
|--------------|------------------|
| --USE_OLLAMA | USE_OLLAMA |
| --USE_LMSTUDIO | USE_LMSTUDIO |
| --OLLAMA_URL | OLLAMA_URL |
| --OLLAMA_MODEL | OLLAMA_MODEL |
| --OLLAMA_KEEP_ALIVE | OLLAMA_KEEP_ALIVE |
| --LMSTUDIO_URL | LMSTUDIO_URL |
| --LMSTUDIO_MODEL | LMSTUDIO_MODEL |
| --LMSTUDIO_CONTEXT_SIZE | LMSTUDIO_CONTEXT_SIZE |
| --CONTEXT_SIZE_BY_MODEL_LOAD | CONTEXT_SIZE_BY_MODEL_LOAD |
| --CONTEXT_SIZE_PER_REQUEST | CONTEXT_SIZE_PER_REQUEST |
| --MAX_PAGES_PER_REQUEST | MAX_PAGES_PER_REQUEST |
| --OCR_PROMPT | OCR_PROMPT |
| --OCR_PROMPT_FILE | OCR_PROMPT_FILE |
| --OUTPUT_DIR | OUTPUT_DIR |
| --OUTPUT_INTO_SAME_DIR | OUTPUT_INTO_SAME_DIR |
| --OVERWRITE_OUTPUT_FILES | OVERWRITE_OUTPUT_FILES |
| --KEEP_TEMP_FILES | KEEP_TEMP_FILES |
| --FILENAME_INCLUDE_MODEL_TAG | FILENAME_INCLUDE_MODEL_TAG |
| --OUTPUT_INCLUDE_METADATA | OUTPUT_INCLUDE_METADATA |
| --TEST_PDF | TEST_PDF |

## Output Metadata-Tag (bei OUTPUT_INCLUDE_METADATA=1)

```markdown
<!--
model: gemma3-4b
provider: lmstudio
prompt_file: ocr_prompt_detailed.md
context_configured: 16384
usage: prompt_tokens=1226, completion_tokens=1261, total_tokens=2487
pages: 3
-->
```

## Known Issues

### LM Studio Context Size

| Feature | Status | Hinweis |
|---------|--------|--------|
| `CONTEXT_SIZE_BY_MODEL_LOAD=1` | ⚠️ nicht empfohlen | Langsam, kein Query der geladenen Modelle möglich |
| `CONTEXT_SIZE_PER_REQUEST=1` | ❌ broken | Funktioniert nicht wie erwartet |
| `LMSTUDIO_CONTEXT_SIZE` | ⚠️ partly working | Wird manchmal ignoriert, Context-Size muss manuell im LM Studio eingestellt werden |

**Empfehlung:** 
- Modell **manuell in LM Studio GUI** mit gewünschter Context-Size laden
- Oder **Template in LM Studio** anlegen und dort das Modell mit passender Context-Size definieren

### REST API Bugs
- `GET /api/v1/models` gibt leere Antwort (sollte geladene Modelle mit context_length zeigen)
- Keine Möglichkeit, aktuell geladene Modelle mit context_length abzufragen
- Modell wird bei jedem Laden neu geladen (es gibt keine saubere Prüfung ob passendes Modell bereits existiert)

## Processing Strategy

| Pages | Strategy |
|-------|----------|
| 1-4 | All pages in single request (default) |
| >4 | 2-phase approach (prepared, not implemented) |

## Prompts

Prompts can be defined inline in .env or in separate files. If `*_FILE` is set, the file content takes precedence.

```
prompts/
├── ocr_prompt.md                    # Current (unused)
├── ocr_prompt_plain.md               # Basic version
├── ocr_prompt_detailed.md            # Recommended: metadata + multi-page
├── ocr_prompt_minimal.md             # Short version
└── ocr_prompt_2phase_concept.md     # Future: 2-phase documentation
```

**Loading logic:**
1. Load prompt from .env (e.g., `OCR_PROMPT`)
2. If `OCR_PROMPT_FILE` is set and file exists → overwrite with file content
3. If file doesn't exist → use .env value as fallback

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
| 4 | Images → Markdown via LLM | ✓ done |
| 5 | Save Markdown file | ✓ done |
| 6 | Custom Prompts from .env or FILE | ✓ done |
| 7 | Multi-page: All pages in single request | ✓ done |
| 8 | **Output-Tagging für Tuning** | **current** |
| 9 | Multi-page: 2-phase (metadata + content) | pending |

### Step 1: Connection
- [x] Connects to URL based on USE_OLLAMA / USE_LMSTUDIO
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
- [x] Send image to LLM (Ollama OR LM Studio)
- [x] Get Markdown response

### Step 5: Save Markdown
- [x] Combine page Markdowns
- [x] Save .md file

### Step 6: Custom Prompts
- [x] Load prompts from .env or *_FILE
- [x] Support prompts/ directory

### Step 7: Multi-page Support (Current)
- [ ] Send all pages at once for documents with pages <= MAX_PAGES_PER_REQUEST
- [ ] Prompt includes page context (page X of Y)
- [ ] Extract metadata from first page

### Step 8: Output-Tagging für Tuning (Current)
- [ ] Implement FILENAME_INCLUDE_MODEL_TAG=1 → [model_name] im Dateinamen
- [ ] Implement OUTPUT_INCLUDE_METADATA=1 → Metadata-Kommentar am Dateianfang
- [ ] Model-Name aus Config lesen (OLLAMA_MODEL oder LMSTUDIO_MODEL)
- [ ] Provider-Debug-Info (prompt_tokens, completion_tokens, total_tokens) aus Response extrahieren
- [ ] Prompt-File-Name aus OCR_PROMPT_FILE extrahieren
- [ ] **CLI-Parameter**: Alle ENV-Variablen per CLI überschreibbar (gleiche Namen, inkl. Capslock)

### Step 9: 2-Phase Approach (NOT IMPLEMENTED)
- [ ] Phase 1: Extract metadata from all pages at once
- [ ] Phase 2: Extract content page-by-page
- [ ] Merge metadata + content

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
| MVP | in progress - multi-page support |
| 2-Phase | pending - prepared but not implemented |

## Gemma3-4b Parameters

For optimal OCR results with gemma3-4b:

```env
OLLAMA_MODEL=gemma3:4b
# Recommended settings in Modelfile:
# PARAMETER num_ctx 16384
# PARAMETER num_predict 8192
# PARAMETER temperature 0
# PARAMETER top_p 0.00001
```