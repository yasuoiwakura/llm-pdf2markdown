# llm-pdf2markdown

Convert PDFs to Markdown using a local LLM (Ollama or LM Studio).

## Status: MVP (Multi-phase OCR)

## Run

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
OLLAMA_MODEL=gemma3-4b
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

# Multi-phase Processing
MULTIPHASE_MODE=0    # 1 = 3-phase processing (step1+2+3), 0 = single-pass

# Step 1: Plain OCR (einzelne Seiten)
OCR_PROMPT_FILE_STEP1=prompts/multiphase_step1_ocr.md

# Step 2: Metadaten
OCR_PROMPT_FILE_STEP2=prompts/multiphase_step2_metadata.md

# Step 3: Finalisierung
OCR_PROMPT_FILE_STEP3=prompts/multiphase_step3_finalize.md

TEST_PDF=exampledata/test.pdf
```

## Multi-Phase Processing (3-Stufig)

Das 3-stufige Verfahren sorgt für maximale Vollständigkeit bei minimaler Halluzination:

| Stufe | Input | Output | Datei-Suffix | Ziel |
|-------|-------|--------|--------------|------|
| **1** | Einzelne Seiten (1 Call/Seite) | `[filename]_single_pages.md` | OCR verbatim, 100% vollständig |
| **2** | Alle Seiten als Bild | `metadata.yaml` | Strukturierte Extrahiertung |
| **3** | Beide Markdown-Files | `[filename].md` | Zusammenhängendes Dokument |

### Reihenfolge: Step 1 → Step 2 → Step 3

**WICHTIG:** Step 1 ist das MVP - das wichtigste Kriterium ist Vollständigkeit. Das Resultat von Step 1 ist im Zweifel produktionsreif.

### Step 1: Plain OCR (Step 1)

- **Input:** 1 Rastergrafik pro API-Call
- **Output:** Markdown mit allen Inhalten (ggf. redundant)
- **Ziel:** 100% Vollständigkeit, KEINE Umschreibung
- **Regeln:**
  - KEINE Interpretation
  - KEINE Korrektur (außer offensichtliche OCR-Fehler)
  - KEINE Zusammenfassung
  - Alles was im Bild steht, muss im Markdown stehen

### Step 1: Output Format (Page Markers)

Das Markdown wird mit Page-Markern strukturiert:

```
# page 1/3

<!-- start content page 1 of 3 -->
[Content Seite 1]
<!-- end content page 1 of 3 -->

# page 2/3

<!-- start content page 2 of 3 -->
[Content Seite 2]
<!-- end content page 2 of 3 -->

# page 3/3

<!-- start content page 3 of 3 -->
[Content Seite 3]
<!-- end content page 3 of 3 -->
```

**LLM-Regel:** Header ab `##` (nicht `#`) - `#` ist für Page-Marker reserviert.

**Python:** Fügt `# page n/total` + `<!-- start/end content -->` zwischen Seiten ein.

**Output-Dateiname:** `[filename]_single_pages.md`

### Step 2: Metadaten-Extraktion (Step 2)

- **Input:** Alle Seiten als Rastergrafik (1 Call)
- **Output:** YAML-Datei mit Metadaten
- **Extrahiert:**
  - Absender (Name, Adresse, Kontakt)
  - Empfänger (Name, Adresse)
  - Dokument-Typ (zeugnis, brief, rechnung, etc.)
  - Sprache
  - Kopfzeilen/Fußzeilen (identifizieren für Redundanz-Entfernung)
  - Original-Dateiname (wird vom Python eingefügt)

### Step 3: Finalisierung (Step 3)

- **Input:** `[filename]_single_pages.md` + `metadata.yaml`
- **Output:** `[filename].md` (zusammenhängend, redundant bereinigt)
- **WICHTIG:** Keine Rastergrafiken - nur die已有 Markdown-Files
- **Ziel:** Sauberes, strukturiertes Dokument ohne Redundanz

## CLI Parameters

Alle ENV-Variablen können per CLI überschrieben werden. Parameter-Namen sind identisch mit ENV-Variablen (inkl. Capslock).

