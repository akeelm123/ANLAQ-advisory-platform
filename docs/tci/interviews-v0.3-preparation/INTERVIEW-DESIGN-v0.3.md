# ANLAQ TCI™ intelligent stakeholder interviews — v0.3 preparation

26 November 2026. Preparatory design and acceptance plan only. v0.3 implementation remains gated on formal v0.2 owner acceptance; this document does not approve a production interview or live client handling.

## Objective and workflow

Frame the assessment decision, stakeholders and independent persona perspectives. Present each of the 28 approved source questions with the relevant criterion, intent, stakeholder suggestion and mapped evidence. Capture the response in the speaker's words and separately record the assessor's interpretation. A response is a claim, not documentary evidence or a performance score. Link the claim to existing evidence versions and exact locations where available. Check source reliability, completeness, applicability, gaps, contradictions and relevance; ask one targeted, neutral follow-up at a time. Record missing, declined or unknown responses explicitly. Never infer consent, ownership, benefit, score or judgment from an omitted answer.

1. **Prepare:** authorised assessment scope, intended decision, stakeholder list, roles and approved version.
2. **Ask:** choose source question naturally for assigned role; preserve original question ID and approved intent.
3. **Capture:** immutable response, responder and timestamp; keep original statement separate from interpretation.
4. **Follow up:** choose a scoped prompt from the approved validation rules and the proposed trigger set; show reason and evidence request.
5. **Triangulate:** examine mapped accepted sources and separate persona opinions; record contradiction and missing evidence.
6. **Review:** assessor drafts findings; independent reviewer accepts or returns only where evidence supports the condition. Do not substitute interview response scores for evidence.
7. **Close:** preserve unresolved items, responsible owner, follow-up and review status. No executive release or numerical score.

## Data and service contract

| Record | Required attributes |
|---|---|
| Interview session | Assessment ID, stakeholder pseudonymous ID, persona/role, scope, consent if applicable, moderator, time, approved register and validation version |
| Question turn | Session ID, question ID, approved intent, prompt text, evidence request IDs, created time |
| Response | Immutable response ID, turn ID, verbatim statement, responder role, timestamp, capture method, explicit unknown/declined state |
| Claim | Response link, criterion, draft interpretation, class/strength separately, evidence version/locator, decision relevance, materiality and uncertainty |
| Follow-up | Claim/criterion, proposed trigger, scoped question, reason, requested mapped evidence, answer state, responsible owner |
| Contradiction | Two or more immutable statements/evidence versions, conflict topic, materiality, reconciliation rationale, reviewer |
| Review | Authenticated independent reviewer, scope, decision, rationale, source versions and time |
| Audit | Append-only actor, event, record/version reference, timestamp; no raw client response in operational logs |

Owner, contributor, assessor and reviewer permissions remain separate. A model may propose one follow-up and cite the relevant criterion/claim, but has no authority to run tools, approve evidence, assign a score, schedule or contact stakeholders autonomously. Interview recording/transcription and third-party processing are out of scope until privacy, consent and processor approvals exist. No public data plane.

## Acceptance plan

The machine-readable specification contains 28 question cards, all 89 mapped relationships, 10 proposed follow-up triggers and 14 planned scenario tests. INTERVIEW-GOLDEN-FIXTURES.json supplies seven two-persona fictional interview cases, one per dimension, with expected follow-ups. Reconcile identifiers and wording with the approved register and validation specification before implementation. Test independent persona preservation, missing source, E3 assertion, contradictory claims, forecast/actual distinction, conditional applicability, declined answers, untrusted content, stale evidence, independent approval, scoring locks and private data handling.

No v0.3 functional tests have been executed yet: this is specification preparation. Review proposed follow-up behavior before implementation. No real-client interviews or automated scoring.
