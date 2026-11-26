"""Reconcile the actual synthetic benchmark and regression records; never authorise deployment."""
from pathlib import Path
import json,re
from narrative import prepare,METHOD
ROOT=Path(__file__).resolve().parent
def check():
    fixtures=json.loads((ROOT/"narrative-fixtures.json").read_text())["fixtures"]
    bench=json.loads((ROOT/"NARRATIVE-BENCHMARK.json").read_text())["rows"]
    rows={r["id"]:r for r in bench};checks=[];coverage=[];total=matched=0;missing_controls=0;missing_pass=0;quote_count=0;digest=set()
    for f in fixtures:
        r=rows.get(f["id"],{});expected=f["expected"];total+=len(expected);x={"fixture":f["id"],"criterion":f["criterionId"],"expected":len(expected),"matched":0,"expectedMissing":len(f.get("expectedMissing",[])),"missingConfirmed":0}
        if r.get("status")!="executed":
            checks.append({"id":f["id"],"pass":False,"detail":"Model benchmark missing"});coverage.append(x);continue
        d=r["result"];digest.add(d.get("modelDigest"));fields={x["key"]:x for x in d["fields"]};_,segs=prepare(f["filename"],f["text"].encode());source={s["location"]:s["text"] for s in segs}
        valid=True
        for v in fields.values():
            for c in v["citations"]:
                quote_count+=1;raw=source.get(c["location"])
                if raw is None or c["excerpt"]!=raw or raw[c["startColumn"]-1:c["endColumn"]]!=c["value"]:valid=False
        for k,phrases in expected.items():
            field=fields.get(k,{})
            quote=" ".join(c["value"] for c in field.get("citations",[])).casefold()
            if field.get("status")=="candidate" and all(p.casefold() in quote for p in phrases):x["matched"]+=1
        for k in f.get("expectedMissing",[]):
            missing_controls+=1
            if fields.get(k,{}).get("status")=="missing":x["missingConfirmed"]+=1;missing_pass+=1
        matched+=x["matched"];coverage.append(x)
        checks.append({"id":f["id"],"pass":x["matched"]==x["expected"] and x["missingConfirmed"]==x["expectedMissing"] and valid and d.get("method")==METHOD and d.get("scoringEligible") is False and d.get("semanticReviewRequired") is True,"detail":"Expected field phrases, expected absence, exact source citations, draft gate"})
    checks.append({"id":"coverage","pass":len(fixtures)==8 and len(rows)==8 and len({f["criterionId"] for f in fixtures})==7,"detail":"8 fictional reports, 7 dimension-representative criteria"})
    checks.append({"id":"model_provenance","pass":len(digest)==1 and all(isinstance(d,str) and len(d)>10 for d in digest),"detail":"Consistent model digest"})
    test=(ROOT/"TEST-RESULTS.txt").read_text();m=re.search(r"Ran (\d+) tests",test)
    checks.append({"id":"regression","pass":bool(m and test.strip().endswith("OK")),"detail":f"{m.group(1) if m else 'unverified'} tests"})
    for name in ["BROWSER-RESULTS.txt","NARRATIVE-BROWSER-RESULTS.txt"]:
        p=ROOT/name;checks.append({"id":name,"pass":p.exists() and p.read_text().startswith("PASS:"),"detail":"Fresh synthetic browser workflow"})
    result={"version":METHOD,"gate":"engineering_acceptance_ready_for_owner_review" if all(c["pass"] for c in checks) else "blocked","benchmark":{"expected":total,"matched":matched,"expectedMissing":missing_controls,"missingConfirmed":missing_pass,"sourceCitationsVerified":quote_count,"coverage":coverage},"checks":checks,"ownerReleaseApproved":False,"productionSecurityApproved":False,"realClientDataEnabled":False,"deploymentEnabled":False,"scoringEnabled":False,"note":"Synthetic curated acceptance evidence only, not general semantic accuracy or real-client release approval."}
    (ROOT/"V02-ACCEPTANCE-RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"gate":result["gate"],"matched":matched,"expected":total,"missingConfirmed":missing_pass,"expectedMissing":missing_controls,"sourceCitationsVerified":quote_count,"failed":[c for c in checks if not c["pass"]]},indent=2))
if __name__=="__main__":check()
