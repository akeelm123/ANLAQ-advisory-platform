# ANLAQ TCI™ authenticated evidence workbench — v0.9.0-alpha.1

Owner-approved v0.7 foundation plus integrated fictional Aurora pilot candidate. Approved question bank and validation specification hash-pinned. No real-client interviews, automatic contact, recording, scoring or deployment.

## Local review

Run `python serve.py` from this folder with declared dependencies installed in an isolated Python environment. Optional `--enable-local-model` permits the already-installed local gpt-oss:20b model to propose narrative excerpts and interview follow-up wording only. No external provider or model pull. The application binds loopback and generates ephemeral role credentials; use fictional inputs only.

As assessor, start a fictional session for each stakeholder/persona, select an approved criterion question, capture the verbatim response and separate interpretation/uncertainty, link eligible accepted current evidence (optional) and record explicit assessor observation flags. Record material contradictory statements as separate claims. The rule engine proposes one targeted follow-up based on explicit observations and evidence gaps. If local model is enabled it can suggest wording using an exact response quote; the assessor must review/edit and explicitly record the question. Capture the answer without claiming the gap resolved. Independent reviewer confirms capture or returns; claims remain unverified E3/E4 until separately validated against evidence. Owner sees separate personas and open contradictions; release stays locked.

## Verification

```text
python -m unittest -v test_data_plane.py test_api.py test_extraction.py test_document_parser.py test_narrative.py test_interviews.py test_validation_workflow.py test_scoring.py test_executive.py test_reassessment.py test_aurora_pilot.py
python benchmark_interview.py
node browser-smoke.cjs
node browser-narrative-smoke.cjs
node browser-interview-smoke.cjs
node browser-validation-smoke.cjs
node browser-scoring-smoke.cjs
node browser-executive-smoke.cjs
node browser-reassessment-smoke.cjs
node browser-aurora-smoke.cjs
```

Tests resolve exact register, validation and interview preparation files within the repository. If local layout differs use TCI_REGISTER, TCI_SPEC, TCI_INTERVIEW_SPEC and TCI_INTERVIEW_FIXTURES; TCI_PYTHON and PLAYWRIGHT_MODULE select alternate runtimes. Chrome is required for browser tests; local model needed only for optional wording benchmark and narrative/interview model browser journeys.

244 automated tests and two browser workflows passed for v0.9, including the local fingerprinted source workbook; prior model-specific workflows remain documented in v0.3. See AURORA-ACCEPTANCE.md and V07-APPROVAL.json. Formal v0.9 acceptance, semantic calibration, private pilot, real-client handling, production scoring and public deployment remain gated.

## Validation workflow

In section 09, select a criterion, inspect its approved rules and choose accepted, current mapped sources. Enter exact parser locators and quotes. Record condition, evidence class, strength, materiality, responsible owner, rationale and follow-up. Documentary and interview contradictions block support. Sign in as reviewer, preview every cited source in the accepted evidence section, record a reasoned reconciliation if needed, and accept only when the structural checks and independent human assessment support the outcome. Owners see supported or unresolved states; no score is calculated. Historical approvals remain visible but superseded source versions invalidate current support.

## Restricted synthetic scoring
Run the local server with `--enable-pilot-scoring` only for fictional calibration; default is disabled. In section 10 choose the latest independently accepted criterion finding, an explicit anchor and rationale, plus sustained operating evidence for 4–5. An independent reviewer confirms evidence, anchor and material flags. Each dimension requires complete accepted criterion coverage and canonical pilot score requires all 28. Persona perspectives and weakest dimension are separately visible. No automatic bands, caps or decision direction. See SCORING-ACCEPTANCE.md.

## Executive decision support
Section 11 summarises current criterion evidence, gaps and contradictions. As assessor, draft a human synthesis, limitations, linked supported findings, two considered options and accountable follow-up. As reviewer, preview current supported and reconciliation sources and independently review or return. As owner, explicitly record a direction from reviewed options and residual conditions. Incomplete coverage permits only Reassess in the synthetic candidate. Source, validation, conflict, request or newer brief changes supersede historical review and direction. No client-ready release or automated investment decision.

