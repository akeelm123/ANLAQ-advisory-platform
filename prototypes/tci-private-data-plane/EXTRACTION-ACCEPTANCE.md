# v0.2 document extraction acceptance — alpha.1

26 November 2026. Synthetic release candidate, not an approved v0.2 release.

| Requirement | Evidence | Status |
|---|---|---|
| EX-01 Schema traceable to approved specification | 28 criteria; 190 exact field phrases; schema validated against SHA-256 and 89 mapping references | Pass |
| EX-02 Source value and precise locator | 28 labelled-text golden fixtures and 190 exact field values; line/column/excerpt test | Pass for synthetic labelled text |
| EX-03 Missing and ambiguous evidence | Per-criterion missing, conflicting and unsupported text tests; no invented values | Pass |
| EX-04 Scope and source provenance | Authenticated assessor, accepted current mapped source only, immutable source ID/digest | Pass local |
| EX-05 Derived-data protection | AES-GCM encrypted extraction payload, immutable run metadata, scoped retrieval, audit | Pass local |
| EX-06 Independent review | Reviewer role, source preview and explicit confirmation; unresolved fields returned; stale source invalidates readiness | Pass local/browser |
| EX-07 Browser journey | Four roles from request through extraction and finding review; scoring gate locked | Pass synthetic |
| EX-08 Free-form text, PDF, DOCX, XLSX and image extraction | Not implemented; approved parser, document golden cases and exact citations required | Outstanding |
| EX-09 Semantic accuracy and real-world completeness | No semantic inference in alpha.1; assess against independently reviewed representative documents | Outstanding |
| EX-10 Hosted security and client-data processing | Separate approved privacy, retention, identity, managed storage and screening gates | Outstanding |

**Test evidence:** 142 automated tests passed (116 extraction unit/fixture cases, 20 data-plane tests, 6 loopback API tests); browser workflow passed. Golden fixtures are fictional labelled text, not representative unstructured business evidence. Field label matching is exact after case and boundary whitespace normalisation. Composite labels are retained as written in the approved specification; interpreting numeric values, resolving applicability, and confirming material sufficiency stay human-owned. Line/column citations are 1-based Unicode codepoint positions. No AI model or external processor was invoked.

**Go:** continued synthetic formative prototyping. **No-go:** real-client documents, free-form extraction accuracy claims, approved v0.2 release, numerical scoring, executive judgement or public deployment.
