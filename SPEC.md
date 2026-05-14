# llm-pdf2markdown

Convert PDFs to Markdown using a local LLM (Ollama or LM Studio).

## Status: MVP (Multi-phase OCR + Batch)

### Stabil (Getestet)
- ✓ TOML-basierte Modellkonfiguration
- ✓ Step-spezifische CONTEXT_SIZE_BY_MODEL_LOAD
- ✓ Verbose/Debug Output
- ✓ Keine Bugs (zirkulärer Import, doppelter Durchlauf)
- ✓ Batch/Verzeichnis-Verarbeitung (--input-dir, --recursive)
- ✓ Output-Struktur (preserve/flat)

### Geplant (NICHT im Code)
- Step 3: Metadaten-Einbettung in finales Markdown

### Auf Eis
- SIMPLE_ENV_MODE (simple .env mode)

### CLI Help

`--help` und `-h` müssen alle verfügbaren CLI-Parameter anzeigen:

```bash
python run.py --help
python run.py -h
```

**CLI-Parameter-Anforderungen:**
- Alle ENV-Variablen als CLI-Parameter verfügbar (identische Namen, inkl. Capslock)
- Hilfe-Text für jeden Parameter
- Gruppen: Input, Output, LLM, Model Config

## README.md

User-Dokumentation: Siehe README.md

## Model Configuration (model_config.toml)

Separate TOML-Datei für Modellzuordnung pro Step.

### Struktur

```toml
# Zuordnung: welche Config für welchen Step
step1_cfg="step1"
step2_cfg="step_2_and_3"
step3_cfg="step_2_and_3"

[step1]
model="glm-ocr@f16"
prompt="do OCR"                    # ODER
prompt_file="prompts/step1.md"    # ODER

[step_2_and_3]
model="google/gemma-3-12b-16k"
context_size=16384
prompt="extract metadata"          # ODER
prompt_file="prompts/step2.md"     # ODER
```

### Prompt Präzedenz

```
WENN prompt_file definiert:
    → Lese Prompt aus Datei (höchste Priorität)
SONST WENN prompt definiert:
    → Nutze inline Prompt
SONST:
    → Fallback auf .env (OCR_PROMPT)
```

### Logik

- `step1_cfg`, `step2_cfg`, `step3_cfg` referenzieren Section-Namen
- `[step1]` → Step 1 Modell (eigenständig)
- `[step_2_and_3]` → Step 2+3 Modell (shared)

### Instance Management

**Single Mode (TEST_PDF gesetzt):**
```
1. Lade benötigte LLM-Instanzen
2. Führe alle Steps aus
3. Schließe alle LLM-Instanzen
```

**Batch Mode (INPUT_DIR gesetzt):**
```
1. Lade alle benötigten LLM-Instanzen (basierend auf model_config.toml)
2. Für jede PDF-Datei:
    a. Wiederverwendung der Instanzen wenn Config identisch
    b. Alte Instanz schließen wenn Config wechselt
    c. Neue Instanz erstellen wenn nötig
3. Alle LLM-Instanzen schließen
```

**Zwischen Steps (gleiche Config):**
```
WENN next_step_config == current_step_config:
    → Wiederverwendung des gleichen Client-Objekts
    → NICHT neu laden
SONST:
    → Neue Client-Instanz erstellen
    → Alte Instanz entladen (falls nötig)
```

### Preflight Check

Nur verwendete Modelle prüfen (keine Duplikate):

```
1. Lese step*_cfg Zuordnungen
2. Extrahiere EINMALIGE Config-Namen (unique)
3. Prüfe nur diese Modelle via API
4. Bei Fehler: Stopp + klare Fehlermeldung
```

**Beispiel:**
```toml
step1_cfg="step1"
step2_cfg="step_2_and_3"
step3_cfg="step_2_and_3"
```
→ Prüfe: `step1`, `step_2_and_3` (2 Modelle, nicht 3)

## Run

```bash
python run.py
```

## Configuration Strategy

### SIMPLE_ENV_MODE

```env
SIMPLE_ENV_MODE=0  # Default: 0 = TOML (komplex), 1 = einfache .env
```

### Fallback-Logik

| SIMPLE_ENV_MODE | model_config.toml | Modus |
|----------------|-------------------|-------|
| 0 | Vorhanden | TOML (3-Step) |
| 0 | Nicht vorhanden | Fehler |
| 1 | - | Einfache .env (single-pass, zukünftig) |

```
WENN SIMPLE_ENV_MODE=0 UND model_config.toml existiert:
    → Nutze TOML (3-Step)
WENN SIMPLE_ENV_MODE=1:
    → Nutze einfache .env Variablen (single-pass, zukünftig)
```

### Ersetzte Variablen (Deprecated - für SIMPLE_ENV_MODE=1 später)

