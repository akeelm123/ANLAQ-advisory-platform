# Secure evidence handling checkpoint — v0.1.0-dev.1

Approved design: Secure Evidence Handling Design v1.0 RC.1. Implementation is a local service reference, not a networked or hosted system. No security release gate has been accepted. 19 synthetic regression tests passed.

| Design acceptance ID | Local implementation evidence | Remaining production work |
|---|---|---|
| SE-01 | Tests 01, 05, 11, 14 deny wrong assessment membership and records; role checks on service methods | Authenticated HTTPS API, multi-user/concurrency testing, tenant isolation at production storage layer |
| SE-02 | Tests 01, 02, 05, 15 deny unauthorised, expired or revoked access | Scoped short-lived private download mechanism, HTTP/TLS and replay tests |
| SE-03 | Tests 02, 03, 06 enforce text-only format/size, quarantine, independent manual disposition | Approved file format policy, malware scanning and controlled parser, upload intents |
| SE-04 | Tests 04, 12, 18 demonstrate digest, encrypted version bytes, immutability, superseded readiness and reopen | Managed encryption/key rotation, object storage, versioned review reassessment |
| SE-05 | Tests 07, 08, 09 reject author role and unconfirmed decisions; distinct source identities for E2 | External identity/MFA, immutable human identity across accounts and assignments |
| SE-06 | Tests 07, 16, 18 verify immutable review and HMAC-linked activity | External audit anchoring, tamper detection under privileged operator access, monitoring |
| SE-07 | Test 16 confirms no raw evidence in synthetic audit events; temporary DB only | Real-system data flow, logs/assets and redaction review; no client data in GitHub |
| SE-08 | Tests 10, 11, 13, 19 enforce approved mappings and exact spec hashes; unsupported conditional review fails closed | Isolated extraction worker, document-based golden test set, independent semantic validation |
| SE-09 | Test 18 verifies local persisted reopen integrity | Approved retention and legal hold, verified deletion, production backup and recovery |
| SE-10 | Tests 14, 15 check membership revocation and expiry; no stored plaintext session tokens | Managed identity, secret store, MFA, rotation, lockout/rate controls |
| SE-11 | Not yet tested | Hosting region/processor, incident and recovery process, policy ownership |
| SE-12 | Test 17 locks release for every role | Formal approval of implemented controls, private pilot and release decision |

The local service is synthetic-only and intentionally has no HTTP listener. Its existence does not mean that v0.1 is accepted or that a production security review has passed. Next milestone: implement scoped authenticated API and browser integration, specify approved hosting and retention decisions before real-client data, then execute the acceptance suite on an isolated pilot system. Scoring remains locked pending calibration.
