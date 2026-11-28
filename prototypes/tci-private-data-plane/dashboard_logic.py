"""Executive dashboard for fictional assessment: guided intake, evidence-first action suggestions."""
from decimal import Decimal
import base64,hashlib,json,time,uuid
from simple_scoring import SimpleAssessment
from scoring import weighted_dimensions
from dashboard_parser import parse_dashboard_document,MAX_DASHBOARD_FILE
from dashboard_classification import suggest_categories,build_index

class DashboardAssessment(SimpleAssessment):
    MAX_FILES=64
    MAX_FILE_BYTES=MAX_DASHBOARD_FILE
    parser=staticmethod(parse_dashboard_document)
    MAX_TOTAL_BYTES=8*1024*1024
    def __init__(self,reg,spec):
        super().__init__(reg,spec)
        self.category_index=build_index(self.catalogue,self.rules)
        self.raw_files={};self.workspace={"answers":{},"reviews":{},"edits":{},"title":"Executive Confidence Snapshot","persona":"Canonical TCI","target":None};self.snapshots=[]
        self.lenses={name:{r[0]:float(Decimal(str(r[i]))*100) for r in reg["personaWeights"]} for i,name in enumerate(["Board","CIO","Chief Platform Officer","Transformation Office"],1)}
        if any(sum(v.values())!=100 for v in self.lenses.values()):raise ValueError("Invalid persona weights")
    def metadata(self):
        base=super().metadata()
        return {**base,"documentGuide":list(self.catalogue.values()),"personaWeights":self.lenses,"maxFiles":self.MAX_FILES,"maxFileBytes":self.MAX_FILE_BYTES,"maxTotalBytes":self.MAX_TOTAL_BYTES,"methodologyVersion":"v1.0-reconstructed-rc.1"}
    def add(self,name,raw,request_id=None):
        if request_id not in (None,"") and request_id not in self.catalogue:raise ValueError("Unknown recommended document category")
        digest=hashlib.sha256(raw).hexdigest()
        if digest not in self.raw_files and sum(len(v) for v in self.raw_files.values())+len(raw)>self.MAX_TOTAL_BYTES:raise ValueError("Fictional workspace aggregate limit is 8 MiB")
        new=digest not in self.raw_files
        meta=super().add(name,raw)
        self.raw_files[digest]=raw
        if new:
            self.workspace["reviews"]={};self.workspace["edits"]={};meta["suggestedRequests"]=suggest_categories(self.catalogue,self.files[digest]["segments"],self.category_index)
        meta.setdefault("declaredRequests",[])
        if request_id:self.tag(digest,request_id)
        return meta
    def tag(self,digest,request_id):
        if request_id not in self.catalogue or digest not in self.files:raise ValueError("Unknown document or recommended category")
        meta=self.files[digest]["meta"];meta.setdefault("declaredRequests",[])
        if request_id not in meta["declaredRequests"]:
            meta["declaredRequests"].append(request_id);self._analysis_cache=None;self.proposals.clear();self.workspace["reviews"]={};self.workspace["edits"]={}
        return meta
    def analyze(self):
        r=super().analyze()
        declared={k for f in r["files"] for k in f.get("declaredRequests",[])}
        r["guide"]=[{"id":e["id"],"declared":e["id"] in declared} for e in self.catalogue.values()]
        return r
    def calculate(self,rows,interviews):
        if not isinstance(rows,dict):raise ValueError("Invalid review")
        byid={r["id"]:r for r in self.analyze()["criteria"]}
        eligible={}
        for q,row in rows.items():
            if q not in byid or not isinstance(row,dict):raise ValueError("Invalid criterion review")
            refs=row.get("sourceIds",[])
            if isinstance(refs,list) and refs and len(set(refs))==len(refs) and all(isinstance(i,str) and i.isdigit() and 1<=int(i)<=len(byid[q]["sources"]) for i in refs):eligible[q]=row
        r=super().calculate(eligible,interviews)
        for criterion in r["criterionResults"]:
            q=criterion["id"];criterion["proposalStatus"]=self.proposals.get(q,{}).get("status") if self.proposals.get(q,{}).get("answer")==interviews.get(q) else None;criterion["sourceRefs"]=self.proposals.get(q,{}).get("sourceRefs",[]) if criterion["proposalStatus"] else []
            if criterion["reviewedScore"] is not None:
                refs=[byid[q]["sources"][int(i)-1] for i in eligible[q]["sourceIds"]];criterion["sourceRefs"]=[{"digest":s["digest"],"locator":s["locator"],"quoteSha256":hashlib.sha256(s["quote"].encode()).hexdigest()} for s in refs]
        r["personaScores"]={}
        for name,w in self.lenses.items():
            for field in ("score","proposal"):
                values={d:v[field] for d,v in r["dimensions"].items()}
                r["personaScores"].setdefault(name,{})[field]=float(weighted_dimensions(values,w)) if all(v is not None for v in values.values()) else None
        r["actionPlan"]=self.plan(r["criterionResults"])
        return r
    def load_example(self,fixtures):
        if self.files or self.workspace["answers"] or self.snapshots:raise ValueError("Example requires an empty workspace; existing work is not overwritten")
        seen=set()
        for f in fixtures:
            q=f["criterionId"]
            if q in seen:continue
            seen.add(q);self.add(f["filename"],f["text"].encode(),f["requestId"])
        if len(seen)!=28:raise ValueError("Incomplete fictional example")
        self.workspace["answers"]={q:"Fictional sample response: assess the supplied documentary record; no additional independent corroboration is provided." for q in seen}
        self.workspace["title"]="Fictional narrative UAT example"
        return {"analysis":self.analyze(),"workspace":self.workspace_view()}
    def source(self,digest):
        if digest not in self.raw_files or hashlib.sha256(self.raw_files[digest]).hexdigest()!=digest:raise ValueError("Unknown or changed source")
        return {"digest":digest,"name":self.files[digest]["meta"]["name"],"segments":self.files[digest]["segments"]}
    def workspace_view(self):
        return {**self.workspace,"snapshots":[{k:s[k] for k in ("id","title","date","lens","score","status")} for s in self.snapshots]}
    def save_workspace(self,data):
        if not isinstance(data,dict) or not {"answers","reviews","edits","title","persona"}<=set(data) or not set(data)<={"answers","reviews","edits","title","persona","target"}:raise ValueError("Invalid workspace")
        data={**data,"target":data.get("target")};target=data["target"]
        if target is not None and (type(target) is not int or target not in range(1,6)):raise ValueError("Invalid optional target")
        answers,reviews,edits=data["answers"],data["reviews"],data["edits"]
        ids={c["id"] for c in self.criteria}
        if not isinstance(answers,dict) or not isinstance(reviews,dict) or not isinstance(edits,dict) or not set(answers)<=ids or not set(reviews)<=ids:raise ValueError("Invalid workspace criteria")
        if any(not isinstance(v,str) or len(v)>4000 for v in answers.values()):raise ValueError("Invalid interview response")
        for v in reviews.values():
            if not isinstance(v,dict) or not set(v)<={"score","confirmed","conflict","operating","rationale","sourceIds","model","candidateStatus"}:raise ValueError("Invalid review draft")
            if v.get("score") is not None and (type(v["score"]) is not int or v["score"] not in range(1,6)):raise ValueError("Invalid anchor")
            if any(type(v.get(k,False)) is not bool for k in ("confirmed","conflict","operating")) or not isinstance(v.get("rationale",""),str) or len(v.get("rationale",""))>2000:raise ValueError("Invalid review draft")
            if "sourceIds" in v and (not isinstance(v["sourceIds"],list) or len(v["sourceIds"])>5 or any(x not in ("1","2","3","4","5") for x in v["sourceIds"])):raise ValueError("Invalid source references")
            if "model" in v and (not isinstance(v["model"],str) or len(v["model"])>100):raise ValueError("Invalid model label")
            if "candidateStatus" in v and v["candidateStatus"] not in ("model_candidate","model_withheld","model_unavailable","conflict_review_required","operating_evidence_review_required"):raise ValueError("Invalid candidate status")
        result=self.calculate(reviews,answers);valid={x["id"] for x in result["actionPlan"]}
        if not set(edits)<=valid:raise ValueError("Action edits are stale; regenerate from current assessment")
        for v in edits.values():
            if not isinstance(v,dict) or set(v)!={"owner","action","success"} or any(not isinstance(x,str) or len(x)>4000 for x in v.values()) or len(v["owner"])>140:raise ValueError("Invalid action edit")
        if not isinstance(data["title"],str) or len(data["title"])>100 or data["persona"] not in {"Canonical TCI",*self.lenses}:raise ValueError("Invalid assessment metadata")
        self.workspace=json.loads(json.dumps(data))
        return self.workspace_view()
    def current_plan(self,result):
        return [{**a,**self.workspace["edits"].get(a["id"],{}),"status":"Edited proposal" if a["id"] in self.workspace["edits"] else "Proposed"} for a in result["actionPlan"]]
    def snapshot(self):
        if len(self.snapshots)>=20:raise ValueError("Maximum 20 fictional snapshots per workspace")
        w=self.workspace;title=w["title"].strip()
        if not title:raise ValueError("Assessment title required")
        r=self.calculate(w["reviews"],w["answers"]);lens=w["persona"]
        score=r["draftScore"] if lens=="Canonical TCI" else r["personaScores"][lens]["score"]
        candidate=r["unreviewedModelScore"] if lens=="Canonical TCI" else r["personaScores"][lens]["proposal"]
        status="Reviewed fictional draft" if score is not None else "Unreviewed AI candidate" if candidate is not None else "Incomplete"
        snap={"id":uuid.uuid4().hex,"title":title,"date":time.strftime("%Y-%m-%d %H:%M:%S UTC",time.gmtime()),"lens":lens,"score":score if score is not None else candidate,"status":status,"target":w.get("target"),"result":r,"actions":self.current_plan(r),"inputDigests":list(self.raw_files)}
        self.snapshots.append(snap)
        return self.workspace_view()
    def snapshot_detail(self,id):
        for snap in self.snapshots:
            if snap["id"]==id:return json.loads(json.dumps(snap))
        raise ValueError("Unknown saved snapshot")
    def export_state(self):
        return {"format":1,"documents":[{"digest":d,"name":self.files[d]["meta"]["name"],"raw":base64.b64encode(raw).decode(),"requests":self.files[d]["meta"].get("declaredRequests",[])} for d,raw in self.raw_files.items()],"workspace":self.workspace,"proposals":self.proposals,"snapshots":self.snapshots}
    def restore_state(self,state):
        if state.get("format")!=1 or self.files:raise ValueError("Invalid or nonempty workspace restore")
        for f in state["documents"]:
            raw=base64.b64decode(f["raw"],validate=True)
            if hashlib.sha256(raw).hexdigest()!=f["digest"]:raise ValueError("Source digest mismatch")
            self.add(f["name"],raw)
            for req in f["requests"]:self.add(f["name"],raw,req)
        self.proposals=state["proposals"];self.save_workspace(state["workspace"]);self.snapshots=state["snapshots"]
    def plan(self,results):
        byid={r["id"]:r for r in results};actions=[]
        for d in self.weights:
            group=[c for c in self.criteria if c["dimension"]==d]
            gaps=[];weak=[];tentative=[];strong=[]
            for c in group:
                q=c["id"];r=byid[q];reviewed=r["reviewedScore"];candidate=r["candidateScore"]
                if reviewed is not None:
                    if reviewed<=2:weak.append((c,reviewed))
                    elif reviewed==3:weak.append((c,reviewed))
                    else:strong.append((c,reviewed))
                else:
                    gaps.append(c)
                    if candidate is not None and candidate<=3:tentative.append((c,candidate))
            if gaps:
                gaps.sort(key=lambda c:(byid[c["id"]].get("proposalStatus")!="conflict_review_required",-c["criterionWeight"]));ids=[c["id"] for c in gaps]; requests=list(dict.fromkeys(k for c in gaps for k in self.rules[c["id"]]["primary"]))
                titles=[self.catalogue[k]["title"] for k in requests if k in self.catalogue]
                desc="Obtain or verify the primary documents and stakeholder responses for "+", ".join(c["criterion"] for c in gaps)+". Recommended sources: "+"; ".join(titles)+". Resolve material contradictions and review exact citations before confirming scores."
                if tentative:desc+=" Investigate tentative lower anchors for "+", ".join(c["criterion"] for c,s in tentative)+"; these are not confirmed deficiencies."
                discrepancies=[c["criterion"] for c in gaps if byid[c["id"]].get("proposalStatus")=="conflict_review_required"]
                if discrepancies:desc+=" Check measurement basis and potential interview/document discrepancies or documentary conflicts for "+", ".join(discrepancies)+"."
                operating=[c["criterion"] for c in gaps if byid[c["id"]].get("proposalStatus")=="operating_evidence_review_required"]
                if operating:desc+=" Obtain comparable operating evidence across periods for "+", ".join(operating)+"."
                actions.append({"id":d+"-30","horizon":30,"dimension":d,"type":"Evidence verification","priority":"Review first","owner":gaps[0]["stakeholder"],"criteria":ids,"requests":requests,"action":desc,"success":f"{len(gaps)} of {len(gaps)} listed criteria have current evidence and interview context reviewed, with a documented disposition, owner and follow-up for each.","basis":"Unreviewed / incomplete criteria","status":"Proposed"})
            if weak or tentative:
                weak.sort(key=lambda x:(x[1],-x[0]["criterionWeight"]));tentative.sort(key=lambda x:(x[1],-x[0]["criterionWeight"]))
                combined=weak+tentative;ids=[c["id"] for c,s in combined];details=[]
                for c,s in weak:
                    anchor=next(a for a in self.anchors[c["id"]] if a[1]==s)
                    details.append(c["criterion"]+" ("+str(s)+"/5): "+anchor[6]+" "+self.rules[c["id"]]["followUp"])
                for c,s in tentative:
                    anchor=next(a for a in self.anchors[c["id"]] if a[1]==s)
                    details.append(c["criterion"]+" (unreviewed candidate "+str(s)+"/5): if independently verified, "+anchor[6]+" "+self.rules[c["id"]]["followUp"])
                both=bool(weak and tentative)
                basis="Reviewed fictional anchors plus conditional AI candidates" if both else "Reviewed fictional performance anchors; subject to independent acceptance" if weak else "Conditional unreviewed AI anchor; do not treat as confirmed deficiency"
                actions.append({"id":d+"-90","horizon":90,"dimension":d,"type":"Remediation / improvement" if weak else "Conditional improvement","priority":"High" if weak and weak[0][1]<=2 else "Medium" if weak else "Review first","owner":combined[0][0]["stakeholder"],"criteria":ids,"requests":list(dict.fromkeys(k for c,s in combined for k in self.rules[c["id"]]["primary"])),"action":"; ".join(details),"success":f"For all {len(combined)} listed criteria, confirm the baseline, agree a measurable improvement outcome, attach updated evidence and record residual gaps; conditional actions start only after verification.","basis":basis,"status":"Proposed"})
            if weak or gaps or strong:
                actions.append({"id":d+"-180","horizon":180,"dimension":d,"type":"Reassessment","priority":"Follow-up","owner":group[0]["stakeholder"],"criteria":[c["id"] for c in group],"requests":[],"action":"Reassess "+d+" against the same four criteria and comparable measurement basis; verify closure of agreed actions and sustained operating evidence. If no approved baseline exists, establish one first.","success":"Four of four dimension criteria reassessed on the same basis, with independently reviewed follow-up evidence and action closure or escalation.","basis":"Proposed follow-up, not an approved commitment","status":"Proposed"})
        weights=self.weights;criteria={c["id"]:c for c in self.criteria}
        for a in actions:
            share=sum(Decimal(str(weights[criteria[q]["dimension"]]))*Decimal(str(criteria[q]["criterionWeight"]))/100 for q in a["criteria"])
            a["weightedScope"]=float(share)
            conflicts=sum(byid[q].get("proposalStatus")=="conflict_review_required" for q in a["criteria"])
            a["priorityReason"]=f"{float(share):.2f}% of canonical criterion weight in scope"+(f"; {conflicts} possible evidence discrepancies to review first" if conflicts else "")
            a["dependency"]="Resolve evidence and interview gaps first" if a["horizon"]==90 else "Establish reviewed baseline and agreed improvement actions" if a["horizon"]==180 else "Confirm source relevance and responsible role"
            a["evidenceLinks"]=[{"criterion":q,**ref} for q in a["criteria"] for ref in byid[q].get("sourceRefs",[])][:20]
        return sorted(actions,key=lambda a:(a["horizon"],0 if a["horizon"]==30 and any(byid[q].get("proposalStatus")=="conflict_review_required" for q in a["criteria"]) else 1,{"High":0,"Medium":1,"Review first":2,"Follow-up":3}[a["priority"]],-a["weightedScope"],a["dimension"]))

