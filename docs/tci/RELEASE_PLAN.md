# TCI™ release plan — proposed baseline
**Version:** 0.1 · **Last updated:** 26 November 2026 · **Delivery dates:** not committed

Releases are capability gates, not calendar promises. Only mark released when the corresponding acceptance tests, evidence and human approval exist.

| Release | Capability | Acceptance gate | Status |
|---|---|---|---|
| v0.1.0-alpha | Manual evidence workbench | Synthetic workflow and control tests | Implemented; formative review pending |
| v0.1 | Evidence collection | Evidence coverage and usability | Proposed |
| v0.2 | Evidence intelligence | Extraction accuracy | Proposed |
| v0.3 | Intelligent interviews | Interview quality | Proposed |
| v0.4 | Validation engine | Validation accuracy | Proposed |
| v0.5 | Assessment and scoring | Scoring calibration | Proposed |
| v0.6 | Executive decision support | Executive usefulness | Proposed |
| v0.7 | Longitudinal assessment | Reassessment accuracy | Proposed |
| v0.9 | Integrated pilot | Pilot acceptance | Proposed |
| v1.0 | Production release | Go-live approval | Proposed |

## Release acceptance criteria

1. Features demonstrated against written requirements, with tests and defects recorded.
2. Evidence sources traceable and protected; no fabricated evidence, scores or thresholds.
3. Human approval before any executive judgement is finalised, and before public deployment.
4. All changes linked to a PR/commit; incomplete features remain marked accordingly.
5. Data security/privacy review ahead of external client uploads.

## Key dependencies

- **v0.1:** functional requirements, evidence handling and secure upload design.
- **v0.2–v0.4:** criterion-specific Evidence Validation Specification (currently outstanding).
- **v0.5:** scoring and decision rules; pilot scoring is not production-calibrated.
- **v0.9:** Project Aurora pilot, scenario tests and user acceptance.
- **v1.0:** security, auditability, support and explicit final release approval.

The 7 dimensions are Strategic Alignment; Leadership Commitment; Technology Readiness; People & Culture; Data & AI Confidence; Delivery Excellence; Business Value Realisation. Canonical scoring weights are 15%, 10%, 15%, 10%, 15%, 15% and 20%, respectively. They are methodology baselines—not verified deployed code.

[Detailed alpha release plan and gates](../../prototypes/tci-evidence-workbench/RELEASE_PLAN.md). Scoring and release remain locked.
