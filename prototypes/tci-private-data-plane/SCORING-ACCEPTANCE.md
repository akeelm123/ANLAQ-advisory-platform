# v0.5.0-alpha.1 — restricted synthetic scoring candidate

## Authority and scope
v0.4 was accepted by the project owner on 27 November 2026 (V04-APPROVAL.json). MD-001–007, the hash-pinned reconstructed register and evidence validation specification are the controlling methodology. Scoring remains disabled by default; explicit local synthetic mode only. No production scores, real-client records, automated recommendations or deployment.

## Implemented
- 28 criteria / 140 response anchors, seven canonical dimension weights, four separate persona lenses (Board, CIO, Chief Platform Officer, Transformation Office).
- Each score requires an explicitly chosen integer anchor, current/latest independent validation acceptance, anchor-specific human rationale; supported minimum maps to 3–5, supported adverse to 1–2. No unknown-as-1 or default 3. E1/E2 and evidence strength are not scores.
- A 4 or 5 requires explicit assessor and independent reviewer sustained operating evidence confirmation. Reviewer must have previewed cited evidence, confirm anchor and materiality, and give rationale.
- Immutable encrypted proposal/review records, scoped role controls and audit. New validation, contradictory or stale evidence, or a newer unapproved score proposal withholds current aggregate.
- Each complete dimension is a criterion-weighted result; canonical overall is withheld until all 28 current score proposals are independently accepted. Weakest dimension(s), explicit material red flags, and persona lenses remain separate. No denominator reweighting for N/A. No automatic bands, risk caps or decision direction.
- Owner sees synthetic-only summary; contributors cannot see scoring records. Production release locked.

## Workbook reconciliation
The three fictional dimension-level cases in TCI_Calibration_Test_Cases.xlsx (source hash in SCORING-CALIBRATION-FIXTURES.json) reproduce exact arithmetic:
- Northstar: 4.110; workbook 4.11.
- Aurora: 3.090; workbook 3.09.
- Atlas: 1.855; workbook 1.85. This is an unresolved presentation/rounding inconsistency, not authority to use either rounding convention. Engine retains exact decimal values.
These are arithmetic fixtures, not independently assessed 28-criterion case evidence. The workbook's proposed BVR cap and contextual People & Culture constraint remain unapproved; no automatic cap or confidence band.

## Verification
Seven new scoring tests include all 28 validated and reviewed synthetic criteria, all three workbook fixtures, four persona lenses, weakest dimension, material flags, partial coverage, adverse condition, anchor and sustained-evidence gating, independent approval, supersession, new unreviewed drafts, role isolation and default-disabled mode. 215 in-process service tests pass including prior regressions. 10 loopback API tests passed; two browser flows verify disabled default and explicit synthetic scoring, Q01 exact evidence validation and independently accepted score while the overall score remains withheld (1/28). See V05-SERVICE-TEST-RESULTS.txt, V05-API-TEST-RESULTS.txt and SCORING-BROWSER-RESULTS.txt. Prior optional model-specific browser benchmarks not rerun.

## Remaining acceptance gates
Owner approval of candidate, explicit cross-assessor semantic calibration against complete fictional evidence, historical/real-data authorisation and calibration, rounding/display convention, critical-risk/cap thresholds and N/A treatment, operational security and production release. No automatically selected executive direction. The browser demonstration is one criterion; the complete assessment test is an in-process synthetic structural test, not real-world calibration. v0.6 executive decision support must not treat pilot figures as validated outcomes.
