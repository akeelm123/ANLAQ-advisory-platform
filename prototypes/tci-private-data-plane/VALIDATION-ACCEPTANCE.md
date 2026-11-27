# v0.4.0-alpha.1 — synthetic evidence validation acceptance candidate

## Scope and authority
Owner approved v0.3 on 2026-11-27 (V03-APPROVAL.json). This candidate applies the pinned evidence-validation specification to 28 criteria across seven dimensions. It is a structural human-led validation workbench, not automated semantic validation or scoring. Candidate owner acceptance is pending.

## Delivered controls
- Assessor selects approved criterion and sees required fields, intent, validation test, contradiction and corroboration guidance and evidence mappings.
- Source quote is checked against accepted current version, verified intake request mapping, parser locator, unique exact span and digest. Source provenance includes owner, period, source version and contributor identity.
- Explicit assessor observations establish applicability, condition, evidence class/strength, fields, common basis, materiality, contradictory evidence, corroboration requirement, rationale, responsible owner and follow-up.
- Missing primary/equivalent, weak or asserted support, unresolved conditional applicability, open material contradiction and missing corroboration block acceptance. Exceptions remain pending. Structural distinctness is not proof of independence.
- Independent reviewer previews every source and confirms meaning, common basis, credibility, materiality and condition; equivalent evidence, conditional applicability and independence need specific confirmations when relevant.
- Contradictory interview accounts remain immutable, with separate source-backed independent reconciliation. Superseding evidence invalidates prior support or resolution.
- Owner sees outcomes; contributor cannot see validation records. Validation records encrypted, immutable and audited. Scoring and release locked.

## Verification (2026-11-27)
- 208 in-process service tests passed: prior regression suite plus 10 validation tests. One test exercises 112 synthetic structural scenarios (met, adverse, insufficient and contradictory for each of 28 criteria). These are control-flow tests, not 112 semantically reviewed real-world examples.
- 9 loopback API tests passed, including validation integration. Initial test fixture incorrectly used supplementary material alone; acceptance was correctly blocked; fixture corrected to approved primary mapping and rerun passed.
- New browser test passed: fictional Aurora mandate upload, quarantine, exact citation, draft, denied review before preview, independent acceptance, owner visibility, locked scoring/release, contributor isolation, logout and mobile width.
- Existing document/extraction/finding browser regression passed.
- Prior local narrative and interview model benchmarks and browser journeys are inherited from the approved v0.3 candidate; model-specific browser reruns are not included in this acceptance run. No new model use for validation.
- Syntax checks passed for changed Python and JavaScript.

## Limitations and gates
Human observation and semantic judgement are required; structural tests do not certify actual field completeness, source truth, materiality or independence. The Aurora walkthrough is a single fictional criterion, not the complete multi-dimensional real engagement. Current browser form accepts one citation per source; the service accepts multiple distinct precise references. Exact-source locator support follows the existing bounded parser. Real-client processing, production operational security, private pilot infrastructure, data retention policy, scoring calibration, N/A denominator handling, public deployment and v0.4 owner acceptance remain separate gates. No client records or secrets included. Do not merge to main or deploy publicly.
