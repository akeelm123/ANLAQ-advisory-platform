# ANLAQ TCI™ programme dashboard

> **Version-controlled programme tracker** · Baseline: 26 November 2026 · **Scope:** methodology, evidence validation, platform, prototype, assurance and releases.

[Open interactive dashboard](./dashboard.html) · [Machine-readable tracker](./data/programme-tracker.json) · [Release plan](./RELEASE_PLAN.md) · [Governance](./GOVERNANCE.md)

**Source of truth:** `data/programme-tracker.json`. The HTML view reads this file. Change statuses only with evidence in a PR, and maintain `updated_at` and `evidence`.

## Current state

- **Approved / complete (conversation-confirmed):** authoritative IP collection; reconciliation; MD-001–007; Master Evidence Register v1.0.
- **Not completed / not verified:** Evidence Validation Specification, platform architecture, prototype implementation, testing and deployment.
- **Approval queue:** no new deliverable ready for approval. The first planned gate is the Evidence Validation Specification.
- **Repository verification:** At baseline the default branch contained only its initial README. This tracker introduces the first implementation artefacts.

## Update procedure

1. Open a change branch and edit `data/programme-tracker.json`.
2. For completed work, provide a link to a source file, commit, test run or approved decision under `evidence`.
3. Update the relevant deliverable and release statuses only when verified.
4. Open a pull request. Request the user's approval at explicit gates. Do not auto-merge or deploy.
5. Review `dashboard.html` locally or open the corresponding files in GitHub.

**Status meanings:** `planned` = scope proposed, not started; `outstanding` = next work required; `in_progress` = verified active execution; `complete` = completed with evidence; `approved` = human approved; `blocked` = identified blocker; `not_verified` = existence/completion cannot be confirmed.

> This is a repository-based, versioned tracker—not a continuously connected live feed. It changes when contributors commit updates. No background prototype execution is implied.
