# ANLAQ TCI™ authenticated evidence workbench — v0.1.0-rc.2

Integrated local synthetic release candidate. The browser now uses a loopback-only authenticated API calling the tested evidence data plane. The approved register and validation specification are pinned by SHA-256. No cloud service, client data, external processor, live scoring or public deployment.

## Local formative review

Run from this directory with Python and the requirement installed in an isolated environment:

```text
python serve.py
```

The launcher binds only to 127.0.0.1:8765 (use --port 0 to allocate a free port). It prints the localhost URL and randomly generated temporary credentials for contributor, assessor, reviewer, owner and separate synthetic tenant. Use the printed URL and roles to test the workflow. Never reuse these accounts, enter real evidence or publish the console output. The browser stores the bearer token in memory only; sign-out revokes it and clears assessment data from the DOM. The service uses a temporary synthetic database; graceful shutdown removes it. Keys are per-run and not persisted. A server restart begins a new synthetic session.

Review flow: sign in as assessor, raise a request, sign out; contributor selects an approved criterion/request, enters provenance and uploads a UTF-8 synthetic .txt source; assessor inspects quarantine and records disposition, then drafts a finding linked to an accepted source version; independent reviewer previews evidence and records a review; owner sees the result but release remains locked. Source receipt is not evidence sufficiency.

## Reproduce verification

```text
python -m unittest -v test_data_plane.py test_api.py
node browser-smoke.cjs
```

Use Playwright and Chrome for the browser test. If the repo directory structure differs, set TCI_REGISTER and TCI_SPEC to the exact approved JSON files; TCI_PYTHON can select the Python runtime and PLAYWRIGHT_MODULE can select the installed Playwright module. The tests spawn a transient localhost service with randomly generated credentials and no real data.

23 service/API tests and the four-role browser workflow passed. Review TEST-RESULTS.txt, BROWSER-RESULTS.txt and SECURITY-ACCEPTANCE.md. The earlier workbench remains a separate local-only illustrative client; this integrated candidate is here in the data-plane directory.

## Production limitations

This is not production security acceptance. HTTP is loopback only; no external IdP/MFA, HTTPS deployment, managed secret store, multi-tenant cloud storage, malware scanning, production retention/deletion, backup/recovery, external audit anchoring or secure export. Scope is bootstrapped for the synthetic session; real assessment provisioning is not implemented. Only synthetic text up to 256 KiB is accepted. Manual screening is not malware scanning. Alternative evidence and conditional applicability acceptance are still conservatively blocked. Semantic evidence extraction and actual-document validation remain separate work. No formal v0.1 release, real-client processing, scoring, executive output or deployment is authorised.
