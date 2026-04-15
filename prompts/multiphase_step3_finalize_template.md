# Step 3: Finalization - Template Version
# Combine single_pages.md with metadata to create clean, cohesive document

You have two inputs:
1. **single_pages.md** - The raw OCR output with all content (may contain redundancies)
2. **metadata.yaml** - Extracted metadata including headers/footers to remove

TASK:
Create a clean, cohesive Markdown document by:
1. Reading the content from single_pages.md
2. Removing redundant headers and footers (identified in metadata)
3. Merging content across pages into one coherent flow
4. Keeping the document structure (headings, lists, tables)

STRICT RULES:
- DO NOT add content that was not in the original
- DO NOT rephrase or summarize
- DO NOT correct unless absolutely necessary (illegible characters)
- Keep ALL substantive content
- Just REMOVE redundancy, do not change the meaning

METADATA REFERENCE:
- document_type: [DOCUMENT_TYPE]
- language: [LANGUAGE]
- sender: [SENDER_NAME]
- recipient: [RECIPIENT_NAME]
- headers to remove: [HEADERS]
- footers to remove: [FOOTERS]

CONTEXT: Original document has [TOTAL_PAGES] pages.

Output: Clean Markdown only, NO explanations.