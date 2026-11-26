# Model-assisted narrative extraction — v0.2.0-alpha.3

26 November 2026 · Synthetic review candidate only.

## Actual local-model benchmark

Model: existing local Ollama gpt-oss:20b; exact model digest recorded per result in NARRATIVE-BENCHMARK.json. Four fictional narrative reports; no external processor or real client data. Model output is constrained to field key, source segment ID and verbatim quote. The deterministic verifier rejects fabricated, repeated/unlocatable or incorrectly located quotes, unrecognised fields and malformed output. Captured values are candidate passages, not verified business facts or evidence sufficiency.

| Fixture | Expected field matches | Observation |
|---|---:|---|
| INV-01 fictional investment paper / Q02 | 7/7 | All expected field phrases matched |
| GOV-01 fictional governance minutes / Q05 | 6/7 | Materiality omitted |
| BEN-01 fictional benefits report / Q26 | 8/9 | Currency/unit missing; one proposal rejected by quote verifier |
| BEN-02 incomplete fictional benefits report / Q26 | 2/3 | Separate forecast omitted; actual realised outcome, original target, underlying source and benefit basis correctly unresolved |
| Total | 23/26 | 88.5% expected field-phrase matches on this small benchmark only |

The incomplete report's SGD 9000 forecast was not promoted to realised value. Expected missing fields remained missing in this case. This is not an accuracy estimate for unstructured business documents at large. Exact substrings do not establish correct field attribution, completeness, truth or materiality. The three omissions remain defects for refinement. The benchmark uses three criterion IDs, not semantic coverage across all 28.

## Control acceptance

| Requirement | Evidence | Result |
|---|---|---|
| Local model opt-in, no external fallback | Fixed localhost service; default disabled; existing model queried without download | Implemented |
| Exact citation verification | Reject absent/incorrect/ambiguous spans; preserve original source location and columns | Unit tests pass |
| Model provenance | Record model and digest, method version, encrypted draft result and source digest | Actual benchmark + service replay test |
| Missing, rejected and conflicting proposals | Explicit unresolved status; acceptance blocked pending correction | Unit tests pass |
| Human review | Reviewer must preview source, confirm field meaning/context and record rationale | In-process replay test passes |
| Full regression | 171 in-process service, extraction and parser tests pass | Pass |
| Fresh API/browser regression | Loopback permission review timed out; not executed for alpha.3 | Outstanding |
| Semantic quality acceptance | 23/26 expected fields on four fictional reports; expand independent goldens and improve omissions | Outstanding |
| Production security and client-data processing | Local synthetic only; no real data or hosting selection | Outstanding |

The previous alpha.2 browser result is preserved in commit 2120b7a62294956cceb13272fc03332ff6102d20 and is not evidence of current alpha.3 browser behaviour. No automatic scoring, judgement or release.