## Reassessment
Section 12 captures a labelled period with explicit start/end dates and consistent population/measurement basis. Have an independent reviewer accept the current snapshot before evidence changes. Capture and review a subsequent non-overlapping period; compare accepted snapshots with the same scope, methodology and basis. Account for each baseline executive action and link supported follow-up evidence for closure. The reviewer verifies both periods and action evidence. Historical accepted snapshots remain intact; unsupported criteria are not assigned performance deltas. No cross-assessment comparisons, automatic decisions or production scoring.

## Integrated fictional Aurora dry run
Set `TCI_AURORA_WORKBOOK` to the local, fingerprinted TCI_End_to_End_Interview_Pilot_Project_Aurora.xlsx (see AURORA-PILOT-INPUTS.json). Launch with `python serve.py --enable-pilot-scoring --aurora-pilot-workbook "$TCI_AURORA_WORKBOOK"`. The opt-in source-only demo preloads simulated test actions, not actual human approvals. All claims remain unverified, no score is produced, no calendar follow-up invented. The raw workbook is not included in the public repository. The full mock lifecycle test is a separate isolated assessment and uses existing labelled golden fixtures. Source test skips if the environment variable is absent; source browser test requires it. See AURORA-ACCEPTANCE.md and PRIVATE-PILOT-READINESS.md.

## Private pilot readiness (0.9.1-readiness.1)
The integrated app remains v0.9 synthetic loopback only. The offline storage reference `pilot_storage.py` supports explicit synthetic archive and in-memory restore; it is not a hosted persistence integration. Run `python -m unittest -v test_pilot_storage.py test_pilot_readiness.py` with the existing pinned methodology variables and optional Aurora workbook path. Run `python pilot_readiness.py` for the structured local gate report. See PRIVATE-PILOT-IMPLEMENTATION-PLAN.md and READINESS-ACCEPTANCE.md. No deployment or data-handling approval is inferred from local tests.

## Architecture choices (0.9.1-readiness.2)
See PRIVATE-PILOT-ARCHITECTURE.md for local workstation and AWS Singapore reference options. Run python pilot_architecture.py and python -m unittest -v test_pilot_architecture.py for offline design contract checks. No deployment or operational gate accepted; choose an option and obtain independent design review before implementation.

## Persistent local pilot (v0.9.2-alpha.1)
Approved Option A. On the owner's Mac double-click start-local-pilot.command, confirm fictional-only use and create/unlock the named-account encrypted vault. See LOCAL-PILOT-START.md for exact startup, backup and recovery procedures and LOCAL-PILOT-ACCEPTANCE.md for tests and limitations. The existing serve.py launcher remains ephemeral synthetic mode. Run the additional test_local_store.py and test_local_api.py suites and browser-local-pilot-smoke.cjs with pinned methodology paths. No actual user vault, cloud deployment, production scoring or real-client processing authorised.

## Intelligent evidence matching (v0.9.3-alpha.1)
Section 08a searches accepted current sources for a criterion/optional interview claim, shows exact citations and potential discrepancies. Preview original document, explicitly confirm mapped relevance or reject, select confirmed citations in the validation draft and separately obtain independent validation review. Unmapped discovery candidates cannot be imported. Ranked local discovery works without model. For optional fixed-loopback model labels only in an explicitly enabled synthetic demo, use validation_demo.py --matching-preview --enable-local-model --port 8768. See MATCHING-ACCEPTANCE.md. No actual client inputs or automatic scores.

## Local pilot user acceptance (0.9.3-uat.1)
Run the synthetic complete persistent API rehearsal with pinned paths: python -m unittest -v test_local_full_uat.py. See LOCAL-HUMAN-UAT.md and uat-fixtures/UAT-FIXTURE-MANIFEST.json for independent human testing. Run local_machine_check.py for private read-only machine checks; do not publish its device-specific output. No operational gate is automatically accepted. See LOCAL-UAT-ACCEPTANCE.md.

## Local intake assurance and calibration (v0.9.4-alpha.1)
Section 04a reports format-only vs clean scan. Persistent local mode uses bounded child parsing (not an OS sandbox). Optional --require-malware-scan requires installed ClamAV and refuses unavailable/detected scans. Offline retention_review.py authenticates selected archive expiry without deleting or restoring. Blank blind calibration template and comparator require independent human records. See INTAKE-RETENTION-CALIBRATION.md and V094-ACCEPTANCE.md.
