# v0.1 evidence collection — acceptance record
Candidate: v0.1.0-beta.1 · 26 November 2026 · Not released

## Scope and acceptance
| ID | Requirement | Evidence | Status |
|---|---|---|---|
| EC-01 | Capture assessment title, decision, boundaries, period and owner before evidence | core.test.cjs; browser-smoke.cjs | Pass, synthetic |
| EC-02 | Present source-attributed request catalogue and provisional dimension labels | requests.json; core.test.cjs | Pass for 21 legacy items only |
| EC-03 | Record requested/missing plus named actor and rationale; derive received from a linked record | core.test.cjs; browser-smoke.cjs | Pass |
| EC-04 | Capture source title, version, owner, reporting period, locator, digest and criterion link | core.test.cjs; browser-smoke.cjs | Pass for synthetic files |
| EC-05 | Preserve ad hoc evidence separately; reject a cross-dimension request association | core.test.cjs | Pass; actual criterion-to-request mapping unverified |
| EC-06 | Record traceable draft finding, gap, contradiction and independent review | core.test.cjs; browser-smoke.cjs | Pass structural controls only |
| EC-07 | Export and restore versioned snapshot using replay; fail on invalid references, version or baseline | core.test.cjs; browser-smoke.cjs | Pass for beta snapshots |
| EC-08 | Keep pilot scoring and executive release disabled even after restore | core.test.cjs; browser-smoke.cjs | Pass |
| EC-09 | Confirm 32-item approved catalogue and 89 reported mappings; source hash and signed reconciliation | Master Evidence Register v1.0 | Blocked: workbook not retrieved |
| EC-10 | Approve handling of real client documents, storage, access, retention and audit integrity | Security design and review | Outstanding |
| EC-11 | Owner acceptance of usability, completeness and readiness for next release | Documented human sign-off | Not yet approved |

The 21 legacy items come from TCI_Evidence_Collection_Guide_v1.xlsx, Evidence Request List. They are a provisional checklist only. A received item is not validated evidence and 21/21 is not approved evidence coverage. Cross-dimension matching is a structural guard, not approved mapping. Imported records are self-declared and structural replay is not authentication; original files are not persisted. Alpha snapshots intentionally unsupported. No client data should be entered.

## Go/no-go
- **Go:** synthetic formative review of beta.1.
- **No-go:** v0.1 formal release, real-client use, numerical pilot scoring, executive outputs or deployment.
- Owner decision required: provide/retrieve approved register and reconcile its exact file; approve coverage and secure evidence handling before accepting v0.1.
- Release owner records date, version, reviewed evidence, decision and outstanding exceptions. No automatic progression.
- Next implementation: verified catalogue ingestion and coverage acceptance; then v0.2 extraction golden fixtures, exact source locations and human review. No unapproved rule is to be treated as authoritative.
