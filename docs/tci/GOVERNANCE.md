# Dashboard governance

## Branch and review policy
- Tracker changes are made on a feature branch via pull request; do not write progress updates directly to `main`.
- Approval gates require a documented reviewer decision. Merging a tracker change is not equivalent to approval of the underlying methodology or deployment.
- Avoid vague statuses such as “almost done”. Use `planned`, `outstanding`, `in_progress`, `blocked`, `complete`, `approved` or `not_verified`.
- A `complete` implementation item requires evidence: commit, test result, build, screenshot with context or artefact URL.
- A `blocked` item must explain the precise required action. External Work sessions do not automatically update this repository.
- The approved Master Evidence Register v1.0 and MD-001–007 are acknowledged from project conversation, **not** independently verified as files in this repository.

## Confidentiality
**This repository is public.** Do not commit proprietary unredacted TCI source files, calibration cases, user assessment responses, client documents, personal data, access tokens or connection secrets without an explicit publication decision and required controls.

## Updating `data/programme-tracker.json`
Maintain machine-readable statuses, a date and proof note. A versioned change is visible in git history. Release status is `proposed` until acceptance; human gates are not bypassed. Link PRs/issues as needed; `github_issue: null` signals not yet associated.

## No synthetic progress
Task-closure percentage is unweighted and should not be presented as delivery effort. A future automated checker may inspect CI and issue changes, but this initial dashboard only displays committed JSON. Until automation is implemented and verified, progress is updated by commits.
