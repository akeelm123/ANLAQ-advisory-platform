# ANLAQ TCI™ authenticated evidence workbench — v0.2.0-rc.1

Synthetic evidence intelligence release candidate. The approved register and validation specification remain hash pinned. Optional local Ollama gpt-oss:20b narrative extraction preserves exact source passages; deterministic labelled TXT/PDF/DOCX/XLSX extraction remains available. No external AI provider, real client evidence, scoring or public deployment.

## Review and test

Run `python serve.py` for the local synthetic labelled extraction candidate. For local narrative mode use `python serve.py --enable-local-model` with the already installed gpt-oss:20b model; no model pull, redirect or external fallback. Launcher binds only to 127.0.0.1 and prints ephemeral synthetic credentials. Use fictional fixtures only. Model results are exact-quote candidates, not validated facts; independently review source meaning, context and citations. Missing or ambiguous values remain unresolved.

```text
python -m unittest -v test_data_plane.py test_api.py test_extraction.py test_document_parser.py test_narrative.py
python benchmark_narrative.py
node browser-smoke.cjs
node browser-narrative-smoke.cjs
python acceptance_check.py
```

The observed acceptance benchmark matched 53/53 expected field phrases in eight fictional reports across all seven dimensions, preserved 4/4 expected missing fields, independently verified 54 source citations, passed 181 regression tests and both synthetic browser journeys. See V02-ACCEPTANCE.md, V02-ACCEPTANCE-RESULT.json and NARRATIVE-BENCHMARK.json. Past alpha benchmark records are retained separately.

These results do not establish general semantic accuracy or real-client readiness. Formal owner acceptance of this synthetic v0.2 candidate remains pending; v0.3 is not started. Production parser security, OCR, broader unstructured document coverage, managed identity, hosting, data residency, retention, private pilot security and scoring require their own gates.

## Private pilot preparation

See the separate provider-neutral pilot-readiness package in docs/tci/pilot-readiness. It prepares a configuration manifest, decision packet and fail-closed preflight review; no provider or cloud resources have been selected or provisioned.
