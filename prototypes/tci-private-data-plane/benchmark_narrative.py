"""Run local model on fictional reports only. No credentials or client data."""
import json,pathlib,os,sys,time
from extraction import load_schema
from narrative import extract_narrative,NarrativeUnavailable
HERE=pathlib.Path(__file__).parent;root=HERE.parent.parent
spec=pathlib.Path(os.environ.get("TCI_SPEC",root/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
rules,_=load_schema(HERE/"extraction-schema.json",spec.read_bytes())
fixtures=json.loads((HERE/"narrative-fixtures.json").read_text())["fixtures"]
rows=[]
for f in fixtures:
 try:
  start=time.monotonic();r=extract_narrative(f["filename"],f["text"].encode(),rules[f["criterionId"]]);fields={x["key"]:x for x in r["fields"]}
  matches=[];misses=[];unexpected=[]
  for k,phrases in f["expected"].items():
   q=fields[k];text=" ".join(c["value"] for c in q["citations"]).casefold()
   (matches if all(p.casefold() in text for p in phrases) and q["status"]=="candidate" else misses).append(k)
  for k in f.get("expectedMissing",[]):
   if fields[k]["status"]!="missing":unexpected.append(k)
  row={"id":f["id"],"status":"executed","durationSeconds":round(time.monotonic()-start,2),"expectedFields":len(f["expected"]),"matchedExpectedFields":len(matches),"missedFields":misses,"unexpectedNonMissing":unexpected,"result":r}
 except NarrativeUnavailable as e:row={"id":f["id"],"status":"blocked","reason":str(e)}
 rows.append(row);print(f"{f['id']} {row['status']} {row.get('matchedExpectedFields','-')}/{row.get('expectedFields','-')} expected fields; {row.get('durationSeconds','-')}s",flush=True)
 (HERE/"NARRATIVE-BENCHMARK.json").write_text(json.dumps({"scope":"Fictional local-model benchmark only; field attribution and completeness are not established by exact quotes","rows":rows},ensure_ascii=False,indent=2)+"\n")
