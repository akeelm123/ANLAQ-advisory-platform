"""Synthetic human-owned executive decision brief, independent review and freshness controls."""
from hashlib import sha256
import json
from uuid import uuid4

METHOD="0.6.0-alpha.1"
DIRECTIONS=("Invest","Correct","Reset","Stop","Reassess")
SUPPORTED={"supported_met","supported_not_met"}

class ExecutiveWorkflow:
    def __init__(self,dp,invalid,denied,required):
        self.dp=dp;self.db=dp.db;self.Invalid=invalid;self.Denied=denied;self.required=required
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS executive_briefs(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),author TEXT NOT NULL REFERENCES users(id),snapshot_hash TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS executive_reviews(id TEXT PRIMARY KEY,brief_id TEXT UNIQUE NOT NULL REFERENCES executive_briefs(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS executive_directions(id TEXT PRIMARY KEY,brief_id TEXT UNIQUE NOT NULL REFERENCES executive_briefs(id),owner TEXT NOT NULL REFERENCES users(id),payload TEXT NOT NULL,created_at REAL NOT NULL);
        """)
        for table in ("executive_briefs","executive_reviews","executive_directions"):
            self.db.executescript(f"CREATE TRIGGER IF NOT EXISTS {table}_immutable_update BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT,'immutable executive record'); END; CREATE TRIGGER IF NOT EXISTS {table}_immutable_delete BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT,'immutable executive record'); END;")
    def snapshot(self,token,aid):
        self.dp._actor(token,aid,{"assessor","reviewer","owner"})
        v=self.dp.validation.view(token,aid); latest={d["criterion"]:d for d in v["drafts"]}
        criteria=[]
        for rule in v["rules"]:
            q=rule["criterionId"];d=latest.get(q);state=d["state"]["state"] if d else "insufficient"
            criteria.append({"criterion":q,"dimension":rule["dimension"],"label":rule["criterion"],"validationId":d["id"] if d else None,"state":state,"reason":d["state"]["reason"] if d else "No criterion validation draft",
                "finding":d["payload"]["claim"] if d else None,"rationale":d["payload"]["rationale"] if d else None,"owner":d["payload"]["owner"] if d else None,"followUp":d["payload"]["followUp"] if d else rule["followUp"],"evidenceClass":d["payload"]["evidenceClass"] if d else None,"strength":d["payload"]["strength"] if d else None,"refs":d["payload"]["refs"] if d else [],"review":d["review"] if d else None,
                "primary":rule["primary"],"conditional":rule["conditional"]})
        # Include current source history, request updates and reconciliation records in freshness checks.
        latest_versions={}
        for source in self.dp.list_versions(token,aid):
            if source["documentId"] not in latest_versions or source["version"]>latest_versions[source["documentId"]]["version"]:
                latest_versions[source["documentId"]]={k:source[k] for k in ("documentId","versionId","version","status","sha256","requestId")}
        requests=self.dp.catalogue_view(token,aid)["requests"]
        for request in requests:
            update=self.db.execute("SELECT id,reason FROM request_updates WHERE assessment_id=? AND request_id=? ORDER BY id DESC LIMIT 1",(aid,request["id"])).fetchone()
            request["lastUpdate"]=dict(update) if update else None
        interview=self.dp.interviews.view(token,aid)
        claims={c["id"]:c for c in interview["claims"]}
        interview_conflicts={c["id"]:c for c in interview["conflicts"]}
        conflicts=[]
        for conflict in v["conflicts"]:
            origin=interview_conflicts[conflict["id"]]
            accounts=[{k:claims[id][k] for k in ("id","persona","verbatim","interpretation","responseStatus","claimClass","links")} for id in (origin["claimA"],origin["claimB"])]
            conflicts.append({**conflict,"topic":origin["topic"],"accounts":accounts})
        supported=[c for c in criteria if c["state"] in SUPPORTED]
        complete=len(supported)==len(criteria) and not any(c["material"] and c["status"]!="resolved" for c in conflicts)
        result={"registerHash":self.dp.register_hash,"specHash":self.dp.spec_hash,"criteria":criteria,"requests":requests,"conflicts":conflicts,"sources":sorted(latest_versions.values(),key=lambda v:v["documentId"]),"supportedCount":len(supported),"complete":complete}
        return result,sha256(json.dumps(result,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
    def draft(self,token,aid,body):
        with self.db:
            a=self.dp._actor(token,aid,{"assessor"})
            if not isinstance(body,dict):raise self.Invalid("Structured executive brief required")
            snap,h=self.snapshot(token,aid)
            links=body.get("findingIds")
            if not isinstance(links,list) or any(not isinstance(x,str) for x in links) or len(links)!=len(set(links)):raise self.Invalid("Unique supported finding references required")
            supported={c["validationId"] for c in snap["criteria"] if c["state"] in SUPPORTED}
            if not set(links)<=supported:raise self.Invalid("Link only current independently supported findings")
            if supported and not links:raise self.Invalid("At least one current supported finding must be linked")
            options=body.get("options");actions=body.get("actions")
            if not isinstance(options,list) or not 2<=len(options)<=5:raise self.Invalid("At least two distinct human-authored decision options required")
            if not isinstance(actions,list) or not 1<=len(actions)<=28:raise self.Invalid("Explicit material condition, owner and follow-up required")
            choices=[]
            for o in options:
                if not isinstance(o,dict) or o.get("direction") not in DIRECTIONS or o["direction"] in [x["direction"] for x in choices]:raise self.Invalid("Distinct approved decision directions required")
                choices.append({"direction":o["direction"],"rationale":self.required(o.get("rationale"),"option rationale"),"consequences":self.required(o.get("consequences"),"option consequences")})
            obligations=[]
            for o in actions:
                if not isinstance(o,dict):raise self.Invalid("Structured action required")
                obligations.append({k:self.required(o.get(k),k) for k in ("condition","owner","followUp")})
            p={"title":self.required(body.get("title"),"brief title"),"summary":self.required(body.get("summary"),"human executive synthesis"),"limitations":self.required(body.get("limitations"),"limitations and residual uncertainty"),"findingIds":links,"options":choices,"actions":obligations,"snapshot":snap}
            id=uuid4().hex;self.db.execute("INSERT INTO executive_briefs VALUES (?,?,?,?,?,?)",(id,aid,a["id"],h,self.dp.validation._seal(id,p),self.dp.clock()))
            self.dp._audit(aid,a["id"],"executive brief drafted",id);return id
    def _brief(self,aid,id):
        r=self.db.execute("SELECT * FROM executive_briefs WHERE id=? AND assessment_id=?",(id,aid)).fetchone()
        if not r:raise self.Denied("Access denied")
        return r,self.dp.validation._open(id,r["payload"])
    def _latest(self,aid,id):
        r=self.db.execute("SELECT id FROM executive_briefs WHERE assessment_id=? ORDER BY created_at DESC,rowid DESC LIMIT 1",(aid,)).fetchone()
        return bool(r and r["id"]==id)
    def review(self,token,aid,id,decision,reason,confirmed):
        with self.db:
            a=self.dp._actor(token,aid,{"reviewer"});r,p=self._brief(aid,id)
            if a["id"]==r["author"]:raise self.Denied("Independent reviewer required")
            if decision not in ("accept","return") or self.db.execute("SELECT 1 FROM executive_reviews WHERE brief_id=?",(id,)).fetchone():raise self.Invalid("Invalid or duplicate executive review")
            if decision=="accept":
                snap,h=self.snapshot(token,aid)
                if h!=r["snapshot_hash"] or not self._latest(aid,id):raise self.Invalid("Brief superseded; draft against current evidence")
                if confirmed is not True:raise self.Invalid("Explicit review of conclusions, all current findings and residual gaps required")
                refs=[ref for c in snap["criteria"] if c["state"] in SUPPORTED for ref in c["refs"]]
                # A reconciliation may rely on evidence not cited by the final validation finding.
                refs.extend(ref for c in snap["conflicts"] if c["status"]=="resolved" for ref in c["resolutions"][-1]["refs"])
                if not self.dp.validation._previewed(a,aid,refs):raise self.Invalid("Reviewer must preview every current supported and reconciliation source")
            rid=uuid4().hex;self.db.execute("INSERT INTO executive_reviews VALUES (?,?,?,?,?,?)",(rid,id,a["id"],decision,self.dp.validation._seal(rid,{"reason":self.required(reason,"independent review rationale"),"confirmed":confirmed is True}),self.dp.clock()))
            self.dp._audit(aid,a["id"],"executive brief "+decision,rid);return rid
    def direction(self,token,aid,id,direction,reason,conditions,confirmed):
        with self.db:
            a=self.dp._actor(token,aid,{"owner"});r,p=self._brief(aid,id)
            review=self.db.execute("SELECT * FROM executive_reviews WHERE brief_id=?",(id,)).fetchone()
            snap,h=self.snapshot(token,aid)
            if not review or review["decision"]!="accept" or h!=r["snapshot_hash"] or not self._latest(aid,id):raise self.Invalid("Current independently reviewed executive brief required")
            if direction not in [o["direction"] for o in p["options"]]:raise self.Invalid("Choose explicitly from reviewed options")
            if not snap["complete"] and direction!="Reassess":raise self.Invalid("Incomplete or contradictory support: only Reassess may be recorded pending closure")
            if confirmed is not True or self.db.execute("SELECT 1 FROM executive_directions WHERE brief_id=?",(id,)).fetchone():raise self.Invalid("Explicit human direction and unique record required")
            rid=uuid4().hex;self.db.execute("INSERT INTO executive_directions VALUES (?,?,?,?,?)",(rid,id,a["id"],self.dp.validation._seal(rid,{"direction":direction,"reason":self.required(reason,"owner decision rationale"),"conditions":self.required(conditions,"residual conditions"),"confirmed":True}),self.dp.clock()))
            self.dp._audit(aid,a["id"],"synthetic owner direction recorded",rid);return rid
    def view(self,token,aid):
        snap,h=self.snapshot(token,aid);items=[]
        for r in self.db.execute("SELECT * FROM executive_briefs WHERE assessment_id=? ORDER BY created_at,rowid",(aid,)):
            p=self.dp.validation._open(r["id"],r["payload"])
            rev=self.db.execute("SELECT * FROM executive_reviews WHERE brief_id=?",(r["id"],)).fetchone()
            dire=self.db.execute("SELECT * FROM executive_directions WHERE brief_id=?",(r["id"],)).fetchone()
            current=h==r["snapshot_hash"] and self._latest(aid,r["id"])
            state="superseded" if not current else ("review_pending" if not rev else ("returned" if rev["decision"]=="return" else ("reviewed_complete" if snap["complete"] else "reviewed_with_gaps")))
            items.append({"id":r["id"],"snapshotHash":r["snapshot_hash"],"state":state,"payload":p,"review":{**self.dp.validation._open(rev["id"],rev["payload"]),"decision":rev["decision"]} if rev else None,"direction":self.dp.validation._open(dire["id"],dire["payload"]) if dire else None,"directionCurrent":bool(dire and current and state.startswith("reviewed_"))})
        return {"method":METHOD,"snapshot":snap,"snapshotHash":h,"briefs":items,"productionLocked":True,"automaticDecision":False}
