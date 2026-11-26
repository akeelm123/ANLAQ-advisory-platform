# Transformation Confidence Index™ by ANLAQ — release plan
Version 0.3 draft · 26 November 2026

This extends the verified public programme roadmap, rather than replacing it. No release has been approved; all dates are uncommitted.

| Release | Capability | Acceptance gate | Status |
|---|---|---|---|
| 0.1.0-alpha | Local manual evidence capture, source hashes, criterion links, review ledger | Synthetic workflow, provenance and gate tests | Implemented locally; acceptance pending |
| 0.1.0-beta.1 | Assessment scope, provisional 21-request checklist, request tracking, versioned snapshot recovery | Synthetic control tests and browser workflow | Implemented; formative review pending |
| 0.1 | Evidence collection | Retrieve and reconcile approved Master Evidence Register; requirements and coverage acceptance; secure storage design | Blocked by baseline retrieval and approval |
| 0.2 | Document extraction and traceability | Golden extraction test set; source citations; review accuracy | Planned |
| 0.3 | Interview assistant | Persona separation, follow-up and assertion handling | Planned |
| 0.4 | Validation engine | Approved criterion-level specification, triangulation and contradictions tested | Planned |
| 0.5 | Restricted pilot scoring | Approved scoring rules, missing evidence controls, critical risk warnings, calibration and human sign-off | Locked |
| 0.6 | Executive decision support | Traceable findings; independent human acceptance | Planned |
| 0.7 | Reassessment | Versioned snapshots and comparable scope/period | Planned |
| 0.9 | Integrated Project Aurora pilot | End-to-end synthetic then authorised pilot UAT | Planned |
| 1.0 | Production | Security/privacy, authentication, retention, audit, operational readiness, explicit go-live approval | Locked |

## Required gates
- Methodology owner: confirm exact register version and hash; approve criterion mappings and Evidence Validation Specification.
- Independent assessor: accept findings only after source review; record rationale and resolve material contradictions.
- Pilot calibration owner: validate scoring and risk thresholds with labelled scenarios. Until then no numerical scores, bands or executive recommendations.
- Release owner: review written requirements, automated tests, UI acceptance, defects and security/privacy findings; approve release explicitly.
- Public deployment requires separate explicit approval. Never publish proprietary register, source artefacts or assessment data in public GitHub.

## Current acceptance checkpoint
See [v0.1 acceptance record](ACCEPTANCE-v0.1.md). 19/19 automated control tests plus synthetic browser workflow passed. v0.1 remains blocked pending the approved register file, coverage reconciliation and secure evidence handling approval. Do not equate beta.1 with v0.1 formal release.
