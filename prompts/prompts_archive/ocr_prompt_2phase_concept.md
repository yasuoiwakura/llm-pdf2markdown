# 2-Phase OCR Prompt (NOT IMPLEMENTED)
# This is documentation for a potential future implementation

## Concept

The 2-phase approach splits the OCR process into two distinct passes:

### Phase 1: Metadata Extraction
- Send ALL pages at once to the LLM
- Task: Extract only metadata from the document
- Output: YAML frontmatter only

### Phase 2: Content Extraction  
- Process each page individually (or in batches under threshold)
- Task: Extract content as plain Markdown
- Merge with metadata later

## Implementation Logic (NOT IMPLEMENTED)

```
if pages <= MAX_PAGES_PER_REQUEST:
    # Single-pass: all pages at once
    send_all_pages_at_once()
else:
    # 2-phase: metadata + content separately
    metadata = extract_metadata_all_pages()
    content_pages = []
    for page in pages:
        content = extract_content_single_page(page)
        content_pages.append(content)
    final_output = merge(metadata, content_pages)
```

## Prompt Files (NOT IMPLEMENTED)

```
prompts/
├── ocr_prompt.md              # Current: single-pass
├── ocr_prompt_metadata.md     # Phase 1: metadata extraction
└── ocr_prompt_content.md      # Phase 2: content extraction
```

## When to Use

- Short documents (≤MAX_PAGES_PER_REQUEST): Single-pass is fine
- Long documents (>MAX_PAGES_PER_REQUEST): 2-phase recommended for better quality
- Current use case (Zeugnisse, 1-3 pages): Single-pass is sufficient

## Open Questions

- Does metadata extraction from all pages at once work better than individual?
- Is the overhead worth it for short documents?
- Should this be the default or opt-in?