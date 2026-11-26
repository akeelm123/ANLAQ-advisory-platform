"""Retest only affected criteria and revalidate all unchanged source quotes against final guard."""
import json,pathlib,os,time,argparse
from extraction import load_schema
from narrative import extract_narrative,prepare,verify_proposals,NarrativeUnavailable
HERE=pathlib.Path(__file__).parent;root=HERE.parent.parent
spec=pathlib.Path(os.environ.get("TCI_SPEC",root/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
rules,_=load_schema(HERE/"extraction-schema.json",spec.read_bytes())
fixtures=json.loads((HERE/"narrative-fixtures.json").read_text())["fixtures"]
p=argparse.ArgumentParser();p.add_argument("--input",default="NARRATIVE-BENCHMARK-expanded-initial.json");p.add_argument("--affected",default="Q08,Q17,Q23,Q13,Q26");args=p.parse_args()
initial={r["id"]:r for r in json.loads((HERE/args.input).read_text())["rows"]}
affected=set(args.affected.split(","))
rows=[]
def evaluate(f,r):
 fields={x["key"]:x for x in r["fields"]};matches=[];misses=[];unexpected=[]
 for k,phrases in f["expected"].items():
  q=fields[k];text=" ".join(c["value"] for c in q["citations"]).casefold()
  (matches if all(p.casefold() in text for p in phrases) and q["status"]=="candidate" else misses).append(k)
 for k in f.get("expectedMissing",[]):
  if fields[k]["status"]!="missing":unexpected.append(k)
 return {"expectedFields":len(f["expected"]),"matchedExpectedFields":len(matches),"missedFields":misses,"unexpectedNonMissing":unexpected}
for f in fixtures:
 old=initial[f["id"]]
 if f["criterionId"] in affected:
  try:
   start=time.monotonic();r=extract_narrative(f["filename"],f["text"].encode(),rules[f["criterionId"]]);row={"id":f["id"],"status":"executed","runStage":"targeted final candidate retest","durationSeconds":round(time.monotonic()-start,2),**evaluate(f,r),"result":r}
  except NarrativeUnavailable as e:row={"id":f["id"],"status":"blocked","reason":str(e)}
  print(f"{f['id']} retest {row.get('matchedExpectedFields','-')}/{row.get('expectedFields','-')} {row.get('unexpectedNonMissing',[])}",flush=True)
 else:
  # No field-specific prompt changes for these criteria. Re-verify saved exact candidate quotes
  # with the updated explicit-absence guard; preserve original actual model output/provenance.
  orig=old["result"];_,segs=prepare(f["filename"],f["text"].encode());sid={s["location"]:s["id"] for s in segs};proposals=[]
  for item in orig["fields"]:
   for c in item["citations"]+item.get("absenceCitations",[]):proposals.append({"fieldKey":item["key"],"segmentId":sid[c["location"]],"quote":c["value"]})
  verified=verify_proposals(rules[f["criterionId"]],segs,{"proposals":proposals})
  r={**orig,"fields":verified["fields"],"counts":verified["counts"],"postGuardRejectedProposals":verified["rejectedProposals"]}
  row={**old,"runStage":old.get("runStage","initial actual model output")+"; reverified with final guard",**evaluate(f,r),"result":r}
 rows.append(row)
 (HERE/"NARRATIVE-BENCHMARK-expanded.json").write_text(json.dumps({"scope":"Fictional 32-report suite; initial actual model outputs preserved, affected criteria retested and unchanged quotes reverified","rows":rows},ensure_ascii=False,indent=2)+"\n")
