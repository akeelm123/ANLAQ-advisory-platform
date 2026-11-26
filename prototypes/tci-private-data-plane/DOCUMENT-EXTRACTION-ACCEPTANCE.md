# Cross-format extraction acceptance — v0.2.0-alpha.2

26 November 2026 · Synthetic release candidate, not formal v0.2 acceptance.

| Capability | Evidence | Status |
|---|---|---|
| TXT labelled values | Previous 28 fixtures / 190 field labels retained | Pass |
| PDF text layer | 7 fictional PDF fixtures, page and extracted-line references | Pass |
| DOCX labelled tables and body paragraphs | 7 fictional Word fixtures; precise table/row/cell or paragraph locator | Pass for fixture structure |
| XLSX labelled two-column tables | 7 fictional workbooks; exact worksheet/cell locator | Pass |
| Literal Excel numeric cell | Additional fixture; typed value and number-format provenance | Pass |
| Excel formula handling | Formula values not evaluated or taken from caches | Pass |
| Cross-format fixtures | 21 documents / 138 expected field-location pairs | Pass |
| Source-integrity and independent review | Accepted current source, digest and encrypted extraction records; reviewer previews original-derived text; invalidation on supersession | Pass local |
| Integrated API and browser | All three document formats through API; Excel submission, extraction, exact-cell citation and review through Chrome | Pass synthetic |
| Full semantic extraction | Unstructured prose inference, OCR, complex multi-column PDF, merged/nested Word tables, formula results, arbitrary spreadsheet layouts unsupported | Outstanding |
| Client security and hosted acceptance | Production parser isolation, malware screening, identity, managed storage, approved region and retention required | Outstanding |

168 automated tests passed (116 prior labelled-text tests; 25 parser tests; 20 data-plane tests; 7 API tests); integrated browser workflow passed. 138 golden source values are fixture expectations, not measured real-world extraction accuracy.

Supported source limits: passive synthetic TXT/PDF/DOCX/XLSX only, max 256 KiB each. Bounded format preflight rejects malformed or unsupported packages; this is not security sandboxing or malware scanning. PDF line locators refer to extracted text, not geometric page coordinates. Word table locators identify body tables and unmerged cells. Excel values refer to visible sheet cells; literal raw type and number format are retained, no formula evaluation or inferred display conversion. Missing or ambiguous fields are unresolved. Scoring and executive release remain locked.
