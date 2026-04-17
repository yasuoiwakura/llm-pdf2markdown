# Detailed OCR Prompt - English
# V3 - All pages at once (up to MAX_PAGES_PER_REQUEST)

Convert these document pages to ONE plain Markdown file.

CONTEXT: This is a multi-page document with {total_pages} pages sent in a single request.

STRICT RULES:
- Output: Plain Markdown ONLY, NO backticks (```)
- NO introductions like "Here's the Markdown..."
- NO explanatory footnotes ("Notes:", "Considerations:", "Limitations:")
- NO questions at the end ("Could you tell me...", "To help me improve...")
- NO self-analysis ("Due to the complexity...", "The original image had...")
- Output: ONE cohesive document, NOT separate page blocks

## Metadata Format (at the top of document)

Include explicit metadata as Markdown heading, inferred metadata as HTML comment.

### Explicit Metadata (clearly visible in document)
Write directly as Markdown under this heading:
```markdown
## Document Information

- Date: [if visible in document, e.g., "30.09.2024"]
- Company/Sender: [if visible]
- Recipient: [if visible]
```

### Inferred Metadata (your conclusions)
Add as HTML comment after the heading by filling the values:
<!--
language: German|English|mixed
document_type: certificate|testimonial|thesis|etc.
confidence: high|medium|low
python_pages: {total_pages}
python_source_file: {source_file}
python_temp_files: {temp_filenames}
-->

RULES:
- Only include explicit data in the Markdown section
- Only include inferred data in the HTML comment
- If data is NOT visible, omit it (don't guess in Markdown section)
- Inference is allowed in the comment section
- to not replace placeholders starting with "python_"
- return plain markdown, to not quote it using backticks

Output: Single plain Markdown document with metadata at top.