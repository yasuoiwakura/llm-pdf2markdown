# Step 2: Metadata Extraction
# Extract structured metadata from all document pages

Analyze all document pages and extract metadata.

OUTPUT FORMAT (YAML ONLY, NO MARKDOWN CODE BLOCKS):
```yaml
sender:
  name: ""
  company: ""
  address: ""
  email: ""
  phone: ""
  fax: ""
  bank_details: ""

recipient:
  name: ""
  company: ""
  address: ""
  email: ""
  phone: ""

document_type: ""
# Options: zeugnis (arbeitszeugnis), brief, rechnung, vertrag, protokoll, dokument, other

main_language: ""
# Detected primary language (e.g., German, English)
languages: []

headers: []
# List of repeated header text appearing on multiple pages

footers: []
# List of repeated footer text appearing on multiple pages (page numbers, company info)

dates:
  document_date: ""
  # Date shown IN the document (YYYY-MM-DD or null)
  issue_date: ""
  # Date of document issuance if different

notes: ""
# Any additional observations about the document structure
```

RULES:
- Output ONLY valid YAML (no markdown code blocks, no explanations)
- Fill in fields ONLY if explicitly visible in the document
- Leave empty strings if not visible
- Be precise: "if not visible" means "if not visible", not "probably"
- For headers/footers: identify text that appears on multiple pages
- original_filename will be added by the Python script

CONTEXT: This document has {total_pages} pages.

Output: Valid YAML only.