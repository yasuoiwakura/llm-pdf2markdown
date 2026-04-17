# llm-pdf2markdown

Convert PDFs to Markdown using a local LLM (Ollama or LM Studio).

## Was ist das?

Ein Python-Tool, das PDFs per OCR in Markdown konvertiert. 
Nutzt lokale LLMs - Ihre Dokumente verlassen nie Ihren Computer.

## Warum?

- **Lokal:** Keine Cloud, keine externen Dienste
- **Datenschutz:** Vollständige Kontrolle über Ihre Daten  
- **Flexibel:** Eigene Modelle nutzbar (LM Studio getestet)

## Für wen?

- Wer PDF-Dokumente digitalisieren muss
- Datenschutz-bewusste Anwender
- Entwickler, die OCR lokal testen wollen

## Schnellstart

```bash
# Basis
python run.py

# Mit LM Studio
python run.py --USE_LMSTUDIO 1 --LMSTUDIO_MODEL gemma3-4b --TEST_PDF datei.pdf

# Multi-Phase (3-Stufen OCR für maximale Qualität)
python run.py --MULTIPHASE_MODE 1 --MULTIPHASE_MODEL_STEP1_OCR glm-ocr@f16
```

## Voraussetzungen

- Python 3.10+
- [LM Studio](https://lmstudio.ai) (empfohlen) oder [Ollama](https://ollama.com)
- .env Datei konfigurieren

## Anpassung

- Modelle, Prompts, ENV-Variablen: Siehe [SPEC.md](SPEC.md#Config)
- Known Issues: Siehe [SPEC.md#Known-Issues](SPEC.md#Known-Issues)

## Mehr Details

- Technische Dokumentation: [SPEC.md](SPEC.md)
- Changelog: CHANGELOG.md