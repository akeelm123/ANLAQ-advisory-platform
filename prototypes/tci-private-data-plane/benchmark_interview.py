"""Run local wording proposals on seven explicitly fictional planned interview cases."""
import json,os,time
from pathlib import Path
from interview_ai import propose
from narrative import NarrativeUnavailable
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
S=Path(os.environ.get("TCI_INTERVIEW_SPEC",ROOT/"docs/tci/interviews-v0.3-preparation/INTERVIEW-SPEC-v0.3-preparation.json"))
F=Path(os.environ.get("TCI_INTERVIEW_FIXTURES",ROOT/"docs/tci/interviews-v0.3-preparation/INTERVIEW-GOLDEN-FIXTURES.json"))
spec=json.loads(S.read_text());cards={x["questionId"]:x for x in spec["cards"]};triggers={x["id"]:x for x in spec["followUpTriggers"]};rows=[]
for case in json.loads(F.read_text())["fixtures"]:
 c=cards[case["criterionId"]];t="FUP-05" if "FUP-05" in case["expectedFollowUpTriggers"] else "FUP-04" if "FUP-04" in case["expectedFollowUpTriggers"] else case["expectedFollowUpTriggers"][0]
 response=case["responses"][0]["verbatimSyntheticResponse"]
 try:
  start=time.monotonic();r=propose(response,t,triggers[t]["trigger"],c["targetedFollowUp"],case["requestIds"]);row={"id":case["id"],"criterionId":case["criterionId"],"status":"executed","triggerId":t,"durationSeconds":round(time.monotonic()-start,2),"result":r,"humanSemanticReview":"pending; no automatic follow-up recorded"}
 except NarrativeUnavailable as e:row={"id":case["id"],"status":"blocked","reason":str(e)}
 rows.append(row);print(case["id"],row["status"],row.get("durationSeconds","-"),flush=True)
 (HERE/"INTERVIEW-AI-BENCHMARK.json").write_text(json.dumps({"scope":"Seven fictional local model wording proposals; exact quote verification only, human quality review required","rows":rows},indent=2,ensure_ascii=False)+"\n")
