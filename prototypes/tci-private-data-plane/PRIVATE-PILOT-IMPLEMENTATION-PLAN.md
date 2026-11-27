# Private pilot implementation plan — 0.9.1-readiness.1
2026-11-27 · Stage 1: local recovery and control evidence

## Proposed deployment boundary (not provisioned)
A single, isolated pilot environment, accessible only to explicitly authorised users through private ingress. Use a managed identity provider with MFA, server-side identity verification and a separate membership/role mapping per assessment. The application is not the identity authority. Use private application-to-storage connectivity, managed encrypted database/object storage and a separately managed key/secret service; no public repository, browser storage, public object URLs or anonymous endpoints for pilot records. Keep model processing disabled until separately approved. Deploy no infrastructure until the owner accepts the hosting architecture, region, budget, identity provider and access cohort.

## Delivery sequence
| Stage | Implement / verify | Exit evidence |
|---|---|---|
| 1 Local control evidence | Encrypted synthetic archive, in-memory restore, active-session removal, retention expiry guard, readiness report | Local test results; no operational acceptance |
| 2 Environment design | Select private hosting, data region, ingress, identity, storage and secret model; independent design review | Approved architecture, cost and participant charter |
| 3 Controlled implementation | Identity federation, role lifecycle, persistent encrypted storage, source quarantine/scanning, secure parser isolation, retention and key lifecycle; external audit | Independently verified isolated test environment, no client inputs |
| 4 Operational assurance | Restore exercise, monitoring, incident response, support, privacy/data lifecycle, independent security review | Evidence of rollback, recovery, access revocation, archival/deletion |
| 5 Synthetic cohort UAT | Run full lifecycle with named authorised reviewers; defect triage, assessors compare judgements, methodology decision register | Signed UAT and calibration outcomes |
| 6 Private pilot go/no-go | Review open risks, authorised data categories and participants; obtain separate owner approval | Explicit acceptance; public/production release remains locked |

## Operational responsibilities
Project owner: charter, hosting decision, budget, participants, go/no-go. Infrastructure owner: private environment and network, access and recovery. Security/identity owner: independent verification of authentication, role lifecycle and parser boundaries. Data protection owner: permitted data, notices/consent as applicable, retention and deletion including archive/backups. Methodology owner: decision rules, cross-assessor calibration, optional model approval. Operations owner: monitoring, service recovery, incident response. Roles are accountable placeholders, not assigned individuals; owner must assign before hosting.

## Synthetic archive controls
The offline recovery module seals an entire SQLite snapshot inside an authenticated encryption envelope using a distinct vault key; metadata and evidence records are encrypted as a whole. It strips active sessions from the image. Reopening requires the correct three keys, pinned methodology, unexpired archive and database/audit/source verification. Recovered database is in memory; default scoring/model modes remain disabled. Archive writing uses a new owner-only file and refuses overwrite. Expiry refuses restore, not automatic deletion. The 30-day upper bound is a synthetic testing limit, not an approved retention policy. No key material, archive or user records are committed. Production recovery requires managed keys, versioned encrypted durable storage, backup retention/deletion, independent audit anchoring and approved RPO/RTO. Archive recovery is not connected to a hosted server.

## Calibration and UAT plan
Subject to separate approval: recruit independent assessors; blind review fictional cases and complete labelled evidence packs; record condition agreement, score distributions, evidence gaps and material contradiction decisions without forcing consensus. Reconcile against agreed anchors and review disagreements. Resolve Atlas rounding, risk/cap bands, exceptions/denominator treatment before any production scoring. Use the Aurora source-only case as an example of withholding scores, not as a validated case. No historical or real data without separate authority.

## Go/no-go
Machine-readable PILOT-GATES.json and pilot_readiness.py make local evidence vs operational acceptance explicit. No operational gate has been accepted. Report never authorises deployment. Separate owner approval is required for a specific hosted pilot environment and any real-client data.
