"""Compare two explicit, completed independent fictional assessor records; no scores or consensus inference."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
CONDITIONS={"supported_met","supported_not_met","insufficient","contradiction","exception_pending"}
CLASSES={"E1","E2","E3","E4"}
STRENGTH={"Strong","Moderate","Weak","Not assessed"}
def compare(first,second):
    manifest=HERE/"uat-fixtures/UAT-FIXTURE-MANIFEST.json"
    source=json.loads(manifest.read_text());expected={s["criterion"]:s for s in source["sources"]};digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
    def checked(record):
        if record.get("case")!="SEVEN-DIMENSION-FICTIONAL-UAT" or record.get("manifestSha256")!=digest:raise ValueError("Identical pinned fictional case required")
        assessor=record.get("assessorRef")
        if not isinstance(assessor,str) or not assessor.strip():raise ValueError("Distinct assessor pseudonym required")
        rows=record.get("judgements")
        if not isinstance(rows,list) or len(rows)!=len(expected) or {r.get("criterion") for r in rows}!=set(expected):raise ValueError("Complete unique criterion coverage required")
        for r in rows:
            if r.get("condition") not in CONDITIONS or r.get("evidenceClass") not in CLASSES or r.get("strength") not in STRENGTH or not isinstance(r.get("rationale"),str) or not r["rationale"].strip():raise ValueError("Explicit condition, evidence class, strength and rationale required")
            refs=r.get("citationRefs")
            if not isinstance(refs,list) or any(not isinstance(x,str) or not x.strip() for x in refs) or (r["condition"].startswith("supported_") and not refs):raise ValueError("Explicit citations required for supported judgement")
            if r["condition"].startswith("supported_") and r["evidenceClass"] not in ("E1","E2"):raise ValueError("Supported judgement requires E1/E2 evidence")
        return assessor.strip(),{r["criterion"]:r for r in rows}
    a,x=checked(first);b,y=checked(second)
    if a.casefold()==b.casefold():raise ValueError("Distinct independent assessor references required")
    fields=("condition","evidenceClass","strength")
    rows=[{"criterion":q,"agreement":{k:x[q][k]==y[q][k] for k in fields},"first":x[q],"second":y[q],"citationReferenceAgreement":set(x[q]["citationRefs"])==set(y[q]["citationRefs"])} for q in expected]
    return {"scope":"Fictional local calibration comparison; independence and citation meaning need human review","caseManifestSha256":digest,"criteria":len(rows),"exactAgreementCounts":{k:sum(r["agreement"][k] for r in rows) for k in fields},"citationReferenceAgreementCount":sum(r["citationReferenceAgreement"] for r in rows),"differences":[r for r in rows if not all(r["agreement"].values()) or not r["citationReferenceAgreement"]],"consensusApproved":False,"scoringAuthorised":False}
def main():
    p=argparse.ArgumentParser(description="Compare two independently completed fictional calibration records")
    p.add_argument("first");p.add_argument("second");a=p.parse_args()
    try:print(json.dumps(compare(json.loads(Path(a.first).read_text()),json.loads(Path(a.second).read_text())),indent=2))
    except (ValueError,KeyError,TypeError,OSError):raise SystemExit("Comparison refused: complete distinct human records on the pinned fixture required") from None
if __name__=="__main__":main()
