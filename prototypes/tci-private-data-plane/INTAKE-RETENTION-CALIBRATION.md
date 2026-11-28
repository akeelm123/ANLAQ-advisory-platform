# Local synthetic assurance — v0.9.4-alpha.1
2026-11-28 · Candidate. FileVault assurance deferred for fictional-only local testing by owner; real-data and production restrictions unchanged.

## Intake assurance
Persistent local mode now executes document parsing in a child process with a wall timeout, CPU limit, bounded input and parsed output; exact TXT/PDF/DOCX/XLSX citations preserved. The child runs as the same OS user; it is not an OS-denied-network sandbox, privilege isolation or malware detector. The root local synthetic app still uses manual independent screening. Format-only intake records are clearly not scanned.

Optional strict mode requires an installed trusted ClamAV clamscan executable, successful local scanner invocation and explicit clean result before storing an uploaded source. Detected, unavailable or invalid results refuse storage; refused attempts keep digest/status only, not source bytes. A strict acceptance requires an immutable clean ledger entry for that exact source version/digest; older unscanned quarantined sources cannot be accepted under strict mode. Older already-accepted synthetic sources are not automatically rescanned or invalidated; an operational transition requires separate re-ingestion policy. The official local scanner is not installed on the current environment; no scanner was installed, downloaded or enabled. Adapter result handling is tested using simulated clean/detected/unavailable states, not actual malware or validated signature freshness. The strict option is explicit and fail-closed, not default for fictional UAT. Before operational approval independently install/verify trusted scanner, signature updates and policy and use an approved OS isolation boundary.

Start persistent synthetic mode normally with start-local-pilot.command. For a scanner-equipped environment only, invoke local_pilot.py with --confirm-synthetic --require-malware-scan and pinned methodology paths. If scanner unavailable, uploads are refused. Section 04a shows policy, scanner presence, clean-scan records and refused attempts; no automatic acceptance.

## Retention
The existing rolling synthetic archive expiry limit remains a test cap only. New retention_review.py accepts explicit archive paths, original salt and prompted original passphrase; it authenticates archive metadata, reports creation/expiry and whether restore is blocked without opening the database or modifying files. Wrong key, methodology or invalid archives refuse inventory. Example:
```sh
python retention_review.py --confirm-synthetic --salt "/approved/local/salt.bin" --archive "/approved/offline/backup.tci"
```
Keep results private. No automatic deletion, erasure, legal hold or approved retention policy. Expiry blocks restore, not retention deletion. Actual deletion of assessment rows, backup and copies needs approved lifecycle and explicit authorisation; no deletion routine provided.

## Independent assessor calibration
CALIBRATION-BLIND-TEMPLATE.json uses the exact seven-source UAT fixture manifest. Two distinct human assessors each copy the blank template to a private location, independently inspect the same mock sources, enter their pseudonym, condition, evidence class, strength, precise citation references and rationale for all seven criteria. Do not share judgements before completing both. Permitted conditions: supported_met, supported_not_met, insufficient, contradiction, exception_pending; E1–E4; Strong / Moderate / Weak / Not assessed. Supported condition requires E1/E2 and citations. Run:
```sh
python calibration_review.py "/private/assessor-a.json" "/private/assessor-b.json"
```
Exact agreement counts and differences support a human reconciliation session. Citation string agreement is not proof of semantic equivalence and different citations may both be valid. No ratings are fabricated, averaged or approved; output must stay private. No completed independent assessments received. Production scoring and thresholds remain separately locked. This is not formal semantic or statistical reliability calibration.
