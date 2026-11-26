# ANLAQ TCI™ authenticated evidence workbench — v0.2.0-rc.2

Synthetic narrative quality expansion of the RC.1 evidence intelligence candidate. Approved register and validation specification remain hash pinned. Optional local gpt-oss:20b model proposes exact source passages; deterministic labelled TXT/PDF/DOCX/XLSX remains available. No external provider, real client data, scoring or public deployment.

## Local review and verification

Run `python serve.py` with declared dependencies in an isolated Python environment; for optional synthetic narrative mode run `python serve.py --enable-local-model` with the already installed model. Only loopback, no model pull or external fallback; ephemeral account credentials are printed locally. Never upload real client files.

```text
python -m unittest -v test_data_plane.py test_api.py test_extraction.py test_document_parser.py test_narrative.py
python benchmark_narrative.py
node browser-smoke.cjs
node browser-narrative-smoke.cjs
python expanded_quality_check.py
```

The 32-report expansion covers all 28 criteria and seven dimensions. Recorded final targeted-ret-test results: 201/201 curated field phrases, 12/12 expected missing controls, 208 source citations checked without invalid citations, 189 regression tests and both browser workflows passed. See EXPANDED-QUALITY-REPORT.md and EXPANDED-QUALITY-RESULT.json. Original and remediation outputs remain separate so readers can inspect the improvement path. The older RC.1 acceptance result is preserved in V02-ACCEPTANCE-RESULT.json. A new full model run may produce different results; no production accuracy claim.

## v0.3 preparation

The provider-independent interview workflow design, 28 approved question cards, 10 proposed follow-up triggers, 14 planned scenario tests and seven fictional two-persona golden cases are in docs/tci/interviews-v0.3-preparation. Six source-reconciliation checks passed. v0.3 implementation remains gated pending formal owner acceptance; no client interviews, recording or automated scores.

Private pilot preparation remains in docs/tci/pilot-readiness. Hosting, regional/privacy decisions, managed security, private pilot and scoring remain separate gates.
