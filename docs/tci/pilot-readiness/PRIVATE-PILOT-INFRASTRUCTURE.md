# ANLAQ TCI™ private pilot infrastructure preparation

26 November 2026 · Design and configuration readiness package. No cloud resources have been purchased, provisioned or deployed. No provider, region, processor, retention period or real-client processing is assumed approved.

## Scope and logical deployment

The pilot data plane is separate from the public repository and GitHub Pages programme dashboard. Source code and synthetic test assets may be versioned in GitHub; client records, document content, keys, credentials, operational logs and exports must never be placed there.

| Layer | Required component | Provisioning deliverable |
|---|---|---|
| Entry | Private authenticated ingress, HTTPS, no public document endpoint | Private application endpoint; access policy and certificate configuration |
| Identity | Managed named identities, MFA, assessment membership and immutable identity | IdP configuration; contributor, assessor, reviewer and owner role assignments |
| API | Production service implementation; server-side tenant/record authorisation | Private runtime and tested scoped API |
| Data | Managed transactional metadata store and private versioned object store | Tenant isolation, encryption, private connectivity, backup and restore |
| Key management | Managed secrets and key service, rotation, least privilege | Workload identity and key policy; no credentials in repo |
| Intake | Quarantine storage, supported-format allowlist, malware screening, isolated parser | Technical scan evidence and human screening workflow |
| Extraction | Isolated worker processing only accepted mapped evidence; approved model processor | Scoped queue/worker identity, no unrestricted outbound access |
| Audit | Tamper-evident server events, independent access, monitoring | External audit anchor, retention, alerting and incident evidence |
| Release | Explicit owner approval, redacted scoped export and reversible release process | UAT, security assessment and signed go/no-go |

The current synthetic localhost reference service is not a production runtime. Its ephemeral credentials, local SQLite store, in-memory keys, loopback HTTP and manual screening must not be reused for real-client use.

## Decision packet — owner approval required before implementation involving client data

| Decision | Required outcome | Current state |
|---|---|---|
| Hosting provider and region | Approve private host, residency, contractual/privacy requirements and permitted subprocessors | Outstanding |
| Identity | Approve identity provider, MFA, invitation/provisioning, reviewer segregation and revocation | Outstanding |
| Storage and key management | Approve database/object services, key custody and backup/recovery policy | Outstanding |
| Document processing | Approve file types, malware screening, isolated parser and approved model/processor | Outstanding |
| Data retention | Approve retention duration by record type, legal hold, deletion verification and exit handling | Outstanding |
| Client pilot scope | Approve named authorised pilot, data classification, data use and contract/privacy review | Outstanding |
| Operational responsibility | Assign incident owner, independent security reviewer, support and recovery responsibility | Outstanding |
| Final release | Owner accepts actual SE-01–12 evidence independently; no decision inferred from this document | Outstanding |

If Singapore is the preferred data residency, record that explicitly, including storage, backup and processor location; it is not inferred from the project owner's timezone. Provider and region choice precede provisioning, not vice versa.

## Phased implementation

1. **Prepare:** review the provider-neutral configuration, choose region/identity/storage/processor and responsibilities; retain explicit approval evidence. No resources created.
2. **Isolated synthetic environment:** provision private network and managed services only after authorisation; verify identity, isolation, encryption and secret management. Seed synthetic data only.
3. **Security acceptance:** execute SE-01–12 from the approved Secure Evidence Handling Design; retain evidence in a non-public controlled location. Independent reviewer assesses tenant isolation, document screening, audit integrity, retention, deletion, restore and operational response.
4. **Pilot readiness:** owner confirms processor and data handling terms, allowed evidence, access, revocation, support, rollback and explicit real-client pilot decision. No automated scoring without separate calibration.
5. **Controlled pilot:** run authorised data in the private environment only, with human review and no public endpoint or export beyond authorised audience.

## Readiness checks

Run `python pilot_preflight.py`. The example manifest deliberately contains unresolved decisions; it must report blocked. Record decision references and reviewed SE-01–12 evidence, not keys, client files or confidential content. The preflight is a completeness checker only, cannot verify external approval claims, and cannot enable deployment, client data or scoring. Even a complete synthetic configuration yields ready for formal review, not release.

Current result: 38 unresolved decision/evidence controls; 6 preflight unit tests passed. This is a readiness work package, not provisioned infrastructure.
