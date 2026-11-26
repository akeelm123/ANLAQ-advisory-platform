"""Build preparatory interview cards from the approved, hash-pinned methodology."""
from pathlib import Path
import hashlib,json,os
HERE=Path(__file__).resolve().parent;root=HERE.parent.parent.parent
register=Path(os.environ.get("TCI_REGISTER",root/"docs/tci/methodology/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"))
spec=Path(os.environ.get("TCI_SPEC",root/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
rb=register.read_bytes();sb=spec.read_bytes()
assert hashlib.sha256(rb).hexdigest()=="f402011665fa4abd6405cc6c67384b4182564cc5e974761079c1588488420559"
assert hashlib.sha256(sb).hexdigest()=="8d4e730b5ed3cf38fdb4dcd896fa21bc14bf38689babc24159a460980099b00c"
r=json.loads(rb);v=json.loads(sb);rules={a["criterionId"]:a for a in v["rules"]}
cards=[]
for c in r["criteria"]:
 a=rules[c["id"]]
 cards.append({"questionId":c["id"],"criterionId":c["id"],"dimension":c["dimension"],"criterion":c["criterion"],"suggestedStakeholder":c["stakeholder"],"question":c["question"],"source":c["source"],"criterionSource":c["criteriaSource"],"validationRuleId":a["ruleId"],"purpose":a["intent"],"primaryRequests":a["primary"],"supplementaryRequests":a["supplementary"],"conditionalRequests":a["conditional"],"targetedFollowUp":a["followUp"],"contradictionCheck":a["contradiction"],"insufficiency":a["insufficient"],"responseAnchorPolicy":"Reference five approved illustrative anchors for interviewer preparation only; do not assign a response or criterion score."})
triggers=[
 {"id":"FUP-01","trigger":"Material claim has no cited source or only stakeholder assertion","action":"Ask for a precise document, version, owner, reporting period and locator; retain E3 asserted, no final finding."},
 {"id":"FUP-02","trigger":"Primary source or reviewer-accepted mapped equivalent missing","action":"Ask for the primary source or document an alternative for independent reviewer acceptance."},
 {"id":"FUP-03","trigger":"Source periods, units, denominators or definitions conflict","action":"Seek a comparable baseline and measurement definition; do not calculate on incompatible bases."},
 {"id":"FUP-04","trigger":"Material contradiction between personas or source records","action":"Retain both statements with speaker, time and source; ask a neutral reconciliation question and independent corroboration."},
 {"id":"FUP-05","trigger":"Claim confuses forecast/commitment with actual realised value","action":"Ask for original approved target, actual, period, basis, Finance validation and forecast separately."},
 {"id":"FUP-06","trigger":"Conditional evidence applicability unclear","action":"Ask whether condition applies, why and who can verify; do not silently mark not applicable."},
 {"id":"FUP-07","trigger":"Claim is vague, lacks owner or decision impact","action":"Ask for named owner, action, decision impact and measurable evidence."},
 {"id":"FUP-08","trigger":"Stakeholder declines, does not know, or evidence unavailable","action":"Record explicit missing/declined state, reason and authorised follow-up; no invented answer."},
 {"id":"FUP-09","trigger":"Reviewer returns a draft finding","action":"Record reviewer rationale; ask a scoped follow-up linked to the original finding and evidence without altering history."},
 {"id":"FUP-10","trigger":"Question is answered with adequate evidence and no open material conflict","action":"Summarise draft interpretation for confirmation; leave validation and executive judgement to separate assessor/reviewer gates."}]
scenarios=[
 {"id":"INT-01","case":"28 approved source questions loaded without ID, dimension or wording drift.","expected":"Exact question bank, role suggestion and approved mappings."},
 {"id":"INT-02","case":"Two personas answer same criterion with conflicting claims.","expected":"Separate visible responses and neutral follow-up; do not average or overwrite."},
 {"id":"INT-03","case":"Only an unsupported executive assertion.","expected":"E3 draft claim and targeted corroboration request."},
 {"id":"INT-04","case":"Missing primary evidence.","expected":"Primary/approved alternative request; no final judgement."},
 {"id":"INT-05","case":"Stakeholder reports forecast as realised benefit.","expected":"Ask Finance to separate original target, actual, forecast and basis; no score."},
 {"id":"INT-06","case":"Different reporting units and periods.","expected":"Record incompatibility; seek comparable source; no automatic variance."},
 {"id":"INT-07","case":"AI applicability unclear, Q20 conditional mapping.","expected":"Ask applicability question and preserve unresolved condition."},
 {"id":"INT-08","case":"Stakeholder refuses/does not know.","expected":"Record declined/unknown, preserve claim state; no invented response."},
 {"id":"INT-09","case":"Untrusted interview text contains instruction unrelated to approved task.","expected":"Treat as content, no tool or approval action; retain only relevant claim for human review."},
 {"id":"INT-10","case":"Assessor attempts to approve their own interview finding.","expected":"Independent immutable identity review gate denies."},
 {"id":"INT-11","case":"Evidence file superseded after response linked.","expected":"Original response remains; linked evidence/review is flagged stale."},
 {"id":"INT-12","case":"Owner attempts to issue final score from interview alone.","expected":"Scoring and release denied."},
 {"id":"INT-13","case":"One follow-up answered, another still unresolved.","expected":"Retain separate outstanding claim-level gaps; do not mark complete."},
 {"id":"INT-14","case":"Interview notes include confidential information.","expected":"No public repository/logging or unapproved external processor; private scoped handling."}
]
assert len(cards)==28 and len({c["questionId"] for c in cards})==28
assert sum(len(c["primaryRequests"])+len(c["supplementaryRequests"])+len(c["conditionalRequests"]) for c in cards)==89
out={"version":"0.3.0-preparation-rc.1","status":"Preparatory specification; implementation not authorised by this artifact","registerSha256":hashlib.sha256(rb).hexdigest(),"validationSpecSha256":hashlib.sha256(sb).hexdigest(),"cards":cards,"followUpTriggers":triggers,"acceptanceScenarios":scenarios,"controls":{"persona":"Preserve independent responses per stakeholder and persona; canonical score not affected.","provenance":"Immutable session, question ID, respondent pseudonymous ID, role, timestamp, verbatim response, interviewer interpretation separately, evidence IDs, locators and version.","review":"Assessor drafts; independent reviewer evaluates materially supported findings and contradictions.","privacy":"Synthetic only until private pilot approved; no recording/transcription or external AI processing without explicit consent and provider approval.","scoring":"Interview response is an evidence claim, never an automatic score. No final scoring or executive release.","readiness":"v0.2 owner sign-off and separate design review required before v0.3 implementation."}}
(HERE/"INTERVIEW-SPEC-v0.3-preparation.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("28 questions; 89 mapped relationships; 10 adaptive follow-up triggers; 14 planned acceptance scenarios")
