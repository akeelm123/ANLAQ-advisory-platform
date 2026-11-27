# Private pilot readiness — v0.9 candidate
2026-11-27 · Design and verification checklist, not deployment approval

## Current decision
Local fictional test environment only. No external access, persistent pilot storage, real-client records, production identity, live stakeholders or cloud deployment approved. The loopback demo uses an ephemeral SQLite database, generated per-run credentials and encryption keys, scoped roles and append-only records. These controls are prototype evidence, not a production security assurance.

| Gate | Required evidence before private pilot | Status |
|---|---|---|
| Pilot scope / authority | Named pilot sponsor, permitted input classes, participants, boundaries, separate written approval | Open |
| Hosting / network | Owner-approved private hosting architecture, authenticated access, no public exposure, environment isolation | Open |
| Identity / access | Production identity provider, MFA, membership provisioning/revocation, least privilege, distinct reviewer and owner roles | Open |
| Tenant isolation | Independently reviewed storage and access boundaries, negative authorization tests, isolation evidence | Local synthetic controls only |
| Documents | Approved formats, malware scanning/quarantine, safe parsing, size limits, source retention and deletion policy | Bounded local parser only |
| Encryption and secrets | Managed encryption keys, rotation, access separation, secret store, backup encryption and restore tests | Ephemeral keys only |
| Audit | Durable tamper-evident audit store, access monitoring, retention, incident response and recovery exercise | Local hash-linked audit only |
| Privacy / consent | Approved lawful handling, data minimisation, stakeholder notices/consent where required, redaction and retention, data export/deletion procedures | Open |
| Models | Approved processing location and model access, no unapproved external payloads, model reliability and human review evidence | Local opt-in previous synthetic benchmarks only |
| Calibration | Cross-assessor labelled cases, historical/real-data approval separately, scoring thresholds/rounding/N/A decisions and independent review | Open |
| Reliability | Backup/restore, disaster recovery, monitoring, performance and release rollback | Open |
| UAT | Named authorised synthetic/pilot cohort, scenarios, defects, acceptance evidence and go/no-go record | Synthetic integration tests only |
| Production | Separate owner go-live approval, security/privacy and operational sign-off, no public deployment without explicit approval | Locked |

The original methodology workbooks remain local; GitHub is authoritative for the versioned software, source hashes, mapping, test results and release records. Do not upload client records, credentials or private pilot data to the public repository. No infrastructure resource was created or deployed.
