"""Deterministic synthetic labelled-text extraction, not semantic validation."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

VERSION="0.2.0-alpha.1"
SPEC_HASH="8d4e730b5ed3cf38fdb4dcd896fa21bc14bf38689babc24159a460980099b00c"

def load_schema(path,spec_bytes):
    raw=Path(path).read_bytes();schema=json.loads(raw)
    if hashlib.sha256(spec_bytes).hexdigest()!=SPEC_HASH or schema.get("specSha256")!=SPEC_HASH or schema.get("version")!=VERSION:raise ValueError("Extraction specification mismatch")
    spec=json.loads(spec_bytes);actual={r["criterionId"]:r for r in schema["rules"]}
    if len(actual)!=28 or len(schema["rules"])!=28:raise ValueError("Extraction criterion count mismatch")
    for r in spec["rules"]:
        a=actual.get(r["criterionId"])
        if not a or a["ruleId"]!=r["ruleId"] or [f["sourcePhrase"] for f in a["fields"]]!=[f.strip() for f in r["fields"].split(",")] or any(a[k]!=r[k] for k in ["primary","supplementary","conditional"]):raise ValueError("Extraction schema does not match approved fields/mappings")
        labels=[f["label"].strip().casefold() for f in a["fields"]]
        if labels!=[f["sourcePhrase"].strip().casefold() for f in a["fields"]] or len({f["key"] for f in a["fields"]})!=len(labels):raise ValueError("Invalid field labels or keys")
    return actual,hashlib.sha256(raw).hexdigest()

def extract(text,rule):
    if not isinstance(text,str) or len(text)>256*1024:raise ValueError("Synthetic text limit")
    fields=rule["fields"];labels={f["label"].strip().casefold():f["key"] for f in fields};matched={f["key"]:[] for f in fields}
    for number,line in enumerate(text.splitlines(),1):
        left,colon,right=line.partition(":")
        if not colon:continue
        key=labels.get(left.strip().casefold())
        if key is None or not right.strip():continue
        value=right.strip()
        # 1-based Unicode codepoint columns in the original line; end inclusive.
        start=len(left)+1+(len(right)-len(right.lstrip()))+1
        matched[key].append({"value":value,"line":number,"startColumn":start,"endColumn":start+len(value)-1,"excerpt":line})
    records=[]
    for f in fields:
        candidates=matched[f["key"]];values={c["value"] for c in candidates}
        status="missing" if not candidates else "present" if len(values)==1 else "ambiguous"
        records.append({"key":f["key"],"label":f["label"],"status":status,"value":candidates[0]["value"] if status=="present" else None,"citations":candidates})
    return {"criterionId":rule["criterionId"],"ruleId":rule["ruleId"],"method":VERSION,"status":"draft","scoringEligible":False,"fields":records,"counts":{k:sum(x["status"]==k for x in records) for k in ("present","missing","ambiguous")}}
