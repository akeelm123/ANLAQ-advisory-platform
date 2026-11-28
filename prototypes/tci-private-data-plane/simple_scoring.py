"""Synthetic simplified workflow. Ranked suggestions are not validated judgement."""
from decimal import Decimal
import hashlib,re,copy
from document_parser import parse_document,MAX_FILE
from evidence_matching import terms,ranked_relevance
from scoring import weighted_dimensions

class SimpleAssessment:
    MAX_FILES=20
    MAX_FILE_BYTES=MAX_FILE
    parser=staticmethod(parse_document)
    def __init__(self,reg,spec):
        self.weights=reg["weights"]
        self.criteria=reg["criteria"]
        self.rules={r["criterionId"]:r for r in spec["rules"]}
        self.anchors={q["id"]:[a for a in reg["responseAnchors"] if a[0]==q["id"]] for q in self.criteria}
        self.catalogue={e["id"]:e for e in reg["evidenceCatalogue"]}
        self.files={};self.proposals={};self._analysis_cache=None
        if len(self.criteria)!=28 or len(self.weights)!=7 or sum(self.weights.values())!=100:raise ValueError("Invalid methodology")
        for d in self.weights:
            if sum(c["criterionWeight"] for c in self.criteria if c["dimension"]==d)!=100:raise ValueError("Invalid criterion weights")
        if any(len(a)!=5 for a in self.anchors.values()):raise ValueError("Invalid anchor register")
    def metadata(self):
        return {"weights":self.weights,"criteria":[{**c,"anchors":[{"score":a[1],"label":a[2],"description":a[5]} for a in self.anchors[c["id"]]]} for c in self.criteria],"method":"approved register baseline; ranked lexical candidate only"}
    def add(self,name,raw):
        if not isinstance(name,str) or len(name)>250 or not isinstance(raw,bytes) or not 0<len(raw)<=self.MAX_FILE_BYTES:raise ValueError("File exceeds preview limit")
        digest=hashlib.sha256(raw).hexdigest()
        if digest in self.files:return self.files[digest]["meta"]
        if len(self.files)>=self.MAX_FILES:raise ValueError(f"Maximum {self.MAX_FILES} fictional files per preview")
        parsed=self.parser(name,raw)
        meta={"name":name,"digest":digest,"segments":len(parsed["segments"]),"format":parsed["format"],"scanStatus":"not_scanned"}
        self.files[digest]={"meta":meta,"segments":parsed["segments"]};self.proposals.clear();self._analysis_cache=None
        return meta
    def analyze(self):
        if self._analysis_cache is not None:return copy.deepcopy(self._analysis_cache)
        results=[]
        indexed=[(digest,record,segment,terms(segment["text"])) for digest,record in self.files.items() for segment in record["segments"]]
        for c in self.criteria:
            q=c["id"];rule=self.rules[q]
            primary=" ".join(self.catalogue[k]["title"]+" "+self.catalogue[k]["extract"] for k in rule["primary"] if k in self.catalogue)
            query=" ".join([c["criterion"],c["question"],c["minimum"],primary,rule.get("test",""),rule.get("fields","")])
            candidates=[]
            qterms=terms(query);primary_ids=set(rule["primary"]);other_ids=set(rule.get("supplementary",[])+rule.get("conditional",[]))
            for digest,record,s,segment_terms in indexed:
                overlap=qterms&segment_terms;ordinary=len([w for w in overlap if not w.startswith("concept")]);value=ordinary*3+(len(overlap)-ordinary)*2
                tags=set(record["meta"].get("declaredRequests",[]));primary_match=bool(tags&primary_ids);other_match=bool(tags&other_ids)
                if (value>=9 and ordinary>=2) or (primary_match and value>=6 and ordinary>=1):
                    candidates.append({"digest":digest,"file":record["meta"]["name"],"locator":s["location"],"quote":s["text"][:1200],"relevance":value,"rank":value+(12 if primary_match else 4 if other_match else 0),"declaredCategory":"primary" if primary_match else "related" if other_match else None})
            candidates.sort(key=lambda x:(-x["rank"],x["digest"],x["locator"]))
            first=[];later=[];seen=set()
            for x in candidates:
                (first if x["digest"] not in seen else later).append(x);seen.add(x["digest"])
            candidates=(first+later)[:5]
            # Compare discriminating anchor vocabulary, not evidence volume or evidence class.
            vocab={a[1]:terms(a[5]) for a in self.anchors[q]}
            ranked=[]
            for a in self.anchors[q]:
                exclusive=vocab[a[1]]-set.union(*(v for n,v in vocab.items() if n!=a[1]))
                ordinary={w for w in exclusive if not w.startswith("concept")}
                best=max((len(ordinary&terms(s["quote"])) for s in candidates),default=0)
                ranked.append((best,a[1]))
            ranked.sort(reverse=True)
            suggestion=ranked[0][1] if candidates and ranked[0][0]>=3 and ranked[0][0]-ranked[1][0]>=2 else None
            results.append({"id":q,"sources":candidates,"suggested":suggestion,"status":"candidate_only" if suggestion is not None else "review_needed" if candidates else "no_evidence"})
        self._analysis_cache={"files":[f["meta"] for f in self.files.values()],"criteria":results};return copy.deepcopy(self._analysis_cache)
    def record_proposals(self,candidates,interviews,model=None,model_digest=None):
        byid={r["id"]:r for r in self.analyze()["criteria"]}
        for q,c in candidates.items():
            refs=[byid[q]["sources"][int(i)-1] for i in c.get("sourceIds",[]) if isinstance(i,str) and i.isdigit() and 1<=int(i)<=len(byid[q]["sources"])]
            self.proposals[q]={"score":c["score"],"answer":interviews[q],"status":c.get("status","test_fixture"),"rationale":c.get("rationale",""),"model":model,"modelDigest":model_digest,"sourceRefs":[{"digest":s["digest"],"locator":s["locator"],"quoteSha256":hashlib.sha256(s["quote"].encode()).hexdigest()} for s in refs]}
    def calculate(self,rows,interviews):
        if not isinstance(rows,dict) or not isinstance(interviews,dict):raise ValueError("Invalid review")
        expected={c["id"] for c in self.criteria}
        if not set(rows)<=expected or not set(interviews)<=expected:raise ValueError("Unknown criterion")
        results={r["id"]:r for r in self.analyze()["criteria"]}
        accepted={}
        for q,item in rows.items():
            if not isinstance(item,dict):raise ValueError("Invalid criterion review")
            score=item.get("score")
            if type(score) is not int or score not in range(1,6):continue
            if item.get("confirmed") is not True or item.get("conflict") is not False:continue
            if not isinstance(item.get("rationale"),str) or not item["rationale"].strip() or len(item["rationale"])>2000:continue
            if not results[q]["sources"] or (score>=4 and item.get("operating") is not True):continue
            interview=interviews.get(q)
            if not isinstance(interview,str) or not interview.strip() or len(interview)>4000:continue
            accepted[q]=score
        proposed={q:p["score"] for q,p in self.proposals.items() if p["score"] is not None and p["answer"]==interviews.get(q) and results[q]["sources"]}
        dimensions={}
        for d in self.weights:
            group=[c for c in self.criteria if c["dimension"]==d]; ids={c["id"] for c in group}
            dimensions[d]={"weight":self.weights[d],"reviewed":len(ids&accepted.keys()),"total":len(ids),"proposal":float(sum(Decimal(proposed[c["id"]])*Decimal(c["criterionWeight"])/100 for c in group)) if ids<=proposed.keys() else None,"score":float(sum(Decimal(accepted[c["id"]])*Decimal(c["criterionWeight"])/100 for c in group)) if ids<=accepted.keys() else None}
        total=weighted_dimensions({d:v["score"] for d,v in dimensions.items()},self.weights) if len(accepted)==28 else None
        suggestion=weighted_dimensions({d:v["proposal"] for d,v in dimensions.items()},self.weights) if len(proposed)==28 else None
        return {"criterionResults":[{"id":q,"reviewedScore":accepted.get(q),"candidateScore":proposed.get(q),"sourceCount":len(results[q]["sources"]),"interviewCaptured":isinstance(interviews.get(q),str) and bool(interviews[q].strip()),"materialConflict":isinstance(rows.get(q),dict) and rows[q].get("conflict") is True} for q in sorted(expected)],"unreviewedModelScore":float(suggestion) if suggestion is not None else None,"proposedCriteria":len(proposed),"reviewed":len(accepted),"totalCriteria":28,"dimensions":dimensions,"draftScore":float(total) if total is not None else None,"productionLocked":True,"independentReviewRequired":True}