| Alte Variable | Status | Zukunft |
|---------------|--------|---------|
| `MULTIPHASE_MODE` | **ERSETZT** | → `SIMPLE_ENV_MODE` |
| `LMSTUDIO_MODEL` (global) | Deprecated | → TOML `[step*]` sections |
| `LMSTUDIO_CONTEXT_SIZE` | Deprecated | → TOML `context_size` |
| `OCR_PROMPT_FILE_STEP*` | Deprecated | → TOML `prompt`/`prompt_file` |

**Hinweis:** Diese Variablen werden für `SIMPLE_ENV_MODE=1` später wieder implementiert. Aktuell auf Eis gelegt.

## Batch Processing

### Input Modes

| Mode | ENV | CLI | Beschreibung |
|------|-----|-----|---------------|
| Single | `TEST_PDF=pfad/datei.pdf` | `--TEST_PDF pfad/datei.pdf` | Einzelne Datei |
| Directory | `INPUT_DIR=./pdfs` | `--INPUT_DIR ./pdfs` | Alle PDFs im Ordner |
| Recursive | `INPUT_DIR=./pdfs` + `RECURSIVE=1` | `--INPUT_DIR ./pdfs --RECURSIVE 1` | Inkl. Unterordner |

### ENV-Variablen

```env
# Input
INPUT_MODE=single          # single | directory | recursive (default: single)
INPUT_DIR=./pdfs           # Verzeichnis für Batch
RECURSIVE=0                # 1 = inkl. Unterordner

# Output
OUTPUT_DIR=./output        # Ausgabe-Verzeichnis
OUTPUT_STRUCTURE=preserve  # preserve | flat
```

### CLI-Parameter

```bash
# Single PDF
python run.py --TEST_PDF datei.pdf

# Batch: alle PDFs im Ordner
python run.py --INPUT_DIR ./pdfs

# Batch: rekursiv inkl. Unterordner
python run.py --INPUT_DIR ./pdfs --RECURSIVE 1
```

### Output-Struktur

| INPUT_MODE | Input | Output |
|------------|-------|--------|
| single | `datei.pdf` | `output/datei.md` |
| directory | `./pdfs/datei.pdf` | `output/datei.md` |
| recursive | `./pdfs/sub/datei.pdf` | `output/sub/datei.md` |

### Pro PDF generierte Dateien

- `[name].md` - Finales Markdown
- `[name]_single_pages.md` - Step 1 Output (bei MULTIPHASE)
- `[name]_metadata.yaml` - Step 2 Output (bei MULTIPHASE)

### Batch-Logik

```
1. Input sammeln (single/directory/recursive)
2. Für jede PDF-Datei:
   a. Preflight-Check (Modelle verfügbar?)
   b. PDF → PNG (jede Seite)
   c. Step 1 (wenn step1_cfg gesetzt)
   d. Step 2 (wenn step2_cfg gesetzt)
   e. Step 3 (wenn step3_cfg gesetzt)
   f. Output-Dateien schreiben
3. Zusammenfassung: X Dateien erfolgreich, Y Fehler
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

# Step 1: Separate model for OCR (halluzinationsfreies Modell)
MULTIPHASE_MODEL_STEP1_OCR=glm-ocr@f16
# Falls gesetzt und != LMSTUDIO_MODEL → separate LLM-Instanz für Step 1
# Falls nicht gesetzt oder == LMSTUDIO_MODEL → verwende default_client

# Step 1: Plain OCR (einzelne Seiten)
OCR_PROMPT_FILE_STEP1=prompts/multiphase_step1_ocr.md

# Step 2: Metadaten
OCR_PROMPT_FILE_STEP2=prompts/multiphase_step2_metadata.md

# Step 3: Finalisierung
OCR_PROMPT_FILE_STEP3=prompts/multiphase_step3_finalize.md

# Batch Processing
TEST_PDF=exampledata/test.pdf
INPUT_MODE=single
INPUT_DIR=./pdfs
RECURSIVE=0
OUTPUT_STRUCTURE=preserve
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
python run.py --OLLAMA_MODEL gemma3-4b --OUTPUT_INCLUDE_METADATA 1
```

### --help Anforderung

`python run.py --help` muss alle verfügbaren CLI-Parameter anzeigen.

