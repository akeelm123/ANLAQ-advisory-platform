# ANLAQ TCI™ private evidence workbench — 0.1.0-alpha

Open index.html using a local browser. If file hashing is unavailable on your browser's file protocol, run from this directory: python3 -m http.server 8765 --bind 127.0.0.1 then open http://127.0.0.1:8765. No external dependencies or network calls. Synthetic materials only.

Select a provisional criterion, capture a synthetic file and its provenance, draft an evidence-linked finding, then record a different named reviewer's decision. Download the JSON snapshot before closing the browser. The session is not persisted and snapshots are not reloadable. It is not a secure document store, actual evidence extraction engine, authenticated approval system or tamper-proof audit log. The file itself is not retained; only metadata and digest. Evidence classes are assessor-entered, not machine-validated. No score or final judgement can be issued.

Run node --test core.test.cjs. See TEST-RESULTS.txt, sources.json (seven locally located file hashes and 28 provisional response-bank criterion references), VALIDATION_SPEC_DRAFT.md and RELEASE_PLAN.md.

The existing public website executive diagnostic prototype was inspected and left intact. This version is maintained on the prototyping branch as directed by the project owner. Do not merge or deploy without release approval. GitHub Pages publishes only the programme dashboard from main. Never enter client data into this alpha. The actual approved register file and approved validation specification are not located.

Synthetic browser smoke test also passed in Chrome (see TEST-RESULTS.txt).
