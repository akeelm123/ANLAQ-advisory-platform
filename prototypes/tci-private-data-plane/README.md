# ANLAQ TCI™ authenticated evidence workbench — v0.2.0-alpha.1

The approved v0.1.0-rc.2 synthetic candidate is recorded in RC2-APPROVAL.json. This extension implements deterministic labelled-text extraction linked to the exact approved register and validation specification. The integrated browser and backend are synthetic-only, loopback-only and not a production or hosted security implementation.

## Local demonstration

Run from this directory with Python and the declared dependency installed into an isolated environment:

```text
python serve.py
```

The launcher binds only to 127.0.0.1:8765 (or --port 0). It prints the temporary localhost URL and randomly generated synthetic credentials for each role. Never publish console credentials or submit real data. Use an assessor to raise a request, contributor to submit a fictional labelled text fixture, assessor to inspect/accept quarantine and run extraction, reviewer to preview the source and review captured fields, owner to confirm release is locked.

The schema is tied to the approved specification hash. See extraction-schema.json (28 criteria, 190 field labels) and golden-fixtures.json (28 entirely fictional labelled examples). The extractor returns exact text, source line and column, excerpt, missing or ambiguous state. Extraction results are encrypted at rest in a temporary local database, linked to an immutable accepted source version and digest, and independently reviewed. Acceptance refers to captured field accuracy only; extraction does not establish claim truth, evidence sufficiency or executive judgement. Superseding evidence invalidates the extraction state.

## Verification

```text
python -m unittest -v test_data_plane.py test_api.py test_extraction.py
node browser-smoke.cjs
```

Tests resolve the approved register and specification files in the repository. If local layout differs, use TCI_REGISTER and TCI_SPEC to point to their exact JSON files. Set TCI_PYTHON and PLAYWRIGHT_MODULE for a non-default Python or Playwright installation. Chrome is required for the browser smoke test. See EXTRACTION-ACCEPTANCE.md, TEST-RESULTS.txt, EXTRACTION-TEST-RESULTS.txt and BROWSER-RESULTS.txt.

## Limits

Only synthetic UTF-8 labelled .txt files up to 256 KiB are supported. This is not AI extraction, OCR, free-form document interpretation or proof of production security. The original field labels may contain multiple related attributes; no automatic semantic decomposition or numeric conversion. Unknown labels remain missing; conflicting values remain ambiguous. The authenticated local store has no external IdP/MFA, managed keys, TLS deployment, private cloud infrastructure, production malware screening, retention, secure exports or operational security assessment. Scope is bootstrapped for synthetic testing. No formal production release, scoring, client processing or public deployment is authorised.
