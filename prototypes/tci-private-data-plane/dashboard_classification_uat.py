"""Fictional category identification benchmark. Expected request IDs are fixture metadata, never input text."""
import json
from serve import REGISTER,SPEC,HERE
from dashboard_logic import DashboardAssessment
from dashboard_classification import suggest_categories
def main():
    assessment=DashboardAssessment(json.loads(REGISTER.read_text()),json.loads(SPEC.read_text()))
    reports=[]
    for name in ("narrative-fixtures.json","golden-fixtures.json"):
        fixtures=json.loads((HERE/name).read_text())["fixtures"];seen=set();rows=[]
        for f in fixtures:
            q=f["criterionId"]
            if q in seen:continue
            seen.add(q)
            # Exact fixture text, no filenames or expected request tags supplied to classifier.
            segments=[{"location":f"Text line {i}","text":t} for i,t in enumerate(f["text"].splitlines(),1) if t]
            out=suggest_categories(assessment.catalogue,segments,assessment.category_index);ids=[x["id"] for x in out]
            rows.append({"criterion":q,"expected":f["requestId"],"suggestions":ids,"top1":bool(ids and ids[0]==f["requestId"]),"top3":f["requestId"] in ids})
        reports.append({"fixture":name,"count":len(rows),"top1":sum(x["top1"] for x in rows),"top3":sum(x["top3"] for x in rows),"rows":rows})
    result={"scope":"Fictional labelled source category benchmark; development narrative and labelled golden fixtures, not real-world classification accuracy or validation.","reports":reports}
    (HERE/"V098-CLASSIFICATION-UAT.json").write_text(json.dumps(result,indent=2)+"\n")
    for r in reports:print(r["fixture"],r["count"],"top1",r["top1"],"top3",r["top3"])
if __name__=="__main__":main()
