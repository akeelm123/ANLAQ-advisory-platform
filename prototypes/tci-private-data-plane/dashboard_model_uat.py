"""Opt-in actual local model UAT with existing fictional narrative fixtures only."""
import json,time
from pathlib import Path
from serve import REGISTER,SPEC,HERE
from dashboard_logic import DashboardAssessment
from simple_ai import propose,prepare
def main():
    a=DashboardAssessment(json.loads(REGISTER.read_text()),json.loads(SPEC.read_text()))
    fixture=json.loads((HERE/"narrative-fixtures.json").read_text())["fixtures"]
    seen=set()
    for f in fixture:
        q=f["criterionId"]
        if q in seen:continue
        seen.add(q);a.add(f["filename"],f["text"].encode(),f["requestId"])
    assert len(seen)==28
    interviews={q:"Fictional stakeholder response: please assess on the supplied documentary record; no extra corroboration is provided in this response." for q in seen}
    rows=[]
    for d in a.weights:
        started=time.monotonic();items=prepare(a,d,interviews)
        try:
            r=propose(a,d,interviews);a.record_proposals(r["candidates"],interviews)
            row={"dimension":d,"eligible":len(items),"returned":sum(c["status"]!="model_unavailable" for c in r["candidates"].values()),"unavailable":sum(c["status"]=="model_unavailable" for c in r["candidates"].values()),"anchors":sum(c["score"] is not None for c in r["candidates"].values()),"withheld":sum(c["status"]=="model_withheld" for c in r["candidates"].values()),"conflictReview":sum(c["status"]=="conflict_review_required" for c in r["candidates"].values()),"durationSeconds":round(time.monotonic()-started,2),"status":"structured response validated"}
        except Exception as e:
            row={"dimension":d,"eligible":len(items),"returned":0,"anchors":0,"withheld":0,"durationSeconds":round(time.monotonic()-started,2),"status":"failed: "+type(e).__name__}
        rows.append(row);print(json.dumps(row),flush=True)
    r=a.calculate({},interviews)
    result={"scope":"Existing fictional narrative fixtures; structural local-model UAT only, not semantic accuracy or calibration","inputCriteria":len(seen),"files":len(a.files),"dimensions":rows,"candidateCriteria":r["proposedCriteria"],"candidateScoreCalculated":r["unreviewedModelScore"] is not None,"reviewed":r["reviewed"],"productionLocked":r["productionLocked"],"actions":len(r["actionPlan"])}
    print(json.dumps(result,indent=2),flush=True)
    (HERE/"DASHBOARD-MODEL-UAT.json").write_text(json.dumps(result,indent=2)+"\n")
    assert r["productionLocked"] and r["reviewed"]==0 and r["draftScore"] is None
    if any(x["status"].startswith("failed") for x in rows):raise SystemExit(1)
if __name__=="__main__":main()
