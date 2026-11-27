# ANLAQ TCI™ authenticated evidence workbench — v0.5.0-alpha.1

Owner-approved v0.4 foundation plus a restricted synthetic scoring candidate. Approved question bank and validation specification hash-pinned. No real-client interviews, automatic contact, recording, scoring or deployment.

## Local review

Run `python serve.py` from this folder with declared dependencies installed in an isolated Python environment. Optional `--enable-local-model` permits the already-installed local gpt-oss:20b model to propose narrative excerpts and interview follow-up wording only. No external provider or model pull. The application binds loopback and generates ephemeral role credentials; use fictional inputs only.

As assessor, start a fictional session for each stakeholder/persona, select an approved criterion question, capture the verbatim response and separate interpretation/uncertainty, link eligible accepted current evidence (optional) and record explicit assessor observation flags. Record material contradictory statements as separate claims. The rule engine proposes one targeted follow-up based on explicit observations and evidence gaps. If local model is enabled it can suggest wording using an exact response quote; the assessor must review/edit and explicitly record the question. Capture the answer without claiming the gap resolved. Independent reviewer confirms capture or returns; claims remain unverified E3/E4 until separately validated against evidence. Owner sees separate personas and open contradictions; release stays locked.

## Verification

```text
python -m unittest -v test_data_plane.py test_api.py test_extraction.py test_document_parser.py test_narrative.py test_interviews.py test_validation_workflow.py test_scoring.py
python benchmark_interview.py
node browser-smoke.cjs
node browser-narrative-smoke.cjs
node browser-interview-smoke.cjs
node browser-validation-smoke.cjs
node browser-scoring-smoke.cjs
```

Tests resolve exact register, validation and interview preparation files within the repository. If local layout differs use TCI_REGISTER, TCI_SPEC, TCI_INTERVIEW_SPEC and TCI_INTERVIEW_FIXTURES; TCI_PYTHON and PLAYWRIGHT_MODULE select alternate runtimes. Chrome is required for browser tests; local model needed only for optional wording benchmark and narrative/interview model browser journeys.

225 automated tests and two browser workflows passed for v0.5; prior model-specific workflows remain documented in v0.3. See SCORING-ACCEPTANCE.md and V04-APPROVAL.json. Formal v0.5 acceptance, semantic calibration, private pilot, real-client handling, production scoring and public deployment remain gated.

## Validation workflow

In section 09, select a criterion, inspect its approved rules and choose accepted, current mapped sources. Enter exact parser locators and quotes. Record condition, evidence class, strength, materiality, responsible owner, rationale and follow-up. Documentary and interview contradictions block support. Sign in as reviewer, preview every cited source in the accepted evidence section, record a reasoned reconciliation if needed, and accept only when the structural checks and independent human assessment support the outcome. Owners see supported or unresolved states; no score is calculated. Historical approvals remain visible but superseded source versions invalidate current support.

## Restricted synthetic scoring
Run the local server with `--enable-pilot-scoring` only for fictional calibration; default is disabled. In section 10 choose the latest independently accepted criterion finding, an explicit anchor and rationale, plus sustained operating evidence for 4–5. An independent reviewer confirms evidence, anchor and material flags. Each dimension requires complete accepted criterion coverage and canonical pilot score requires all 28. Persona perspectives and weakest dimension are separately visible. No automatic bands, caps or decision direction. See SCORING-ACCEPTANCE.md.