| CLI-Parameter | Überschreibt ENV | Status |
|--------------|------------------|--------|
| --USE_OLLAMA | USE_OLLAMA | ✓ |
| --USE_LMSTUDIO | USE_LMSTUDIO | ✓ |
| --OLLAMA_URL | OLLAMA_URL | ✓ |
| --OLLAMA_MODEL | OLLAMA_MODEL | ✓ |
| --OLLAMA_KEEP_ALIVE | OLLAMA_KEEP_ALIVE | ✓ |
| --LMSTUDIO_URL | LMSTUDIO_URL | ✓ |
| --LMSTUDIO_MODEL | LMSTUDIO_MODEL | ✓ |
| --LMSTUDIO_CONTEXT_SIZE | LMSTUDIO_CONTEXT_SIZE | ✓ |
| --CONTEXT_SIZE_BY_MODEL_LOAD | CONTEXT_SIZE_BY_MODEL_LOAD | ✓ |
| --CONTEXT_SIZE_PER_REQUEST | CONTEXT_SIZE_PER_REQUEST | ⚠️ broken |
| --MAX_PAGES_PER_REQUEST | MAX_PAGES_PER_REQUEST | ✓ |
| --OCR_PROMPT | OCR_PROMPT | ✓ |
| --OCR_PROMPT_FILE | OCR_PROMPT_FILE | ✓ |
| --OUTPUT_DIR | OUTPUT_DIR | ✓ |
| --OUTPUT_INTO_SAME_DIR | OUTPUT_INTO_SAME_DIR | ✓ |
| --OVERWRITE_OUTPUT_FILES | OVERWRITE_OUTPUT_FILES | ✓ |
| --KEEP_TEMP_FILES | KEEP_TEMP_FILES | ✓ |
| --FILENAME_INCLUDE_MODEL_TAG | FILENAME_INCLUDE_MODEL_TAG | ✓ |
| --OUTPUT_INCLUDE_METADATA | OUTPUT_INCLUDE_METADATA | ✓ |
| --TEST_PDF | TEST_PDF | ✓ |
| --INPUT_MODE | INPUT_MODE | skipped (CLI uses --input-dir directly) |
| --INPUT_DIR | INPUT_DIR | ✓ implemented |
| --RECURSIVE | RECURSIVE | ✓ implemented |
| --OUTPUT_STRUCTURE | OUTPUT_STRUCTURE | ✓ implemented |

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
├── old/                         # Legacy (alter Ansatz - ggf. später revalidieren)
│   ├── ocr_prompt.md            # Alter Ansatz: single-pass OCR
│   ├── ocr_prompt_plain.md    # Einfache Version
│   ├── ocr_prompt_detailed.md # Mit Metadaten
│   └── ocr_prompt_minimal.md   # Minimale Version
├── multiphase_step1_ocr.md      # Step 1: Plain OCR
├── multiphase_step2_metadata.md  # Step 2: Metadaten
└── multiphase_step3_finalize.md # Step 3: Finalisierung
```

**Hinweis zu _template.md:**
- (*_template.md Dateien wurden NICHT erstellt - Konzept für Output-Vorlagen, nicht MVP-geplant)

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
├── __init__.py           # Exports
├── config.py             # Config loader (ENV + CLI)
├── clients/
│   ├── __init__.py       # Client factory + exports
│   ├── base.py           # Abstract LLMClient (ABC)
│   ├── ollama.py         # Ollama implementation
│   └── lmstudio.py       # LM Studio implementation
├── manager.py            # LLMManager (Instanz-Management)
├── client.py             # Legacy (alias für Rückwärtskompatibilität)
└── pdf.py                # PDF converter
```

## LLM Client Abstraktion

### Ziel
- Saubere Trennung zwischen API-Logik und Hauptskript
- Flexibles Laden verschiedener Modelle/Provider pro Step
- Mehrere LLM-Instanzen parallel verwaltbar

### Architektur: clients/base.py

```python
from abc import ABC, abstractmethod
from pathlib import Path

class LLMClient(ABC):
    """Abstract base class for all LLM clients."""
    
    model: str           # Modellname
    provider: str        # "ollama" oder "lmstudio"
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Text-only prompt → response."""
    
    @abstractmethod
    def generate_with_image(self, image_path: Path, prompt: str) -> str:
        """Image + prompt → markdown response."""
    
    @abstractmethod
    def get_usage(self) -> dict:
        """Return: {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}"""
    
    @abstractmethod
    def close(self):
        """Cleanup resources."""
    
    @abstractmethod
    def ping(self) -> bool:
        """Check connection."""
```

### clients/ollama.py

```python
from .base import LLMClient

class OllamaClient(LLMClient):
    def __init__(self, url: str, model: str, keep_alive: str = "30m"):
        self.url = url
        self.model = model
        self.provider = "ollama"
        self._client = httpx.Client(...)
    
    # Implementiert alle abstract methods
    # API: POST /api/generate
```

### clients/lmstudio.py

```python
from .base import LLMClient

class LMStudioClient(LLMClient):
    def __init__(self, url: str, model: str, context_size: int = 4096):
        self.url = url
        self.model = model
        self.provider = "lmstudio"
        self._client = httpx.Client(...)
    
    # Implementiert alle abstract methods
    # API: POST /v1/chat/completions (OpenAI-kompatibel)
    # get_usage() → aus response["usage"] extrahieren
```