```bash
python run.py --OLLAMA_MODEL gemma3-4b --OUTPUT_INCLUDE_METADATA 1 --MULTIPHASE_MODE 1
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
| --MULTIPHASE_MODE | MULTIPHASE_MODE |
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
| 1-4 | All pages in single request (default, ohne MULTIPHASE_MODE) |
| >4 | 2-phase approach (prepared, not implemented) |
| MULTIPHASE_MODE=1 | 3-phase: Step1 → Step2 → Step3 (alle Seitenanzahlen) |

## Prompts

```
prompts/
├── ocr_prompt.md                    # Legacy (unused)
├── ocr_prompt_plain.md              # Legacy (unused)
├── ocr_prompt_detailed.md           # Legacy (single-pass)
├── ocr_prompt_minimal.md            # Legacy (unused)
├── ocr_prompt_2phase_concept.md     # Documentation
├── multiphase_step1_ocr.md          # Step 1: Plain OCR
├── multiphase_step1_ocr_template.md # Step 1 mit Platzhaltern
├── multiphase_step2_metadata.md     # Step 2: Metadaten
├── multiphase_step2_metadata_template.md  # Step 2 mit Platzhaltern
└── multiphase_step3_finalize.md     # Step 3: Finalisierung
├── multiphase_step3_finalize_template.md  # Step 3 mit Platzhaltern
```

## Python Functions

```python
def step1_ocr_single_pages(image_paths, prompt) -> str:
    """Step 1: Plain OCR, jede Seite einzeln
    Args:
        image_paths: Liste der Rastergrafik-Pfade (1 pro Seite)
        prompt: Prompt aus multiphase_step1_ocr.md
    Returns:
        Markdown-String mit allen Seiteninhalten (ggf. redundant)
    """

def step2_extract_metadata(image_paths, prompt) -> dict:
    """Step 2: Metadaten extrahieren
    Args:
        image_paths: Alle Rastergrafiken (1 Call)
        prompt: Prompt aus multiphase_step2_metadata.md
    Returns:
        Dict mit: sender, recipient, document_type, language, headers, footer, original_filename
    """

def step3_finalize(single_pages_md_path, metadata_yaml_path, prompt) -> str:
    """Step 3: Zusammenführen
    Args:
        single_pages_md_path: Pfad zur _single_pages.md Datei
        metadata_yaml_path: Pfad zur metadata.yaml
        prompt: Prompt aus multiphase_step3_finalize.md
    Returns:
        Finaler Markdown-String
    """
```

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
| 8 | Output-Tagging für Tuning | ✓ done |
| 9 | **Step 1: Plain OCR (single pages)** | **current** |
| 10 | Step 2: Metadata extraction | pending |
| 11 | Step 3: Finalization | pending |

### Step 1: Plain OCR (Current - MVP)
- [ ] Process each page individually (1 API call per page)
- [ ] Load prompt from `OCR_PROMPT_FILE_STEP1`
- [ ] Add page markers for reference
- [ ] Save output as `[filename]_single_pages.md`
- [ ] **STRICT:** NO rephrasing, NO interpretation, NO correction (except obvious OCR errors)

### Step 10: Metadata Extraction
- [ ] Send all pages in single request
- [ ] Load prompt from `OCR_PROMPT_FILE_STEP2`
- [ ] Output structured YAML
- [ ] Save as `metadata.yaml`

### Step 11: Finalization
- [ ] Read `_single_pages.md` and `metadata.yaml`
- [ ] Load prompt from `OCR_PROMPT_FILE_STEP3`
- [ ] Remove redundant headers/footers based on metadata
- [ ] Output clean, cohesive markdown

## Critical Rules

1. NEVER skip steps or implement future steps
2. ALWAYS verify current step works before proceeding
3. Keep each step as small as possible
4. If stuck, ask user before implementing more
5. Only implement ONE step at a time
6. **Step 1 is the MVP** - even if imperfect, it must be complete and verbatim

## Phases

| Phase | Status |
|-------|--------|
| PoC | ✓ complete |
| MVP | in progress - Step 1 (single page OCR) |
| Metadata | pending |
| Finalization | pending |

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
