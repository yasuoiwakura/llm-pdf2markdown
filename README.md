# llm-pdf2markdown

Convert PDFs to Markdown using a local LLM (Ollama or LM Studio).

## Was ist das?

Ein Python-Tool, das PDFs per OCR in Markdown konvertiert.
Nutzt lokale LLMs (Ollama oder LM Studio) für die Konvertierung.

## Warum?

- **Lokal:** Keine Cloud, Ihre Dokumente verlassen nie Ihren Computer
- **Datenschutz:** Vollständige Kontrolle über Ihre Daten
- **Flexibel:** Eigene Modelle nutzbar (getestet: LM Studio)

## Für wen?

- Wer PDF-Dokumente digitalisieren muss
- Datenschutz-bewusste User
- Entwickler, die OCR lokal testen wollen

## Schnellstart

```bash
# Basis
python run.py

# Mit LM Studio
python run.py --USE_LMSTUDIO 1 --LMSTUDIO_MODEL gemma3-4b --TEST_PDF datei.pdf
```

## Voraussetzungen

- Python 3.10+
- [LM Studio](https://lmstudio.ai) (getestet) oder [Ollama](https://ollama.com)
- .env konfigurieren

## Anpassung

- Modelle, Prompts, ENV: Siehe [SPEC.md](SPEC.md#Config)
- Known Issues: Siehe [SPEC.md#Known-Issues](SPEC.md#Known-Issues)

## Mehr Details

- Technische Dokumentation: [SPEC.md](SPEC.md)
- Changelog: CHANGELOG.md