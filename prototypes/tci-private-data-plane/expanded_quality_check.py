"""Recompute expanded benchmark evidence independently, including absence citations."""
import json,pathlib
from narrative import prepare,METHOD
ROOT=pathlib.Path(__file__).resolve().parent
schema=json.loads((ROOT/"extraction-schema.json").read_text())["rules"]
base=json.loads((ROOT/"narrative-fixtures-rc1.json").read_text())["fixtures"];prior={x["id"] for x in base}
fixtures=json.loads((ROOT/"narrative-fixtures.json").read_text())["fixtures"]
rows={r["id"]:r for r in json.loads((ROOT/"NARRATIVE-BENCHMARK-expanded.json").read_text())["rows"]}
dims=["Strategic Alignment","Leadership Commitment","Technology Readiness","People & Culture","Data & AI Confidence","Delivery Excellence","Business Value Realisation"]
dimension=lambda cid:dims[(int(cid[1:])-1)//4]
grouped={d:{"reports":0,"expected":0,"matched":0,"missingExpected":0,"missingConfirmed":0} for d in dims}
out=[];total=matched=absence=absence_ok=citations=bad_citations=0;old_expected=old_matched=0;digests=set()
for f in fixtures:
 expected=f["expected"];x={"id":f["id"],"criterion":f["criterionId"],"dimension":dimension(f["criterionId"]),"expected":len(expected),"matched":0,"missingExpected":len(f.get("expectedMissing",[])),"missingConfirmed":0,"missed":[],"unexpectedNonMissing":[]}
 total+=x["expected"];absence+=x["missingExpected"];r=rows.get(f["id"],{})
 if r.get("status")=="executed":
  result=r["result"];digests.add(result["modelDigest"]);fields={a["key"]:a for a in result["fields"]};_,segments=prepare(f["filename"],f["text"].encode());source={s["location"]:s["text"] for s in segments}
  for a in fields.values():
   for c in a["citations"]+a.get("absenceCitations",[]):
    citations+=1;t=source.get(c["location"])
    if t is None or c["excerpt"]!=t or t[c["startColumn"]-1:c["endColumn"]]!=c["value"]:bad_citations+=1
  for k,values in expected.items():
   a=fields[k];text=" ".join(c["value"] for c in a["citations"]).casefold()
   if a["status"]=="candidate" and all(v.casefold() in text for v in values):x["matched"]+=1
   else:x["missed"].append(k)
  for k in f.get("expectedMissing",[]):
   if fields[k]["status"]=="missing":x["missingConfirmed"]+=1
   else:x["unexpectedNonMissing"].append(k)
  x["method"]=result["method"];x["scoringEligible"]=result["scoringEligible"]
 else:x["status"]="blocked or unfinished";x["missed"]=list(expected)
 matched+=x["matched"];absence_ok+=x["missingConfirmed"]
 if f["id"] in prior:old_expected+=x["expected"];old_matched+=x["matched"]
 z=grouped[x["dimension"]];z["reports"]+=1
 for k in ("expected","matched","missingExpected","missingConfirmed"):z[k]+=x[k]
 out.append(x)
data={"version":METHOD,"reports":len(fixtures),"executed":sum(r.get("status")=="executed" for r in rows.values()),"criteria":len({f["criterionId"] for f in fixtures}),"dimensions":grouped,"expected":total,"matched":matched,"expectedMissing":absence,"confirmedMissing":absence_ok,"sourceCitationsChecked":citations,"invalidCitations":bad_citations,"modelDigests":sorted(digests),"priorFixtureRegression":{"expected":old_expected,"matched":old_matched},"rows":out,"generalAccuracyClaim":False,"ownerApproval":False,"v03Implemented":False}
(ROOT/"EXPANDED-QUALITY-RESULT.json").write_text(json.dumps(data,indent=2)+"\n")
print(json.dumps({k:v for k,v in data.items() if k!="rows"},indent=2))
