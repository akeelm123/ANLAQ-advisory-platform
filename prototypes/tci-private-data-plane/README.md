# ANLAQ TCI™ authenticated evidence workbench — v0.2.0-alpha.2

Synthetic-only cross-format extraction candidate. The approved register and validation specification remain pinned at their exact SHA-256. The local browser and authenticated data plane now accept passive synthetic TXT, PDF, DOCX and XLSX (max 256 KiB per file). No public deployment, external model or processor.

## Review locally

Run `python serve.py` with declared requirements installed in an isolated Python environment. The launcher binds only to 127.0.0.1 and prints randomly generated temporary synthetic credentials. Use the temporary accounts to raise a request, submit a synthetic fixture, inspect quarantine and accept, extract draft labelled fields, independently preview and review the source, and observe release remains locked. Do not upload real client documents.

`document-fixtures.zip` contains 21 fictional documents spanning seven dimensions, with exact SHA-256 and expected values/locations in golden-document-fixtures.json. Extract the specific synthetic file locally for manual demonstration. numeric-formula-fixture.xlsx demonstrates direct typed numeric cells and unevaluated formulas. Prior 28 labelled TXT fixtures remain in golden-fixtures.json.

## Verification

```text
python -m unittest -v test_data_plane.py test_api.py test_extraction.py test_document_parser.py
node browser-smoke.cjs
```

Tests resolve the exact approved JSON files in the repository. If local layout differs use TCI_REGISTER and TCI_SPEC. TCI_PYTHON and PLAYWRIGHT_MODULE select alternate local runtimes. Chrome is required for the browser smoke. 168 automated tests and integrated Excel browser journey passed. See DOCUMENT-EXTRACTION-ACCEPTANCE.md and TEST-RESULTS.txt.

The fixture builders use python-docx, reportlab and @oai/artifact-tool for synthetic generation; the committed archive contains the actual verified bytes. Regenerating files changes binary checksums unless deterministic writers are configured; the existing manifest describes the committed bytes.

## Limitations

This recognises labelled field/value text and simple tables, not semantic extraction of arbitrary documents. PDF text layer only; no OCR, complex reading-order support or geometric citations. Word body paragraphs and simple two-cell rows only; nested/merged content unsupported. Excel visible sheet columns A/B, literal values only; formulas are left missing. Extracted values remain draft and require independent source review. Production malware screening, parser isolation, managed security, real-client processing, formal v0.2 release, scoring and public deployment remain outstanding. Do not treat this localhost prototype as production security.
