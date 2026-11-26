# ANLAQ TCI™ authenticated evidence workbench — v0.2.0-alpha.3

Adds optional local model-assisted narrative passage extraction to the deterministic TXT/PDF/DOCX/XLSX labelled-field candidate. Synthetic-only. The approved register and validation specification remain hash pinned. No external AI provider, documents, credentials or model weights are placed in the repository.

## Local synthetic demonstration

Install requirements in an isolated local Python environment from this folder and run `python serve.py` for deterministic labelled extraction. To enable narrative mode, ensure the existing local Ollama service has gpt-oss:20b installed and run `python serve.py --enable-local-model`. The application and model endpoints are loopback only; the adapter will not pull models, follow redirects, use proxies or fall back to an external service. The launcher prints ephemeral synthetic account credentials; never share them or upload real data. The default mode is labelled extraction, with narrative disabled.

The assessor selects an accepted mapped source and criterion, requests narrative extraction, and the model proposes field keys and verbatim source quotes. An independent deterministic verifier checks each quote against the original segment, retains location and columns, and flags missing or ambiguous passages. The encrypted draft record includes the source digest, schema/version, model name and digest. Exact quote does not mean semantic correctness. A different reviewer must inspect and confirm field meaning, context and citation; missing, ambiguous or rejected proposals cannot be accepted, and scoring remains locked.

## Verification

```text
python -m unittest -v test_data_plane.py test_extraction.py test_document_parser.py test_narrative.py
python benchmark_narrative.py
```

The benchmark uses only narrative-fixtures.json (four fictional reports); it invokes the installed local model and records actual outputs. The observed result was 23/26 expected field-phrase matches, with omissions explicitly recorded. 171 in-process tests pass, including saved benchmark result replay through the encrypted service and reviewer gate. A fresh API/browser regression was blocked by the permission review timing out; previous alpha.2 browser evidence remains historical. When local testing is available, run `python -m unittest -v test_api.py` and `node browser-smoke.cjs`. See NARRATIVE-ACCEPTANCE.md and TEST-RESULTS.txt.

## Limits

Narrative results are provisional excerpts only. Model omissions, misattribution and modified model behaviour remain possible even when a quote matches. The benchmark covers three criteria, not all 28 semantic extraction behaviours. Bounded synthetic text window only, no OCR, complex document reading order or full-document semantic accuracy. No production malware screening, parser sandbox, external identity/MFA, managed storage, TLS deployment, privacy/retention approval, real-client data, scoring or public deployment. Formal v0.2 acceptance remains gated.
