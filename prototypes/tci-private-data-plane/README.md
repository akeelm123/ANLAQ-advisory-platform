# ANLAQ TCI™ private evidence data plane — v0.1.0-dev.1

A local, synthetic-only reference implementation of the approved evidence handling and validation designs. **Not a production backend or deployed service.** No network listener, cloud connection, external processor, client data or executable extraction. The existing browser workbench is not yet connected to this data plane.

The Python service interface persists evidence metadata and authenticated users in a local SQLite database and encrypts synthetic document bytes using AES-GCM with independently supplied in-memory keys. Passwords use scrypt; session tokens are random, stored only as hashes, expire after 30 minutes and require live assessment membership. Each method checks membership and role; access to versions, findings and reviews is constrained to an assessment. Original source versions, dispositions, evidence associations, findings and reviews are immutable in the service model. Review acceptance checks approved criterion mappings, independent reviewer identity, class/strength, material contradiction, primary evidence and current source versions. Alternative evidence and conditional applicability workflow are conservatively blocked pending integration. A chained HMAC audit log detects changes within the local trust model; it is not an externally anchored production audit system.

Only synthetic UTF-8 .txt files up to 256 KiB are accepted. An independent assessor inspects quarantined content and records disposition; this is basic format validation and manual synthetic screening, NOT malware detection. Other document formats, malware scanning, storage provider, private network API, TLS, MFA, managed keys, key rotation, metadata encryption, retention/deletion, production backup/recovery, monitoring and operational security sign-off remain outstanding. Do not use real client data. Never put database, credentials, keys, uploaded documents or exports in the repository.

## Run synthetic regression tests

From this folder in the repository, install the declared dependency in an isolated local environment and run:

```text
python -m unittest -v test_data_plane.py
```

Tests resolve the exact approved JSON register and specification from the repository; if the directory layout differs, explicitly pass TCI_REGISTER and TCI_SPEC environment variables pointing at those artefacts. SHA-256 mismatch fails closed. A temporary database is created and removed by tests; synthetic credentials and keys are generated at runtime. No default user passwords or keys are committed. See TEST-RESULTS.txt and SECURITY-ACCEPTANCE.md.

The approved baseline is separately recorded in approval.json. No scoring, executive release, live-client processing or deployment is authorised.
