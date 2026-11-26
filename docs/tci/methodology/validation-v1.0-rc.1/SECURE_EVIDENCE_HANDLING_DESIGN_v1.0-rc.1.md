# Secure evidence handling design — v1.0 RC.1
Transformation Confidence Index™ by ANLAQ · 26 November 2026

**Design candidate, not implemented or approved.** The current browser workbench is synthetic-only: local digest capture, self-declared identities and downloadable snapshots are not a secure client document system. This design is a prerequisite to formal v0.1 acceptance and any real-client use. No hosting service, client-data jurisdiction, vendor, retention period or deployment has been authorised.

## 1. Design boundaries

Separate the public GitHub source/methodology repository and programme dashboard from the private client assessment data plane. Never commit assessment files, client records, credentials, logs containing client information or exported assessment snapshots into GitHub. Use a private authenticated application and isolated storage. No public URL for evidence. Do not expose a document to an AI service or external processor without client/ANLAQ approval, agreed retention and approved processing arrangements. Before pilot, record hosting region, contractual and privacy requirements, data classification, consent, provider and deletion/retention policy. No hard-coded claims of compliance.

## 2. Logical architecture

| Layer | Design requirement |
|---|---|
| Access | Authenticated named identity and MFA where supported. Server-enforced tenant and assessment membership. Separate assessor, reviewer and release approver permissions. |
| API | All reads, writes, downloads and approvals checked server-side against tenant, assessment, record and permitted role. Deny by default. No unauthenticated object-store URLs. |
| Evidence upload | Short-lived scoped upload intent, size/type policy, private quarantine, integrity digest on server, malware/content safety screening, controlled extraction, human disposition. Treat all embedded document text as untrusted material. |
| Document store | Private encrypted object storage, per-tenant logical isolation, immutable source versions, controlled short-lived access, no raw evidence in public assets or application logs. |
| Metadata store | Tenant-scoped records with transactional associations; enforce record ownership and unique IDs; version approved methodology and evaluation schemas. |
| Validation worker | Isolated read-only view of approved evidence, least-privilege identity, constrained jobs, no free access to repositories or external services. Record extraction version and exact source locator; human verify material results. |
| Review and audit | Append-only server-generated review events with authenticated actor, time, version, rationale, status and evidence references. Separate integrity protection and access controls; no overwrite of historical decisions. |
| Export | Tenant-scoped exports with explicit role and release authorisation; redact/minimise by default. Record creation and download. |
| Lifecycle | Approved retention policy, legal-hold workflow, access removal, verified deletion of source and derived data, backup and restore tests. |

## 3. Roles and segregation of duties

| Role | Permitted activity | Not permitted |
|---|---|---|
| Client evidence contributor | Submit approved files within assigned assessment; view own authorised submissions | Browse other tenants, edit findings or approve review |
| Assessor | Define scope; request evidence; inspect authorised sources; draft findings | Approve own finding; publish executive assessment |
| Independent reviewer | Verify provenance, relevance, class, strength, contradictions and adequacy; accept/return assigned finding | Change original evidence or silently alter prior decisions |
| Assessment owner | Approve methodology version, scope and exceptions; accept formal release when entitled | Bypass independent evidence review, scoring calibration or privacy gates |
| System operator | Administer infrastructure and access policy; auditable emergency access if authorised | Routine content access without explicit scoped reason; alter findings or approvals |
| Extraction service | Read only explicitly allocated, screened evidence; write versioned draft extraction output | Approve findings, modify source or release results |

Explicit rule: a user cannot self-review regardless of display-name changes. Compare immutable identity IDs, not names. Verify membership on every operation; role changes are audited.

## 4. Core records and lifecycle

Required IDs: tenant, assessment, user membership, source document, immutable document version, evidence excerpt, criterion, mapping relationship, finding revision, validation decision, review decision, approval event and export. Every evidence link refers to one immutable document version and precise locator. Classification, strength, materiality, contradiction, condition and scoring eligibility are independent fields. Preserve the assigned approved register commit and validation version in every assessment. Use optimistic concurrency or transaction constraints; append corrected versions rather than overwrite history.

Workflow: scoped upload requested → received to quarantine → technical checks → accepted/rejected with rationale → authorised extraction → assessor evidence linkage → independent review returned/accepted → approval gate → authorised export. Rejected data stays inaccessible outside controlled quarantine until disposition. Source digest does not establish authenticity. Replacing a file creates a new document version; invalidate affected draft/review readiness and require reassessment. No automated decision on material evidence without a human.

## 5. Data protection and release boundaries

- Encrypted transit and storage, managed key rotation and secrets management; no credentials in repository or browser.
- Minimise document and extraction content; explicitly tag sensitive information; avoid unnecessary personal data in logs, analytics, support and exported results.
- Privacy review before selection of region and processor. Agree appropriate contractual safeguards, retention/deletion commitments and incident response responsibilities.
- Separate developer/test/production environments with synthetic test data. Company/client records require a dedicated authorised pilot environment.
- Review dependencies and file-processing controls; restrict formats and size; sandbox document parsing; reject active content or quarantine until specialist review.
- Operational monitoring records relevant access and anomalies, protects logs, and alerts designated staff; validate backup access, restore integrity and retention.
- No public deployment of the assessment platform without separate written approval. Formal v0.1 release does not authorise scoring or final executive judgement.

## 6. Acceptance test plan (not executed)

| ID | Acceptance requirement | Evidence expected |
|---|---|---|
| SE-01 | Authenticated users cannot read or write outside authorised tenant/assessment | Positive and negative server permission tests; membership change and revocation |
| SE-02 | Unauthorised download denied; expired link cannot provide file access | Scoped download tests and access logs |
| SE-03 | Document upload controlled by explicit intent, allowed format, size, quarantine and screening | Synthetic accepted/rejected file cases; no real data |
| SE-04 | Original bytes immutable; new version retains unique digest and traceability | Integrity/version tests and invalidation of stale findings |
| SE-05 | Self-review rejected by immutable identity, including alternate display names | Role separation test and review audit event |
| SE-06 | Every approval tied to actor, time, version and rationale, with no silent mutation | Record integrity test, event history review |
| SE-07 | Client data absent from public assets, telemetry, repository and unauthorised exports | Data-flow review; documented sample log/asset inspection |
| SE-08 | Extraction operates only on accepted, allocated records; outputs remain draft | Worker permission/isolation and prompt-content handling tests |
| SE-09 | Retention/deletion and legal holds enforced; verified backup/restore process | Dry-run retention scenarios and restoration integrity evidence |
| SE-10 | Credentials securely held; revoked role/session loses access | Configuration review and session revocation tests |
| SE-11 | Incident and recovery process tested; policy owners and region documented | Incident tabletop, recovery test, approved governance record |
| SE-12 | Owner reviews test evidence and authorises real-client pilot and v0.1 release separately | Signed, versioned release decision |

## 7. Approval decisions required

Confirm design boundaries, responsible roles, approved hosting and processor, data residency, permitted document kinds, retention and deletion policy, risk acceptance and pilot scope. Then implement the private data plane; execute the security acceptance tests with synthetic data; obtain independent review and owner release acceptance. This design alone is not evidence that the controls exist.
