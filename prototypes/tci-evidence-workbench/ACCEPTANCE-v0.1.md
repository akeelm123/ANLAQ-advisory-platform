# Evidence collection acceptance — v0.1.0-rc.1

26 November 2026. Register approved, release candidate not accepted for production.

| Control | Result | Evidence |
|---|---|---|
| EC-01 Scope and immutable decision boundary | Pass | Automated + browser |
| EC-02 Exact approved register projection | Pass: 28 criteria, 32 catalogue items, 89 mappings | approval.json, sources.json, requests.json |
| EC-03 Requested / missing / recorded status; no false receipt | Pass | Automated + browser |
| EC-04 Source provenance and digest | Pass, synthetic | Automated + browser |
| EC-05 Mapped criterion relationships, including approved cross-dimension records | Pass | Automated; approved mapping tests |
| EC-06 Class and strength distinct, contradictions and reviewer gates | Pass, structural only | Automated + browser |
| EC-07 Versioned export and replay, reject older / invalid baseline | Pass | Automated + browser |
| EC-08 No numerical scoring or executive release | Pass | Automated |
| EC-09 Register reapproval recorded against exact commit and hashes | Pass | approval.json |
| EC-10 Secure storage, authenticated roles, retention and audit integrity | Outstanding | Security design and review |
| EC-11 Formal v0.1 acceptance | Pending | Release owner sign-off |

23 automated controls and synthetic Chrome workflow pass. This is a formative review candidate only. Approved register mappings are now the collection baseline, not a final validation engine. No real client inputs; no scoring, executive outputs or public deployment. Next gate: secure handling requirements and formal v0.1 acceptance; separate criterion-level validation specification review before v0.4.
