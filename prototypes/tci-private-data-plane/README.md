# ANLAQ TCI™ authenticated evidence workbench — v0.3.0-alpha.1

Owner-approved v0.2 RC.2 foundation plus a synthetic stakeholder interview candidate. Approved question bank and validation specification hash-pinned. No real-client interviews, automatic contact, recording, scoring or deployment.

## Local review

Run `python serve.py` from this folder with declared dependencies installed in an isolated Python environment. Optional `--enable-local-model` permits the already-installed local gpt-oss:20b model to propose narrative excerpts and interview follow-up wording only. No external provider or model pull. The application binds loopback and generates ephemeral role credentials; use fictional inputs only.

As assessor, start a fictional session for each stakeholder/persona, select an approved criterion question, capture the verbatim response and separate interpretation/uncertainty, link eligible accepted current evidence (optional) and record explicit assessor observation flags. Record material contradictory statements as separate claims. The rule engine proposes one targeted follow-up based on explicit observations and evidence gaps. If local model is enabled it can suggest wording using an exact response quote; the assessor must review/edit and explicitly record the question. Capture the answer without claiming the gap resolved. Independent reviewer confirms capture or returns; claims remain unverified E3/E4 until later evidence validation. Owner sees separate personas and open contradictions; release stays locked.

## Verification

```text
python -m unittest -v test_data_plane.py test_api.py test_extraction.py test_document_parser.py test_narrative.py test_interviews.py
python benchmark_interview.py
node browser-smoke.cjs
node browser-narrative-smoke.cjs
node browser-interview-smoke.cjs
```

Tests resolve exact register, validation and interview preparation files within the repository. If local layout differs use TCI_REGISTER, TCI_SPEC, TCI_INTERVIEW_SPEC and TCI_INTERVIEW_FIXTURES; TCI_PYTHON and PLAYWRIGHT_MODULE select alternate runtimes. Chrome is required for browser tests; local model needed only for optional wording benchmark and narrative/interview model browser journeys.

206 automated tests, seven structural local-model wording proposals and three browser workflows passed. See INTERVIEW-ACCEPTANCE.md and V02-APPROVAL.json. Previous v0.2 expanded benchmark remains recorded separately. Local synthetic encrypted storage and authenticated roles are not production identity or security acceptance. Formal v0.3 acceptance, private pilot, real-client handling, scoring and public deployment remain gated.