### clients/__init__.py (Factory)

```python
def create_client(provider: str, model: str, config: dict) -> LLMClient:
    """Factory: Erstellt passenden Client basierend auf provider."""
    if provider == "ollama":
        return OllamaClient(
            url=config["OLLAMA_URL"],
            model=model,
            keep_alive=config.get("OLLAMA_KEEP_ALIVE", "30m")
        )
    elif provider == "lmstudio":
        return LMStudioClient(
            url=config["LMSTUDIO_URL"],
            model=model,
            context_size=config.get("LMSTUDIO_CONTEXT_SIZE", 4096)
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

### manager.py (Instanz-Management)

```python
from .clients import create_client

class LLMManager:
    """Verwaltet LLM-Instanzen für verschiedene Steps."""
    
    def __init__(self, config: dict):
        self.config = config
        self.default_client: LLMClient = None  # Für Step 2+3
        self.step1_client: LLMClient = None    # Für Step 1 (falls verschieden)
    
    def init_clients(self, provider: str):
        """Initialisiert Clients basierend auf MULTIPHASE_MODE."""
        
        # Default-Client für Step 2+3
        default_model = provider == "ollama" and config.get("OLLAMA_MODEL") or config.get("LMSTUDIO_MODEL")
        self.default_client = create_client(provider, default_model, config)
        
        # Step 1 Client (nur wenn unterschiedlich)
        if config.get("MULTIPHASE_MODE") == 1:
            step1_model = config.get("MULTIPHASE_MODEL_STEP1_OCR")
            if step1_model and step1_model != default_model:
                self.step1_client = create_client(provider, step1_model, config)
            else:
                self.step1_client = self.default_client  # Wiederverwendung
    
    def get_client(self, step: int) -> LLMClient:
        """Gibt passenden Client für Step zurück."""
        if step == 1:
            return self.step1_client or self.default_client
        else:
            return self.default_client
    
    def cleanup_after_step1(self):
        """Entlädt step1_client nach Step 1 falls != default_client."""
        if self.step1_client and self.step1_client != self.default_client:
            self.step1_client.close()
            self.step1_client = None
    
    def close_all(self):
        """Schließt alle Clients."""
        if self.default_client:
            self.default_client.close()
        if self.step1_client and self.step1_client != self.default_client:
            self.step1_client.close()
```

### Logik für Instanz-Management

```
WENN MULTIPHASE_MODE=1 UND MULTIPHASE_MODEL_STEP1_OCR != LMSTUDIO_MODEL:
    → Lade step1_client mit MULTIPHASE_MODEL_STEP1_OCR
    → Lade default_client mit LMSTUDIO_MODEL
    → Step 1 → step1_client
    → Step 2/3 → default_client
    → NACH Step 1 → cleanup_after_step1() (entlädt step1_client)

SONST:
    → Lade nur default_client (wiederverwendet für alle Steps)
    → Step 1, 2, 3 → default_client
```

### Coding-LLM Hinweise

**WICHTIG: Implementations-Reihenfolge**

1. **Erst** `clients/base.py` mit ABC definieren
2. **Dann** `clients/ollama.py` und `clients/lmstudio.py` implementieren
3. **Dann** `clients/__init__.py` mit Factory-Funktion
4. **Dann** `manager.py` mit LLMManager
5. **Zuletzt** `run.py` refaktorieren um LLMManager zu nutzen

**Prinzipien:**
- Keep it simple: Keine überflüssigen Abstraktionen
- Single Responsibility: Jede Klasse hat eine klar definierte Aufgabe
- Rückwärtskompatibilität: `client.py` bleibt als Alias erhalten
- Test-Driven: Erst Test schreiben, dann implementieren (für komplexere Funktionen)

**Env + CLI Integration:**
```python
# config.py
def load_config():
    # Lädt .env mit python-dotenv
    # Parst CLI-Argumente mit argparse (großgeschrieben)
    # CLI-Argumente überschreiben ENV-Werte
    return config
```

## Implementation Guidelines

ALWAYS start with the MINIMUM viable implementation:
- Begin with the smallest, simplest working code
- Verify it works before adding features
- NEVER implement multiple features at once

**Virtual Environment:**
- If `.venv` exists, use it for testing (`source .venv/Scripts/activate` on Windows)
- Install dependencies: `pip install -r requirements.txt`

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
| 9 | TOML-basierte Modellkonfiguration | ✓ done |
| 10 | Step-spezifische Client-Instanzen | ✓ done |
| 11 | Verbose/Debug Output | ✓ done |
| 12 | **Batch/Verzeichnis-Verarbeitung** | ✓ done |
| 13 | Step 3: Metadaten-Einbettung | planned |

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
